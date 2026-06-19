"""
sanitize.py — Content sanitization pipeline.

Every piece of user-submitted text runs through clean_and_validate() before
it touches the database. This handles three threats in one pass:
  1. XSS — escape HTML characters so scripts can't run in the browser
  2. Length — enforce min/max per field so layout can't be broken
  3. Profanity/abuse — block inappropriate content before it's saved
"""

import html
from better_profanity import profanity

# Load the default profanity word list on module import
profanity.load_censor_words()

# ── Character limits per field ────────────────────────────────────────────────
# (min, max) — chosen to fit common quote lengths without allowing monologues
CHAR_LIMITS = {
    'username':   (3,  30),
    'email':      (5,  120),
    'password':   (8,  128),
    'quote_text': (20, 600),
    'speaker':    (2,  100),
    'perspective':(0,  400),   # optional, so min is 0
    'comment':    (1,  500),
}


def sanitize_text(text):
    """
    Strip whitespace and escape HTML special characters.
    This is the first thing that runs on any user input.
    '&', '<', '>' and '"' become their HTML entities so they display
    safely without executing as code.
    """
    if not text:
        return ''
    return html.escape(text.strip(), quote=True)


def check_length(text, field):
    """
    Returns (ok, error_message).
    ok is True if the text length is within the allowed range for this field.
    """
    min_len, max_len = CHAR_LIMITS.get(field, (0, 10_000))
    length = len(text)

    if length < min_len:
        return False, f'Too short — minimum {min_len} character{"s" if min_len != 1 else ""}.'
    if length > max_len:
        return False, f'Too long — maximum {max_len} characters.'
    return True, ''


def contains_profanity(text):
    """Returns True if the text contains profanity or slurs."""
    return profanity.contains_profanity(text)


def clean_and_validate(text, field):
    """
    Full sanitization pipeline — run this on every field before saving.

    Returns (cleaned_text, error_message).
      - If error_message is '', the text is safe to save.
      - If error_message is set, the text was rejected and cleaned_text is None.

    Steps in order:
      1. Sanitize (escape HTML, strip whitespace)
      2. Check length limits
      3. Check for profanity / inappropriate content
    """
    cleaned = sanitize_text(text)

    # Empty optional fields (like perspective) pass through
    if field == 'perspective' and not cleaned:
        return '', ''

    ok, err = check_length(cleaned, field)
    if not ok:
        return None, err

    if contains_profanity(cleaned):
        return None, 'Content contains inappropriate language and cannot be posted.'

    return cleaned, ''


def is_banned_session(session_id: str) -> bool:
    """
    Checks if a session ID is currently banned.
    Import is deferred to avoid circular imports with models.
    """
    from models import BanRecord
    return BanRecord.query.filter_by(session_id=session_id).first() is not None


def ban_session(session_id: str, reason: str) -> None:
    """Records a ban for an anonymous session."""
    from extensions import db
    from models import BanRecord
    record = BanRecord(session_id=session_id, reason=reason, banned_by='system')
    db.session.add(record)
    db.session.commit()
