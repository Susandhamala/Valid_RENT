from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='tenant')  # landlord | tenant | admin
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # RSA key pair (PEM-encoded, stored as text)
    private_key_pem = db.Column(db.Text)
    public_key_pem = db.Column(db.Text)

    # Multi-role support: comma-separated e.g. "landlord" / "tenant" / "landlord,tenant"
    roles = db.Column(db.String(100))

    # Relationships
    certificates = db.relationship('Certificate', back_populates='user', lazy='dynamic')
    assets = db.relationship('RentalAsset', back_populates='owner', lazy='dynamic')
    photos = db.relationship('IdentityPhoto', back_populates='user', lazy='dynamic',
                             foreign_keys='IdentityPhoto.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, r):
        effective = self.roles or self.role
        return r in effective.split(',')

    def add_role(self, r):
        current = set((self.roles or self.role).split(','))
        current.add(r)
        self.roles = ','.join(sorted(current))

    @property
    def display_role(self):
        return self.role.capitalize()

    @property
    def all_roles(self):
        return (self.roles or self.role).split(',')

    def __repr__(self):
        return f'<User {self.email}>'
