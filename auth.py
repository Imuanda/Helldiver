"""
auth.py — Authentication blueprint.
Handles signup, login, and logout.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from sanitize import clean_and_validate

auth_bp = Blueprint('auth', __name__)


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

        # Password length check — we store a hash, never the plain text
        _, err = clean_and_validate(password, 'password')
        if err:
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

        if not user or not user.check_password(password):
            # Deliberately vague — don't reveal whether email exists
            error = 'Incorrect email or password.'
        elif user.is_banned:
            error = 'This account has been suspended.'
        else:
            login_user(user)
            # Redirect to the page they were trying to reach, or home
            next_page = request.args.get('next') or url_for('home')
            return redirect(next_page)

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))
