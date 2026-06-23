import os
import random
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from extensions import db

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))

# Use PostgreSQL on Render (DATABASE_URL is set automatically when you link the DB)
# Fall back to local SQLite for development
database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    # Render provides 'postgres://' but SQLAlchemy requires 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development — SQLite file next to app.py
    db_path = os.environ.get('DATABASE_PATH', os.path.join(basedir, 'database.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Session cookie hardening ──────────────────────────────────────────────────
# HttpOnly — JS cannot read the cookie (prevents cookie theft via XSS)
# SameSite=Lax — cookie not sent on cross-site requests (CSRF mitigation)
# Secure — cookie only sent over HTTPS (disabled in local dev where HTTP is used)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Secure flag is True in production (gunicorn, debug=False), False in local dev (debug=True)
app.config['SESSION_COOKIE_SECURE']   = os.environ.get('FLASK_ENV') == 'production'

# SECRET_KEY is required — the app will refuse to start without it
# Local dev: set it in .env | PythonAnywhere: set it in the WSGI file
_secret = os.environ.get('SECRET_KEY')
if not _secret:
    raise RuntimeError(
        'SECRET_KEY environment variable is not set. '
        'Add SECRET_KEY=your-random-string to your .env file. '
        'Generate one with: python3 -c "import secrets; print(secrets.token_hex(32))"'
    )
app.config['SECRET_KEY'] = _secret

# ── Application logging ───────────────────────────────────────────────────────
# Writes structured logs to logs/app.log — rotates at 1 MB, keeps 5 old files
logs_dir = os.path.join(basedir, 'logs')
os.makedirs(logs_dir, exist_ok=True)

_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'app.log'),
    maxBytes=1_000_000,   # 1 MB per file
    backupCount=5,        # keep up to 5 rotated files (5 MB total max)
    encoding='utf-8',
)
_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
))
_handler.setLevel(logging.INFO)
app.logger.addHandler(_handler)
app.logger.setLevel(logging.INFO)

# ── Extensions ────────────────────────────────────────────────────────────────
db.init_app(app)

# CSRF protection — adds a hidden token to every form; rejects requests without it
csrf = CSRFProtect(app)

# Rate limiting — restricts how many requests one IP can make per window
# API endpoints (react, comment) get tighter limits than page loads
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=['200 per day', '60 per hour'],
    storage_uri='memory://',   # in-memory store — fine for single-server dev/prod
)

# Flask-Login — manages user sessions and the current_user proxy
login_manager = LoginManager(app)
login_manager.login_view     = 'auth.login'
login_manager.login_message  = 'Please sign in to submit a quote.'

from models import Quote, User, DailyVisit, LandingQuote  # import after db is bound to app

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login calls this to reload the user from the session on each request
    return User.query.get(int(user_id))

# ── Register blueprints ───────────────────────────────────────────────────────
from auth         import auth_bp
from interactions import interactions_bp
from submit       import submit_bp
from admin        import admin_bp
from suggest      import suggest_bp

app.register_blueprint(auth_bp)
app.register_blueprint(interactions_bp)
app.register_blueprint(submit_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(suggest_bp)

# ── Color + Others data ───────────────────────────────────────────────────────
COLORS = {
    'gold': {
        'name': 'Gold', 'hex': '#d4af37', 'caste': 'The Ruling Caste',
        'description': (
            'The ruling caste of the Society — emperors, senators, generals, and warlords. '
            'Golds believe themselves divinely chosen to govern all lesser Colors, a mandate '
            'of intellect, beauty, and ferocity drilled into them from birth through brutal '
            'institutions like the Institute on Mars. They control the legions, the Senate, '
            'the Sovereign\'s court, and the destiny of the solar system. Their culture is '
            'one of conquest, ambition, and honor — or the illusion of it.'
        ),
    },
    'red': {
        'name': 'Red', 'hex': '#c0392b', 'caste': 'The Laboring Caste',
        'description': (
            'The foundation of civilization, though they will never know it. Reds mine the '
            'helium-3 that powers civilization across the solar system, toiling in tunnels '
            'beneath the surface of planets they are told they are terraforming for future '
            'generations. It is a lie. Reds are the lowest caste by design — and the first '
            'spark of revolution. Darrow of Lykos, a Red from the mines of Lykos on Mars, '
            'would become the match that lit the fire.'
        ),
    },
    'obsidian': {
        'name': 'Obsidian', 'hex': '#3a3a3a', 'caste': 'The Warrior Caste',
        'description': (
            'The deadliest warriors the Society has ever engineered. Towering, fearless, and '
            'bred for combat above all else, Obsidians serve as the Gold caste\'s elite soldiers '
            'and personal bodyguards. They follow a warrior code older than the Society itself '
            'and were historically told that Golds are gods incarnate. Among the most iconic '
            'Obsidians is Ragnar Volarus — whose loyalty and fearlessness became legend across '
            'the solar system. When an Obsidian\'s belief in Gold divinity shatters, there is '
            'nothing more dangerous alive.'
        ),
    },
    'gray': {
        'name': 'Gray', 'hex': '#8e9aaf', 'caste': 'The Soldier Caste',
        'description': (
            'The soldiers, police, and guards who enforce the Society\'s order across every '
            'planet and station. Grays are the backbone of law enforcement — pragmatic, '
            'disciplined, loyal to their chain of command above all else. They fill the '
            'legions, patrol the cities and warrens, and keep the lower Colors in line. '
            'Often the first face of authority that a Red, Pink, or Copper ever sees.'
        ),
    },
    'silver': {
        'name': 'Silver', 'hex': '#b0b0c0', 'caste': 'The Merchant Caste',
        'description': (
            'The financiers and merchants who control the Society\'s economy. Silvers operate '
            'the banks, the trade fleets, and the great commercial houses that move resources '
            'across the solar system. The most powerful among them — Quicksilver — accumulates '
            'influence that rivals the most decorated Gold families, funding revolutions and '
            'counter-revolutions alike from the shadows of commerce.'
        ),
    },
    'pink': {
        'name': 'Pink', 'hex': '#e75480', 'caste': 'The Companion Caste',
        'description': (
            'Trained from birth to serve the Society\'s elite as companions, entertainers, and '
            'confidants. Behind their cultivated grace lies one of the Society\'s most profound '
            'injustices — their lives belong entirely to others from the moment they are born. '
            'Yet some Pinks, armed with the secrets they keep and the trust they earn, become '
            'the most dangerous political players in the entire solar system.'
        ),
    },
    'blue': {
        'name': 'Blue', 'hex': '#4a90e2', 'caste': 'The Navigator Caste',
        'description': (
            'The pilots, navigators, and astrogators of the Society\'s fleets. Blues command '
            'the great warships with mathematical precision and an almost religious devotion '
            'to their craft. Without Blues, the solar system goes dark. Among the most '
            'celebrated Blues is Orion xe Aquarii, Darrow\'s admiral aboard the Morning Star, '
            'whose tactical brilliance shaped the fate of the Republic.'
        ),
    },
}

OTHERS = [
    {'name': 'White',  'hex': '#f0ece4',
     'description': 'Priests, judges, and arbiters of the Society\'s laws and spiritual rites. Whites maintain the religious and legal frameworks that give the Society its veneer of divine order and moral authority. Their robes are a symbol of neutrality — though in practice, neutrality serves whoever holds power.'},
    {'name': 'Copper', 'hex': '#b87333',
     'description': 'Administrators, bureaucrats, and record keepers who manage the day-to-day operations of government across the solar system. Coppers file the paperwork, track the census, process the permits, and hold civilization together at its most tedious and essential level.'},
    {'name': 'Orange', 'hex': '#e07b39',
     'description': 'Mechanics and engineers who maintain the machines, ships, and infrastructure of the Society. Without Oranges, nothing runs. Every engine, every life support system, every weapon of war depends on the hands of an Orange somewhere in the chain.'},
    {'name': 'Green',  'hex': '#50c878',
     'description': 'Programmers, scientists, and researchers who advance the Society\'s technology and maintain its digital systems. Greens write the code that governs the networks, develop new weapons and medicines, and push the boundaries of what is possible — always in service of the Colors above them.'},
    {'name': 'Violet', 'hex': '#8a4fff',
     'description': 'Artists, architects, and creatives who craft the beauty and culture of the Society. Violets design the towers of Hyperion, compose the music played in the courts of Gold, and paint the portraits that hang in the Senate. Art in the Society is never neutral — it glorifies the hierarchy.'},
    {'name': 'Yellow', 'hex': '#f5c842',
     'description': 'Doctors, surgeons, and medical researchers who care for the bodies of the Society\'s citizens — from battlefield surgeons to the finest physicians in the Core. The quality of care a Yellow provides depends entirely on the Color of the patient they serve.'},
    {'name': 'Bronze', 'hex': '#cd7f32',
     'description': 'Mid-level administrators and functionaries who serve as the connective tissue between the ruling Golds and the bureaucratic Coppers. Bronzes manage regional offices, coordinate logistics, and carry messages between the powerful.'},
    {'name': 'Tan',    'hex': '#c8a87a',
     'description': 'The farmers and agricultural workers who grow the food supply for the Society\'s billions across terraformed worlds and hydroponic stations. Tans work the soil so that every other Color can eat — and like so many essential castes, they are largely invisible to those they feed.'},
]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def landing():
    # Load the active intro quote — fall back to Cassius's quote if none is set
    intro = LandingQuote.query.filter_by(is_active=True).first()
    if not intro:
        # Default fallback so the page is never blank
        class _Default:
            text   = ('I am Cassius Bellona, son of Tiberius, son of Julia, '
                      'brother of Darrow, Morning Knight of the Solar Republic, '
                      'and my honor remains.')
            author = 'Cassius au Bellona · Lightbringer'
        intro = _Default()
    return render_template('landing.html', intro=intro)


@app.route('/home')
def home():
    validated = Quote.query.filter_by(status='validated').all()
    if not validated:
        return render_template('home.html', quote=None, quote_ids=[], active_page='home')
    quote = random.choice(validated)
    # Pass all IDs so the JS navigator knows the full sequence
    quote_ids = [q.id for q in validated]
    return render_template('home.html', quote=quote, quote_ids=quote_ids, active_page='home')


@app.route('/api/quote/<int:quote_id>')
def api_quote(quote_id):
    """Returns a single validated quote as JSON — used by the swipe navigator."""
    from flask import jsonify
    quote = Quote.query.get_or_404(quote_id)
    if quote.status != 'validated':
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id':            quote.id,
        'text':          quote.text,
        'speaker':       quote.speaker,
        'book':          quote.book,
        'chapter':       quote.chapter,
        'page':          quote.page,
        'heart_count':   quote.heart_count,
        'fire_count':    quote.fire_count,
        'shocked_count': quote.shocked_count,
        'likes':         quote.likes,
        'perspective':   quote.perspective,
    })


@app.route('/colors/others')
def others_page():
    return render_template('others.html', colors=OTHERS, active_page='others')


@app.route('/colors/<slug>')
def color_page(slug):
    color = COLORS.get(slug.lower())
    if not color:
        return redirect(url_for('home'))
    quotes = (Quote.query
              .filter_by(color=slug.lower(), status='validated')
              .order_by(Quote.created_at.desc())
              .all())
    return render_template('color.html', color=color, quotes=quotes, active_page=slug.lower())


# ── Maintenance mode ─────────────────────────────────────────────────────────
# Create the file  ~/Helldiver/maintenance.flag  to put the site in maintenance.
# Delete that file to bring it back. No code change or reload required.
MAINTENANCE_FLAG = os.path.join(basedir, 'maintenance.flag')

@app.before_request
def track_visit():
    """Counts unique sessions per day — one DB row per visitor per day."""
    # Skip static files, admin routes, and API calls — only count real page views
    if (request.path.startswith('/static') or
            request.path.startswith('/admin') or
            request.path.startswith('/api') or
            request.path.startswith('/quote/')):
        return
    try:
        from anon_names import get_or_create_anon
        from datetime import date
        from sqlalchemy.exc import IntegrityError
        anon_id, _ = get_or_create_anon(session)
        visit = DailyVisit(session_id=anon_id, date=date.today())
        db.session.add(visit)
        db.session.commit()
    except Exception:
        db.session.rollback()  # silently ignore duplicates and errors


@app.before_request
def check_maintenance():
    if not os.path.exists(MAINTENANCE_FLAG):
        return  # site is live — do nothing
    # Admins can still browse normally while the site is "down"
    if current_user.is_authenticated and current_user.is_admin:
        return
    # Everyone else sees the maintenance page
    if request.endpoint not in ('static',):
        return render_template('maintenance.html'), 503


# ── CSRF exemptions — AJAX endpoints send JSON, not form tokens ───────────────
csrf.exempt(interactions_bp)

# ── Rate limiting on sensitive routes ─────────────────────────────────────────
# These decorators apply tighter limits on top of the global defaults
limiter.limit('10 per minute')(interactions_bp.view_functions.get('interactions.react', lambda: None))
limiter.limit('5 per minute')(interactions_bp.view_functions.get('interactions.add_comment', lambda: None))


# ── Security headers — added to every response ────────────────────────────────
@app.after_request
def set_security_headers(response):
    # Prevents the site being loaded in an iframe (clickjacking protection)
    response.headers['X-Frame-Options'] = 'DENY'
    # Stops browsers guessing content types (MIME-sniffing protection)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Limits what resources the browser can load (XSS reduction layer)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    # HSTS — tells browsers to always use HTTPS for this domain for 2 years
    # Only sent in production (not local dev) to avoid locking out HTTP localhost
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
    return response


# ── Graceful error pages ──────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f'404 — {request.method} {request.path}')
    return render_template('404.html', active_page=''), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f'500 — {request.method} {request.path} — {e}')
    return render_template('500.html', active_page=''), 500

@app.errorhandler(429)
def rate_limited(e):
    app.logger.warning(f'429 rate limit hit — {request.method} {request.path}')
    if request.accept_mimetypes.accept_json:
        from flask import jsonify as _jsonify
        return _jsonify({'error': 'Too many requests — please slow down.'}), 429
    return render_template('500.html', active_page=''), 429


if __name__ == '__main__':
    # IMPORTANT: set debug=False before any production deployment
    app.run(debug=True, port=5001)
