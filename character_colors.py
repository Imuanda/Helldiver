"""
character_colors.py — Known character → Society Color lookup.

When a user submits a quote, we try to auto-detect the speaker's Color
from this table. If the speaker isn't found, the user is asked to pick
the Color themselves from a dropdown.

Keys are lowercase — always .lower().strip() the speaker name before lookup.
"""

CHARACTER_COLORS = {

    # ── Gold ─── rulers, generals, warlords ────────────────────────────────
    'darrow':                  'gold',   # born Red, carved to Gold
    'darrow of lykos':         'gold',
    'darrow au andromedus':    'gold',
    'virginia':                'gold',
    'virginia au augustus':    'gold',
    'mustang':                 'gold',   # Virginia's call sign
    'cassius':                 'gold',
    'cassius au bellona':      'gold',
    'cassius bellona':         'gold',
    'roque':                   'gold',
    'roque au fabii':          'gold',
    'pax':                     'gold',
    'pax au telemanus':        'gold',
    'quinn':                   'gold',
    'quinn au regulus':        'gold',
    'tactus':                  'gold',
    'tactus au rath':          'gold',
    'fitchner':                'gold',
    'fitchner au barca':       'gold',
    'aja':                     'gold',
    'aja au grimmus':          'gold',
    'octavia':                 'gold',
    'octavia au lune':         'gold',
    'nero':                    'gold',
    'nero au augustus':        'gold',
    'victra':                  'gold',
    'victra au julii':         'gold',
    'lysander':                'gold',
    'lysander au lune':        'gold',
    'sevro':                   'gold',   # half Gold/Red — registered as Gold
    'sevro au barca':          'gold',
    'kavax':                   'gold',
    'kavax au telemanus':      'gold',
    'daxo':                    'gold',
    'daxo au telemanus':       'gold',
    'adrius':                  'gold',
    'adrius au augustus':      'gold',
    'atlas':                   'gold',
    'atlas au raa':            'gold',

    # ── Red ─── miners, the lowest caste ────────────────────────────────────
    'eo':                      'red',
    'eo of lykos':             'red',
    'kieran':                  'red',
    'kieran of lykos':         'red',
    'ryanna':                  'red',
    'lyria':                   'red',
    'lyria of lagalos':        'red',
    'bryn':                    'red',    # Sevro's mother — confirmed Red by owner

    # ── Obsidian ─── elite warriors ─────────────────────────────────────────
    'ragnar':                  'obsidian',
    'ragnar volarus':          'obsidian',
    'sefi':                    'obsidian',
    'sefi au volarus':         'obsidian',
    'xenophon':                'obsidian',

    # ── Blue ─── pilots and navigators ──────────────────────────────────────
    'orion':                   'blue',
    'orion xe aquarii':        'blue',   # Darrow's admiral, NOT Roque (who is Gold)

    # ── Silver ─── financiers and merchants ─────────────────────────────────
    'quicksilver':             'silver',
    'magnus au grimmus':       'silver', # Note: Magnus is Gold in some references —
                                         # Quicksilver is his Silver alias/identity

    # ── Pink ─── companions ──────────────────────────────────────────────────
    'dancer':                  'red',    # Red resistance leader
    'harmony':                 'red',

    # ── Gray ─── soldiers ────────────────────────────────────────────────────

    # ── White / Copper / Orange / Green / Violet / Yellow / Bronze / Tan ────
    # Add more as the fact-checking queue is cleared
}


def lookup_color(speaker_name):
    """
    Returns the Society Color for a known speaker, or None if not found.
    The caller should then ask the user to select the Color manually.
    """
    if not speaker_name:
        return None
    return CHARACTER_COLORS.get(speaker_name.lower().strip())


# The 6 valid book titles — used in form dropdowns and validation
VALID_BOOKS = [
    'Red Rising',
    'Golden Son',
    'Morning Star',
    'Iron Gold',
    'Dark Age',
    'Lightbringer',
]

# All Society Colors — used in the quote submission dropdown
VALID_COLORS = [
    'gold', 'red', 'obsidian', 'gray', 'silver', 'pink', 'blue',
    'white', 'copper', 'orange', 'green', 'violet', 'yellow', 'bronze', 'tan',
]
