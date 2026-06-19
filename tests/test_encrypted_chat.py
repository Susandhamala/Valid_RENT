"""Tests: encrypted chat storage and message decryption."""
import pytest
from app.services.chat_service import (
    generate_thread_key, encrypt_message, decrypt_message, decrypt_thread_messages
)
from app.models.chat import ChatThread, ChatMessage


class TestChatEncryption:
    def test_encrypt_decrypt_roundtrip(self, app):
        with app.app_context():
            key = generate_thread_key()
            plaintext = "Hello, this is a secret rental negotiation message."
            ct, nonce, h = encrypt_message(key, plaintext)
            assert ct != plaintext
            assert nonce
            result = decrypt_message(key, ct, nonce)
            assert result == plaintext

    def test_different_messages_produce_different_ciphertexts(self, app):
        with app.app_context():
            key = generate_thread_key()
            ct1, n1, _ = encrypt_message(key, "Message one")
            ct2, n2, _ = encrypt_message(key, "Message two")
            assert ct1 != ct2
            assert n1 != n2   # different nonces per message

    def test_tampered_ciphertext_fails_decryption(self, app):
        with app.app_context():
            key = generate_thread_key()
            ct, nonce, _ = encrypt_message(key, "Sensitive message")
            tampered = ct[:-4] + "XXXX"
            with pytest.raises(Exception):
                decrypt_message(key, tampered, nonce)

    def test_wrong_key_fails_decryption(self, app):
        with app.app_context():
            key1 = generate_thread_key()
            key2 = generate_thread_key()
            ct, nonce, _ = encrypt_message(key1, "My secret")
            with pytest.raises(Exception):
                decrypt_message(key2, ct, nonce)

    def test_send_message_api_requires_login(self, client, app):
        r = client.post('/chat/thread/999/send',
                        json={'text': 'hello'},
                        content_type='application/json')
        # Should redirect to login (302) or return 401/403
        assert r.status_code in (302, 401, 403)

    def test_empty_message_rejected(self, client, app):
        from tests.conftest import _register, _login
        _register(client, 'chatl@test.com', 'landlord', 'Chat Landlord')
        _register(client, 'chatt@test.com', 'tenant', 'Chat Tenant')
        _login(client, 'chatl@test.com')

        # First create a real thread via a request
        asset_id = _create_asset_for_chat(client, app, 'chatl@test.com')
        from tests.conftest import _logout
        _logout(client)

        _login(client, 'chatt@test.com')
        client.post(f'/requests/new/{asset_id}', data={
            'rental_category': 'House',
            'start_date': '2026-07-01',
            'proposed_rent': '8000',
            'currency': 'NPR',
            'tenant_message': 'Test',
        })

        from app.models.request import AgreementRequest
        with app.app_context():
            req = AgreementRequest.query.filter_by(rental_category='House').first()
            thread_id = req.chat_thread.id if req.chat_thread else None

        if thread_id:
            r = client.post(f'/chat/thread/{thread_id}/send',
                            json={'text': '   '},
                            content_type='application/json')
            assert r.status_code == 400
            data = r.get_json()
            assert not data['success']


def _create_asset_for_chat(client, app, landlord_email):
    from app.models.user import User
    from app.models.asset import AssetCategory, RentalAsset
    from app.extensions import db
    with app.app_context():
        landlord = User.query.filter_by(email=landlord_email).first()
        cat = AssetCategory.query.filter_by(name='House').first()
        asset = RentalAsset(
            owner_id=landlord.id, category_id=cat.id,
            asset_title='Chat Test House', location='Bhaktapur',
            status='available',
        )
        db.session.add(asset)
        db.session.commit()
        return asset.id
