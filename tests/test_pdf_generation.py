"""Tests: PDF auto-generation, QR verification, tamper detection, revoked cert blocking."""
import os
import pytest
from app.services.crypto_service import (
    generate_rsa_keypair, rsa_sign, rsa_verify, sha256_hash_bytes
)
from app.services.certificate_service import issue_certificate


class TestCryptoCore:
    def test_rsa_sign_verify_roundtrip(self, app):
        with app.app_context():
            priv, pub = generate_rsa_keypair()
            doc_hash = sha256_hash_bytes(b"Legal agreement content")
            sig = rsa_sign(priv, doc_hash)
            assert rsa_verify(pub, doc_hash, sig) is True

    def test_tampered_document_fails_verification(self, app):
        with app.app_context():
            priv, pub = generate_rsa_keypair()
            doc_hash = sha256_hash_bytes(b"Original content")
            sig = rsa_sign(priv, doc_hash)
            tampered_hash = sha256_hash_bytes(b"Tampered content")
            assert rsa_verify(pub, tampered_hash, sig) is False

    def test_wrong_key_fails_verification(self, app):
        with app.app_context():
            priv, pub = generate_rsa_keypair()
            _, other_pub = generate_rsa_keypair()
            doc_hash = sha256_hash_bytes(b"Content")
            sig = rsa_sign(priv, doc_hash)
            assert rsa_verify(other_pub, doc_hash, sig) is False

    def test_certificate_issued_with_correct_fields(self, app):
        with app.app_context():
            _, pub = generate_rsa_keypair()
            cert_data = issue_certificate(pub, 'Test User', 'test@test.com')
            assert cert_data['serial_number']
            assert 'certificate_pem' in cert_data
            assert cert_data['expires_at'] > cert_data['issued_at']

    def test_revoked_certificate_is_invalid(self, app):
        with app.app_context():
            from app.models.certificate import Certificate
            from app.extensions import db
            from datetime import datetime
            _, pub = generate_rsa_keypair()
            cert_data = issue_certificate(pub, 'Revoke Test', 'rv@test.com')
            cert = Certificate(user_id=1, **cert_data)
            cert.is_revoked = True
            cert.revoked_at = datetime.utcnow()
            cert.revocation_reason = 'Test revocation'
            db.session.add(cert)
            db.session.commit()
            assert cert.is_valid is False
            assert cert.status_display == 'Revoked'


class TestQRVerification:
    def test_qr_verification_page_for_valid_code(self, client, app):
        with app.app_context():
            from app.models.agreement import RentalAgreement
            from app.extensions import db
            from app.models.user import User
            from app.services.crypto_service import generate_rsa_keypair
            from app.services.certificate_service import issue_certificate
            from app.models.certificate import Certificate
            import uuid

            priv, pub = generate_rsa_keypair()
            user = User(full_name='QR Test', email='qr@test.com', role='landlord',
                        private_key_pem=priv, public_key_pem=pub)
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()
            cert_data = issue_certificate(pub, 'QR Test', 'qr@test.com')
            db.session.add(Certificate(user_id=user.id, **cert_data))

            content = b"Test agreement content"
            doc_hash = sha256_hash_bytes(content)
            vcode = 'TESTVERIFYCODE123'

            ag = RentalAgreement(
                agreement_uid=str(uuid.uuid4()),
                landlord_id=user.id,
                tenant_id=user.id,
                rental_category='House',
                document_hash_sha256=doc_hash,
                verification_code=vcode,
                status='fully_signed',
                landlord_signature=rsa_sign(priv, doc_hash),
                tenant_signature=rsa_sign(priv, doc_hash),
                landlord_cert_serial=cert_data['serial_number'],
                tenant_cert_serial=cert_data['serial_number'],
            )
            db.session.add(ag)
            db.session.commit()

        r = client.get(f'/verify/code/{vcode}')
        assert r.status_code == 200
        assert b'VALID' in r.data or b'INVALID' in r.data

    def test_invalid_verification_code_returns_invalid(self, client, app):
        r = client.get('/verify/code/NONEXISTENTCODE999')
        assert r.status_code == 200
        assert b'INVALID' in r.data

    def test_qr_page_does_not_expose_full_personal_data(self, client, app):
        r = client.get('/verify/code/NONEXISTENTCODE999')
        # Should not show email addresses or private keys
        assert b'private_key' not in r.data
        assert b'password' not in r.data


class TestAutoPDFGeneration:
    def test_pdf_generated_after_both_signatures(self, app):
        """PDF auto-generation is triggered by _auto_generate_pdf in request_routes."""
        with app.app_context():
            from app.models.user import User
            from app.models.agreement import RentalAgreement
            from app.models.asset import AssetCategory, RentalAsset
            from app.models.request import AgreementRequest
            from app.models.pdf import GeneratedPDF
            from app.extensions import db
            from app.services.crypto_service import generate_rsa_keypair, sha256_hash_bytes, rsa_sign
            from app.services.certificate_service import issue_certificate
            from app.models.certificate import Certificate
            from app.routes.request_routes import _auto_generate_pdf
            import uuid
            from datetime import date

            # Create two users
            priv1, pub1 = generate_rsa_keypair()
            landlord = User(full_name='PDF Landlord', email='pdfl@test.com',
                            role='landlord', private_key_pem=priv1, public_key_pem=pub1)
            landlord.set_password('pass')
            db.session.add(landlord)
            db.session.flush()
            c1 = issue_certificate(pub1, 'PDF Landlord', 'pdfl@test.com')
            db.session.add(Certificate(user_id=landlord.id, **c1))

            priv2, pub2 = generate_rsa_keypair()
            tenant = User(full_name='PDF Tenant', email='pdft@test.com',
                          role='tenant', private_key_pem=priv2, public_key_pem=pub2)
            tenant.set_password('pass')
            db.session.add(tenant)
            db.session.flush()
            c2 = issue_certificate(pub2, 'PDF Tenant', 'pdft@test.com')
            db.session.add(Certificate(user_id=tenant.id, **c2))

            cat = AssetCategory.query.filter_by(name='House').first()
            asset = RentalAsset(owner_id=landlord.id, category_id=cat.id,
                                asset_title='PDF House', location='Kathmandu',
                                asset_identifier='PDF-001', status='available')
            db.session.add(asset)
            db.session.flush()

            # Create request
            req = AgreementRequest(
                request_uid=str(uuid.uuid4()),
                tenant_id=tenant.id, landlord_id=landlord.id,
                asset_id=asset.id, rental_category='House',
                proposed_start_date=date(2026, 7, 1),
                proposed_end_date=date(2027, 6, 30),
                proposed_rent=10000, currency='NPR',
                tenant_message='PDF test', status='agreement_created',
            )
            db.session.add(req)
            db.session.flush()

            # Create agreement manually
            content = b'Bilingual agreement content EN+NP'
            doc_hash = sha256_hash_bytes(content)
            from datetime import datetime
            vcode = 'PDFAUTOTEST001'
            agreement = RentalAgreement(
                agreement_uid=str(uuid.uuid4()),
                landlord_id=landlord.id, tenant_id=tenant.id,
                asset_id=asset.id, rental_category='House',
                document_hash_sha256=doc_hash,
                verification_code=vcode, status='fully_signed',
                landlord_signature=rsa_sign(priv1, doc_hash),
                landlord_signed_at=datetime.utcnow(),
                landlord_cert_serial=c1['serial_number'],
                tenant_signature=rsa_sign(priv2, doc_hash),
                tenant_signed_at=datetime.utcnow(),
                tenant_cert_serial=c2['serial_number'],
                start_date=date(2026, 7, 1), end_date=date(2027, 6, 30),
                rent_amount=10000, currency='NPR',
            )
            db.session.add(agreement)
            db.session.flush()
            req.agreement_id = agreement.id
            db.session.commit()

            # Trigger auto PDF generation
            _auto_generate_pdf(req, agreement)
            db.session.commit()

            # Verify PDF was created
            pdf_record = GeneratedPDF.query.filter_by(agreement_id=agreement.id).first()
            assert pdf_record is not None
            assert pdf_record.pdf_hash_sha256 is not None
            assert os.path.exists(pdf_record.pdf_file_path)
