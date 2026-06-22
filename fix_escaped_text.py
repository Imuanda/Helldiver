"""
fix_escaped_text.py — One-time migration to fix double-escaped characters in the database.

The old sanitize.py called html.escape() before saving, which turned:
  '  →  &#x27;
  &  →  &amp;
  "  →  &quot;
  <  →  &lt;
  >  →  &gt;

This script reverses that by unescaping every text field in the database.
Run it ONCE on PythonAnywhere after deploying the sanitize.py fix:

    python fix_escaped_text.py

It is safe to run multiple times — unescaping already-clean text does nothing.
"""

import sys, html
sys.path.insert(0, '.')

from app import app
from extensions import db
from models import Quote, Comment

def fix():
    with app.app_context():
        fixed_quotes    = 0
        fixed_comments  = 0

        # Fix quote text, speaker names, and perspectives
        for q in Quote.query.all():
            changed = False

            clean_text = html.unescape(q.text)
            if clean_text != q.text:
                q.text  = clean_text
                changed = True

            clean_speaker = html.unescape(q.speaker)
            if clean_speaker != q.speaker:
                q.speaker = clean_speaker
                changed   = True

            if q.perspective:
                clean_persp = html.unescape(q.perspective)
                if clean_persp != q.perspective:
                    q.perspective = clean_persp
                    changed       = True

            if changed:
                fixed_quotes += 1
                print(f'  Fixed quote {q.id}: {q.speaker[:40]}')

        # Fix comment text
        for c in Comment.query.all():
            clean = html.unescape(c.text)
            if clean != c.text:
                c.text = clean
                fixed_comments += 1
                print(f'  Fixed comment {c.id}: {c.author_name}')

        db.session.commit()
        print(f'\nDone. {fixed_quotes} quote(s) and {fixed_comments} comment(s) fixed.')

if __name__ == '__main__':
    fix()
