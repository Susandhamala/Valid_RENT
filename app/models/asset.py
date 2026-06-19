from datetime import datetime
from app.extensions import db


class AssetCategory(db.Model):
    __tablename__ = 'asset_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='building')
    risk_level = db.Column(db.String(20), default='medium')  # low | medium | high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assets = db.relationship('RentalAsset', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<AssetCategory {self.name}>'


class RentalAsset(db.Model):
    __tablename__ = 'rental_assets'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('asset_categories.id'), nullable=False)
    asset_title = db.Column(db.String(200), nullable=False)
    asset_type = db.Column(db.String(100))
    asset_identifier = db.Column(db.String(200))  # plate no, plot no, serial no, etc.
    description = db.Column(db.Text)
    location = db.Column(db.String(300))
    estimated_value = db.Column(db.Float)
    rent_period = db.Column(db.String(20), default='per_month')  # per_month | per_day | per_year | fixed
    status = db.Column(db.String(20), default='available')  # available | rented | inactive
    photo_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', back_populates='assets')
    category = db.relationship('AssetCategory', back_populates='assets')
    agreements = db.relationship('RentalAgreement', back_populates='asset', lazy='dynamic')

    _PERIOD_LABELS = {
        'per_month': '/ month',
        'per_day': '/ day',
        'per_year': '/ year',
        'fixed': 'fixed price',
    }

    @property
    def rent_period_label(self):
        return self._PERIOD_LABELS.get(self.rent_period or 'per_month', '/ month')

    def __repr__(self):
        return f'<RentalAsset {self.asset_title}>'
