from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models.agreement import RentalAgreement
from app.models.asset import RentalAsset
from app.models.certificate import Certificate
from app.models.request import AgreementRequest

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.home'))


@dashboard_bp.route('/dashboard')
@login_required
def home():
    cert = Certificate.query.filter_by(user_id=current_user.id, is_revoked=False).first()

    # All agreements where user is either party
    all_agreements_q = RentalAgreement.query.filter(
        or_(
            RentalAgreement.landlord_id == current_user.id,
            RentalAgreement.tenant_id == current_user.id,
        )
    ).order_by(RentalAgreement.created_at.desc())

    agreements = all_agreements_q.limit(8).all()
    total_agreements = all_agreements_q.count()

    pending = sum(1 for a in agreements
                  if a.status in ('draft', 'pending_tenant', 'landlord_signed', 'pending_signatures'))
    verified = sum(1 for a in agreements if a.status in ('fully_signed', 'verified'))

    # ── Landlord-side data ────────────────────────────────────────────────────
    assets = []
    total_assets = 0
    rented_assets = []      # landlord's properties that are currently rented (with tenant info)
    pending_requests = []

    if current_user.has_role('landlord'):
        assets = RentalAsset.query.filter_by(owner_id=current_user.id).order_by(
            RentalAsset.created_at.desc()).limit(6).all()
        total_assets = RentalAsset.query.filter_by(owner_id=current_user.id).count()

        # Pending incoming tenant requests
        pending_requests = AgreementRequest.query.filter_by(
            landlord_id=current_user.id, status='pending',
            initiated_by_landlord=False,
        ).order_by(AgreementRequest.created_at.desc()).all()

        # Rented assets: find the active (fully_signed) agreement for each rented asset
        rented_asset_rows = RentalAsset.query.filter_by(
            owner_id=current_user.id, status='rented').all()
        for asset in rented_asset_rows:
            active_ag = RentalAgreement.query.filter_by(
                asset_id=asset.id, landlord_id=current_user.id
            ).filter(RentalAgreement.status.in_(['fully_signed', 'verified'])
            ).order_by(RentalAgreement.created_at.desc()).first()
            rented_assets.append({'asset': asset, 'agreement': active_ag})

    # ── Tenant-side data ──────────────────────────────────────────────────────
    active_rentals = []         # fully-signed agreements where I am the tenant
    my_requests = []
    pending_direct_agreements = []  # landlord-initiated agreements awaiting my response

    if current_user.has_role('tenant'):
        active_rentals = RentalAgreement.query.filter_by(
            tenant_id=current_user.id
        ).filter(RentalAgreement.status.in_(['fully_signed', 'verified'])
        ).order_by(RentalAgreement.created_at.desc()).all()

        my_requests = AgreementRequest.query.filter_by(
            tenant_id=current_user.id
        ).order_by(AgreementRequest.created_at.desc()).limit(5).all()

        # Direct agreements sent by landlords that the tenant hasn't responded to yet
        pending_direct_agreements = AgreementRequest.query.filter_by(
            tenant_id=current_user.id,
            initiated_by_landlord=True,
            status='pending',
        ).order_by(AgreementRequest.created_at.desc()).all()

    return render_template('dashboard/dashboard.html',
                           pending_direct_agreements=pending_direct_agreements,
                           cert=cert,
                           agreements=agreements,
                           assets=assets,
                           total_agreements=total_agreements,
                           total_assets=total_assets,
                           pending=pending,
                           verified=verified,
                           pending_requests=pending_requests,
                           rented_assets=rented_assets,
                           active_rentals=active_rentals,
                           my_requests=my_requests)


@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not full_name:
            flash('Full name is required.', 'error')
            return redirect(url_for('dashboard.settings'))

        current_user.full_name = full_name
        current_user.phone = phone or None

        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('dashboard.settings'))
            if len(new_password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return redirect(url_for('dashboard.settings'))
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('dashboard.settings'))

    return render_template('dashboard/settings.html')
