from datetime import datetime
from app.extensions import db


class LegalDocumentTemplate(db.Model):
    """Bilingual legal agreement templates per rental category."""
    __tablename__ = 'legal_document_templates'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)   # house, vehicle, land, …
    version = db.Column(db.String(10), default='1.0')
    # English template (Jinja2-compatible with {{ }} placeholders)
    template_en = db.Column(db.Text, nullable=False)
    # Nepali template
    template_np = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
