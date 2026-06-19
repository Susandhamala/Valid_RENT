"""
Rental request workflow:
  tenant creates → landlord reviews → both chat/negotiate →
  landlord approves terms → tenant approves terms →
  system generates bilingual draft → both capture photos →
  both sign digitally → PDF auto-generated.
"""
import os
import uuid
import hashlib
from datetime import datetime, date as date_type
from pathlib import Path
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, jsonify)
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.asset import RentalAsset, AssetCategory
from app.models.request import AgreementRequest, PartyApproval
from app.models.chat import ChatThread, ChatMessage
from app.models.agreement import RentalAgreement
from app.models.certificate import Certificate
from app.models.photo import IdentityPhoto
from app.models.pdf import GeneratedPDF
from app.services.chat_service import generate_thread_key, encrypt_message
from app.services.legal_service import generate_bilingual_document
from app.services.crypto_service import (
    sha256_hash_bytes, encrypt_file_aes256gcm, encrypt_rsa_oaep,
    rsa_sign, rsa_verify
)
from app.services.qr_service import generate_verification_code

req_bp = Blueprint('req', __name__, url_prefix='/requests')


# ── HELPERS ────────────────────────────────────────────────────────────────

def _post_system_message(thread, text: str):
    """Post an encrypted system notification into a chat thread."""
    ct, nonce, h = encrypt_message(thread.encrypted_thread_key, text)
    msg = ChatMessage(thread_id=thread.id, sender_id=1,   # system user id=1 or first landlord
                      ciphertext_b64=ct, nonce_b64=nonce,
                      message_hash=h, is_system=True)
    db.session.add(msg)


def _get_or_create_thread(req_obj):
    if req_obj.chat_thread:
        return req_obj.chat_thread
    thread_key = generate_thread_key()
    thread = ChatThread(request_id=req_obj.id, encrypted_thread_key=thread_key)
    db.session.add(thread)
    db.session.flush()
    return thread


def _approval_for(req_id, user_id, stage):
    return PartyApproval.query.filter_by(
        request_id=req_id, user_id=user_id, stage=stage).first()


def _both_approved(req_obj, stage):
    l_ok = PartyApproval.query.filter_by(
        request_id=req_obj.id, stage=stage, approved=True,
        role='landlord').first()
    t_ok = PartyApproval.query.filter_by(
        request_id=req_obj.id, stage=stage, approved=True,
        role='tenant').first()
    return bool(l_ok and t_ok)


# ── TENANT: CREATE REQUEST ─────────────────────────────────────────────────

@req_bp.route('/new/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def create_request(asset_id):
    if not current_user.has_role('tenant'):
        flash('Only tenants can create rental requests. Add the Tenant role from your dashboard.', 'error')
        return redirect(url_for('dashboard.home'))

    asset = RentalAsset.query.get_or_404(asset_id)
    if asset.owner_id == current_user.id:
        flash('You cannot request your own listing.', 'error')
        return redirect(url_for('asset.view_asset', asset_id=asset_id))
    if asset.status != 'available':
        flash('This asset is not currently available.', 'error')
        return redirect(url_for('asset.browse'))

    categories = AssetCategory.query.order_by(AssetCategory.name).all()

    if request.method == 'POST':
        rental_category = request.form.get('rental_category', asset.category.name if asset.category else 'Other')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        proposed_rent = request.form.get('proposed_rent', '').strip()
        tenant_message = request.form.get('tenant_message', '').strip()

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
        except ValueError:
            start_date = end_date = None

        # ── Date validation ────────────────────────────────────────────────
        today = date_type.today()
        date_errors = []
        if start_date and start_date < today:
            date_errors.append('Start date cannot be in the past.')
        if start_date and end_date and end_date <= start_date:
            date_errors.append('End date must be later than start date.')
        if date_errors:
            for e in date_errors:
                flash(e, 'error')
            return render_template('requests/create_request.html',
                                   asset=asset, categories=categories)

        try:
            proposed_rent = float(proposed_rent) if proposed_rent else None
        except ValueError:
            proposed_rent = None

        req_obj = AgreementRequest(
            request_uid=str(uuid.uuid4()),
            tenant_id=current_user.id,
            landlord_id=asset.owner_id,
            asset_id=asset.id,
            rental_category=rental_category,
            proposed_start_date=start_date,
            proposed_end_date=end_date,
            proposed_rent=proposed_rent,
            currency=request.form.get('currency', 'NPR'),
            tenant_message=tenant_message,
            status='pending',
        )
        db.session.add(req_obj)
        db.session.flush()

        # Create chat thread for this request
        thread = _get_or_create_thread(req_obj)
        _post_system_message(
            thread,
            f"📋 Rental request created by {current_user.full_name} "
            f"for '{asset.asset_title}'. Proposed rent: {req_obj.currency} {proposed_rent or 'TBD'}."
        )
        # Post the tenant's message as a real chat message so the landlord sees it
        if tenant_message:
            ct, nonce, h = encrypt_message(thread.encrypted_thread_key, tenant_message)
            db.session.add(ChatMessage(
                thread_id=thread.id,
                sender_id=current_user.id,
                ciphertext_b64=ct,
                nonce_b64=nonce,
                message_hash=h,
                is_system=False,
            ))
        db.session.commit()

        flash('Rental request sent! The landlord will review it shortly.', 'success')
        return redirect(url_for('req.view_request', req_id=req_obj.id))

    return render_template('requests/create_request.html',
                           asset=asset, categories=categories)


# ── VIEW REQUEST ───────────────────────────────────────────────────────────

@req_bp.route('/<int:req_id>')
@login_required
def view_request(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    # Always ensure a chat thread exists so chat is available immediately
    thread = _get_or_create_thread(req_obj)
    db.session.commit()
    from app.services.chat_service import decrypt_thread_messages, generate_thread_key, encrypt_message as _enc
    from app.models.chat import ChatMessage as _CM

    # Validate the thread key directly — catches corruption even when there are no messages
    try:
        _enc(thread.encrypted_thread_key, '_key_test_')
    except Exception:
        _CM.query.filter_by(thread_id=thread.id).delete()
        thread.encrypted_thread_key = generate_thread_key()
        db.session.commit()

    try:
        messages = decrypt_thread_messages(thread)
        if any(m['text'] == '[decryption error]' for m in messages):
            raise ValueError('corrupt key')
    except Exception:
        _CM.query.filter_by(thread_id=thread.id).delete()
        thread.encrypted_thread_key = generate_thread_key()
        db.session.commit()
        messages = []

    # Which approvals exist?
    my_terms_approval = _approval_for(req_id, current_user.id, 'terms_approval')
    terms_both = _both_approved(req_obj, 'terms_approval')

    # Photos
    my_photo = IdentityPhoto.query.filter_by(
        user_id=current_user.id,
        agreement_id=req_obj.agreement_id
    ).first() if req_obj.agreement_id else None

    l_photo = IdentityPhoto.query.filter_by(
        user_id=req_obj.landlord_id,
        agreement_id=req_obj.agreement_id
    ).first() if req_obj.agreement_id else None

    t_photo = IdentityPhoto.query.filter_by(
        user_id=req_obj.tenant_id,
        agreement_id=req_obj.agreement_id
    ).first() if req_obj.agreement_id else None

    agreement = req_obj.agreement
    gen_pdf = None
    if agreement:
        gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()

    return render_template('requests/view_request.html',
                           req=req_obj,
                           messages=messages,
                           thread=thread,
                           my_terms_approval=my_terms_approval,
                           terms_both=terms_both,
                           my_photo=my_photo,
                           l_photo=l_photo,
                           t_photo=t_photo,
                           agreement=agreement,
                           gen_pdf=gen_pdf)


# ── LANDLORD: REVIEW (mark under_review, open chat) ───────────────────────

@req_bp.route('/<int:req_id>/review', methods=['POST'])
@login_required
def mark_under_review(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id != req_obj.landlord_id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    req_obj.status = 'under_review'
    req_obj.reviewed_at = datetime.utcnow()
    thread = _get_or_create_thread(req_obj)
    _post_system_message(thread, f"👀 Landlord {current_user.full_name} is reviewing your request.")
    db.session.commit()
    flash('Request marked as under review. Chat with the tenant below.', 'success')
    return redirect(url_for('req.view_request', req_id=req_id))


# ── LANDLORD: COUNTER-OFFER ────────────────────────────────────────────────

@req_bp.route('/<int:req_id>/counter', methods=['POST'])
@login_required
def counter_offer(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id != req_obj.landlord_id:
        flash('Access denied.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    counter_rent = request.form.get('counter_rent', '').strip()
    landlord_note = request.form.get('landlord_note', '').strip()

    try:
        counter_rent_val = float(counter_rent) if counter_rent else None
    except ValueError:
        counter_rent_val = None

    req_obj.landlord_counter_rent = counter_rent_val
    req_obj.landlord_note = landlord_note
    req_obj.status = 'negotiating'

    thread = _get_or_create_thread(req_obj)
    note_text = f" Note: {landlord_note}" if landlord_note else ''
    _post_system_message(
        thread,
        f"💬 Landlord counter-offer: {req_obj.currency} {counter_rent_val or 'unchanged'}/month.{note_text}"
    )
    db.session.commit()
    flash('Counter-offer sent to tenant.', 'success')
    return redirect(url_for('req.view_request', req_id=req_id))


# ── LANDLORD: REJECT ───────────────────────────────────────────────────────

@req_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
def reject_request(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id != req_obj.landlord_id:
        flash('Access denied.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    reason = request.form.get('reason', '').strip()
    req_obj.status = 'rejected'
    thread = _get_or_create_thread(req_obj)
    _post_system_message(thread, f"❌ Request rejected by landlord. Reason: {reason or 'Not specified'}")
    db.session.commit()
    flash('Request rejected.', 'info')
    return redirect(url_for('req.view_request', req_id=req_id))


# ── APPROVE TERMS (both parties) ───────────────────────────────────────────

@req_bp.route('/<int:req_id>/approve-terms', methods=['POST'])
@login_required
def approve_terms(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    role = 'landlord' if current_user.id == req_obj.landlord_id else 'tenant'
    existing = _approval_for(req_id, current_user.id, 'terms_approval')

    if not existing:
        ap = PartyApproval(
            request_id=req_id, user_id=current_user.id,
            role=role, stage='terms_approval',
            approved=True, approved_at=datetime.utcnow()
        )
        db.session.add(ap)

        thread = _get_or_create_thread(req_obj)
        _post_system_message(
            thread,
            f"✅ {current_user.full_name} ({role}) approved the proposed terms."
        )

    # If both approved → generate bilingual agreement draft
    db.session.flush()
    if _both_approved(req_obj, 'terms_approval'):
        req_obj.status = 'approved'
        req_obj.approved_at = datetime.utcnow()
        _create_agreement_from_request(req_obj)

    db.session.commit()
    flash('Terms approved! Waiting for the other party if not done.', 'success')
    return redirect(url_for('req.view_request', req_id=req_id))


def _create_agreement_from_request(req_obj: AgreementRequest):
    """Create RentalAgreement from an approved AgreementRequest."""
    if req_obj.agreement_id:
        return  # already created

    # Generate bilingual document content
    en_text, np_text = generate_bilingual_document(req_obj)
    combined_text = f"=== ENGLISH ===\n{en_text}\n\n=== नेपाली ===\n{np_text}"
    content_bytes = combined_text.encode('utf-8')

    agreements_dir = current_app.config['AGREEMENTS_DIR']
    Path(agreements_dir).mkdir(parents=True, exist_ok=True)

    uid = str(uuid.uuid4())

    # Write plaintext draft to temp file, hash it, then encrypt
    temp_path = os.path.join(agreements_dir, f"temp_{uid}.txt")
    with open(temp_path, 'wb') as f:
        f.write(content_bytes)

    doc_hash = sha256_hash_bytes(content_bytes)

    enc_filename = f"enc_{uid}.bin"
    enc_path = os.path.join(agreements_dir, enc_filename)
    import base64 as _b64
    aes_key_b64, nonce_b64 = encrypt_file_aes256gcm(temp_path, enc_path)
    os.remove(temp_path)

    landlord = req_obj.landlord
    aes_key_bytes = _b64.b64decode(aes_key_b64)
    aes_key_encrypted = encrypt_rsa_oaep(landlord.public_key_pem, aes_key_bytes)

    vcode = generate_verification_code()

    from datetime import date
    agreement = RentalAgreement(
        agreement_uid=uid,
        landlord_id=req_obj.landlord_id,
        tenant_id=req_obj.tenant_id,
        asset_id=req_obj.asset_id,
        rental_category=req_obj.rental_category,
        encrypted_file_path=enc_path,
        original_filename=f"agreement_{uid[:8]}.txt",
        document_hash_sha256=doc_hash,
        aes_key_encrypted=aes_key_encrypted,
        aes_nonce=nonce_b64,
        start_date=req_obj.proposed_start_date,
        end_date=req_obj.proposed_end_date,
        rent_amount=req_obj.effective_rent,
        currency=req_obj.currency,
        terms=req_obj.tenant_message,
        verification_code=vcode,
        status='pending_signatures',
    )
    db.session.add(agreement)
    db.session.flush()

    req_obj.agreement_id = agreement.id
    req_obj.status = 'agreement_created'

    thread = req_obj.chat_thread
    if thread:
        _post_system_message(
            thread,
            f"📄 Bilingual rental agreement generated (EN + NP). "
            f"Document hash: {doc_hash[:16]}... "
            f"Both parties must now capture identity photos and sign digitally."
        )


# ── DIGITAL SIGNING ────────────────────────────────────────────────────────

@req_bp.route('/<int:req_id>/sign', methods=['POST'])
@login_required
def sign_agreement(req_id):
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    agreement = req_obj.agreement
    if not agreement:
        flash('No agreement generated yet.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    # Verify cert
    cert = Certificate.query.filter_by(user_id=current_user.id, is_revoked=False).first()
    if not cert or not cert.is_valid:
        flash('Your certificate is invalid or revoked. Cannot sign.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    # Identity photo is mandatory before signing
    my_photo = IdentityPhoto.query.filter_by(
        user_id=current_user.id, agreement_id=agreement.id).first()
    if not my_photo:
        flash('You must capture your identity photo before signing. Please capture your photo first.', 'error')
        return redirect(url_for('photo.capture_photo', agreement_id=agreement.id))

    signing_remarks = request.form.get('signing_remarks', '').strip()[:500]
    sig = rsa_sign(current_user.private_key_pem, agreement.document_hash_sha256)
    role = 'landlord' if current_user.id == req_obj.landlord_id else 'tenant'

    if role == 'landlord':
        agreement.landlord_signature = sig
        agreement.landlord_signed_at = datetime.utcnow()
        agreement.landlord_cert_serial = cert.serial_number
        if signing_remarks:
            agreement.landlord_remarks = signing_remarks
    else:
        # Verify landlord signature first
        if agreement.landlord_signature:
            if not rsa_verify(req_obj.landlord.public_key_pem,
                              agreement.document_hash_sha256,
                              agreement.landlord_signature):
                flash('Landlord signature verification FAILED — document may be tampered!', 'error')
                return redirect(url_for('req.view_request', req_id=req_id))
        agreement.tenant_signature = sig
        agreement.tenant_signed_at = datetime.utcnow()
        agreement.tenant_cert_serial = cert.serial_number
        if signing_remarks:
            agreement.tenant_remarks = signing_remarks

    # Check if both signed
    if agreement.landlord_signature and agreement.tenant_signature:
        agreement.status = 'fully_signed'
        thread = _get_or_create_thread(req_obj)
        _post_system_message(
            thread,
            "🔐 Both parties have digitally signed. Generating final PDF certificate…"
        )
        db.session.flush()
        _auto_generate_pdf(req_obj, agreement)
    else:
        agreement.status = 'landlord_signed' if role == 'landlord' else 'pending_signatures'

    db.session.commit()
    flash(f'Agreement signed as {role}! Signature verified against your X.509 certificate.', 'success')
    return redirect(url_for('req.view_request', req_id=req_id))


def _auto_generate_pdf(req_obj: AgreementRequest, agreement: RentalAgreement):
    """Automatically generate the final bilingual PDF after both signatures."""
    from app.services.pdf_service import generate_certificate_pdf
    from app.services.qr_service import generate_qr_code

    landlord = req_obj.landlord
    tenant = User.query.get(req_obj.tenant_id)
    landlord_cert = Certificate.query.filter_by(user_id=req_obj.landlord_id).order_by(
        Certificate.issued_at.desc()).first()
    tenant_cert = Certificate.query.filter_by(user_id=req_obj.tenant_id).order_by(
        Certificate.issued_at.desc()).first()

    l_photo = IdentityPhoto.query.filter_by(
        user_id=req_obj.landlord_id, agreement_id=agreement.id).first()
    t_photo = IdentityPhoto.query.filter_by(
        user_id=req_obj.tenant_id, agreement_id=agreement.id).first()

    # Generate bilingual text for PDF inclusion
    en_text, np_text = generate_bilingual_document(req_obj, agreement)

    qr_dir = str(current_app.config['QR_DIR'])
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    verify_url = f"{base_url}/verify/code/{agreement.verification_code}"
    qr_path = generate_qr_code(verify_url, qr_dir, agreement.verification_code)

    pdfs_dir = str(current_app.config['PDFS_DIR'])
    os.makedirs(pdfs_dir, exist_ok=True)
    pdf_path = os.path.join(pdfs_dir, f"certificate_{agreement.agreement_uid}.pdf")

    try:
        pdf_hash = generate_certificate_pdf(
            agreement=agreement,
            landlord=landlord,
            tenant=tenant or landlord,
            landlord_cert=landlord_cert,
            tenant_cert=tenant_cert,
            qr_image_path=qr_path,
            output_path=pdf_path,
            verification_code=agreement.verification_code,
            landlord_photo_path=l_photo.photo_encrypted_path if l_photo else None,
            tenant_photo_path=t_photo.photo_encrypted_path if t_photo else None,
            en_legal_text=en_text,
            np_legal_text=np_text,
        )

        existing = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()
        if existing:
            existing.pdf_file_path = pdf_path
            existing.pdf_hash_sha256 = pdf_hash
            existing.qr_code_path = qr_path
            existing.verification_code = agreement.verification_code
            existing.generated_by = req_obj.landlord_id
        else:
            db.session.add(GeneratedPDF(
                agreement_id=agreement.id,
                pdf_file_path=pdf_path,
                pdf_hash_sha256=pdf_hash,
                verification_code=agreement.verification_code,
                qr_code_path=qr_path,
                generated_by=req_obj.landlord_id,
            ))
        agreement.final_pdf_status = 'generated'
    except Exception as e:
        agreement.final_pdf_status = 'failed'
        current_app.logger.error(f"PDF auto-generation failed: {e}")


# ── TENANT: LIST MY REQUESTS ───────────────────────────────────────────────

@req_bp.route('/')
@login_required
def list_requests():
    from sqlalchemy import or_
    reqs = AgreementRequest.query.filter(
        or_(
            AgreementRequest.tenant_id == current_user.id,
            AgreementRequest.landlord_id == current_user.id,
        )
    ).order_by(AgreementRequest.created_at.desc()).all()
    return render_template('requests/list_requests.html', reqs=reqs)


# ── STATUS POLLING ENDPOINT ────────────────────────────────────────────────

@req_bp.route('/<int:req_id>/status')
@login_required
def request_status(req_id):
    """Lightweight JSON endpoint polled by frontend to detect status changes."""
    req_obj = AgreementRequest.query.get_or_404(req_id)
    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        return jsonify({'error': 'Access denied'}), 403

    terms_both = _both_approved(req_obj, 'terms_approval')
    my_terms = bool(_approval_for(req_id, current_user.id, 'terms_approval'))

    agreement = req_obj.agreement
    gen_pdf = None
    if agreement:
        gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()

    return jsonify({
        'status': req_obj.status,
        'status_label': req_obj.status_label,
        'agreement_id': req_obj.agreement_id,
        'terms_both': terms_both,
        'my_terms_approved': my_terms,
        'landlord_signed': bool(agreement.landlord_signature) if agreement else False,
        'tenant_signed': bool(agreement.tenant_signature) if agreement else False,
        'pdf_ready': bool(gen_pdf) if gen_pdf else False,
        'pdf_status': agreement.final_pdf_status if agreement else None,
    })


# ── ACCEPT DIRECT AGREEMENT (tenant) ──────────────────────────────────────────

@req_bp.route('/<int:req_id>/accept-direct', methods=['POST'])
@login_required
def accept_direct_agreement(req_id):
    """Tenant accepts a landlord-created direct agreement."""
    req_obj = AgreementRequest.query.get_or_404(req_id)

    if not req_obj.initiated_by_landlord or current_user.id != req_obj.tenant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('req.list_requests'))

    if req_obj.status != 'pending':
        flash('This request has already been responded to.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    req_obj.status = 'approved'
    req_obj.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Agreement accepted. You can now sign it.', 'success')
    if req_obj.agreement_id:
        return redirect(url_for('agreement.view_agreement', agreement_id=req_obj.agreement_id))
    return redirect(url_for('req.view_request', req_id=req_id))


# ── REJECT DIRECT AGREEMENT (tenant) ──────────────────────────────────────────

@req_bp.route('/<int:req_id>/reject-direct', methods=['POST'])
@login_required
def reject_direct_agreement(req_id):
    """Tenant rejects a landlord-created direct agreement, cancelling it."""
    req_obj = AgreementRequest.query.get_or_404(req_id)

    if not req_obj.initiated_by_landlord or current_user.id != req_obj.tenant_id:
        flash('Access denied.', 'error')
        return redirect(url_for('req.list_requests'))

    if req_obj.status != 'pending':
        flash('This request has already been responded to.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    req_obj.status = 'rejected'
    if req_obj.agreement:
        req_obj.agreement.status = 'cancelled'
    db.session.commit()
    flash('Agreement rejected and cancelled.', 'info')
    return redirect(url_for('req.list_requests'))


# ── DELETE REQUEST ─────────────────────────────────────────────────────────────

@req_bp.route('/<int:req_id>/delete', methods=['POST'])
@login_required
def delete_request(req_id):
    """Delete a request that has not led to a fully-signed agreement."""
    req_obj = AgreementRequest.query.get_or_404(req_id)

    if current_user.id not in (req_obj.tenant_id, req_obj.landlord_id):
        flash('Access denied.', 'error')
        return redirect(url_for('req.list_requests'))

    # Block deletion if a fully-signed agreement is linked
    if req_obj.agreement and req_obj.agreement.is_fully_signed:
        flash('Cannot delete a request linked to a fully-signed agreement. Use "Request Mutual Deletion" on the agreement instead.', 'error')
        return redirect(url_for('req.view_request', req_id=req_id))

    # If there's a linked unsigned agreement, cancel it
    if req_obj.agreement and not req_obj.agreement.is_fully_signed:
        req_obj.agreement.status = 'cancelled'

    # Delete dependent records first to avoid FK constraint errors
    PartyApproval.query.filter_by(request_id=req_id).delete()

    thread = req_obj.chat_thread
    if thread:
        ChatMessage.query.filter_by(thread_id=thread.id).delete()
        db.session.delete(thread)

    db.session.delete(req_obj)
    db.session.commit()
    flash('Request deleted.', 'success')
    return redirect(url_for('req.list_requests'))
