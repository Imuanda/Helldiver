"""
anon_names.py — Anonymous identity system.

Every visitor who hasn't created an account gets:
  - A session ID (random hex string, stored in their browser cookie)
  - An anonymous name inspired by the Red Rising universe (also in their cookie)

The same name sticks for their entire session so conversations feel coherent.
"""

import random
import secrets

# ── Name pool — Red Rising inspired ─────────────────────────────────────────
# Places, roles, and atmospheric terms from the books.
# Chosen to feel thematic without directly impersonating named characters.
ANON_NAME_POOL = [
    # Places and settlements
    'Stoneside', 'Lykos', 'Tyche', 'Deepmine', 'Laureltide',
    'Hookpoint', 'Caldwell', 'Sunborn', 'Yorath', 'Olympia',
    'Highwater', 'Darkside', 'Sandborn', 'Ironridge', 'Coldbourne',
    'Ashmarked', 'Lowmine', 'Brightstar', 'Stormwatch', 'Nightfall',
    # Roles and titles
    'Helldiver', 'Pioneer', 'Watchman', 'Hauler', 'Dawnbreaker',
    'Ironblood', 'Hardrock', 'Coldfire', 'Sunrock', 'Ashborn',
    # Atmospheric
    'Voidborn', 'Starfall', 'Ironveil', 'Duskrise', 'Crownless',
    'Redearth', 'Goldless', 'Greymantle', 'Darkstone', 'Freeborn',
]


def get_or_create_anon(session):
    """
    Returns (session_id, anon_name) from the Flask session.
    Creates and stores them on first call — subsequent calls return the same values.

    session_id — used to track reactions and comments without requiring an account
    anon_name  — displayed publicly as the commenter's identity
    """
    if 'anon_id' not in session:
        # Generate a cryptographically secure random ID
        session['anon_id'] = secrets.token_hex(16)

    if 'anon_name' not in session:
        # Pick a random name and add a number suffix for uniqueness
        base = random.choice(ANON_NAME_POOL)
        suffix = random.randint(10, 999)
        session['anon_name'] = f'{base}_{suffix}'

    return session['anon_id'], session['anon_name']
