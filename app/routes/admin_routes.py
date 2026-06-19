"""Admin panel — full control over users, assets, agreements, requests, categories."""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models.user import User
from app.models.asset import RentalAsset, AssetCategory
from app.models.agreement import RentalAgreement
from app.models.request import AgreementRequest
from app.models.certificate import Certificate
from app.models.chat import ChatThread, ChatMessage
from app.models.photo import IdentityPhoto
from app.models.pdf import GeneratedPDF

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'users':       User.query.count(),
        'landlords':   User.query.filter_by(role='landlord').count(),
        'tenants':     User.query.filter_by(role='tenant').count(),
        'assets':      RentalAsset.query.count(),
        'agreements':  RentalAgreement.query.count(),
        'requests':    AgreementRequest.query.count(),
        'certs':       Certificate.query.count(),
        'pdfs':        GeneratedPDF.query.count(),
        'messages':    ChatMessage.query.count(),
        'photos':      IdentityPhoto.query.count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_requests = AgreementRequest.query.order_by(AgreementRequest.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users, recent_requests=recent_requests)


# ── USERS ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@admin_required
def users():
    q = request.args.get('q', '').strip()
    role = request.args.get('role', '')
    query = User.query
    if q:
        query = query.filter(
            db.or_(User.full_name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'))
        )
    if role:
        query = query.filter_by(role=role)
    users_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users_list, q=q, role=role)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        role      = request.form.get('role', 'tenant')
        password  = request.form.get('password', '')
        gen_keys  = request.form.get('gen_keys') == '1'

        if not full_name or not email or not password:
            flash('Name, email and password are required.', 'danger')
            return redirect(url_for('admin.create_user'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.create_user'))

        user = User(full_name=full_name, email=email, phone=phone, role=role)
        user.set_password(password)

        if gen_keys:
            from app.services.crypto_service import generate_rsa_keypair
            from app.services.certificate_service import issue_certificate
            priv, pub = generate_rsa_keypair()
            user.private_key_pem = priv
            user.public_key_pem  = pub
            db.session.add(user)
            db.session.flush()
            cert_data = issue_certificate(pub, full_name, email)
            db.session.add(Certificate(user_id=user.id, **cert_data))
        else:
            db.session.add(user)

        db.session.commit()
        flash(f'User {email} created.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html')


@admin_bp.route('/users/<int:user_id>')
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    cert = Certificate.query.filter_by(user_id=user.id).order_by(Certificate.id.desc()).first()
    assets = RentalAsset.query.filter_by(owner_id=user.id).all()
    agreements = RentalAgreement.query.filter(
        db.or_(RentalAgreement.landlord_id == user.id,
               RentalAgreement.tenant_id == user.id)
    ).order_by(RentalAgreement.id.desc()).limit(10).all()
    requests = AgreementRequest.query.filter(
        db.or_(AgreementRequest.tenant_id == user.id,
               AgreementRequest.landlord_id == user.id)
    ).order_by(AgreementRequest.created_at.desc()).limit(10).all()
    return render_template('admin/view_user.html', user=user, cert=cert,
                           assets=assets, agreements=agreements, requests=requests)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.email     = request.form.get('email', user.email).strip().lower()
        user.phone     = request.form.get('phone', '').strip()
        new_role = request.form.get('role', user.role)
        if not (user_id == current_user.id and new_role != 'admin'):
            user.role = new_role
        user.is_active = request.form.get('is_active') == '1'
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('new_password', '').strip()
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'danger')
    else:
        user.set_password(new_pw)
        db.session.commit()
        flash(f'Password for {user.email} reset.', 'success')
    return redirect(url_for('admin.view_user', user_id=user.id))


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.view_user', user_id=user.id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot delete yourself.', 'danger')
        return redirect(url_for('admin.users'))
    email = user.email
    db.session.delete(user)
    db.session.commit()
    flash(f'User {email} deleted.', 'success')
    return redirect(url_for('admin.users'))


# ── ASSETS ───────────────────────────────────────────────────────────────────

@admin_bp.route('/assets')
@admin_required
def assets():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    query = RentalAsset.query
    if q:
        query = query.filter(
            db.or_(RentalAsset.asset_title.ilike(f'%{q}%'),
                   RentalAsset.location.ilike(f'%{q}%'))
        )
    if status:
        query = query.filter_by(status=status)
    assets_list = query.order_by(RentalAsset.created_at.desc()).all()
    return render_template('admin/assets.html', assets=assets_list, q=q, status=status)


@admin_bp.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_asset(asset_id):
    asset = RentalAsset.query.get_or_404(asset_id)
    categories = AssetCategory.query.all()
    if request.method == 'POST':
        asset.asset_title      = request.form.get('asset_title', asset.asset_title).strip()
        asset.location         = request.form.get('location', '').strip()
        asset.description      = request.form.get('description', '').strip()
        asset.asset_identifier = request.form.get('asset_identifier', '').strip()
        asset.status           = request.form.get('status', asset.status)
        cat_id = request.form.get('category_id')
        if cat_id:
            asset.category_id = int(cat_id)
        val = request.form.get('estimated_value', '')
        asset.estimated_value = float(val) if val else None
        db.session.commit()
        flash('Asset updated.', 'success')
        return redirect(url_for('admin.assets'))
    return render_template('admin/edit_asset.html', asset=asset, categories=categories)


@admin_bp.route('/assets/<int:asset_id>/delete', methods=['POST'])
@admin_required
def delete_asset(asset_id):
    asset = RentalAsset.query.get_or_404(asset_id)
    title = asset.asset_title
    db.session.delete(asset)
    db.session.commit()
    flash(f'Asset "{title}" deleted.', 'success')
    return redirect(url_for('admin.assets'))


# ── AGREEMENTS ────────────────────────────────────────────────────────────────

@admin_bp.route('/agreements')
@admin_required
def agreements():
    status = request.args.get('status', '')
    query = RentalAgreement.query
    if status:
        query = query.filter_by(status=status)
    ags = query.order_by(RentalAgreement.id.desc()).all()
    return render_template('admin/agreements.html', agreements=ags, status=status)


@admin_bp.route('/agreements/<int:ag_id>/delete', methods=['POST'])
@admin_required
def delete_agreement(ag_id):
    ag = RentalAgreement.query.get_or_404(ag_id)
    uid = str(ag.agreement_uid)[:12]
    db.session.delete(ag)
    db.session.commit()
    flash(f'Agreement {uid}... deleted.', 'success')
    return redirect(url_for('admin.agreements'))


# ── REQUESTS ──────────────────────────────────────────────────────────────────

@admin_bp.route('/requests')
@admin_required
def requests_list():
    status = request.args.get('status', '')
    query = AgreementRequest.query
    if status:
        query = query.filter_by(status=status)
    reqs = query.order_by(AgreementRequest.created_at.desc()).all()
    return render_template('admin/requests.html', requests=reqs, status=status)


@admin_bp.route('/requests/<int:req_id>/delete', methods=['POST'])
@admin_required
def delete_request(req_id):
    req = AgreementRequest.query.get_or_404(req_id)
    db.session.delete(req)
    db.session.commit()
    flash('Request deleted.', 'success')
    return redirect(url_for('admin.requests_list'))


# ── CERTIFICATES ──────────────────────────────────────────────────────────────

@admin_bp.route('/certificates')
@admin_required
def certificates():
    certs = Certificate.query.order_by(Certificate.id.desc()).all()
    return render_template('admin/certificates.html', certs=certs)


@admin_bp.route('/certificates/<int:cert_id>/revoke', methods=['POST'])
@admin_required
def revoke_cert(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    from datetime import datetime
    cert.is_revoked = True
    cert.revoked_at = datetime.utcnow()
    cert.revocation_reason = request.form.get('reason', 'Revoked by admin')
    db.session.commit()
    flash(f'Certificate {cert.serial_number[:16]}... revoked.', 'success')
    return redirect(url_for('admin.certificates'))


@admin_bp.route('/certificates/<int:cert_id>/restore', methods=['POST'])
@admin_required
def restore_cert(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    cert.is_revoked = False
    cert.revoked_at = None
    cert.revocation_reason = None
    db.session.commit()
    flash('Certificate restored.', 'success')
    return redirect(url_for('admin.certificates'))


# ── CATEGORIES ────────────────────────────────────────────────────────────────

@admin_bp.route('/categories')
@admin_required
def categories():
    cats = AssetCategory.query.all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/create', methods=['POST'])
@admin_required
def create_category():
    name = request.form.get('name', '').strip()
    desc = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'tag').strip()
    risk = request.form.get('risk_level', 'medium')
    if not name:
        flash('Category name is required.', 'danger')
    elif AssetCategory.query.filter_by(name=name).first():
        flash('Category already exists.', 'danger')
    else:
        db.session.add(AssetCategory(name=name, description=desc, icon=icon, risk_level=risk))
        db.session.commit()
        flash(f'Category "{name}" created.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def delete_category(cat_id):
    cat = AssetCategory.query.get_or_404(cat_id)
    if cat.assets.count() > 0:
        flash('Cannot delete category with existing assets.', 'danger')
    else:
        name = cat.name
        db.session.delete(cat)
        db.session.commit()
        flash(f'Category "{name}" deleted.', 'success')
    return redirect(url_for('admin.categories'))
