"""
Shared pytest fixtures for Valid Rent test suite.
Uses an in-memory SQLite database so tests are fast and isolated.
"""
import pytest
from app import create_app
from app.extensions import db as _db
from app.config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-validrent'
    AGREEMENTS_DIR = '/tmp/vr_test/agreements'
    PDFS_DIR = '/tmp/vr_test/pdfs'
    QR_DIR = '/tmp/vr_test/qr'
    PHOTOS_DIR = '/tmp/vr_test/photos'
    ASSET_PHOTOS_DIR = '/tmp/vr_test/asset_photos'
    BASE_URL = 'http://localhost'


@pytest.fixture(scope='session')
def app():
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope='function', autouse=True)
def db_session(app):
    """Wrap every test in a transaction that is rolled back afterwards."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        _db.session.bind = connection

        yield _db.session

        _db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(app):
    return app.test_client()


# ── Helpers ────────────────────────────────────────────────────────────────

def _register(client, email, role, name='Test User', password='ValidR3nt!'):
    return client.post('/auth/register', data={
        'full_name': name,
        'email': email,
        'phone': '9800000000',
        'role': role,
        'password': password,
        'confirm_password': password,
    }, follow_redirects=True)


def _login(client, email, password='ValidR3nt!'):
    return client.post('/auth/login', data={
        'email': email, 'password': password,
    }, follow_redirects=True)


def _logout(client):
    client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def landlord_client(client):
    _register(client, 'landlord@test.com', 'landlord', 'Land Lord')
    _login(client, 'landlord@test.com')
    yield client
    _logout(client)


@pytest.fixture
def tenant_client(client):
    _register(client, 'tenant@test.com', 'tenant', 'Ten Ant')
    _login(client, 'tenant@test.com')
    yield client
    _logout(client)


def make_asset(app, landlord_email='landlord@test.com'):
    """Create a test asset for the landlord with given email."""
    from app.models.user import User
    from app.models.asset import AssetCategory, RentalAsset
    with app.app_context():
        landlord = User.query.filter_by(email=landlord_email).first()
        cat = AssetCategory.query.filter_by(name='House').first()
        asset = RentalAsset(
            owner_id=landlord.id,
            category_id=cat.id,
            asset_title='Test House',
            asset_type='Residential',
            asset_identifier='PLOT-001',
            location='Kathmandu',
            estimated_value=15000,
            status='available',
        )
        _db.session.add(asset)
        _db.session.commit()
        return asset.id
