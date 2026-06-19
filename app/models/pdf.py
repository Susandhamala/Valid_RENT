from datetime import datetime
from app.extensions import db


class GeneratedPDF(db.Model):
    __tablename__ = 'generated_pdfs'

    id = db.Column(db.Integer, primary_key=True)
    agreement_id = db.Column(db.Integer, db.ForeignKey('rental_agreements.id'), nullable=False)
    pdf_file_path = db.Column(db.String(500))
    pdf_hash_sha256 = db.Column(db.String(64))
    verification_code = db.Column(db.String(64), unique=True)
    qr_code_path = db.Column(db.String(500))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    agreement = db.relationship('RentalAgreement', back_populates='generated_pdfs')
