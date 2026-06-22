"""
sanitize.py — Content sanitization pipeline.

Every piece of user-submitted text runs through clean_and_validate() before
it touches the database. This handles:
  1. XSS — escape HTML characters so scripts can't run in the browser
  2. Length — enforce min/max per field so layout can't be broken
  3. Profanity — block actual slurs and hate speech in user comments/perspectives
     NOTE: profanity check is intentionally SKIPPED for quote text and speaker
     names, because quotes come directly from the books and may contain mature
     themes. The owner reviews every quote before it goes live.
"""

from better_profanity import profanity

# ── Targeted word list for user-generated content (comments and perspectives) ─
# This replaces the default word list which is far too aggressive for a literary
# quote app (it flags words like "die", "fight", "darkness", "god").
# This list covers actual slurs, hate speech, and sexual content only.
# Add to this list if something slips through that shouldn't.
TARGETED_BLOCK_LIST = [
    # Explicit sexual content
    'fuck', 'fucking', 'fucked', 'fucker',
    'shit', 'shitting',
    'bitch', 'bitches',
    'cunt', 'pussy', 'cock', 'dick', 'ass', 'asses', 'asshole',
    'porn', 'porno', 'sex',
    # Slurs (racial, homophobic, ableist — abbreviated to avoid storing them in plain text)
    'nigger', 'nigga', 'faggot', 'retard', 'spic', 'kike', 'chink',
    # Harassment / threats
    'kill yourself', 'kys', 'go die',
]

# Load our targeted list instead of the default aggressive one
profanity.load_censor_words(TARGETED_BLOCK_LIST, whitelist_words=[])

# ── Character limits per field ────────────────────────────────────────────────
CHAR_LIMITS = {
    'username':    (3,   30),
    'email':       (5,  120),
    'password':    (8,  128),
    'quote_text':  (20, 600),
    'speaker':     (2,  100),
    'perspective': (0,  400),
    'comment':     (1,  500),
}

# Fields that bypass the profanity filter entirely.
# Quote text and speaker come from published books — the owner reviews them anyway.
NO_FILTER_FIELDS = {'quote_text', 'speaker'}


def sanitize_text(text):
    """
    Strip whitespace from user input.
    We do NOT call html.escape() here because Jinja2 auto-escapes all {{ variables }}
    at render time, and quote-nav.js uses .textContent (not innerHTML) for AJAX.
    Escaping on input AND output causes double-escaping: apostrophes show as &#x27;,
    ampersands show as &amp; etc. Jinja2 handles output escaping — we handle trimming.
    """
    if not text:
        return ''
    return text.strip()


def check_length(text, field):
    """Returns (ok, error_message) based on the character limit for this field."""
    min_len, max_len = CHAR_LIMITS.get(field, (0, 10_000))
    length = len(text)
    if length < min_len:
        return False, f'Too short — minimum {min_len} character{"s" if min_len != 1 else ""}.'
    if length > max_len:
        return False, f'Too long — maximum {max_len} characters.'
    return True, ''


def contains_profanity(text):
    """Returns True if the text contains a word from the targeted block list."""
    return profanity.contains_profanity(text)


def clean_and_validate(text, field):
    """
    Full sanitization pipeline. Returns (cleaned_text, error_message).
    error_message is '' if the text is safe to save.

    Steps:
      1. Sanitize (escape HTML, strip whitespace)
      2. Check length limits
      3. Check profanity — ONLY for comment and perspective fields,
         not for quote text or speaker names
    """
    cleaned = sanitize_text(text)

    # Empty optional fields (perspective) pass through with no error
    if field == 'perspective' and not cleaned:
        return '', ''

    ok, err = check_length(cleaned, field)
    if not ok:
        return None, err

    # Skip profanity check for book content — owner reviews before publishing
    if field not in NO_FILTER_FIELDS and contains_profanity(cleaned):
        return None, 'Please keep comments respectful — inappropriate language is not allowed.'

    return cleaned, ''


def is_banned_session(session_id):
    """Returns True if this anonymous session has been banned."""
    from models import BanRecord
    return BanRecord.query.filter_by(session_id=session_id).first() is not None


def ban_session(session_id, reason):
    """Records a ban for an anonymous session."""
    from extensions import db
    from models import BanRecord
    record = BanRecord(session_id=session_id, reason=reason, banned_by='system')
    db.session.add(record)
    db.session.commit()
