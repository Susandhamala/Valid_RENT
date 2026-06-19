from datetime import datetime
import uuid
from app.extensions import db


class RentalAgreement(db.Model):
    __tablename__ = 'rental_agreements'

    id = db.Column(db.Integer, primary_key=True)
    agreement_uid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    asset_id = db.Column(db.Integer, db.ForeignKey('rental_assets.id'))

    rental_category = db.Column(db.String(100))
    agreement_type = db.Column(db.String(50), default='standard')

    # Encrypted file info
    encrypted_file_path = db.Column(db.String(500))
    shared_file_path = db.Column(db.String(500))   # readable copy served to both parties
    original_filename = db.Column(db.String(200))
    document_hash_sha256 = db.Column(db.String(64))
    aes_key_encrypted = db.Column(db.Text)  # AES key encrypted with landlord's RSA public key
    aes_nonce = db.Column(db.String(32))

    # Agreement details
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    rent_amount = db.Column(db.Float)
    currency = db.Column(db.String(10), default='NPR')
    terms = db.Column(db.Text)

    # Signing
    landlord_signature = db.Column(db.Text)
    tenant_signature = db.Column(db.Text)
    landlord_signed_at = db.Column(db.DateTime)
    tenant_signed_at = db.Column(db.DateTime)
    landlord_remarks = db.Column(db.Text)
    tenant_remarks = db.Column(db.Text)

    # Mutual deletion consent (fully-signed agreements only)
    landlord_delete_requested = db.Column(db.DateTime)
    tenant_delete_requested = db.Column(db.DateTime)

    # Mutual verification acknowledgement
    landlord_verified_at = db.Column(db.DateTime)
    tenant_verified_at = db.Column(db.DateTime)

    @property
    def both_requested_delete(self):
        return bool(self.landlord_delete_requested and self.tenant_delete_requested)

    # Verification
    landlord_cert_serial = db.Column(db.String(64))
    tenant_cert_serial = db.Column(db.String(64))
    verification_code = db.Column(db.String(64), unique=True)
    final_pdf_status = db.Column(db.String(20), default='pending')  # pending | generated | failed

    # Status
    status = db.Column(db.String(30), default='draft')
    # draft | pending_tenant | landlord_signed | fully_signed | verified | cancelled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    landlord = db.relationship('User', foreign_keys=[landlord_id])
    tenant = db.relationship('User', foreign_keys=[tenant_id])
    asset = db.relationship('RentalAsset', back_populates='agreements')
    photos = db.relationship('IdentityPhoto', back_populates='agreement', lazy='dynamic')
    generated_pdfs = db.relationship('GeneratedPDF', back_populates='agreement', lazy='dynamic')

    @property
    def is_fully_signed(self):
        return bool(self.landlord_signature and self.tenant_signature)
