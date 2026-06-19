from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.agreement import RentalAgreement
from app.models.certificate import Certificate
from app.models.user import User
from app.services.crypto_service import rsa_verify

verification_bp = Blueprint('verification', __name__, url_prefix='/verify')


@verification_bp.route('/crypto')
def crypto_info():
    return render_template('crypto/crypto_page.html')


def _run_independent_checks(agreement):
    """Re-run all cryptographic checks from scratch — no trust in DB flags."""
    import os, hashlib
    from app.models.pdf import GeneratedPDF

    landlord = User.query.get(agreement.landlord_id)
    tenant = User.query.get(agreement.tenant_id) if agreement.tenant_id else None

    landlord_cert = Certificate.query.filter_by(
        serial_number=agreement.landlord_cert_serial).first() if agreement.landlord_cert_serial else None
    tenant_cert = Certificate.query.filter_by(
        serial_number=agreement.tenant_cert_serial).first() if agreement.tenant_cert_serial else None

    # Independent RSA-PSS re-verification
    l_sig_ok = False
    t_sig_ok = False
    if agreement.landlord_signature and landlord:
        try:
            l_sig_ok = rsa_verify(landlord.public_key_pem,
                                  agreement.document_hash_sha256,
                                  agreement.landlord_signature)
        except Exception:
            l_sig_ok = False

    if agreement.tenant_signature and tenant:
        try:
            t_sig_ok = rsa_verify(tenant.public_key_pem,
                                  agreement.document_hash_sha256,
                                  agreement.tenant_signature)
        except Exception:
            t_sig_ok = False

    # PDF hash re-computation
    gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()
    pdf_hash_live = None
    pdf_hash_match = None
    if gen_pdf and gen_pdf.pdf_file_path and os.path.exists(gen_pdf.pdf_file_path):
        try:
            pdf_hash_live = hashlib.sha256(
                open(gen_pdf.pdf_file_path, 'rb').read()).hexdigest()
            pdf_hash_match = (pdf_hash_live == gen_pdf.pdf_hash_sha256)
        except Exception:
            pass

    return {
        'landlord': landlord,
        'tenant': tenant,
        'landlord_cert': landlord_cert,
        'tenant_cert': tenant_cert,
        'l_sig_ok': l_sig_ok,
        't_sig_ok': t_sig_ok,
        'l_cert_valid': landlord_cert.is_valid if landlord_cert else False,
        't_cert_valid': tenant_cert.is_valid if tenant_cert else False,
        'l_cert_revoked': landlord_cert.is_revoked if landlord_cert else False,
        't_cert_revoked': tenant_cert.is_revoked if tenant_cert else False,
        'gen_pdf': gen_pdf,
        'pdf_hash_live': pdf_hash_live,
        'pdf_hash_match': pdf_hash_match,
        'all_valid': (l_sig_ok and t_sig_ok and
                      (landlord_cert.is_valid if landlord_cert else False) and
                      (tenant_cert.is_valid if tenant_cert else False) and
                      not (landlord_cert.is_revoked if landlord_cert else True) and
                      not (tenant_cert.is_revoked if tenant_cert else True)),
    }


@verification_bp.route('/mutual')
@login_required
def mutual_verify_list():
    """List all fully-signed agreements for current user — entry point for hash verification."""
    from sqlalchemy import or_
    agreements = RentalAgreement.query.filter(
        or_(RentalAgreement.landlord_id == current_user.id,
            RentalAgreement.tenant_id == current_user.id),
        RentalAgreement.status == 'fully_signed'
    ).order_by(RentalAgreement.created_at.desc()).all()
    return render_template('verification/mutual_verify_list.html', agreements=agreements)


@verification_bp.route('/mutual/<int:agreement_id>')
@login_required
def mutual_verify_detail(agreement_id):
    """Full hash verification page for one agreement — runs checks independently."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        flash('Access denied.', 'error')
        return redirect(url_for('verification.mutual_verify_list'))

    checks = _run_independent_checks(agreement)
    i_am_landlord = current_user.id == agreement.landlord_id
    my_verified_at = agreement.landlord_verified_at if i_am_landlord else agreement.tenant_verified_at

    return render_template('verification/mutual_verify_detail.html',
                           agreement=agreement,
                           checks=checks,
                           i_am_landlord=i_am_landlord,
                           my_verified_at=my_verified_at)


@verification_bp.route('/mutual/<int:agreement_id>/confirm', methods=['POST'])
@csrf.exempt
@login_required
def mutual_verify_confirm(agreement_id):
    """Record current user's hash match request/confirmation."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        return ('Forbidden', 403)
    if current_user.id == agreement.landlord_id:
        agreement.landlord_verified_at = datetime.utcnow()
    else:
        agreement.tenant_verified_at = datetime.utcnow()
    db.session.commit()
    return ('', 204)


@verification_bp.route('/mutual/<int:agreement_id>/reset', methods=['POST'])
@csrf.exempt
@login_required
def mutual_verify_reset(agreement_id):
    """Clear both hash match confirmations so parties can re-request."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        return ('Forbidden', 403)
    agreement.landlord_verified_at = None
    agreement.tenant_verified_at = None
    db.session.commit()
    return ('', 204)


@verification_bp.route('/mutual/<int:agreement_id>/status')
@login_required
def mutual_verify_status(agreement_id):
    """JSON status endpoint polled by the inline panel."""
    agreement = RentalAgreement.query.get_or_404(agreement_id)
    if current_user.id not in (agreement.landlord_id, agreement.tenant_id):
        return ('Forbidden', 403)
    from flask import jsonify
    i_am_landlord = current_user.id == agreement.landlord_id
    l = agreement.landlord_verified_at
    t = agreement.tenant_verified_at
    return jsonify({
        'landlord_at': l.strftime('%d %b %Y %H:%M') if l else None,
        'tenant_at':   t.strftime('%d %b %Y %H:%M') if t else None,
        'both':        bool(l and t),
        'my_done':     bool((i_am_landlord and l) or (not i_am_landlord and t)),
        'other_done':  bool((i_am_landlord and t) or (not i_am_landlord and l)),
        'landlord_name': agreement.landlord.full_name,
        'tenant_name':   agreement.tenant.full_name if agreement.tenant else '',
        'i_am_landlord': i_am_landlord,
    })


@verification_bp.route('/code/<string:code>')
def verify_by_code(code):
    agreement = RentalAgreement.query.filter_by(verification_code=code).first()
    if not agreement:
        return render_template('pdf/verification_result.html',
                               result='INVALID',
                               reason='Verification code not found.',
                               agreement=None)

    landlord = User.query.get(agreement.landlord_id)
    tenant = User.query.get(agreement.tenant_id) if agreement.tenant_id else None

    checks = {}

    # Document hash check (we can't re-hash encrypted file without decryption key, so just report stored hash)
    checks['document_hash'] = agreement.document_hash_sha256 or 'N/A'

    # Signature checks
    landlord_sig_valid = False
    tenant_sig_valid = False

    if agreement.landlord_signature and landlord:
        landlord_sig_valid = rsa_verify(
            landlord.public_key_pem,
            agreement.document_hash_sha256,
            agreement.landlord_signature
        )

    if agreement.tenant_signature and tenant:
        tenant_sig_valid = rsa_verify(
            tenant.public_key_pem,
            agreement.document_hash_sha256,
            agreement.tenant_signature
        )

    checks['landlord_signed'] = landlord_sig_valid
    checks['tenant_signed'] = tenant_sig_valid

    # Certificate checks
    landlord_cert = Certificate.query.filter_by(
        serial_number=agreement.landlord_cert_serial).first() if agreement.landlord_cert_serial else None
    tenant_cert = Certificate.query.filter_by(
        serial_number=agreement.tenant_cert_serial).first() if agreement.tenant_cert_serial else None

    checks['landlord_cert_valid'] = landlord_cert.is_valid if landlord_cert else False
    checks['landlord_cert_revoked'] = landlord_cert.is_revoked if landlord_cert else False
    checks['tenant_cert_valid'] = tenant_cert.is_valid if tenant_cert else False
    checks['tenant_cert_revoked'] = tenant_cert.is_revoked if tenant_cert else False

    # PDF hash (if generated)
    from app.models.pdf import GeneratedPDF
    gen_pdf = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()

    # Final result
    all_valid = (
        landlord_sig_valid and
        tenant_sig_valid and
        checks['landlord_cert_valid'] and
        checks['tenant_cert_valid'] and
        not checks['landlord_cert_revoked'] and
        not checks['tenant_cert_revoked']
    )

    result = 'VALID' if all_valid else 'INVALID'

    # Public-safe info — full values, no truncation
    public_info = {
        'agreement_id': str(agreement.agreement_uid),
        'rental_category': agreement.rental_category,
        'status': agreement.status,
        'start_date': str(agreement.start_date),
        'end_date': str(agreement.end_date),
        'landlord_name': landlord.full_name if landlord else 'N/A',
        'tenant_name': tenant.full_name if tenant else 'N/A',
    }

    # Full cryptographic evidence
    crypto_evidence = {
        'document_hash_sha256': agreement.document_hash_sha256 or 'N/A',
        'landlord_signature': agreement.landlord_signature or None,
        'tenant_signature': agreement.tenant_signature or None,
        'landlord_cert_serial': agreement.landlord_cert_serial or 'N/A',
        'tenant_cert_serial': agreement.tenant_cert_serial or 'N/A',
        'landlord_signed_at': agreement.landlord_signed_at.strftime('%d %b %Y %H:%M UTC') if agreement.landlord_signed_at else 'N/A',
        'tenant_signed_at': agreement.tenant_signed_at.strftime('%d %b %Y %H:%M UTC') if agreement.tenant_signed_at else 'N/A',
        'pdf_hash_sha256': gen_pdf.pdf_hash_sha256 if gen_pdf else None,
    }

    return render_template('pdf/verification_result.html',
                           result=result,
                           checks=checks,
                           public_info=public_info,
                           crypto_evidence=crypto_evidence,
                           agreement=agreement,
                           code=code)
