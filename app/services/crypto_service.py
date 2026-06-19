import os
import hashlib
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


def generate_rsa_keypair():
    """Generate RSA-2048 key pair, return (private_pem, public_pem) strings."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return private_pem, public_pem


def load_private_key(pem_str):
    return serialization.load_pem_private_key(
        pem_str.encode('utf-8'), password=None, backend=default_backend()
    )


def load_public_key(pem_str):
    return serialization.load_pem_public_key(
        pem_str.encode('utf-8'), backend=default_backend()
    )


def sha256_hash_file(file_path):
    """Return hex SHA-256 hash of file at path."""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encrypt_file_aes256gcm(file_path, output_path):
    """Encrypt file using AES-256-GCM. Returns (aes_key_b64, nonce_b64)."""
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aesgcm = AESGCM(aes_key)

    with open(file_path, 'rb') as f:
        plaintext = f.read()

    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    with open(output_path, 'wb') as f:
        f.write(ciphertext)

    return (
        base64.b64encode(aes_key).decode('utf-8'),
        base64.b64encode(nonce).decode('utf-8')
    )


def decrypt_file_aes256gcm(encrypted_path, output_path, aes_key_b64, nonce_b64):
    """Decrypt AES-256-GCM encrypted file."""
    aes_key = base64.b64decode(aes_key_b64)
    nonce = base64.b64decode(nonce_b64)
    aesgcm = AESGCM(aes_key)

    with open(encrypted_path, 'rb') as f:
        ciphertext = f.read()

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    with open(output_path, 'wb') as f:
        f.write(plaintext)


def rsa_sign(private_key_pem, data_hex):
    """Sign the hex-encoded document hash using RSA-PSS with SHA-256."""
    private_key = load_private_key(private_key_pem)
    data_bytes = bytes.fromhex(data_hex)

    signature = private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')


def rsa_verify(public_key_pem, data_hex, signature_b64):
    """Verify RSA-PSS signature. Returns True if valid."""
    try:
        public_key = load_public_key(public_key_pem)
        data_bytes = bytes.fromhex(data_hex)
        signature = base64.b64decode(signature_b64)

        public_key.verify(
            signature,
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


def encrypt_rsa_oaep(public_key_pem, plaintext_bytes):
    """Encrypt bytes with RSA OAEP (for wrapping AES key)."""
    public_key = load_public_key(public_key_pem)
    ciphertext = public_key.encrypt(
        plaintext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(ciphertext).decode('utf-8')


def decrypt_rsa_oaep(private_key_pem, ciphertext_b64):
    """Decrypt RSA OAEP encrypted bytes."""
    private_key = load_private_key(private_key_pem)
    ciphertext = base64.b64decode(ciphertext_b64)
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext
