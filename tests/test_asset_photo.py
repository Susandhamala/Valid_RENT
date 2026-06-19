"""Tests: asset photo upload."""
import io
import pytest
from tests.conftest import _register, _login, _logout


def _minimal_jpeg():
    """Return a tiny valid JPEG as bytes (1x1 white pixel)."""
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
        b'\xc7\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
        b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08'
        b'\x01\x01\x00\x00?\x00\xf5\x0a\xff\xd9'
    )


def _setup_landlord(client):
    _register(client, 'photo_ll@test.com', 'landlord', 'Photo Landlord')
    _login(client, 'photo_ll@test.com')


def _post_asset(client, photo_data=None, photo_name='test.jpg', content_type='image/jpeg'):
    data = {
        'category_id': '1',
        'asset_title': 'Photo Test House',
        'asset_type': 'Residential',
        'asset_identifier': 'PHOTO-001',
        'location': 'Kathmandu',
        'estimated_value': '10000',
    }
    if photo_data is not None:
        data['photo'] = (io.BytesIO(photo_data), photo_name, content_type)
    return client.post('/assets/create', data=data,
                       content_type='multipart/form-data', follow_redirects=True)


class TestAssetPhoto:
    def test_asset_created_without_photo(self, client, app):
        _setup_landlord(client)
        r = _post_asset(client)
        assert r.status_code == 200
        from app.models.asset import RentalAsset
        with app.app_context():
            a = RentalAsset.query.filter_by(asset_title='Photo Test House').first()
            assert a is not None
            assert a.photo_path is None or a.photo_path == ''

    def test_asset_photo_upload_valid_jpg(self, client, app):
        _setup_landlord(client)
        r = _post_asset(client, photo_data=_minimal_jpeg(), photo_name='house.jpg')
        assert r.status_code == 200
        from app.models.asset import RentalAsset
        with app.app_context():
            # order_by id desc: test_asset_created_without_photo runs first and
            # leaves a row with photo_path=None; take the most recent row instead
            a = RentalAsset.query.filter_by(asset_title='Photo Test House') \
                                 .order_by(RentalAsset.id.desc()).first()
            assert a is not None
            assert a.photo_path

    def test_asset_photo_rejects_oversized_file(self, client, app):
        _setup_landlord(client)
        big = b'\xff\xd8' + b'\x00' * (5 * 1024 * 1024 + 1)
        r = _post_asset(client, photo_data=big, photo_name='big.jpg')
        assert r.status_code == 200
        assert b'5' in r.data or b'large' in r.data or b'size' in r.data

    def test_asset_photo_rejects_pdf_extension(self, client, app):
        _setup_landlord(client)
        r = _post_asset(client, photo_data=b'%PDF-1.4 fake',
                        photo_name='doc.pdf', content_type='application/pdf')
        assert r.status_code == 200
        assert b'JPG' in r.data or b'PNG' in r.data or b'WebP' in r.data or b'allowed' in r.data
