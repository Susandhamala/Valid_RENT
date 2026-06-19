import uuid
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from app.services.crypto_service import load_private_key, load_public_key

# Self-signed CA (generated once at module level for demo)
_CA_KEY = None
_CA_CERT = None


def _get_or_create_ca():
    global _CA_KEY, _CA_CERT
    if _CA_KEY and _CA_CERT:
        return _CA_KEY, _CA_CERT

    from cryptography.hazmat.primitives.asymmetric import rsa
    ca_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'NP'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Bagmati'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Valid Rent Authority Demo'),
        x509.NameAttribute(NameOID.COMMON_NAME, 'Valid Rent Demo CA'),
    ])
    now = datetime.now(timezone.utc)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256(), default_backend())
    )
    _CA_KEY = ca_key
    _CA_CERT = ca_cert
    return _CA_KEY, _CA_CERT


def issue_certificate(user_public_key_pem, user_full_name, user_email):
    """Issue an X.509 certificate signed by the Valid Rent Demo CA."""
    ca_key, ca_cert = _get_or_create_ca()
    public_key = load_public_key(user_public_key_pem)

    serial = x509.random_serial_number()
    serial_hex = format(serial, 'x').upper()

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'NP'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Bagmati'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Valid Rent Platform'),
        x509.NameAttribute(NameOID.COMMON_NAME, user_full_name),
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, user_email),
    ])

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=365)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(public_key)
        .serial_number(serial)
        .not_valid_before(now)
        .not_valid_after(expires_at)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256(), default_backend())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')

    return {
        'serial_number': serial_hex,
        'certificate_pem': cert_pem,
        'issued_at': now.replace(tzinfo=None),
        'expires_at': expires_at.replace(tzinfo=None),
        'subject_cn': user_full_name,
    }


def verify_certificate(cert_pem):
    """Verify a certificate against the Demo CA. Returns (valid: bool, reason: str)."""
    try:
        ca_key, ca_cert = _get_or_create_ca()
        cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())

        # Check not expired
        now = datetime.now(timezone.utc)
        if cert.not_valid_after_utc < now:
            return False, 'Certificate has expired'
        if cert.not_valid_before_utc > now:
            return False, 'Certificate not yet valid'

        # Verify signature against CA
        ca_cert.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            __import__('cryptography.hazmat.primitives.asymmetric.padding', fromlist=['PKCS1v15']).PKCS1v15(),
            cert.signature_hash_algorithm,
        )
        return True, 'Valid'
    except Exception as e:
        return False, str(e)
