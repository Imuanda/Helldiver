"""
suggest.py — Feature suggestion blueprint.
Registered users can submit suggestions. Only admins can view them.
Suggestions are isolated from the rest of the app — they go straight to admin as a message.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Suggestion
from sanitize import clean_and_validate

suggest_bp = Blueprint('suggest', __name__)


@suggest_bp.route('/suggest', methods=['GET', 'POST'])
@login_required
def suggest():
    error = None

    if request.method == 'POST':
        raw_text = request.form.get('suggestion', '')

        cleaned, err = clean_and_validate(raw_text, 'suggestion')
        if err:
            error = err
        else:
            suggestion = Suggestion(text=cleaned, user_id=current_user.id)
            db.session.add(suggestion)
            db.session.commit()
            current_app.logger.info(
                f'Suggestion submitted by {current_user.username} (user {current_user.id})'
            )
            flash('Your suggestion has been sent. Thank you!', 'success')
            return redirect(url_for('home'))

    return render_template('suggest.html', error=error, active_page='suggest')
