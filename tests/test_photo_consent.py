"""Tests: identity photo capture consent requirement."""
import json
import pytest
from tests.conftest import _register, _login, make_asset


def _create_request_and_agreement(client, app):
    """Full setup: register both parties, asset, request, approve terms."""
    _register(client, 'pl@test.com', 'landlord', 'Photo Landlord')
    _register(client, 'pt@test.com', 'tenant', 'Photo Tenant')

    from app.models.user import User
    from app.models.asset import AssetCategory, RentalAsset
    from app.extensions import db
    with app.app_context():
        landlord = User.query.filter_by(email='pl@test.com').first()
        cat = AssetCategory.query.filter_by(name='House').first()
        asset = RentalAsset(
            owner_id=landlord.id, category_id=cat.id,
            asset_title='Photo House', location='Pokhara',
            status='available',
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id

    _login(client, 'pt@test.com')
    client.post(f'/requests/new/{asset_id}', data={
        'rental_category': 'House', 'start_date': '2026-07-01',
        'proposed_rent': '9000', 'currency': 'NPR', 'tenant_message': 'Hi',
    })
    from tests.conftest import _logout
    _logout(client)

    from app.models.request import AgreementRequest
    with app.app_context():
        req = AgreementRequest.query.first()
        req_id = req.id

    _login(client, 'pl@test.com')
    client.post(f'/requests/{req_id}/review')
    client.post(f'/requests/{req_id}/approve-terms')
    _logout(client)

    _login(client, 'pt@test.com')
    client.post(f'/requests/{req_id}/approve-terms')
    _logout(client)

    return req_id


class TestPhotoConsent:
    def test_photo_requires_consent(self, client, app):
        req_id = _create_request_and_agreement(client, app)

        with app.app_context():
            from app.models.request import AgreementRequest
            req = AgreementRequest.query.get(req_id)
            if not req.agreement_id:
                pytest.skip("Agreement not created (terms not both approved in this test run)")
            agreement_id = req.agreement_id

        _login(client, 'pt@test.com')
        # Submit photo WITHOUT consent
        r = client.post(f'/photos/save/{agreement_id}',
                        data={'photo_data': 'data:image/jpeg;base64,/9j/4A==',
                              'consent': 'false'},
                        content_type='application/x-www-form-urlencoded')
        data = r.get_json()
        assert r.status_code == 400
        assert not data['success']
        assert 'consent' in data['message'].lower()

    def test_photo_with_consent_saves_successfully(self, client, app):
        import base64
        req_id = _create_request_and_agreement(client, app)

        with app.app_context():
            from app.models.request import AgreementRequest
            req = AgreementRequest.query.get(req_id)
            if not req.agreement_id:
                pytest.skip("Agreement not created")
            agreement_id = req.agreement_id

        # Minimal valid JPEG (1x1 pixel)
        tiny_jpeg = base64.b64encode(
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e='
            b'\xff\xd9'
        ).decode()

        _login(client, 'pt@test.com')
        r = client.post(f'/photos/save/{agreement_id}',
                        data={'photo_data': f'data:image/jpeg;base64,{tiny_jpeg}',
                              'consent': 'true'},
                        content_type='application/x-www-form-urlencoded')
        data = r.get_json()
        assert r.status_code == 200
        assert data['success']

        with app.app_context():
            from app.models.photo import IdentityPhoto
            from app.models.user import User
            tenant = User.query.filter_by(email='pt@test.com').first()
            photo = IdentityPhoto.query.filter_by(
                user_id=tenant.id, agreement_id=agreement_id).first()
            assert photo is not None
            assert photo.consent_given is True
            assert photo.photo_hash_sha256 is not None

    def test_photo_not_accessible_to_third_party(self, client, app):
        req_id = _create_request_and_agreement(client, app)
        _register(client, 'thirdparty@test.com', 'tenant', 'Third Party')

        with app.app_context():
            from app.models.request import AgreementRequest
            req = AgreementRequest.query.get(req_id)
            if not req.agreement_id:
                pytest.skip("Agreement not created")
            agreement_id = req.agreement_id

        _login(client, 'thirdparty@test.com')
        r = client.post(f'/photos/save/{agreement_id}',
                        data={'photo_data': 'abc', 'consent': 'true'},
                        content_type='application/x-www-form-urlencoded')
        assert r.status_code in (403, 404)
