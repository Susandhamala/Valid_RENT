from flask import Flask, session, redirect, request as flask_request, url_for, jsonify, flash
from flask_login import login_required, current_user
from pathlib import Path
from app.config import Config
from app.extensions import db, login_manager, csrf
from app.i18n import get_translations, SUPPORTED


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Blueprints ──────────────────────────────────────────────────────────
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.asset_routes import asset_bp
    from app.routes.agreement_routes import agreement_bp
    from app.routes.photo_routes import photo_bp
    from app.routes.pdf_routes import pdf_bp
    from app.routes.verification_routes import verification_bp
    from app.routes.request_routes import req_bp
    from app.routes.chat_routes import chat_bp
    from app.routes.admin_routes import admin_bp

    for bp in (auth_bp, dashboard_bp, asset_bp, agreement_bp,
               photo_bp, pdf_bp, verification_bp, req_bp, chat_bp, admin_bp):
        app.register_blueprint(bp)

    # ── User loader ─────────────────────────────────────────────────────────
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Template filter: pending request badge count ─────────────────────
    from app.models.request import AgreementRequest

    @app.template_filter('pending_requests_count')
    def pending_requests_count(user_id):
        # Tenant-initiated requests waiting on this user as landlord
        landlord_pending = AgreementRequest.query.filter_by(
            landlord_id=user_id, status='pending').filter(
            AgreementRequest.initiated_by_landlord == False).count()
        # Landlord-initiated direct agreements waiting on this user as tenant
        tenant_pending = AgreementRequest.query.filter_by(
            tenant_id=user_id, status='pending', initiated_by_landlord=True).count()
        return landlord_pending + tenant_pending

    # ── Language switching ───────────────────────────────────────────────────
    @app.route('/set-lang/<lang>')
    def set_lang(lang):
        if lang in SUPPORTED:
            session['lang'] = lang
        referrer = flask_request.referrer or '/'
        return redirect(referrer)

    # ── Auto role-switching based on page visited ─────────────────────────────
    # Endpoints that are clearly landlord-context
    _LANDLORD_ENDPOINTS = frozenset({
        'asset.list_assets', 'asset.create_asset', 'asset.edit_asset',
        'asset.delete_asset', 'agreement.create_agreement',
        'agreement.list_agreements',
    })
    # Endpoints that are clearly tenant-context
    _TENANT_ENDPOINTS = frozenset({
        'asset.browse', 'asset.view_asset',
        'req.list_requests', 'req.create_request',
    })

    @app.before_request
    def auto_switch_role():
        if not current_user.is_authenticated:
            return
        if len(current_user.all_roles) < 2:
            return  # single-role user, nothing to auto-switch
        endpoint = flask_request.endpoint or ''
        if endpoint in _LANDLORD_ENDPOINTS and current_user.has_role('landlord'):
            session['active_role'] = 'landlord'
        elif endpoint in _TENANT_ENDPOINTS and current_user.has_role('tenant'):
            session['active_role'] = 'tenant'

    # ── Role switching (multi-role support) ──────────────────────────────────
    @app.route('/switch-role', methods=['POST'])
    @login_required
    def switch_role():
        new_role = flask_request.form.get('role', '').strip()
        if new_role not in ('landlord', 'tenant') or not current_user.has_role(new_role):
            flash('You are not authorized to switch to that role.', 'error')
            return redirect(flask_request.referrer or url_for('dashboard.home'))
        session['active_role'] = new_role
        flash(f'Switched to {new_role.capitalize()} mode.', 'success')
        referrer = flask_request.referrer or url_for('dashboard.home')
        return redirect(referrer)

    @app.route('/add-role', methods=['POST'])
    @login_required
    def add_role():
        new_role = flask_request.form.get('role', '').strip()
        if new_role not in ('landlord', 'tenant'):
            flash('Invalid role.', 'error')
            return redirect(flask_request.referrer or url_for('dashboard.home'))
        current_user.add_role(new_role)
        if 'active_role' not in session:
            session['active_role'] = new_role
        db.session.commit()
        flash(f'You can now also act as a {new_role.capitalize()}.', 'success')
        return redirect(flask_request.referrer or url_for('dashboard.home'))

    # ── Translation + active_role context processor ────────────────────────
    @app.context_processor
    def inject_lang():
        lang = session.get('lang', 'en')
        active_role = None
        if current_user.is_authenticated:
            active_role = session.get('active_role', current_user.role)
        return dict(
            tr=get_translations(lang),
            lang=lang,
            supported_langs=SUPPORTED,
            active_role=active_role,
        )

    # ── DB init + seed + migration ──────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _run_migrations()
        _seed_categories()

    return app


def _run_migrations():
    """Add new columns to existing tables without breaking existing data."""
    from sqlalchemy import text
    migrations = [
        ("users", "roles", "ALTER TABLE users ADD COLUMN roles TEXT"),
        ("rental_assets", "photo_path", "ALTER TABLE rental_assets ADD COLUMN photo_path TEXT"),
        ("rental_assets", "rent_period", "ALTER TABLE rental_assets ADD COLUMN rent_period TEXT DEFAULT 'per_month'"),
        ("rental_agreements", "landlord_remarks", "ALTER TABLE rental_agreements ADD COLUMN landlord_remarks TEXT"),
        ("rental_agreements", "tenant_remarks", "ALTER TABLE rental_agreements ADD COLUMN tenant_remarks TEXT"),
        ("rental_agreements", "landlord_delete_requested", "ALTER TABLE rental_agreements ADD COLUMN landlord_delete_requested DATETIME"),
        ("rental_agreements", "tenant_delete_requested", "ALTER TABLE rental_agreements ADD COLUMN tenant_delete_requested DATETIME"),
        ("rental_agreements", "landlord_verified_at", "ALTER TABLE rental_agreements ADD COLUMN landlord_verified_at DATETIME"),
        ("rental_agreements", "tenant_verified_at", "ALTER TABLE rental_agreements ADD COLUMN tenant_verified_at DATETIME"),
        ("rental_agreements", "shared_file_path", "ALTER TABLE rental_agreements ADD COLUMN shared_file_path TEXT"),
        ("agreement_requests", "initiated_by_landlord", "ALTER TABLE agreement_requests ADD COLUMN initiated_by_landlord BOOLEAN DEFAULT 0"),
        ("identity_photos", "document_path", "ALTER TABLE identity_photos ADD COLUMN document_path TEXT"),
        ("identity_photos", "document_type", "ALTER TABLE identity_photos ADD COLUMN document_type TEXT"),
        ("identity_photos", "document_approved", "ALTER TABLE identity_photos ADD COLUMN document_approved BOOLEAN DEFAULT 0"),
        ("identity_photos", "document_approved_at", "ALTER TABLE identity_photos ADD COLUMN document_approved_at DATETIME"),
        ("identity_photos", "document_approved_by", "ALTER TABLE identity_photos ADD COLUMN document_approved_by INTEGER"),
    ]
    for table, column, sql in migrations:
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()

    # Backfill roles from role for existing users
    try:
        db.session.execute(text("UPDATE users SET roles = role WHERE roles IS NULL"))
        db.session.commit()
    except Exception:
        db.session.rollback()


def _seed_categories():
    from app.models.asset import AssetCategory

    categories = [
        {'name': 'House',             'description': 'Residential house rental',          'icon': 'home',      'risk_level': 'medium'},
        {'name': 'Room',              'description': 'Single room rental',                'icon': 'door-open', 'risk_level': 'low'},
        {'name': 'Apartment',         'description': 'Apartment or flat rental',          'icon': 'building',  'risk_level': 'medium'},
        {'name': 'Land',              'description': 'Land lease agreements',             'icon': 'map',       'risk_level': 'high'},
        {'name': 'Automobile',        'description': 'Car, truck, or vehicle rental',     'icon': 'car',       'risk_level': 'high'},
        {'name': 'Bike/Scooter',      'description': 'Motorcycle or scooter rental',      'icon': 'bicycle',   'risk_level': 'medium'},
        {'name': 'Machinery',         'description': 'Heavy machinery or equipment',      'icon': 'gear',      'risk_level': 'high'},
        {'name': 'Office/Commercial', 'description': 'Office or commercial space rental', 'icon': 'briefcase', 'risk_level': 'medium'},
        {'name': 'Storage/Warehouse', 'description': 'Storage unit or warehouse rental',  'icon': 'box',       'risk_level': 'low'},
        {'name': 'Other',             'description': 'Other sensitive rental assets',     'icon': 'tag',       'risk_level': 'medium'},
    ]
    for cat_data in categories:
        if not AssetCategory.query.filter_by(name=cat_data['name']).first():
            db.session.add(AssetCategory(**cat_data))
    db.session.commit()
