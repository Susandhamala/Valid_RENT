import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.agreement import RentalAgreement
from app.models.asset import AssetCategory, RentalAsset
from app.models.certificate import Certificate
from app.models.user import User
from app.services.crypto_service import (
    sha256_hash_file, encrypt_file_aes256gcm, rsa_sign, rsa_verify,
    encrypt_rsa_oaep, sha256_hash_bytes
)
from app.services.qr_service import generate_verification_code

agreement_bp = Blueprint('agreement', __name__, url_prefix='/agreements')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@agreement_bp.route('/')
@login_required
def list_agreements():
    from sqlalchemy import or_
    q = request.args.get('q', '').strip().upper()
    base = RentalAgreement.query.filter(
        or_(
            RentalAgreement.landlord_id == current_user.id,
            RentalAgreement.tenant_id == current_user.id,
        )
    )
    if q:
        base = base.filter(
            RentalAgreement.verification_code.ilike(f'%{q}%'),
            RentalAgreement.status == 'fully_signed'
        )
    agreements = base.order_by(RentalAgreement.created_at.desc()).all()
    return render_template('agreements/list.html', agreements=agreements, search_q=q)


@agreement_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_agreement():
    if not current_user.has_role('landlord'):
        flash('Only landlords can create agreements.', 'error')
        return redirect(url_for('dashboard.home'))

    categories = AssetCategory.query.order_by(AssetCategory.name).all()
    assets = RentalAsset.query.filter_by(owner_id=current_user.id, status='available').all()
    # Find all users who can act as tenant (role='tenant' OR roles contains 'tenant'), excluding self
    from sqlalchemy import or_
    tenants = User.query.filter(
        User.id != current_user.id,
        User.is_active == True,
        or_(User.role == 'tenant', User.roles.like('%tenant%'))
    ).all()

    if request.method == 'POST':
        tenant_id = request.form.get('tenant_id')
        asset_id = request.form.get('asset_id')
        rental_category = request.form.get('rental_category')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        rent_amount = request.form.get('rent_amount', 0)
        currency = request.form.get('currency', 'NPR')
        terms = request.form.get('terms', '')
        uploaded_file = request.files.get('agreement_file')

        if not tenant_id or not rental_category:
            flash('Tenant and category are required.', 'error')
            return render_template('agreements/create.html',
                                   categories=categories, assets=assets,
                                   tenants=tenants, form_data=request.form)

        agreements_dir = current_app.config['AGREEMENTS_DIR']
        shared_dir = os.path.join(agreements_dir, 'shared')
        Path(agreements_dir).mkdir(parents=True, exist_ok=True)
        Path(shared_dir).mkdir(parents=True, exist_ok=True)

        uid = str(uuid.uuid4())
        enc_path = None
        shared_path = None
        original_filename = None
        aes_key_encrypted = None
        nonce_b64 = None

        has_file = uploaded_file and uploaded_file.filename and _allowed_file(uploaded_file.filename)

        if uploaded_file and uploaded_file.filename and not has_file:
            flash('Invalid file type. Allowed: PDF, DOC, DOCX, TXT', 'error')
            return render_template('agreements/create.html',
                                   categories=categories, assets=assets,
                                   tenants=tenants, form_data=request.form)

        if has_file:
            original_filename = secure_filename(uploaded_file.filename)
            temp_path = os.path.join(agreements_dir, f"temp_{uid}_{original_filename}")
            uploaded_file.save(temp_path)

            # Hash original file
            doc_hash = sha256_hash_file(temp_path)

            # Save a shared readable copy for both parties
            ext = original_filename.rsplit('.', 1)[-1].lower()
            shared_path = os.path.join(shared_dir, f"{uid}.{ext}")
            import shutil
            shutil.copy2(temp_path, shared_path)

            # Encrypt file
            enc_filename = f"enc_{uid}.bin"
            enc_path = os.path.join(agreements_dir, enc_filename)
            aes_key_b64, nonce_b64 = encrypt_file_aes256gcm(temp_path, enc_path)
            os.remove(temp_path)

            # Wrap AES key with landlord's RSA public key
            import base64
            aes_key_bytes = base64.b64decode(aes_key_b64)
            aes_key_encrypted = encrypt_rsa_oaep(current_user.public_key_pem, aes_key_bytes)
        else:
            # Derive hash from agreement metadata when no file is uploaded
            meta = f"{uid}|{rental_category}|{tenant_id}|{terms}|{start_date}|{end_date}|{rent_amount}|{currency}"
            doc_hash = sha256_hash_bytes(meta.encode())

        # Verification code
        vcode = generate_verification_code()

        try:
            rent_amount = float(rent_amount)
        except (ValueError, TypeError):
            rent_amount = 0

        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            start_dt = end_dt = None

        if start_dt and end_dt and end_dt <= start_dt:
            flash('End date must be later than start date.', 'error')
            return render_template('agreements/create.html',
                                   categories=categories, assets=assets,
                                   tenants=tenants, form_data=request.form)

        agreement = RentalAgreement(
            agreement_uid=uid,
            landlord_id=current_user.id,
            tenant_id=int(tenant_id),
            asset_id=int(asset_id) if asset_id else None,
            rental_category=rental_category,
            encrypted_file_path=enc_path,
            shared_file_path=shared_path,
            original_filename=original_filename,
            document_hash_sha256=doc_hash,
            aes_key_encrypted=aes_key_encrypted,
            aes_nonce=nonce_b64,
            start_date=start_dt,
            end_date=end_dt,
            rent_amount=rent_amount,
            currency=currency,
            terms=terms,
            verification_code=vcode,
            status='pending_tenant',
        )
        db.session.add(agreement)
        db.session.flush()  # get agreement.id before commit

        # Create a request notification so the tenant can accept or reject
        from app.models.request import AgreementRequest
        direct_req = AgreementRequest(
            tenant_id=int(tenant_id),
            landlord_id=current_user.id,
            asset_id=int(asset_id) if asset_id else None,
            rental_category=rental_category,
            proposed_start_date=start_dt,
            proposed_end_date=end_dt,
            proposed_rent=rent_amount,
            currency=currency,
            tenant_message=terms or 'Agreement created directly by landlord. Please review and accept or reject.',
            status='pending',
            agreement_id=agreement.id,
            initiated_by_landlord=True,
        )
        db.session.add(direct_req)
        db.session.commit()

        flash('Agreement created! The tenant has been notified and must accept before signing.', 'success')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement.id))

    return render_template('agreements/create.html',
                           categories=categories, assets=assets,
                           tenants=tenants, form_data={})


@agreement_bp.route('/<int:agreement_id>')
@login_required
def view_agreement(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('agreement.list_agreements'))

    landlord_cert = Certificate.query.filter_by(
        user_id=agreement.landlord_id, is_revoked=False).first()
    tenant_cert = Certificate.query.filter_by(
        user_id=agreement.tenant_id, is_revoked=False).first() if agreement.tenant_id else None

    from app.models.request import AgreementRequest
    from app.models.photo import IdentityPhoto
    from app.models.chat import ChatThread, ChatMessage

    # linked_req: prefer landlord-initiated (direct), fall back to tenant-initiated
    linked_req = AgreementRequest.query.filter_by(
        agreement_id=agreement_id, initiated_by_landlord=True).first()
    if not linked_req:
        linked_req = AgreementRequest.query.filter_by(agreement_id=agreement_id).first()

    # Get or create the chat thread via the linked request
    thread = None
    chat_messages = []
    if linked_req:
        thread = linked_req.chat_thread
        if not thread:
            from app.services.chat_service import generate_thread_key
            thread = ChatThread(request_id=linked_req.id,
                                encrypted_thread_key=generate_thread_key())
            db.session.add(thread)
            db.session.commit()
        from app.services.chat_service import decrypt_thread_messages
        chat_messages = decrypt_thread_messages(thread)

    my_photo = IdentityPhoto.query.filter_by(
        user_id=current_user.id, agreement_id=agreement_id).first()
    landlord_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.landlord_id, agreement_id=agreement_id).first()
    tenant_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first() if agreement.tenant_id else None

    return_to = request.args.get('return_to', '')
    if return_to == 'request' and linked_req:
        back_url = url_for('req.view_request', req_id=linked_req.id)
    else:
        back_url = url_for('agreement.list_agreements')

    return render_template('agreements/view.html',
                           agreement=agreement,
                           landlord_cert=landlord_cert,
                           tenant_cert=tenant_cert,
                           linked_req=linked_req,
                           my_photo=my_photo,
                           landlord_photo=landlord_photo,
                           tenant_photo=tenant_photo,
                           thread=thread,
                           chat_messages=chat_messages,
                           back_url=back_url)


@agreement_bp.route('/<int:agreement_id>/sign', methods=['POST'])
@login_required
def sign_agreement(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)

    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('agreement.list_agreements'))

    if not agreement.document_hash_sha256:
        flash('No document hash found. Cannot sign.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    cert = Certificate.query.filter_by(user_id=current_user.id, is_revoked=False).first()
    if not cert or not cert.is_valid:
        flash('Your certificate is not valid. Cannot sign.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    # Identity photo is mandatory before signing
    from app.models.photo import IdentityPhoto
    my_photo = IdentityPhoto.query.filter_by(
        user_id=current_user.id, agreement_id=agreement_id).first()
    if not my_photo:
        flash('You must capture your identity photo before signing.', 'error')
        return redirect(url_for('photo.capture_photo', agreement_id=agreement_id))

    from datetime import datetime
    signature = rsa_sign(current_user.private_key_pem, agreement.document_hash_sha256)
    remarks = request.form.get('remarks', '').strip() or None

    if current_user.id == agreement.landlord_id:
        agreement.landlord_signature = signature
        agreement.landlord_signed_at = datetime.utcnow()
        agreement.landlord_cert_serial = cert.serial_number
        agreement.landlord_remarks = remarks
        agreement.status = 'landlord_signed' if not agreement.tenant_signature else 'fully_signed'
    else:
        # Verify landlord signature first
        landlord = User.query.get(agreement.landlord_id)
        if agreement.landlord_signature and not rsa_verify(
                landlord.public_key_pem, agreement.document_hash_sha256, agreement.landlord_signature):
            flash('Landlord signature verification failed! Document may be tampered.', 'error')
            return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

        agreement.tenant_signature = signature
        agreement.tenant_signed_at = datetime.utcnow()
        agreement.tenant_cert_serial = cert.serial_number
        agreement.tenant_remarks = remarks
        agreement.status = 'fully_signed' if agreement.landlord_signature else 'pending_tenant'

    # When fully signed, mark the linked asset as rented
    if agreement.status == 'fully_signed' and agreement.asset:
        agreement.asset.status = 'rented'

    db.session.commit()
    flash('Agreement signed successfully with your digital certificate!', 'success')
    return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))


def _purge_agreement_files(agreement):
    """Delete all files associated with an agreement from disk."""
    import os
    for fpath in (agreement.encrypted_file_path, agreement.shared_file_path):
        if fpath and os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass
    for photo in agreement.photos.all():
        if photo.photo_encrypted_path and os.path.exists(photo.photo_encrypted_path):
            try:
                os.remove(photo.photo_encrypted_path)
            except OSError:
                pass
    for pdf in agreement.generated_pdfs.all():
        for fpath in (pdf.pdf_file_path, pdf.qr_code_path):
            if fpath and os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass


@agreement_bp.route('/<int:agreement_id>/delete', methods=['POST'])
@login_required
def delete_agreement(agreement_id):
    """Delete an unsigned or cancelled agreement. Fully-signed agreements block this."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)

    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('agreement.list_agreements'))

    if agreement.is_fully_signed:
        flash('This agreement is fully signed. Use "Request Mutual Deletion" instead.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    _purge_agreement_files(agreement)

    # Unlink any associated requests rather than deleting them
    from app.models.request import AgreementRequest
    AgreementRequest.query.filter_by(agreement_id=agreement_id).update({'agreement_id': None})

    # Cascade-delete photos, PDFs, then the agreement
    from app.models.photo import IdentityPhoto
    from app.models.pdf import GeneratedPDF
    IdentityPhoto.query.filter_by(agreement_id=agreement_id).delete()
    GeneratedPDF.query.filter_by(agreement_id=agreement_id).delete()
    db.session.delete(agreement)
    db.session.commit()

    flash('Agreement deleted.', 'success')
    return redirect(url_for('agreement.list_agreements'))


@agreement_bp.route('/<int:agreement_id>/request-delete', methods=['POST'])
@login_required
def request_delete_agreement(agreement_id):
    """Record one party's consent to delete a fully-signed agreement.
    When both parties have consented, the agreement is deleted permanently."""
    from datetime import datetime as _dt
    agreement = RentalAgreement.query.get_or_404(agreement_id)

    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('agreement.list_agreements'))

    if not agreement.is_fully_signed:
        flash('Use the Delete button for agreements not yet fully signed.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    now = _dt.utcnow()
    if current_user.id == agreement.landlord_id:
        agreement.landlord_delete_requested = now
    else:
        agreement.tenant_delete_requested = now
    db.session.commit()

    if agreement.both_requested_delete:
        # Free the asset back to available before deleting the agreement
        if agreement.asset and agreement.asset.status == 'rented':
            agreement.asset.status = 'available'

        _purge_agreement_files(agreement)
        from app.models.request import AgreementRequest
        from app.models.photo import IdentityPhoto
        from app.models.pdf import GeneratedPDF
        AgreementRequest.query.filter_by(agreement_id=agreement_id).update({'agreement_id': None})
        IdentityPhoto.query.filter_by(agreement_id=agreement_id).delete()
        GeneratedPDF.query.filter_by(agreement_id=agreement_id).delete()
        db.session.delete(agreement)
        db.session.commit()
        flash('Agreement permanently deleted — both parties consented.', 'success')
        return redirect(url_for('agreement.list_agreements'))

    other = 'tenant' if current_user.id == agreement.landlord_id else 'landlord'
    flash(f'Deletion request recorded. Waiting for the {other} to also agree.', 'info')
    return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))


@agreement_bp.route('/<int:agreement_id>/document')
@login_required
def view_document(agreement_id):
    """Serve the shared (unencrypted) agreement document to both parties."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)

    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('agreement.list_agreements'))

    if not agreement.shared_file_path or not os.path.exists(agreement.shared_file_path):
        flash('No uploaded document is available for this agreement.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    download_name = agreement.original_filename or 'agreement_document'
    return send_file(agreement.shared_file_path, as_attachment=False,
                     download_name=download_name)
