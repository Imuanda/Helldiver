"""
make_admin.py — Promote a registered user to admin.

Run once after creating your account on the site:
    python make_admin.py

You will be prompted for the email address of the account to promote.
Only run this on the server where the database lives.
"""

import sys
sys.path.insert(0, '.')

from app import app
from extensions import db
from models import User


def make_admin():
    email = input('Enter the email address of the account to make admin: ').strip().lower()

    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f'\nNo account found with email: {email}')
            print('Make sure you have signed up at /signup first.')
            return

        if user.is_admin:
            print(f'\n{user.username} is already an admin.')
            return

        user.is_admin = True
        db.session.commit()
        print(f'\nDone. {user.username} ({email}) now has admin access.')
        print('Visit /admin to access the admin panel.')


if __name__ == '__main__':
    make_admin()
