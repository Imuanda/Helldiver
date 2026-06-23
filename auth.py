"""
auth.py — Authentication blueprint.
Handles signup, login, and logout.
"""

import hashlib
import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from sanitize import clean_and_validate

auth_bp = Blueprint('auth', __name__)

# Common weak passwords users should not be allowed to choose
_COMMON_PASSWORDS = {
    'password', 'password1', 'password123', '12345678', '123456789',
    'qwerty123', 'iloveyou', 'admin123', 'helldiver', 'redrising',
    'letmein1', 'welcome1', 'monkey123',
}


def _check_password_strength(password):
    """
    Returns (ok, error_message).
    Checks for minimum length, at least one digit or special char, and common passwords.
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not re.search(r'[0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, 'Password must contain at least one number or special character (e.g. !, @, #, 1).'
    if password.lower() in _COMMON_PASSWORDS:
        return False, 'This password is too common. Please choose something more unique.'
    return True, ''


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # If already logged in, send home
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    errors = {}

    if request.method == 'POST':
        username = request.form.get('username', '')
        email    = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # Sanitize and validate username
        clean_username, err = clean_and_validate(username, 'username')
        if err:
            errors['username'] = err

        # Basic email format check — deeper validation in Step 5
        clean_email, err = clean_and_validate(email, 'email')
        if err:
            errors['email'] = err
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Please enter a valid email address.'

        # Password strength check — length + complexity + common password block
        ok, err = _check_password_strength(password)
        if not ok:
            errors['password'] = err
        elif password != confirm:
            errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            # Check for existing username or email
            if User.query.filter_by(username=clean_username).first():
                errors['username'] = 'That username is already taken.'
            if User.query.filter_by(email=clean_email).first():
                errors['email'] = 'An account with that email already exists.'

        if not errors:
            # Create the user — password is hashed inside set_password()
            user = User(username=clean_username, email=clean_email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f'New user registered — username: {clean_username}')
            login_user(user)
            flash('Welcome to Red Rising. You can now submit quotes.', 'success')
            return redirect(url_for('home'))

    return render_template('signup.html', errors=errors)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    error = None

    if request.method == 'POST':
        email    = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        # Hash the email before logging — never store plaintext emails in logs
        _email_hash = hashlib.sha256(email.encode()).hexdigest()[:12]

        if user and user.locked_until and user.locked_until > datetime.utcnow():
            # Account is temporarily locked after too many failed attempts
            mins = max(1, int((user.locked_until - datetime.utcnow()).seconds / 60) + 1)
            current_app.logger.warning(f'Login attempt on locked account — hash: {_email_hash}')
            error = f'Too many failed attempts. Account locked — try again in {mins} minute(s).'

        elif user and user.is_banned:
            current_app.logger.warning(f'Banned user login attempt — {user.username} (hash: {_email_hash})')
            error = 'This account has been suspended.'

        elif not user or not user.check_password(password):
            current_app.logger.warning(f'Failed login attempt — email hash: {_email_hash}')
            if user:
                # Track consecutive failures on the account
                user.failed_login_count = (user.failed_login_count or 0) + 1
                if user.failed_login_count >= 10:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    current_app.logger.warning(
                        f'Account locked after 10 failed attempts — {user.username}'
                    )
                from extensions import db
                db.session.commit()
            error = 'Incorrect email or password.'

        else:
            # Successful login — reset failure counter
            user.failed_login_count = 0
            user.locked_until       = None
            from extensions import db
            db.session.commit()
            current_app.logger.info(f'User logged in — {user.username}')
            login_user(user)
            next_page = request.args.get('next') or url_for('home')
            return redirect(next_page)

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))
