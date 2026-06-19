import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.certificate import Certificate
from app.services.crypto_service import generate_rsa_keypair
from app.services.certificate_service import issue_certificate

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

_COMMON_PASSWORDS = {
    'password', 'password1', 'password123', '12345678', '123456789',
    'qwerty123', 'qwerty', 'abc12345', 'iloveyou', 'admin123',
    'letmein1', 'welcome1', 'monkey123', 'dragon123', 'validrent',
    'validrent123', 'nepal123', 'kathmandu1',
}


def _validate_password(password: str) -> list[str]:
    errors = []
    if len(password) < 8:
        errors.append('At least 8 characters required.')
    if not re.search(r'[A-Z]', password):
        errors.append('At least one uppercase letter required.')
    if not re.search(r'[a-z]', password):
        errors.append('At least one lowercase letter required.')
    if not re.search(r'\d', password):
        errors.append('At least one number required.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('At least one special character required (!@#$%^&* etc.).')
    if password.lower() in _COMMON_PASSWORDS:
        errors.append('Password is too common. Choose a more unique password.')
    return errors


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'tenant')
        if role not in ('landlord', 'tenant'):
            role = 'tenant'
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')

        pw_errors = _validate_password(password)
        errors.extend(pw_errors)

        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html', form_data=request.form)

        private_pem, public_pem = generate_rsa_keypair()

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            roles='landlord,tenant',
            private_key_pem=private_pem,
            public_key_pem=public_pem,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        cert_data = issue_certificate(public_pem, full_name, email)
        cert = Certificate(
            user_id=user.id,
            serial_number=cert_data['serial_number'],
            certificate_pem=cert_data['certificate_pem'],
            issued_at=cert_data['issued_at'],
            expires_at=cert_data['expires_at'],
            subject_cn=cert_data['subject_cn'],
        )
        db.session.add(cert)
        db.session.commit()

        flash('Account created! Your digital certificate has been issued. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Account is deactivated. Contact support.', 'error')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        # Set active_role from user's primary role on login
        session['active_role'] = user.role
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.home'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('active_role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
