import os
import base64
import hashlib
from pathlib import Path
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, jsonify, send_file, abort)
from flask_login import login_required, current_user
from app.extensions import db
from app.models.agreement import RentalAgreement
from app.models.photo import IdentityPhoto

photo_bp = Blueprint('photo', __name__, url_prefix='/photos')

MAX_PHOTO_SIZE = 5 * 1024 * 1024   # 5 MB
MAX_DOC_SIZE   = 8 * 1024 * 1024   # 8 MB
ALLOWED_DOC_EXTS = {'jpg', 'jpeg', 'png', 'pdf'}

DOCUMENT_TYPES = [
    ('citizenship',     'Citizenship Certificate (नागरिकता)'),
    ('passport',        'Passport (राहदानी)'),
    ('driving_license', 'Driving License (सवारी चालक अनुमतिपत्र)'),
    ('voter_id',        'Voter ID Card (मतदाता परिचयपत्र)'),
    ('national_id',     'National ID Card (राष्ट्रिय परिचयपत्र)'),
]


def _assert_party(agreement):
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        abort(403)


@photo_bp.route('/capture/<int:agreement_id>')
@login_required
def capture_photo(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    _assert_party(agreement)

    existing = IdentityPhoto.query.filter_by(
        user_id=current_user.id, agreement_id=agreement_id).first()
    is_tenant = current_user.id == agreement.tenant_id

    from app.models.request import AgreementRequest
    req_obj = AgreementRequest.query.filter_by(agreement_id=agreement_id).first()

    return_to = request.args.get('return_to', '')
    if return_to == 'request' and req_obj:
        back_url = url_for('req.view_request', req_id=req_obj.id)
    else:
        back_url = url_for('agreement.view_agreement', agreement_id=agreement_id)

    return render_template('photos/capture_photo.html',
                           agreement=agreement,
                           existing_photo=existing,
                           is_tenant=is_tenant,
                           document_types=DOCUMENT_TYPES,
                           back_url=back_url)


@photo_bp.route('/save/<int:agreement_id>', methods=['POST'])
@login_required
def save_photo(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    _assert_party(agreement)

    consent = request.form.get('consent') in ('true', 'on')
    if not consent:
        return jsonify({'success': False, 'message': 'Consent is required.'}), 400

    photo_data = request.form.get('photo_data', '')
    if not photo_data:
        return jsonify({'success': False, 'message': 'No photo data received.'}), 400

    if ',' in photo_data:
        photo_data = photo_data.split(',', 1)[1]

    try:
        photo_bytes = base64.b64decode(photo_data)
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid photo data.'}), 400

    if len(photo_bytes) > MAX_PHOTO_SIZE:
        return jsonify({'success': False, 'message': 'Photo too large (max 5 MB).'}), 400

    is_tenant = current_user.id == agreement.tenant_id
    doc_file = request.files.get('document_file')
    doc_type = request.form.get('document_type', '').strip()

    # ── Tenant document validation ────────────────────────────────────────────
    if is_tenant:
        existing_record = IdentityPhoto.query.filter_by(
            user_id=current_user.id, agreement_id=agreement_id).first()
        has_existing_doc = existing_record and existing_record.document_path
        has_new_doc = doc_file and doc_file.filename
        if not has_existing_doc and not has_new_doc:
            return jsonify({'success': False,
                            'message': 'Please upload your government-issued identity document.'}), 400
        if not doc_type:
            return jsonify({'success': False,
                            'message': 'Please select your document type.'}), 400
    else:
        existing_record = IdentityPhoto.query.filter_by(
            user_id=current_user.id, agreement_id=agreement_id).first()

    # ── Save webcam photo ─────────────────────────────────────────────────────
    try:
        photos_dir = current_app.config['PHOTOS_DIR']
        Path(str(photos_dir)).mkdir(parents=True, exist_ok=True)
        photo_filename = f"photo_{current_user.id}_{agreement_id}.jpg"
        photo_path = str(photos_dir / photo_filename)
        with open(photo_path, 'wb') as f:
            f.write(photo_bytes)
        photo_hash = hashlib.sha256(photo_bytes).hexdigest()
    except Exception as e:
        current_app.logger.error(f"save_photo: failed to save photo: {e}")
        return jsonify({'success': False, 'message': f'Failed to save photo: {e}'}), 500

    # ── Save identity document (tenant only, if a new file was provided) ──────
    doc_path_saved = None
    if is_tenant and doc_file and doc_file.filename:
        ext = doc_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_DOC_EXTS:
            return jsonify({'success': False,
                            'message': 'Document must be JPG, PNG, or PDF.'}), 400
        doc_bytes = doc_file.read()
        if len(doc_bytes) > MAX_DOC_SIZE:
            return jsonify({'success': False,
                            'message': 'Document too large (max 8 MB).'}), 400
        try:
            docs_dir = photos_dir / 'documents'
            docs_dir.mkdir(parents=True, exist_ok=True)
            doc_filename = f"doc_{current_user.id}_{agreement_id}.{ext}"
            doc_path_saved = str(docs_dir / doc_filename)
            with open(doc_path_saved, 'wb') as f:
                f.write(doc_bytes)
        except Exception as e:
            current_app.logger.error(f"save_photo: failed to save document: {e}")
            return jsonify({'success': False, 'message': f'Failed to save document: {e}'}), 500

    # ── Persist to database ───────────────────────────────────────────────────
    try:
        if existing_record:
            existing_record.photo_encrypted_path = photo_path
            existing_record.photo_hash_sha256 = photo_hash
            existing_record.consent_given = True
            if doc_path_saved:
                existing_record.document_path = doc_path_saved
                existing_record.document_type = doc_type
                existing_record.document_approved = False
                existing_record.document_approved_at = None
                existing_record.document_approved_by = None
            elif is_tenant and doc_type and existing_record.document_path:
                # Type changed but no new file — update the type only
                existing_record.document_type = doc_type
        else:
            db.session.add(IdentityPhoto(
                user_id=current_user.id,
                agreement_id=agreement_id,
                photo_encrypted_path=photo_path,
                photo_hash_sha256=photo_hash,
                consent_given=True,
                purpose='agreement_evidence',
                document_path=doc_path_saved,
                document_type=doc_type if doc_path_saved else None,
            ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"save_photo: DB error: {e}")
        return jsonify({'success': False, 'message': f'Database error: {e}'}), 500

    # ── Notify landlord via chat when tenant uploads/updates document ─────────
    if is_tenant and doc_path_saved:
        _post_doc_chat_notification(agreement, doc_type)

    if is_tenant and doc_path_saved:
        msg = 'Photo and document saved. The landlord will be notified to review your document.'
    elif is_tenant:
        msg = 'Photo updated. Your existing document is still on file.'
    else:
        msg = 'Photo saved successfully.'
    return jsonify({'success': True, 'message': msg})


def _post_doc_chat_notification(agreement, doc_type):
    """Post an encrypted system message notifying landlord that document was uploaded."""
    from app.models.request import AgreementRequest
    from app.models.chat import ChatThread
    from app.services.chat_service import encrypt_message
    from app.models.chat import ChatMessage

    req = AgreementRequest.query.filter_by(agreement_id=agreement.id).first()
    if not req:
        return
    thread = req.chat_thread
    if not thread:
        return

    doc_label = dict(DOCUMENT_TYPES).get(doc_type, doc_type or 'Identity Document')
    text = (
        f"📋 {current_user.full_name} (Tenant) has uploaded their identity photo "
        f"and {doc_label}. "
        f"Please review and approve the document from the Agreement page."
    )
    try:
        ct, nonce, h = encrypt_message(thread.encrypted_thread_key, text)
        msg = ChatMessage(thread_id=thread.id, sender_id=current_user.id,
                          ciphertext_b64=ct, nonce_b64=nonce,
                          message_hash=h, is_system=True)
        db.session.add(msg)
        db.session.commit()
    except Exception:
        pass


@photo_bp.route('/approve-document/<int:agreement_id>', methods=['POST'])
@login_required
def approve_document(agreement_id):
    """Landlord approves the tenant's identity document. Supports AJAX (X-Requested-With) and form POST."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if current_user.id != agreement.landlord_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Only the landlord can approve documents.'}), 403
        flash('Only the landlord can approve documents.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    tenant_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first()
    if not tenant_photo or not tenant_photo.document_path:
        if is_ajax:
            return jsonify({'success': False, 'message': 'No tenant document to approve.'}), 404
        flash('No tenant document to approve.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    from datetime import datetime
    now = datetime.utcnow()
    tenant_photo.document_approved = True
    tenant_photo.document_approved_at = now
    tenant_photo.document_approved_by = current_user.id
    db.session.commit()

    from app.models.request import AgreementRequest
    from app.models.chat import ChatMessage
    from app.services.chat_service import encrypt_message
    req = AgreementRequest.query.filter_by(agreement_id=agreement_id).first()
    if req and req.chat_thread:
        try:
            text = (f"✅ Landlord {current_user.full_name} approved the tenant's identity document.")
            ct, nonce, h = encrypt_message(req.chat_thread.encrypted_thread_key, text)
            db.session.add(ChatMessage(thread_id=req.chat_thread.id,
                                       sender_id=current_user.id,
                                       ciphertext_b64=ct, nonce_b64=nonce,
                                       message_hash=h, is_system=True))
            db.session.commit()
        except Exception:
            pass

    if is_ajax:
        return jsonify({'success': True, 'message': 'Document approved.',
                        'approved_at': now.strftime('%d %b %Y')})

    flash('Tenant document approved.', 'success')
    next_url = request.form.get('next', '').strip()
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))


@photo_bp.route('/reject-document/<int:agreement_id>', methods=['POST'])
@login_required
def reject_document(agreement_id):
    """Landlord rejects tenant's identity document — deletes file instantly, notifies via chat."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id != agreement.landlord_id:
        return jsonify({'success': False, 'message': 'Only the landlord can reject documents.'}), 403

    tenant_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first()
    if not tenant_photo or not tenant_photo.document_path:
        return jsonify({'success': False, 'message': 'No document found to reject.'}), 404

    reason = request.form.get('reason', '').strip() or 'Document did not meet requirements.'

    # Delete file from disk immediately
    try:
        if os.path.exists(tenant_photo.document_path):
            os.remove(tenant_photo.document_path)
    except Exception as e:
        current_app.logger.warning(f"reject_document: could not delete file: {e}")

    # Clear all document fields
    tenant_photo.document_path = None
    tenant_photo.document_type = None
    tenant_photo.document_approved = False
    tenant_photo.document_approved_at = None
    tenant_photo.document_approved_by = None
    db.session.commit()

    # Notify tenant via encrypted chat
    from app.models.request import AgreementRequest
    from app.models.chat import ChatMessage
    from app.services.chat_service import encrypt_message
    req = AgreementRequest.query.filter_by(agreement_id=agreement_id).first()
    if req and req.chat_thread:
        try:
            text = (f"❌ Landlord {current_user.full_name} rejected your identity document. "
                    f"Reason: {reason}  Please re-upload a valid document.")
            ct, nonce, h = encrypt_message(req.chat_thread.encrypted_thread_key, text)
            db.session.add(ChatMessage(thread_id=req.chat_thread.id,
                                       sender_id=current_user.id,
                                       ciphertext_b64=ct, nonce_b64=nonce,
                                       message_hash=h, is_system=True))
            db.session.commit()
        except Exception:
            pass

    return jsonify({'success': True,
                    'message': 'Document rejected and deleted. Tenant notified to re-upload.'})


@photo_bp.route('/view/<int:photo_id>')
@login_required
def serve_photo(photo_id):
    photo = IdentityPhoto.query.get_or_404(photo_id)
    agreement = RentalAgreement.query.get(photo.agreement_id)
    if not agreement or current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        abort(403)
    if not photo.photo_encrypted_path or not os.path.exists(photo.photo_encrypted_path):
        abort(404)
    return send_file(photo.photo_encrypted_path, mimetype='image/jpeg')


@photo_bp.route('/view-document/<int:agreement_id>')
@login_required
def serve_document(agreement_id):
    """Serve the tenant's identity document — visible to both parties."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        abort(403)
    photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first()
    if not photo or not photo.document_path or not os.path.exists(photo.document_path):
        abort(404)
    ext = photo.document_path.rsplit('.', 1)[-1].lower()
    mime = {'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}.get(ext, 'image/jpeg')
    return send_file(photo.document_path, mimetype=mime)
