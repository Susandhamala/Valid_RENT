import uuid
from datetime import datetime
from app.extensions import db


class AgreementRequest(db.Model):
    """Tenant-initiated rental request to a landlord for an asset."""
    __tablename__ = 'agreement_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_uid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('rental_assets.id'))

    rental_category = db.Column(db.String(100), nullable=False)
    proposed_start_date = db.Column(db.Date)
    proposed_end_date = db.Column(db.Date)
    proposed_rent = db.Column(db.Float)
    currency = db.Column(db.String(10), default='NPR')
    tenant_message = db.Column(db.Text)          # initial request message

    # Negotiation / counters
    landlord_counter_rent = db.Column(db.Float)
    landlord_note = db.Column(db.Text)

    # Status lifecycle
    # pending → under_review → negotiating → approved → rejected → agreement_created
    status = db.Column(db.String(30), default='pending')

    # After approval → linked agreement
    agreement_id = db.Column(db.Integer, db.ForeignKey('rental_agreements.id'))

    # True when the landlord directly created an agreement and sent it for tenant review
    initiated_by_landlord = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)

    tenant = db.relationship('User', foreign_keys=[tenant_id])
    landlord = db.relationship('User', foreign_keys=[landlord_id])
    asset = db.relationship('RentalAsset')
    agreement = db.relationship('RentalAgreement', foreign_keys=[agreement_id])
    chat_thread = db.relationship('ChatThread', back_populates='request', uselist=False,
                                  cascade='all, delete-orphan', passive_deletes=True)
    approvals = db.relationship('PartyApproval', back_populates='request', lazy='dynamic')

    @property
    def effective_rent(self):
        return self.landlord_counter_rent or self.proposed_rent

    @property
    def status_label(self):
        return {
            'pending': 'Pending Review',
            'under_review': 'Under Review',
            'negotiating': 'Negotiating',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'agreement_created': 'Agreement Created',
        }.get(self.status, self.status.replace('_', ' ').title())


class PartyApproval(db.Model):
    """Tracks per-party approval for a request/agreement stage."""
    __tablename__ = 'party_approvals'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('agreement_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20))           # landlord | tenant
    stage = db.Column(db.String(30))          # terms_approval | document_approval
    approved = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime)
    note = db.Column(db.Text)

    request = db.relationship('AgreementRequest', back_populates='approvals')
    user = db.relationship('User')
