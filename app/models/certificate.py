from datetime import datetime
from app.extensions import db


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    serial_number = db.Column(db.String(64), unique=True, nullable=False)
    subject_cn = db.Column(db.String(200))
    certificate_pem = db.Column(db.Text, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    revoked_at = db.Column(db.DateTime)
    revocation_reason = db.Column(db.String(200))

    user = db.relationship('User', back_populates='certificates')

    @property
    def is_valid(self):
        return not self.is_revoked and datetime.utcnow() < self.expires_at

    @property
    def status_display(self):
        if self.is_revoked:
            return 'Revoked'
        if datetime.utcnow() >= self.expires_at:
            return 'Expired'
        return 'Valid'
