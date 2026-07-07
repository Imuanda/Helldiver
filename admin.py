"""
admin.py — Admin panel blueprint.
All routes require the logged-in user to have is_admin=True.
Access: /admin
"""

import os
import uuid
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user, login_required
from extensions import db
from models import Quote, User, Comment, BanRecord, Reaction, Suggestion, DailyVisit, LandingQuote, Character
from sanitize import clean_and_validate
from validation import validate_quote
from character_colors import lookup_color, VALID_BOOKS, VALID_COLORS

# ── Image upload helpers ──────────────────────────────────────────────────────
_ALLOWED_EXTS   = {'jpg', 'jpeg', 'png', 'webp'}
_MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB

def _save_character_image(file):
    """Validates and saves an uploaded character image. Returns the saved filename."""
    content = file.read()

    if len(content) > _MAX_IMAGE_SIZE:
        raise ValueError('Image must be under 2 MB.')

    # Check extension
    raw_name = file.filename or ''
    ext = raw_name.rsplit('.', 1)[-1].lower() if '.' in raw_name else ''
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in _ALLOWED_EXTS:
        raise ValueError('Only JPG, PNG, or WebP images are accepted.')

    # Verify magic bytes — actual file content, not just the claimed extension
    header = content[:12]
    if header[:3] == b'\xff\xd8\xff':
        detected = 'jpg'
    elif header[:4] == b'\x89PNG':
        detected = 'png'
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        detected = 'webp'
    else:
        raise ValueError('File does not appear to be a valid image.')

    new_filename = f"{uuid.uuid4().hex}.{detected}"
    save_dir = os.path.join(current_app.root_path, 'static', 'characters')
    os.makedirs(save_dir, exist_ok=True)

    with open(os.path.join(save_dir, new_filename), 'wb') as f:
        f.write(content)

    return new_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: user must be logged in AND have is_admin=True."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            # Redirect non-admins silently to home — don't reveal admin panel exists
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    from datetime import date, timedelta
    today      = date.today()
    yesterday  = today - timedelta(days=1)
    last_7     = today - timedelta(days=7)

    stats = {
        'validated':    Quote.query.filter_by(status='validated').count(),
        'pending':      Quote.query.filter_by(status='pending').count(),
        'rejected':     Quote.query.filter_by(status='rejected').count(),
        'users':        User.query.count(),
        'comments':     Comment.query.count(),
        'banned':       User.query.filter_by(is_banned=True).count(),
        'suggestions':  Suggestion.query.filter_by(status='new').count(),
        # Traffic
        'visitors_today':   DailyVisit.query.filter_by(date=today).count(),
        'visitors_yesterday': DailyVisit.query.filter_by(date=yesterday).count(),
        'visitors_7days':   DailyVisit.query.filter(DailyVisit.date >= last_7).count(),
        'visitors_total':   DailyVisit.query.count(),
    }
    # Show the 5 most recent pending quotes on the dashboard
    recent_pending = (Quote.query.filter_by(status='pending')
                      .order_by(Quote.created_at.desc()).limit(5).all())
    return render_template('admin/dashboard.html', stats=stats, recent_pending=recent_pending)


# ── Pending quotes — review and approve/reject ────────────────────────────────
@admin_bp.route('/pending')
@admin_required
def pending_quotes():
    quotes = (Quote.query.filter_by(status='pending')
              .order_by(Quote.created_at.asc()).all())
    return render_template('admin/pending.html', quotes=quotes)


@admin_bp.route('/quotes/<int:quote_id>/approve', methods=['POST'])
@admin_required
def approve_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    quote.status = 'validated'
    db.session.commit()
    current_app.logger.info(f'Admin {current_user.username} approved quote {quote_id} — speaker: {quote.speaker}')
    flash(f'Quote by {quote.speaker} approved.', 'success')
    return redirect(url_for('admin.pending_quotes'))


@admin_bp.route('/quotes/<int:quote_id>/reject', methods=['POST'])
@admin_required
def reject_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    quote.status = 'rejected'
    db.session.commit()
    current_app.logger.info(f'Admin {current_user.username} rejected quote {quote_id} — speaker: {quote.speaker}')
    flash(f'Quote by {quote.speaker} rejected.', 'success')
    return redirect(url_for('admin.pending_quotes'))


# ── Add a quote directly (owner bypass — goes straight to validated) ───────────
@admin_bp.route('/add-quote', methods=['GET', 'POST'])
@admin_required
def add_quote():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        raw_text        = request.form.get('quote_text',  '')
        raw_speaker     = request.form.get('speaker',     '')
        raw_book        = request.form.get('book',        '')
        raw_perspective = request.form.get('perspective', '')
        raw_color       = request.form.get('color',       '')
        raw_chapter     = request.form.get('chapter',     '') or None
        raw_page        = request.form.get('page',        '') or None

        form_data = request.form

        cleaned_text,    err = clean_and_validate(raw_text, 'quote_text')
        if err: errors['quote_text'] = err
        cleaned_speaker, err = clean_and_validate(raw_speaker, 'speaker')
        if err: errors['speaker'] = err
        cleaned_perspective = ''
        if raw_perspective.strip():
            cleaned_perspective, err = clean_and_validate(raw_perspective, 'perspective')
            if err: errors['perspective'] = err
        if raw_book not in VALID_BOOKS:
            errors['book'] = 'Select a valid book.'

        detected_color = lookup_color(cleaned_speaker) if not errors.get('speaker') else None
        final_color = detected_color or raw_color.lower()
        if not final_color or final_color not in VALID_COLORS:
            errors['color'] = 'Select the Color of the speaker.'

        # Prevent duplicates even from admin
        if not errors:
            dupe = Quote.query.filter_by(text=cleaned_text, speaker=cleaned_speaker, book=raw_book).first()
            if dupe:
                errors['quote_text'] = 'This quote already exists in the database.'

        if not errors:
            try:
                page = int(raw_page) if raw_page else None
            except ValueError:
                page = None

            quote = Quote(
                text=cleaned_text,
                speaker=cleaned_speaker,
                book=raw_book,
                chapter=raw_chapter,
                page=page,
                color=final_color,
                perspective=cleaned_perspective or None,
                source='owner',
                status='validated',  # admin quotes go live immediately
            )
            db.session.add(quote)
            db.session.commit()
            flash(f'Quote by {cleaned_speaker} added and is now live.', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/add_quote.html',
                           errors=errors, form_data=form_data,
                           books=VALID_BOOKS, colors=VALID_COLORS)


# ── Users list ────────────────────────────────────────────────────────────────
@admin_bp.route('/quotes/<int:quote_id>/delete', methods=['POST'])
@admin_required
def delete_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    speaker = quote.speaker
    came_from = request.form.get('from', 'pending')
    db.session.delete(quote)
    db.session.commit()
    current_app.logger.info(
        f'Admin {current_user.username} DELETED quote {quote_id} — speaker: {speaker}'
    )
    flash(f'Quote by {speaker} has been permanently deleted.', 'success')
    # Return to wherever the admin was (pending page or all-quotes page)
    if came_from == 'all':
        return redirect(url_for('admin.all_quotes'))
    return redirect(url_for('admin.pending_quotes'))


@admin_bp.route('/quotes')
@admin_required
def all_quotes():
    """Shows every validated (live) quote with an option to delete."""
    quotes = (Quote.query
              .filter_by(status='validated')
              .order_by(Quote.created_at.desc())
              .all())
    return render_template('admin/all_quotes.html', quotes=quotes)


@admin_bp.route('/landing-quote', methods=['GET', 'POST'])
@admin_required
def landing_quote():
    """Manage the quote shown on the star map entry screen."""
    if request.method == 'POST':
        raw_text   = request.form.get('text', '').strip()
        raw_author = request.form.get('author', '').strip()

        # Run both fields through the same sanitization pipeline used everywhere else
        cleaned_text, err = clean_and_validate(raw_text, 'quote_text')
        if err:
            flash(f'Quote text: {err}', 'error')
            return redirect(url_for('admin.landing_quote'))

        # Author field has no profanity pipeline (it's a name/attribution) but cap length
        cleaned_author = raw_author[:150] if raw_author else None

        # Deactivate whatever is currently active
        LandingQuote.query.filter_by(is_active=True).update({'is_active': False})

        new_q = LandingQuote(text=cleaned_text, author=cleaned_author, is_active=True)
        db.session.add(new_q)
        db.session.commit()
        current_app.logger.info(
            f'Admin {current_user.username} set new landing quote (id {new_q.id})'
        )
        flash('New intro quote is now live on the landing page.', 'success')
        return redirect(url_for('admin.landing_quote'))

    active  = LandingQuote.query.filter_by(is_active=True).first()
    history = (LandingQuote.query
               .order_by(LandingQuote.created_at.desc()).all())
    return render_template('admin/landing_quote.html', active=active, history=history)


@admin_bp.route('/landing-quote/<int:quote_id>/activate', methods=['POST'])
@admin_required
def activate_landing_quote(quote_id):
    """Re-activate a past landing quote from the history list."""
    # Deactivate current
    LandingQuote.query.filter_by(is_active=True).update({'is_active': False})
    # Activate the chosen one
    q = LandingQuote.query.get_or_404(quote_id)
    q.is_active = True
    db.session.commit()
    current_app.logger.info(
        f'Admin {current_user.username} reactivated landing quote id {quote_id}'
    )
    flash(f'Intro quote updated — now showing quote from {q.created_at.strftime("%b %d, %Y")}.', 'success')
    return redirect(url_for('admin.landing_quote'))


@admin_bp.route('/suggestions')
@admin_required
def suggestions():
    all_suggestions = (Suggestion.query
                       .order_by(Suggestion.created_at.desc()).all())
    # Mark all 'new' ones as 'read' when admin views them
    for s in all_suggestions:
        if s.status == 'new':
            s.status = 'read'
    db.session.commit()
    return render_template('admin/suggestions.html', suggestions=all_suggestions)


@admin_bp.route('/quotes/<int:quote_id>/reactions')
@admin_required
def quote_reactions(quote_id):
    """Admin-only view of who reacted to a specific quote."""
    quote = Quote.query.get_or_404(quote_id)
    raw   = (Reaction.query
             .filter_by(quote_id=quote_id)
             .order_by(Reaction.created_at.desc()).all())

    # Enrich each reaction with a display name
    reactions = []
    for r in raw:
        name = None
        anon_name = None
        if r.user_id:
            u = User.query.get(r.user_id)
            name = u.username if u else None
        else:
            # Try to find an anon name from a comment left by the same session
            c = Comment.query.filter_by(session_id=r.session_id).first()
            anon_name = c.author_name if c else None
        reactions.append({
            'type':       r.type,
            'username':   name,
            'anon_name':  anon_name,
            'created_at': r.created_at,
        })

    return render_template('admin/reactions.html',
                           quote=quote,
                           reactions=reactions,
                           heart_count=quote.heart_count,
                           fire_count=quote.fire_count,
                           shocked_count=quote.shocked_count)


@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot ban another admin.', 'error')
        return redirect(url_for('admin.users'))
    reason = request.form.get('reason', 'Violation of community guidelines.')
    user.is_banned  = True
    user.ban_reason = reason
    record = BanRecord(user_id=user.id, reason=reason, banned_by=current_user.username)
    db.session.add(record)
    db.session.commit()
    current_app.logger.warning(f'Admin {current_user.username} banned user {user.username} — reason: {reason}')
    flash(f'{user.username} has been banned.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned  = False
    user.ban_reason = None
    db.session.commit()
    current_app.logger.info(f'Admin {current_user.username} unbanned user {user.username}')
    flash(f'{user.username} has been unbanned.', 'success')
    return redirect(url_for('admin.users'))


# ── Character management ──────────────────────────────────────────────────────

@admin_bp.route('/characters')
@admin_required
def characters():
    all_chars = (Character.query
                 .order_by(Character.display_order.asc(), Character.name.asc())
                 .all())
    return render_template('admin/characters.html', characters=all_chars)


@admin_bp.route('/characters/add', methods=['GET', 'POST'])
@admin_required
def add_character():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        form_data = request.form
        name      = request.form.get('name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        color     = request.form.get('color', '').strip().lower()
        bio       = request.form.get('bio', '').strip()
        order     = request.form.get('display_order', '0').strip()

        if not name:
            errors['name'] = 'Name is required.'
        elif len(name) > 50:
            errors['name'] = 'Name must be 50 characters or fewer.'

        if not full_name:
            errors['full_name'] = 'Full name is required.'
        elif len(full_name) > 100:
            errors['full_name'] = 'Full name must be 100 characters or fewer.'

        if color not in VALID_COLORS:
            errors['color'] = 'Select a valid Society Color.'

        if bio and len(bio) > 800:
            errors['bio'] = 'Bio must be 800 characters or fewer.'

        try:
            order = int(order)
        except ValueError:
            order = 0

        image_filename = None
        uploaded = request.files.get('image')
        if uploaded and uploaded.filename:
            try:
                image_filename = _save_character_image(uploaded)
            except ValueError as e:
                errors['image'] = str(e)

        if not errors:
            char = Character(
                name=name,
                full_name=full_name,
                color=color,
                bio=bio or None,
                image_filename=image_filename,
                display_order=order,
                is_visible=True,
            )
            db.session.add(char)
            db.session.commit()
            current_app.logger.info(
                f'Admin {current_user.username} added character "{name}"'
            )
            flash(f'{name} has been added to the roster.', 'success')
            return redirect(url_for('admin.characters'))

    return render_template('admin/character_form.html',
                           mode='add', errors=errors, form_data=form_data,
                           colors=VALID_COLORS, character=None)


@admin_bp.route('/characters/<int:char_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_character(char_id):
    char    = Character.query.get_or_404(char_id)
    errors  = {}

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        color     = request.form.get('color', '').strip().lower()
        bio       = request.form.get('bio', '').strip()
        order     = request.form.get('display_order', '0').strip()

        if not name:
            errors['name'] = 'Name is required.'
        elif len(name) > 50:
            errors['name'] = 'Name must be 50 characters or fewer.'

        if not full_name:
            errors['full_name'] = 'Full name is required.'
        elif len(full_name) > 100:
            errors['full_name'] = 'Full name must be 100 characters or fewer.'

        if color not in VALID_COLORS:
            errors['color'] = 'Select a valid Society Color.'

        if bio and len(bio) > 800:
            errors['bio'] = 'Bio must be 800 characters or fewer.'

        try:
            order = int(order)
        except ValueError:
            order = 0

        uploaded = request.files.get('image')
        if uploaded and uploaded.filename:
            try:
                new_filename = _save_character_image(uploaded)
                # Delete old image file if one exists
                if char.image_filename:
                    old_path = os.path.join(
                        current_app.root_path, 'static', 'characters', char.image_filename
                    )
                    if os.path.exists(old_path):
                        os.remove(old_path)
                char.image_filename = new_filename
            except ValueError as e:
                errors['image'] = str(e)

        if not errors:
            char.name          = name
            char.full_name     = full_name
            char.color         = color
            char.bio           = bio or None
            char.display_order = order
            db.session.commit()
            current_app.logger.info(
                f'Admin {current_user.username} edited character "{name}" (id {char_id})'
            )
            flash(f'{name} updated.', 'success')
            return redirect(url_for('admin.characters'))

    return render_template('admin/character_form.html',
                           mode='edit', errors=errors, form_data=request.form,
                           colors=VALID_COLORS, character=char)


@admin_bp.route('/characters/<int:char_id>/toggle', methods=['POST'])
@admin_required
def toggle_character(char_id):
    char = Character.query.get_or_404(char_id)
    char.is_visible = not char.is_visible
    db.session.commit()
    state = 'visible' if char.is_visible else 'hidden'
    flash(f'{char.name} is now {state}.', 'success')
    return redirect(url_for('admin.characters'))


@admin_bp.route('/characters/<int:char_id>/delete', methods=['POST'])
@admin_required
def delete_character(char_id):
    char = Character.query.get_or_404(char_id)
    name = char.name
    # Remove image file from disk if one was uploaded
    if char.image_filename:
        img_path = os.path.join(
            current_app.root_path, 'static', 'characters', char.image_filename
        )
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(char)
    db.session.commit()
    current_app.logger.info(
        f'Admin {current_user.username} deleted character "{name}" (id {char_id})'
    )
    flash(f'{name} has been removed from the roster.', 'success')
    return redirect(url_for('admin.characters'))
