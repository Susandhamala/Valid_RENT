from datetime import datetime
from app.extensions import db


class IdentityPhoto(db.Model):
    __tablename__ = 'identity_photos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agreement_id = db.Column(db.Integer, db.ForeignKey('rental_agreements.id'), nullable=False)
    photo_encrypted_path = db.Column(db.String(500))
    photo_hash_sha256 = db.Column(db.String(64))
    consent_given = db.Column(db.Boolean, default=False)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)
    purpose = db.Column(db.String(100), default='agreement_evidence')

    # Identity document uploaded by tenant alongside webcam photo
    document_path = db.Column(db.String(500))          # path to ID document image/PDF
    document_type = db.Column(db.String(50))           # citizenship / passport / driving_license / voter_id
    document_approved = db.Column(db.Boolean, default=False)
    document_approved_at = db.Column(db.DateTime)
    document_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User', foreign_keys=[user_id], back_populates='photos')
    approved_by_user = db.relationship('User', foreign_keys=[document_approved_by])
    agreement = db.relationship('RentalAgreement', back_populates='photos')
