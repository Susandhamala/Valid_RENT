import os
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.asset import AssetCategory, RentalAsset

asset_bp = Blueprint('asset', __name__, url_prefix='/assets')

_ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
_MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB


def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_IMAGE_EXTENSIONS


@asset_bp.route('/')
@login_required
def list_assets():
    if not current_user.has_role('landlord'):
        return redirect(url_for('asset.browse'))
    assets = RentalAsset.query.filter_by(owner_id=current_user.id).order_by(
        RentalAsset.created_at.desc()).all()
    return render_template('assets/asset_list.html', assets=assets)


@asset_bp.route('/browse')
@login_required
def browse():
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('q', '').strip()

    q = RentalAsset.query.filter(RentalAsset.status.in_(['available', 'rented']))
    if category_id:
        q = q.filter_by(category_id=category_id)
    if search:
        q = q.filter(
            RentalAsset.asset_title.ilike(f'%{search}%') |
            RentalAsset.location.ilike(f'%{search}%') |
            RentalAsset.description.ilike(f'%{search}%')
        )

    assets = q.order_by(RentalAsset.created_at.desc()).all()
    categories = AssetCategory.query.order_by(AssetCategory.name).all()
    return render_template('assets/browse.html', assets=assets,
                           categories=categories,
                           selected_cat=category_id, search=search)


@asset_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_asset():
    if not current_user.has_role('landlord'):
        flash('Only landlords can create assets. Add the Landlord role from your dashboard.', 'error')
        return redirect(url_for('dashboard.home'))

    categories = AssetCategory.query.order_by(AssetCategory.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        asset_title = request.form.get('asset_title', '').strip()
        asset_type = request.form.get('asset_type', '').strip()
        asset_identifier = request.form.get('asset_identifier', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        estimated_value = request.form.get('estimated_value', 0)

        if not asset_title or not category_id:
            flash('Asset title and category are required.', 'error')
            return render_template('assets/asset_create.html', categories=categories, form_data=request.form)

        try:
            estimated_value = float(estimated_value) if estimated_value else 0
        except ValueError:
            estimated_value = 0

        rent_period = request.form.get('rent_period', 'per_month')

        asset = RentalAsset(
            owner_id=current_user.id,
            category_id=int(category_id),
            asset_title=asset_title,
            asset_type=asset_type,
            asset_identifier=asset_identifier,
            description=description,
            location=location,
            estimated_value=estimated_value,
            rent_period=rent_period,
        )
        db.session.add(asset)
        db.session.flush()

        # ── Photo upload ───────────────────────────────────────────────────
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            if not _allowed_image(photo_file.filename):
                flash('Photo must be JPG, PNG, or WebP.', 'error')
                db.session.rollback()
                return render_template('assets/asset_create.html', categories=categories, form_data=request.form)

            photo_bytes = photo_file.read()
            if len(photo_bytes) > _MAX_PHOTO_BYTES:
                flash('Photo must be under 5 MB.', 'error')
                db.session.rollback()
                return render_template('assets/asset_create.html', categories=categories, form_data=request.form)

            photos_dir = Path(current_app.config['ASSET_PHOTOS_DIR'])
            photos_dir.mkdir(parents=True, exist_ok=True)
            ext = secure_filename(photo_file.filename).rsplit('.', 1)[1].lower()
            filename = f"asset_{asset.id}.{ext}"
            save_path = photos_dir / filename
            save_path.write_bytes(photo_bytes)
            asset.photo_path = str(save_path)

        db.session.commit()
        flash(f'Asset "{asset_title}" created successfully!', 'success')
        return redirect(url_for('asset.list_assets'))

    return render_template('assets/asset_create.html', categories=categories, form_data={})


@asset_bp.route('/<int:asset_id>/photo')
def asset_photo(asset_id):
    """Serve asset listing photo — public, no login required."""
    asset = RentalAsset.query.get_or_404(asset_id)
    if not asset.photo_path or not os.path.exists(asset.photo_path):
        from flask import abort
        abort(404)
    return send_file(asset.photo_path)


@asset_bp.route('/<int:asset_id>')
@login_required
def view_asset(asset_id):
    asset = RentalAsset.query.get_or_404(asset_id)
    return render_template('assets/asset_detail.html', asset=asset)


@asset_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    asset = RentalAsset.query.get_or_404(asset_id)
    if asset.owner_id != current_user.id:
        flash('You can only edit your own listings.', 'error')
        return redirect(url_for('asset.list_assets'))

    categories = AssetCategory.query.order_by(AssetCategory.name).all()

    if request.method == 'POST':
        category_id = request.form.get('category_id')
        asset_title = request.form.get('asset_title', '').strip()
        if not asset_title or not category_id:
            flash('Asset title and category are required.', 'error')
            return render_template('assets/asset_edit.html', asset=asset, categories=categories)

        asset.category_id = int(category_id)
        asset.asset_title = asset_title
        asset.asset_type = request.form.get('asset_type', '').strip()
        asset.asset_identifier = request.form.get('asset_identifier', '').strip()
        asset.description = request.form.get('description', '').strip()
        asset.location = request.form.get('location', '').strip()
        asset.status = request.form.get('status', asset.status)
        asset.rent_period = request.form.get('rent_period', 'per_month')

        try:
            ev = request.form.get('estimated_value', '')
            asset.estimated_value = float(ev) if ev else None
        except ValueError:
            asset.estimated_value = None

        # Optional new photo
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename:
            if not _allowed_image(photo_file.filename):
                flash('Photo must be JPG, PNG, or WebP.', 'error')
                return render_template('assets/asset_edit.html', asset=asset, categories=categories)
            photo_bytes = photo_file.read()
            if len(photo_bytes) > _MAX_PHOTO_BYTES:
                flash('Photo must be under 5 MB.', 'error')
                return render_template('assets/asset_edit.html', asset=asset, categories=categories)
            photos_dir = Path(current_app.config['ASSET_PHOTOS_DIR'])
            photos_dir.mkdir(parents=True, exist_ok=True)
            ext = secure_filename(photo_file.filename).rsplit('.', 1)[1].lower()
            filename = f"asset_{asset.id}.{ext}"
            save_path = photos_dir / filename
            save_path.write_bytes(photo_bytes)
            asset.photo_path = str(save_path)

        db.session.commit()
        flash(f'Listing "{asset.asset_title}" updated successfully.', 'success')
        return redirect(url_for('asset.view_asset', asset_id=asset.id))

    return render_template('assets/asset_edit.html', asset=asset, categories=categories)


@asset_bp.route('/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_asset(asset_id):
    asset = RentalAsset.query.get_or_404(asset_id)
    if asset.owner_id != current_user.id:
        flash('You can only delete your own listings.', 'error')
        return redirect(url_for('asset.list_assets'))

    # Block deletion if active agreement exists
    from app.models.agreement import RentalAgreement
    active = RentalAgreement.query.filter(
        RentalAgreement.asset_id == asset_id,
        RentalAgreement.status.notin_(['fully_signed', 'cancelled'])
    ).first()
    if active:
        flash('Cannot delete a listing with an active or pending agreement.', 'error')
        return redirect(url_for('asset.view_asset', asset_id=asset_id))

    title = asset.asset_title
    # Remove photo file if present
    if asset.photo_path and os.path.exists(asset.photo_path):
        try:
            os.remove(asset.photo_path)
        except OSError:
            pass

    db.session.delete(asset)
    db.session.commit()
    flash(f'Listing "{title}" deleted.', 'success')
    return redirect(url_for('asset.list_assets'))
