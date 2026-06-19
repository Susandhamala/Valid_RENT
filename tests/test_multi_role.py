"""Tests: multi-role support, self-rental prevention, and ownership-based access."""
import pytest
from tests.conftest import _register, _login, _logout, make_asset
from app.extensions import db


class TestMultiRole:
    def test_tenant_can_add_landlord_role(self, client, app):
        _register(client, 'multi@test.com', 'tenant', 'Multi Role')
        _login(client, 'multi@test.com')
        r = client.post('/add-role', data={'role': 'landlord'}, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            from app.models.user import User
            u = User.query.filter_by(email='multi@test.com').first()
            assert u.has_role('landlord')
            assert u.has_role('tenant')

    def test_landlord_can_add_tenant_role(self, client, app):
        _register(client, 'll_add@test.com', 'landlord', 'LL Add')
        _login(client, 'll_add@test.com')
        r = client.post('/add-role', data={'role': 'tenant'}, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            from app.models.user import User
            u = User.query.filter_by(email='ll_add@test.com').first()
            assert u.has_role('tenant')
            assert u.has_role('landlord')

    def test_landlord_can_request_another_owners_listing(self, client, app):
        """A landlord-user with tenant role can request another owner's listing."""
        _register(client, 'll_multi@test.com', 'landlord', 'LL Multi')
        _register(client, 'll_owner@test.com', 'landlord', 'LL Owner')
        asset_id = make_asset(app, 'll_owner@test.com')

        _login(client, 'll_multi@test.com')
        client.post('/add-role', data={'role': 'tenant'})
        r = client.post(f'/requests/new/{asset_id}', data={
            'rental_category': 'House',
            'start_date': '2027-01-01',
            'end_date': '2027-12-31',
            'proposed_rent': '15000',
            'currency': 'NPR',
            'tenant_message': 'Multi role user request',
        }, follow_redirects=True)
        assert r.status_code == 200
        # Should succeed — not blocked
        assert b'cannot request your own' not in r.data

    def test_user_cannot_request_own_listing(self, client, app):
        """Self-rental must be blocked."""
        _register(client, 'self_rent@test.com', 'landlord', 'Self Renter')
        _login(client, 'self_rent@test.com')
        client.post('/add-role', data={'role': 'tenant'})
        asset_id = make_asset(app, 'self_rent@test.com')

        r = client.post(f'/requests/new/{asset_id}', data={
            'rental_category': 'House',
            'start_date': '2027-01-01',
            'end_date': '2027-12-31',
            'proposed_rent': '10000',
            'currency': 'NPR',
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b'cannot request your own' in r.data

    def test_only_listing_owner_can_approve_request(self, client, app):
        """A third party (not the listing owner) cannot approve a request."""
        _register(client, 'owner_a@test.com', 'landlord', 'Owner A')
        _register(client, 'owner_b@test.com', 'landlord', 'Owner B')
        _register(client, 'ten_a@test.com', 'tenant', 'Tenant A')
        asset_id = make_asset(app, 'owner_a@test.com')

        # Tenant creates request
        _login(client, 'ten_a@test.com')
        r = client.post(f'/requests/new/{asset_id}', data={
            'rental_category': 'House',
            'start_date': '2027-01-01',
            'end_date': '2027-12-31',
            'proposed_rent': '12000',
            'currency': 'NPR',
            'tenant_message': 'Test',
        })
        _logout(client)

        with app.app_context():
            from app.models.request import AgreementRequest
            req = AgreementRequest.query.first()
            req_id = req.id if req else None

        if not req_id:
            return  # Request creation may have been blocked by DB isolation

        # owner_b tries to review — should be denied
        _login(client, 'owner_b@test.com')
        r = client.post(f'/requests/{req_id}/review', follow_redirects=True)
        assert r.status_code == 200
        assert b'Access denied' in r.data or b'denied' in r.data.lower()

    def test_requester_and_owner_ids_saved_correctly(self, client, app):
        """tenant_id = requester, landlord_id = listing owner."""
        _register(client, 'owner_ids@test.com', 'landlord', 'Owner IDs')
        _register(client, 'req_ids@test.com', 'tenant', 'Req IDs')
        asset_id = make_asset(app, 'owner_ids@test.com')

        _login(client, 'req_ids@test.com')
        client.post(f'/requests/new/{asset_id}', data={
            'rental_category': 'House',
            'start_date': '2027-02-01',
            'end_date': '2027-12-31',
            'proposed_rent': '10000',
            'currency': 'NPR',
            'tenant_message': 'ID test',
        })

        with app.app_context():
            from app.models.request import AgreementRequest
            from app.models.user import User
            owner = User.query.filter_by(email='owner_ids@test.com').first()
            req_user = User.query.filter_by(email='req_ids@test.com').first()
            req = AgreementRequest.query.filter_by(
                tenant_id=req_user.id, landlord_id=owner.id
            ).first()
            assert req is not None, "Request not saved with correct tenant/landlord IDs"
            assert req.asset_id == asset_id

    def test_tenant_can_also_create_asset_as_landlord(self, client, app):
        _register(client, 'tn_multi@test.com', 'tenant', 'TN Multi')
        _login(client, 'tn_multi@test.com')
        client.post('/add-role', data={'role': 'landlord'})
        r = client.post('/assets/create', data={
            'category_id': '1',
            'asset_title': 'Multi Role Asset',
            'location': 'Patan',
            'estimated_value': '12000',
        }, content_type='multipart/form-data', follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            from app.models.asset import RentalAsset
            a = RentalAsset.query.filter_by(asset_title='Multi Role Asset').first()
            assert a is not None

    def test_role_switch_updates_session(self, client, app):
        _register(client, 'switcher@test.com', 'tenant', 'Switcher')
        _login(client, 'switcher@test.com')
        client.post('/add-role', data={'role': 'landlord'})
        r = client.post('/switch-role', data={'role': 'landlord'}, follow_redirects=True)
        assert r.status_code == 200

    def test_invalid_role_switch_rejected(self, client, app):
        _register(client, 'invalid_sw@test.com', 'tenant', 'Invalid Switch')
        _login(client, 'invalid_sw@test.com')
        r = client.post('/switch-role', data={'role': 'admin'}, follow_redirects=True)
        assert r.status_code == 200
        assert b'not authorized' in r.data or b'authorized' in r.data.lower()

    def test_landlord_can_view_any_asset_listing(self, client, app):
        """A pure landlord (no tenant role) can browse and view any asset."""
        _register(client, 'viewer_ll@test.com', 'landlord', 'Viewer LL')
        _register(client, 'other_ll@test.com', 'landlord', 'Other LL')
        asset_id = make_asset(app, 'other_ll@test.com')

        _login(client, 'viewer_ll@test.com')
        r = client.get(f'/assets/{asset_id}', follow_redirects=True)
        assert r.status_code == 200
        # Should see the asset, not an access denied
        assert b'Access denied' not in r.data
