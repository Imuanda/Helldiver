"""
seed_characters.py — Seed the initial character roster for the Meet them page.

Run once (safe to re-run — checks for existing entries before inserting):
    python seed_characters.py

To add more characters later:
    1. Add a new dict to CHARACTERS below
    2. Re-run this script — it will skip existing names and only add new ones
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from extensions import db
from models import Character

CHARACTERS = [
    {
        'name':          'Eo',
        'full_name':     'Eo of Lykos',
        'color':         'red',
        'display_order': 1,
        'bio': (
            'Darrow\'s wife and the soul of Lykos. A miner\'s daughter who dared to sing an '
            'illegal song of freedom in a world that punished such dreams with death. Her '
            'execution at the hands of the Society did not silence her — it lit a fire that '
            'would reshape the solar system. She is the reason for everything.'
        ),
    },
    {
        'name':          'Darrow',
        'full_name':     'Darrow of Lykos',
        'color':         'red',
        'display_order': 2,
        'bio': (
            'Born in the deep mines of Lykos on Mars, Darrow believed he was sacrificing '
            'everything to terraform a dead world for future generations. When he learned the '
            'truth — that the surface had been green for centuries, that Reds were slaves — '
            'his grief became fury, and his fury became revolution. The Sons of Ares carved '
            'him into a Gold. The Reaper was born.'
        ),
    },
    {
        'name':          'Sevro',
        'full_name':     'Sevro au Barca',
        'color':         'gold',
        'display_order': 3,
        'bio': (
            'The smallest, the strangest, the most dangerous man in any room. Son of Fitchner '
            'au Barca and a Red woman, Sevro is an outsider in every world he inhabits — too '
            'feral for Gold courts, too Gold for the Sons of Ares. He doesn\'t care. Leader '
            'of the Howlers, fiercely loyal to Darrow, and utterly without fear, Sevro is the '
            'one you never see coming.'
        ),
    },
    {
        'name':          'Mustang',
        'full_name':     'Virginia au Augustus',
        'color':         'gold',
        'display_order': 4,
        'bio': (
            'Daughter of the ArchGovernor of Mars, Virginia was Darrow\'s equal in every '
            'sense — in tactics, in vision, and in will. She found him half-dead in the '
            'wilderness of the Institute and chose to trust him. She became the first Sovereign '
            'of the Solar Republic, the political mind behind a revolution that military force '
            'alone could never have won.'
        ),
    },
    {
        'name':          'Victra',
        'full_name':     'Victra au Julii',
        'color':         'gold',
        'display_order': 5,
        'bio': (
            'Blunt, lethal, and loyal to almost no one — until she decides you are worth her '
            'trust. Half-sister to Antonia au Severus-Julii, she was betrayed by family and '
            'came out of it harder and cleaner. She fights without elegance and without mercy. '
            'She is exactly who you want standing next to you when everything falls apart.'
        ),
    },
    {
        'name':          'Quicksilver',
        'full_name':     'Quicksilver',
        'color':         'silver',
        'display_order': 6,
        'bio': (
            'The wealthiest man in the solar system and perhaps its most calculating mind. He '
            'funds what needs funding, backs what will win, and disappears when the odds turn. '
            'Behind the commerce and the careful neutrality is someone who understands that the '
            'future belongs to whoever builds it. He bet on Darrow. That tells you everything.'
        ),
    },
    {
        'name':          'Dancer',
        'full_name':     'Dancer',
        'color':         'red',
        'display_order': 7,
        'bio': (
            'The man who found Darrow in his grief and handed him a purpose. A leader within '
            'the Sons of Ares and later the Free Red movement, Dancer shaped the political '
            'heart of the rebellion. Where Darrow wages war, Dancer fights for what comes '
            'after — and their visions of what that should look like put them on a collision '
            'course.'
        ),
    },
    {
        'name':          'Fitchner',
        'full_name':     'Fitchner au Barca',
        'color':         'gold',
        'display_order': 8,
        'bio': (
            'Darrow\'s Proctor at the Institute on Mars — harsh, unconventional, and seemingly '
            'contemptuous of everything. He was also Ares. The secret founder of the Sons of '
            'Ares, hiding in plain sight inside the very institution he was trying to destroy. '
            'A man who carried a revolution in silence, and whose death changed everything.'
        ),
    },
    {
        'name':          'Cassius',
        'full_name':     'Cassius au Bellona',
        'color':         'gold',
        'display_order': 9,
        'bio': (
            'A duelist of legendary skill from one of the oldest Gold families in the Society. '
            'Cassius was Darrow\'s first real friend at the Institute — and then his most painful '
            'enemy. The tragedy that split them apart ran through years and wars and the deaths '
            'of people they both loved. In the end, aboard a dying ship at the edge of empire, '
            'he chose honor over survival. That choice is his legacy.'
        ),
    },
]


def seed():
    with app.app_context():
        db.create_all()

        # ── Column migrations — adds new columns to existing characters table ──
        from sqlalchemy import text
        _migrations = [
            ('characters', 'image_filename_2', 'VARCHAR(200)'),
            ('characters', 'image_filename_3', 'VARCHAR(200)'),
        ]
        for table, col, col_type in _migrations:
            try:
                db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                db.session.commit()
                print(f'  [migrate]  Added column {table}.{col}')
            except Exception:
                db.session.rollback()  # column already exists — skip silently

        added   = 0
        skipped = 0

        for c in CHARACTERS:
            exists = Character.query.filter_by(name=c['name']).first()
            if exists:
                print(f'  [skip]  Already exists: {c["name"]}')
                skipped += 1
                continue

            char = Character(
                name=c['name'],
                full_name=c['full_name'],
                color=c['color'],
                bio=c['bio'],
                display_order=c['display_order'],
                image_filename=None,
                is_visible=True,
            )
            db.session.add(char)
            added += 1
            print(f'  [added]  {c["name"]} ({c["color"]})')

        db.session.commit()
        print(f'\nDone. {added} character(s) added, {skipped} skipped.')


if __name__ == '__main__':
    seed()
