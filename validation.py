"""
validation.py — Quote validation system.

Every quote, regardless of source (AI, owner, or user), passes through
validate_quote() before being saved to the database.

Invalid quotes are never saved — they are written to flagged_quotes.json
so the owner can review them and understand why they were rejected.
"""

import json
import os
from datetime import datetime

# Path to the flagged quotes log — sits next to app.py in the project root
FLAGGED_FILE = os.path.join(os.path.dirname(__file__), 'flagged_quotes.json')

# The only valid book titles — anything else is rejected immediately
VALID_BOOKS = [
    'Red Rising',
    'Golden Son',
    'Morning Star',
    'Iron Gold',
    'Dark Age',
    'Lightbringer',
]

# All Society Colors — speaker's color must be one of these
VALID_COLORS = [
    'gold', 'red', 'obsidian', 'gray', 'silver', 'pink', 'blue',
    'white', 'copper', 'orange', 'green', 'violet', 'yellow', 'bronze', 'tan',
]


def validate_quote(text, speaker, book, color, chapter=None, page=None, source='user'):
    """
    Validates a quote and returns (is_valid, reason, suggested_status).

    is_valid          — True if the quote passes all checks and can be saved
    reason            — plain-English explanation of the result
    suggested_status  — what DB status to assign: 'validated' | 'pending' | 'rejected'

    Invalid quotes are automatically logged to flagged_quotes.json.
    """

    # ── 1. Text must exist and be meaningful ──────────────────────────────
    if not text or len(text.strip()) < 10:
        reason = 'Quote text is too short or empty (minimum 10 characters).'
        _log_flagged(text, speaker, book, chapter, page, source, reason)
        return False, reason, 'rejected'

    # ── 2. Speaker name is required ────────────────────────────────────────
    if not speaker or len(speaker.strip()) < 2:
        reason = 'Speaker name is missing or too short.'
        _log_flagged(text, speaker, book, chapter, page, source, reason)
        return False, reason, 'rejected'

    # ── 3. Book must be one of the 6 Red Rising titles ────────────────────
    if book not in VALID_BOOKS:
        reason = (
            f'"{book}" is not a recognized Red Rising book. '
            f'Valid titles: {", ".join(VALID_BOOKS)}.'
        )
        _log_flagged(text, speaker, book, chapter, page, source, reason)
        return False, reason, 'rejected'

    # ── 4. Color must be a recognized Society caste ───────────────────────
    if not color or color.lower() not in VALID_COLORS:
        reason = (
            f'"{color}" is not a recognized Society Color. '
            f'Valid colors: {", ".join(VALID_COLORS)}.'
        )
        _log_flagged(text, speaker, book, chapter, page, source, reason)
        return False, reason, 'rejected'

    # ── 5. Source-based trust rules ────────────────────────────────────────
    if source == 'owner':
        # Owner quotes are trusted — go straight to 'validated'
        return True, 'Owner-submitted quote. Marked as validated.', 'validated'

    if source == 'ai':
        # AI quotes pass format checks but need the owner to manually confirm
        # the exact text, speaker, and source before going live
        return True, (
            'AI-sourced quote passed format checks. '
            'Status set to "pending" — owner must confirm exact text and source before it goes live.'
        ), 'pending'

    if source == 'user':
        # User quotes start as pending — owner reviews before they appear publicly
        return True, (
            'User-submitted quote passed format checks. '
            'Status set to "pending" for owner review.'
        ), 'pending'

    # Fallback — unknown source type
    return True, 'Passed format checks. Source type unknown — defaulting to pending.', 'pending'


def _log_flagged(text, speaker, book, chapter, page, source, reason):
    """
    Writes a rejected quote to flagged_quotes.json.
    Each entry records exactly what was submitted and why it failed.
    """
    entry = {
        'quote':          text or '',
        'speaker':        speaker or '',
        'source_claimed': _build_source_string(book, chapter, page),
        'source_type':    source or 'unknown',
        'status':         'Invalid',
        'reason':         reason,
        'flagged_at':     datetime.utcnow().isoformat(),
    }

    # Load existing entries — create an empty list if the file doesn't exist yet
    entries = []
    if os.path.exists(FLAGGED_FILE):
        with open(FLAGGED_FILE, 'r') as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                entries = []  # file existed but was empty or corrupt — start fresh

    entries.append(entry)

    with open(FLAGGED_FILE, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def _build_source_string(book, chapter, page):
    """Builds a readable source string like 'Red Rising, Chapter 3, Page 28'."""
    parts = [book or 'Unknown book']
    if chapter:
        parts.append(f'Chapter {chapter}')
    if page:
        parts.append(f'Page {page}')
    return ', '.join(parts)
