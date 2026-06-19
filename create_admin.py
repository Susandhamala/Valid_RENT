"""Run this once to create the admin user."""
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.certificate import Certificate
from app.services.crypto_service import generate_rsa_keypair
from app.services.certificate_service import issue_certificate

app = create_app()

ADMIN_EMAIL    = 'admin@validrent.com'
ADMIN_PASSWORD = 'Admin@1234'
ADMIN_NAME     = 'System Administrator'

with app.app_context():
    existing = User.query.filter_by(email=ADMIN_EMAIL).first()
    if existing:
        existing.role = 'admin'
        existing.is_active = True
        db.session.commit()
        print(f'[OK] Existing user promoted to admin: {ADMIN_EMAIL}')
    else:
        priv, pub = generate_rsa_keypair()
        admin = User(
            full_name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            role='admin',
            is_active=True,
        )
        admin.set_password(ADMIN_PASSWORD)
        admin.private_key_pem = priv
        admin.public_key_pem  = pub
        db.session.add(admin)
        db.session.flush()

        cert_data = issue_certificate(pub, ADMIN_NAME, ADMIN_EMAIL)
        db.session.add(Certificate(user_id=admin.id, **cert_data))
        db.session.commit()
        print(f'[OK] Admin user created!')

    print(f'    Email   : {ADMIN_EMAIL}')
    print(f'    Password: {ADMIN_PASSWORD}')
    print(f'    URL     : http://127.0.0.1:5000/admin/')
