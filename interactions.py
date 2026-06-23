"""
interactions.py — Reactions and comments blueprint.
No login required — all interactions are tracked by session ID.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user
from extensions import db
from models import Quote, Comment, Reaction
from sanitize import clean_and_validate, is_banned_session, ban_session
from anon_names import get_or_create_anon

interactions_bp = Blueprint('interactions', __name__)


@interactions_bp.route('/quote/<int:quote_id>/react', methods=['POST'])
def react(quote_id):
    """Toggle a reaction (heart / fire / shocked) on a quote. No login needed."""
    quote = Quote.query.get_or_404(quote_id)
    if quote.status != 'validated':
        return jsonify({'error': 'Quote not found.'}), 404

    reaction_type = request.json.get('type', '')
    if reaction_type not in ('heart', 'fire', 'shocked'):
        return jsonify({'error': 'Invalid reaction type.'}), 400

    anon_id, _ = get_or_create_anon(session)

    # Check ban
    if is_banned_session(anon_id):
        current_app.logger.warning(f'Banned session attempted reaction — id: {anon_id[:8]}…')
        return jsonify({'error': 'Your session has been suspended.'}), 403

    # ── 1 reaction per quote per person ──────────────────────────────────────
    # Find ANY existing reaction from this session on this quote (any type)
    existing = Reaction.query.filter_by(
        quote_id=quote_id, session_id=anon_id
    ).first()

    count_col = f'{reaction_type}_count'

    if existing and existing.type == reaction_type:
        # Same button tapped again — toggle OFF
        db.session.delete(existing)
        new_count = max(0, getattr(quote, count_col) - 1)
        setattr(quote, count_col, new_count)
        quote.likes = max(0, quote.likes - 1)
        db.session.commit()
        return jsonify({'status': 'removed', 'count': new_count, 'reacted': False, 'old_type': None})

    old_type = existing.type if existing else None

    if existing:
        # Different button — remove old reaction first (swap)
        old_col = f'{existing.type}_count'
        setattr(quote, old_col, max(0, getattr(quote, old_col) - 1))
        quote.likes = max(0, quote.likes - 1)
        db.session.delete(existing)

    # Add the new reaction
    reaction = Reaction(
        quote_id=quote_id,
        type=reaction_type,
        session_id=anon_id,
        user_id=current_user.id if current_user.is_authenticated else None,
    )
    db.session.add(reaction)
    new_count = getattr(quote, count_col) + 1
    setattr(quote, count_col, new_count)
    quote.likes += 1
    db.session.commit()
    return jsonify({'status': 'added', 'count': new_count, 'reacted': True, 'old_type': old_type})


@interactions_bp.route('/quote/<int:quote_id>/comment', methods=['POST'])
def add_comment(quote_id):
    """Post a comment on a quote. No login needed."""
    quote = Quote.query.get_or_404(quote_id)
    if quote.status != 'validated':
        return jsonify({'error': 'Quote not found.'}), 404

    anon_id, anon_name = get_or_create_anon(session)

    # Check ban before doing anything
    if is_banned_session(anon_id):
        current_app.logger.warning(f'Banned session attempted comment on quote {quote_id} — id: {anon_id[:8]}…')
        return jsonify({'error': 'Your session has been suspended.'}), 403

    text = request.json.get('text', '')
    cleaned, err = clean_and_validate(text, 'comment')

    if err:
        if 'inappropriate' in err:
            ban_session(anon_id, f'Profanity/abuse in comment: "{text[:80]}"')
            current_app.logger.warning(f'Session auto-banned for profanity — id: {anon_id[:8]}…')
            return jsonify({'error': 'Inappropriate content detected. Your session has been suspended.'}), 403
        current_app.logger.info(f'Comment rejected on quote {quote_id} — {err}')
        return jsonify({'error': err}), 400

    # Server-side idempotency — block identical comment from same session within 10 seconds
    from datetime import timedelta
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    recent_dupe = Comment.query.filter(
        Comment.session_id == anon_id,
        Comment.quote_id  == quote_id,
        Comment.text      == cleaned,
        Comment.created_at >= ten_seconds_ago,
    ).first()
    if recent_dupe:
        return jsonify({'error': 'Duplicate comment — please wait a moment before posting again.'}), 429

    # Use registered username if logged in, otherwise the anon name
    display_name = current_user.username if current_user.is_authenticated else anon_name

    comment = Comment(
        quote_id=quote_id,
        text=cleaned,
        author_name=display_name,
        session_id=anon_id,
        user_id=current_user.id if current_user.is_authenticated else None,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'status':  'ok',
        'id':      comment.id,
        'author':  comment.author_name,
        'text':    comment.text,
        'time':    comment.created_at.strftime('%b %d, %Y'),
    })


@interactions_bp.route('/quote/<int:quote_id>/comments', methods=['GET'])
def get_comments(quote_id):
    """Returns the 30 most recent comments for a quote (used on page load)."""
    comments = (
        Comment.query
        .filter_by(quote_id=quote_id)
        .order_by(Comment.created_at.asc())
        .limit(30)
        .all()
    )
    return jsonify([{
        'id':     c.id,
        'author': c.author_name,
        'text':   c.text,
        'time':   c.created_at.strftime('%b %d, %Y'),
    } for c in comments])
