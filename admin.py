"""
admin.py — Admin panel blueprint.
All routes require the logged-in user to have is_admin=True.
Access: /admin
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user, login_required
from extensions import db
from models import Quote, User, Comment, BanRecord, Reaction, Suggestion, DailyVisit
from sanitize import clean_and_validate
from validation import validate_quote
from character_colors import lookup_color, VALID_BOOKS, VALID_COLORS

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
