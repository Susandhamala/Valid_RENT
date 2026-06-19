import os
from flask import Blueprint, render_template, redirect, url_for, flash, send_file, current_app, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.agreement import RentalAgreement
from app.models.certificate import Certificate
from app.models.photo import IdentityPhoto
from app.models.pdf import GeneratedPDF
from app.models.user import User
from app.services.pdf_service import generate_certificate_pdf
from app.services.qr_service import generate_qr_code, generate_verification_code

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')


def _get_parties_and_certs(agreement):
    landlord = User.query.get(agreement.landlord_id)
    tenant = User.query.get(agreement.tenant_id) if agreement.tenant_id else None
    landlord_cert = Certificate.query.filter_by(user_id=agreement.landlord_id).order_by(
        Certificate.issued_at.desc()).first()
    tenant_cert = Certificate.query.filter_by(user_id=agreement.tenant_id).order_by(
        Certificate.issued_at.desc()).first() if agreement.tenant_id else None
    return landlord, tenant, landlord_cert, tenant_cert


@pdf_bp.route('/generate/<int:agreement_id>', methods=['POST'])
@login_required
def generate_pdf(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)

    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    if not agreement.is_fully_signed:
        flash('Both parties must sign before generating the certificate.', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    landlord, tenant, landlord_cert, tenant_cert = _get_parties_and_certs(agreement)

    # Both identity photos are mandatory before PDF generation
    landlord_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.landlord_id, agreement_id=agreement_id).first()
    tenant_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first() if agreement.tenant_id else None

    missing = []
    if not landlord_photo:
        missing.append('Landlord')
    if agreement.tenant_id and not tenant_photo:
        missing.append('Tenant')
    if missing:
        flash(
            f'Cannot generate PDF — identity photo(s) missing for: {", ".join(missing)}. '
            f'Both parties must capture their identity photo before the certificate can be issued.',
            'error'
        )
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))

    vcode = agreement.verification_code or generate_verification_code()
    agreement.verification_code = vcode

    # QR code
    qr_dir = str(current_app.config['QR_DIR'])
    base_url = request.host_url.rstrip('/')
    verify_url = f"{base_url}/verify/code/{vcode}"
    qr_path = generate_qr_code(verify_url, qr_dir, vcode)

    # PDF path
    pdfs_dir = str(current_app.config['PDFS_DIR'])
    os.makedirs(pdfs_dir, exist_ok=True)
    pdf_filename = f"certificate_{agreement.agreement_uid}.pdf"
    pdf_path = os.path.join(pdfs_dir, pdf_filename)

    landlord_photo_path = None
    tenant_photo_path = None
    tenant_document_path = None
    asset_photo_path = None

    if landlord_photo and landlord_photo.photo_encrypted_path:
        p = landlord_photo.photo_encrypted_path
        if os.path.exists(p):
            landlord_photo_path = p

    if tenant_photo and tenant_photo.photo_encrypted_path:
        p = tenant_photo.photo_encrypted_path
        if os.path.exists(p):
            tenant_photo_path = p

    if tenant_photo and tenant_photo.document_path:
        p = tenant_photo.document_path
        if os.path.exists(p):
            tenant_document_path = p

    if agreement.asset and getattr(agreement.asset, 'photo_path', None):
        p = agreement.asset.photo_path
        if os.path.exists(p):
            asset_photo_path = p

    # Generate bilingual legal text with remarks
    from app.models.request import AgreementRequest
    from app.services.legal_service import generate_bilingual_document
    en_legal, np_legal = '', ''
    linked_req = AgreementRequest.query.filter_by(agreement_id=agreement_id).first()
    if linked_req:
        try:
            en_legal, np_legal = generate_bilingual_document(linked_req, agreement)
        except Exception:
            pass

    try:
        pdf_hash = generate_certificate_pdf(
            agreement=agreement,
            landlord=landlord,
            tenant=tenant or landlord,
            landlord_cert=landlord_cert,
            tenant_cert=tenant_cert,
            qr_image_path=qr_path,
            output_path=pdf_path,
            verification_code=vcode,
            landlord_photo_path=landlord_photo_path,
            tenant_photo_path=tenant_photo_path,
            tenant_document_path=tenant_document_path,
            asset_photo_path=asset_photo_path,
            en_legal_text=en_legal,
            np_legal_text=np_legal,
        )

        existing_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement_id).first()
        if existing_pdf:
            existing_pdf.pdf_file_path = pdf_path
            existing_pdf.pdf_hash_sha256 = pdf_hash
            existing_pdf.qr_code_path = qr_path
            existing_pdf.verification_code = vcode
            existing_pdf.generated_by = current_user.id
        else:
            gen_pdf = GeneratedPDF(
                agreement_id=agreement_id,
                pdf_file_path=pdf_path,
                pdf_hash_sha256=pdf_hash,
                verification_code=vcode,
                qr_code_path=qr_path,
                generated_by=current_user.id,
            )
            db.session.add(gen_pdf)

        agreement.final_pdf_status = 'generated'
        db.session.commit()

        flash('Verification certificate generated! Both parties can now download it.', 'success')
        return redirect(url_for('pdf.view_certificate', agreement_id=agreement_id))

    except Exception as e:
        db.session.rollback()
        flash(f'PDF generation failed: {str(e)}', 'error')
        return redirect(url_for('agreement.view_agreement', agreement_id=agreement_id))


@pdf_bp.route('/certificate/<int:agreement_id>')
@login_required
def view_certificate(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    landlord, tenant, landlord_cert, tenant_cert = _get_parties_and_certs(agreement)
    gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement_id).first()
    landlord_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.landlord_id, agreement_id=agreement_id).first()
    tenant_photo = IdentityPhoto.query.filter_by(
        user_id=agreement.tenant_id, agreement_id=agreement_id).first() if agreement.tenant_id else None

    return render_template('pdf/pdf_certificate.html',
                           agreement=agreement,
                           landlord=landlord, tenant=tenant,
                           landlord_cert=landlord_cert, tenant_cert=tenant_cert,
                           gen_pdf=gen_pdf,
                           landlord_photo=landlord_photo,
                           tenant_photo=tenant_photo)


@pdf_bp.route('/request-verification/<int:agreement_id>', methods=['POST'])
@login_required
def request_verification(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))
    from datetime import datetime
    if current_user.id == agreement.landlord_id:
        agreement.landlord_verified_at = datetime.utcnow()
    else:
        agreement.tenant_verified_at = datetime.utcnow()
    db.session.commit()
    flash('Your verification acknowledged. Waiting for the other party.', 'success')
    return redirect(url_for('pdf.view_certificate', agreement_id=agreement_id))


@pdf_bp.route('/download/<int:agreement_id>')
@login_required
def download_pdf(agreement_id):
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.home'))

    gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement_id).first()
    if not gen_pdf or not os.path.exists(gen_pdf.pdf_file_path):
        flash('PDF not yet generated. Please generate it first.', 'error')
        return redirect(url_for('pdf.view_certificate', agreement_id=agreement_id))

    who = 'Landlord' if current_user.id == agreement.landlord_id else 'Tenant'
    download_name = f"ValidRent_Certificate_{agreement.agreement_uid[:8]}_{who}.pdf"
    return send_file(gen_pdf.pdf_file_path, as_attachment=True, download_name=download_name)
