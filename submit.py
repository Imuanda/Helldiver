"""
submit.py — Quote submission blueprint.
Login required. Submitted quotes go to 'pending' status for owner review.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Quote
from sanitize import clean_and_validate
from validation import validate_quote
from character_colors import lookup_color, VALID_BOOKS, VALID_COLORS

submit_bp = Blueprint('submit', __name__)


@submit_bp.route('/submit-quote', methods=['GET', 'POST'])
@login_required
def submit_quote():
    errors   = {}
    form_data = {}

    if request.method == 'POST':
        # Pull raw values from the form
        raw_text        = request.form.get('quote_text',  '')
        raw_speaker     = request.form.get('speaker',     '')
        raw_book        = request.form.get('book',        '')
        raw_perspective = request.form.get('perspective', '')
        raw_color       = request.form.get('color',       '')

        form_data = {
            'quote_text':  raw_text,
            'speaker':     raw_speaker,
            'book':        raw_book,
            'perspective': raw_perspective,
            'color':       raw_color,
        }

        # ── Sanitize each field ────────────────────────────────────────────
        cleaned_text, err = clean_and_validate(raw_text, 'quote_text')
        if err: errors['quote_text'] = err

        cleaned_speaker, err = clean_and_validate(raw_speaker, 'speaker')
        if err: errors['speaker'] = err

        # Perspective is optional — only validate if provided
        cleaned_perspective = ''
        if raw_perspective.strip():
            cleaned_perspective, err = clean_and_validate(raw_perspective, 'perspective')
            if err: errors['perspective'] = err

        # Book must be one of the 6 valid titles
        if raw_book not in VALID_BOOKS:
            errors['book'] = 'Please select one of the 6 Red Rising books.'

        # ── Auto-detect color from speaker name, fall back to user selection ──
        detected_color = lookup_color(cleaned_speaker) if not errors.get('speaker') else None
        final_color    = detected_color or raw_color.lower()

        if not final_color or final_color not in VALID_COLORS:
            errors['color'] = 'Please select the Society Color of the speaker.'

        if not errors:
            # ── Run through the validation pipeline ───────────────────────
            is_valid, reason, _ = validate_quote(
                text=cleaned_text,
                speaker=cleaned_speaker,
                book=raw_book,
                color=final_color,
                source='user',
            )

            if not is_valid:
                errors['quote_text'] = reason

        if not errors:
            # Server-side idempotency — reject if an identical quote already exists
            duplicate = Quote.query.filter_by(
                text=cleaned_text, speaker=cleaned_speaker, book=raw_book
            ).first()
            if duplicate:
                errors['quote_text'] = 'This quote has already been submitted.'

        if not errors:
            quote = Quote(
                text=cleaned_text,
                speaker=cleaned_speaker,
                book=raw_book,
                color=final_color,
                perspective=cleaned_perspective or None,
                source='user',
                status='pending',  # goes live only after owner reviews it
                submitted_by_id=current_user.id,
            )
            db.session.add(quote)
            db.session.commit()

            flash('Your quote has been submitted and is pending review. Thank you!', 'success')
            return redirect(url_for('home'))

    return render_template(
        'submit_quote.html',
        errors=errors,
        form_data=form_data,
        books=VALID_BOOKS,
        colors=VALID_COLORS,
        active_page='submit',
    )
