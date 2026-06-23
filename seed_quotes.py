"""
seed_quotes.py — Initialize the database and load the first quotes.

Run this ONCE to set up the database:
    python seed_quotes.py

You can re-run it safely — it checks for duplicates before inserting.

HOW TO ADD YOUR OWN QUOTES:
  Add a new dict to SEED_QUOTES below with:
    - text:    the exact quote
    - speaker: who said it
    - book:    exact title (must match one of the 6 valid books)
    - chapter: chapter number or name (or None if unknown)
    - page:    page number (or None if unknown)
    - color:   the Society Color of the speaker (lowercase)
    - source:  'owner' for your own quotes (goes straight to validated)
               'ai' for AI-sourced quotes (needs your review before going live)
    - status:  'validated' | 'pending' (owner quotes should be 'validated')
"""

import sys
import os

# Make sure Python can find app.py when running this script directly
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from extensions import db
from models import Quote, LandingQuote
from validation import validate_quote

# ── Initial quotes ────────────────────────────────────────────────────────────
# Keep this list small and accurate.
# It is better to have 2 verified quotes than 20 uncertain ones.
SEED_QUOTES = [

    # ── Confirmed by owner ────────────────────────────────────────────────────
    {
        'text':    'I am Cassius Bellona, son of Tiberius, son of Julia, brother of Darrow, '
                   'Morning Knight of the Solar Republic, and my honor remains.',
        'speaker': 'Cassius au Bellona',
        'book':    'Lightbringer',
        'chapter': None,   # exact chapter not confirmed yet
        'page':    None,   # exact page not confirmed yet
        'color':   'gold',
        'source':  'owner',    # confirmed correct by the project owner
        'status':  'validated',
    },

    # ── Pending owner verification ─────────────────────────────────────────────
    # This quote is used throughout the project — please confirm exact chapter/page
    {
        'text':    'I live for the dream that my children will be born free. '
                   'That they will be what they like. Go where they like.',
        'speaker': 'Eo of Lykos',
        'book':    'Red Rising',
        'chapter': None,   # chapter 3 was a guess — needs owner verification
        'page':    None,   # page 28 was a guess — needs owner verification
        'color':   'red',
        'source':  'ai',      # AI-sourced — pending owner confirmation
        'status':  'pending', # will not appear publicly until confirmed
    },

]


def seed():
    """Creates the database tables and inserts seed quotes."""
    with app.app_context():

        # Create all tables defined in models.py if they don't exist yet
        db.create_all()

        # ── Column migrations — safely adds new columns to existing tables ───
        # SQLite's ALTER TABLE only supports ADD COLUMN, not remove/rename
        from sqlalchemy import text
        _migrations = [
            ('users', 'failed_login_count', 'INTEGER DEFAULT 0'),
            ('users', 'locked_until',       'DATETIME'),
        ]
        for table, col, col_type in _migrations:
            try:
                db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                db.session.commit()
                print(f'  [migrate]  Added column {table}.{col}')
            except Exception:
                db.session.rollback()  # column already exists — skip silently

        print('Database tables ready.\n')

        added = 0
        skipped = 0

        for q in SEED_QUOTES:
            # Skip duplicates — safe to re-run this script
            if Quote.query.filter_by(text=q['text']).first():
                print(f'  [skip]  Already exists: "{q["text"][:60]}..."')
                skipped += 1
                continue

            # Run through the validation system — same path as any other quote source
            is_valid, reason, suggested_status = validate_quote(
                text=q['text'],
                speaker=q['speaker'],
                book=q['book'],
                color=q['color'],
                chapter=q.get('chapter'),
                page=q.get('page'),
                source=q['source'],
            )

            if not is_valid:
                print(f'  [FAIL]  Rejected: {reason}')
                print(f'          Quote: "{q["text"][:60]}..."')
                continue

            # Use the status from the seed data (owner can override validation suggestion)
            final_status = q.get('status', suggested_status)

            quote = Quote(
                text=q['text'],
                speaker=q['speaker'],
                book=q['book'],
                chapter=q.get('chapter'),
                page=q.get('page'),
                color=q['color'],
                source=q['source'],
                status=final_status,
            )
            db.session.add(quote)
            added += 1

            status_label = '[validated]' if final_status == 'validated' else '[pending]  '
            print(f'  {status_label} Added: "{q["text"][:60]}..."')

        db.session.commit()
        print(f'\nDone. {added} quote(s) added, {skipped} skipped.')

        # ── Seed the initial landing page quote ───────────────────────────────
        if not LandingQuote.query.first():
            landing_q = LandingQuote(
                text=(
                    'I am Cassius Bellona, son of Tiberius, son of Julia, '
                    'brother of Darrow, Morning Knight of the Solar Republic, '
                    'and my honor remains.'
                ),
                author='Cassius au Bellona · Lightbringer',
                is_active=True,
            )
            db.session.add(landing_q)
            db.session.commit()
            print('  [landing]  Seeded initial intro quote (Cassius).')
        else:
            print('  [landing]  Intro quote already set — skipping.')

        if added > 0:
            print('\nTo see quotes live:')
            print('  - Validated quotes appear immediately on the Home and Color pages.')
            print('  - Pending quotes need your review — mark them validated in the DB to publish.')


if __name__ == '__main__':
    seed()
