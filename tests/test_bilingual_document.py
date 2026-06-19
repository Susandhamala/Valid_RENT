"""Tests: bilingual legal document generation (English + Nepali)."""
import pytest
from app.services.legal_service import generate_bilingual_document, get_template_for_category


class TestBilingualDocument:
    def test_default_template_returns_both_languages(self, app):
        with app.app_context():
            en, np = get_template_for_category('House')
            assert 'RENTAL AGREEMENT' in en
            assert 'भाडा सम्झौता' in np

    def test_all_categories_have_templates(self, app):
        categories = [
            'House', 'Room', 'Apartment', 'Land',
            'Automobile', 'Bike/Scooter', 'Machinery',
            'Office/Commercial', 'Storage/Warehouse', 'Other'
        ]
        with app.app_context():
            for cat in categories:
                en, np = get_template_for_category(cat)
                assert en, f"Missing English template for {cat}"
                assert np, f"Missing Nepali template for {cat}"

    def test_generated_document_contains_party_details(self, app):
        with app.app_context():
            from tests.conftest import _register, _login
            from app.extensions import db
            from app.models.user import User
            from app.models.asset import AssetCategory, RentalAsset
            from app.models.request import AgreementRequest
            from app.services.crypto_service import generate_rsa_keypair
            from app.services.certificate_service import issue_certificate
            from app.models.certificate import Certificate
            import uuid
            from datetime import date

            # Create landlord
            priv, pub = generate_rsa_keypair()
            landlord = User(full_name='Doc Landlord', email='docl@test.com',
                            role='landlord', private_key_pem=priv, public_key_pem=pub)
            landlord.set_password('password123')
            db.session.add(landlord)
            db.session.flush()
            cert_data = issue_certificate(pub, 'Doc Landlord', 'docl@test.com')
            db.session.add(Certificate(user_id=landlord.id, **cert_data))

            # Create tenant
            priv2, pub2 = generate_rsa_keypair()
            tenant = User(full_name='Doc Tenant', email='doct@test.com',
                          role='tenant', private_key_pem=priv2, public_key_pem=pub2)
            tenant.set_password('password123')
            db.session.add(tenant)
            db.session.flush()

            cat = AssetCategory.query.filter_by(name='House').first()
            asset = RentalAsset(owner_id=landlord.id, category_id=cat.id,
                                asset_title='Doc Test House', location='Lalitpur',
                                asset_identifier='HH-001', status='available')
            db.session.add(asset)
            db.session.flush()

            req = AgreementRequest(
                request_uid=str(uuid.uuid4()),
                tenant_id=tenant.id,
                landlord_id=landlord.id,
                asset_id=asset.id,
                rental_category='House',
                proposed_start_date=date(2026, 7, 1),
                proposed_end_date=date(2027, 6, 30),
                proposed_rent=12000,
                currency='NPR',
                tenant_message='Test special terms',
                status='approved',
            )
            db.session.add(req)
            db.session.commit()

            en_text, np_text = generate_bilingual_document(req)

            # English checks
            assert 'Doc Landlord' in en_text
            assert 'Doc Tenant' in en_text
            assert 'Doc Test House' in en_text
            assert 'Lalitpur' in en_text
            assert '12,000.00' in en_text
            assert 'RENTAL AGREEMENT' in en_text

            # Nepali checks
            assert 'Doc Landlord' in np_text
            assert 'Doc Tenant' in np_text
            assert 'भाडा सम्झौता' in np_text
            assert '12,000.00' in np_text

    def test_land_category_uses_land_override(self, app):
        with app.app_context():
            en, np = get_template_for_category('Land')
            assert 'LAND' in en or 'land' in en.lower()
            assert 'जग्गा' in np

    def test_vehicle_category_override(self, app):
        with app.app_context():
            en, _ = get_template_for_category('Automobile')
            assert 'VEHICLE' in en or 'vehicle' in en.lower()
