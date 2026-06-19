"""
Encrypted chat service.
Thread key: random AES-256 key, stored XOR-encrypted with a derivation of SECRET_KEY.
Each message: encrypted with thread key using AES-256-GCM; nonce per message.
"""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import current_app


def _master_key() -> bytes:
    """Derive a 32-byte master key from the app's SECRET_KEY."""
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    return hashlib.sha256(secret).digest()


def generate_thread_key() -> str:
    """Generate a new AES-256 thread key, return base64-encrypted-with-master."""
    raw_key = AESGCM.generate_key(bit_length=256)
    master = _master_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(master)
    encrypted = aesgcm.encrypt(nonce, raw_key, None)
    payload = nonce + encrypted
    return base64.b64encode(payload).decode('utf-8')


def _decrypt_thread_key(encrypted_thread_key_b64: str) -> bytes:
    payload = base64.b64decode(encrypted_thread_key_b64)
    nonce = payload[:12]
    ciphertext = payload[12:]
    master = _master_key()
    aesgcm = AESGCM(master)
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_message(thread_key_b64: str, plaintext: str) -> tuple[str, str, str]:
    """Encrypt a chat message. Returns (ciphertext_b64, nonce_b64, hash_hex)."""
    thread_key = _decrypt_thread_key(thread_key_b64)
    plaintext_bytes = plaintext.encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(thread_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    msg_hash = hashlib.sha256(plaintext_bytes).hexdigest()
    return (
        base64.b64encode(ciphertext).decode('utf-8'),
        base64.b64encode(nonce).decode('utf-8'),
        msg_hash,
    )


def decrypt_message(thread_key_b64: str, ciphertext_b64: str, nonce_b64: str) -> str:
    """Decrypt a chat message. Returns plaintext string."""
    thread_key = _decrypt_thread_key(thread_key_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(nonce_b64)
    aesgcm = AESGCM(thread_key)
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext_bytes.decode('utf-8')


def decrypt_thread_messages(thread) -> list[dict]:
    """Decrypt all messages in a ChatThread. Returns list of dicts."""
    from flask_login import current_user
    try:
        viewer_id = current_user.id if current_user.is_authenticated else None
    except Exception:
        viewer_id = None

    results = []
    for msg in thread.messages:
        try:
            if thread.encrypted_thread_key:
                text = decrypt_message(
                    thread.encrypted_thread_key,
                    msg.ciphertext_b64,
                    msg.nonce_b64,
                )
            else:
                text = '[encrypted]'
        except Exception:
            text = '[decryption error]'
        results.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name if msg.sender else 'Unknown',
            'sender_role': msg.sender.role if msg.sender else '',
            'text': text,
            'sent_at': msg.sent_at,
            'is_system': msg.is_system,
            'is_mine': msg.sender_id == viewer_id and not msg.is_system,
            'hash': msg.message_hash,
        })
    return results
