from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ── User ─────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    """Registered users — only required for submitting quotes."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(30),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # never store plain passwords
    is_banned          = db.Column(db.Boolean, default=False)
    ban_reason         = db.Column(db.String(200), nullable=True)
    is_admin           = db.Column(db.Boolean, default=False)
    failed_login_count = db.Column(db.Integer, default=0)    # consecutive failed login counter
    locked_until       = db.Column(db.DateTime, nullable=True)  # None = not locked
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    # Link back to quotes and comments this user submitted
    submitted_quotes = db.relationship('Quote',   backref='submitter', lazy=True,
                                       foreign_keys='Quote.submitted_by_id')
    comments         = db.relationship('Comment', backref='author',    lazy=True)

    def set_password(self, password):
        # Hashes the password before storing — we NEVER save the plain text
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Compares input against the stored hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# ── Quote ─────────────────────────────────────────────────────────────────────
class Quote(db.Model):
    """A quote from the Red Rising saga, submitted by AI, owner, or a user."""
    __tablename__ = 'quotes'

    id          = db.Column(db.Integer, primary_key=True)
    text        = db.Column(db.String(600), nullable=False)
    speaker     = db.Column(db.String(100), nullable=False)
    book        = db.Column(db.String(100), nullable=False)
    chapter     = db.Column(db.String(20),  nullable=True)
    page        = db.Column(db.Integer,     nullable=True)

    # Society Color of the speaker — determines which Color page shows this quote
    color       = db.Column(db.String(50), nullable=False)

    # Optional: the submitter's perspective on why they love this quote
    perspective = db.Column(db.String(400), nullable=True)

    # Where the quote came from: 'ai' | 'owner' | 'user'
    source      = db.Column(db.String(20), nullable=False, default='ai')

    # Lifecycle: 'validated' = live | 'pending' = awaiting review | 'rejected' = blocked
    status      = db.Column(db.String(20), nullable=False, default='pending')

    # Reaction counts — updated when users react
    heart_count   = db.Column(db.Integer, default=0)
    fire_count    = db.Column(db.Integer, default=0)
    shocked_count = db.Column(db.Integer, default=0)
    likes         = db.Column(db.Integer, default=0)  # total across all reaction types

    # Who submitted it — null for AI/owner quotes
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Related comments
    comments = db.relationship('Comment', backref='quote', lazy=True,
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quote {self.id}: {self.speaker} — {self.book}>'


# ── Comment ───────────────────────────────────────────────────────────────────
class Comment(db.Model):
    """A comment on a quote — no login required, tracked by session."""
    __tablename__ = 'comments'

    id          = db.Column(db.Integer, primary_key=True)
    quote_id    = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    text        = db.Column(db.String(500), nullable=False)

    # The name shown publicly (anon name or registered username)
    author_name = db.Column(db.String(60), nullable=False)

    # Filled for registered users; null for anonymous commenters
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Session ID for anonymous tracking — allows ban without requiring an account
    session_id  = db.Column(db.String(100), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.id} by {self.author_name}>'


# ── Reaction ──────────────────────────────────────────────────────────────────
class Reaction(db.Model):
    """Tracks who reacted to what — prevents the same session from reacting twice."""
    __tablename__ = 'reactions'

    id         = db.Column(db.Integer, primary_key=True)
    quote_id   = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    type       = db.Column(db.String(20), nullable=False)  # heart | fire | shocked
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One reaction of each type per session per quote
    __table_args__ = (
        db.UniqueConstraint('quote_id', 'type', 'session_id', name='uq_reaction_session'),
    )

    def __repr__(self):
        return f'<Reaction {self.type} on Quote {self.quote_id}>'


# ── LandingQuote ─────────────────────────────────────────────────────────────
class LandingQuote(db.Model):
    """The quote displayed on the star map landing page — managed by admin."""
    __tablename__ = 'landing_quotes'

    id         = db.Column(db.Integer, primary_key=True)
    text       = db.Column(db.String(600), nullable=False)
    # Optional attribution shown below the quote (e.g. "Cassius au Bellona · Lightbringer")
    author     = db.Column(db.String(150), nullable=True)
    # Only one row should have is_active=True at any time
    is_active  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LandingQuote {self.id}: active={self.is_active}>'


# ── Suggestion ───────────────────────────────────────────────────────────────
class Suggestion(db.Model):
    """Feature suggestion submitted by a registered user — visible only to admin."""
    __tablename__ = 'suggestions'

    id         = db.Column(db.Integer, primary_key=True)
    text       = db.Column(db.String(1000), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status     = db.Column(db.String(20), default='new')  # new | read | done
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='suggestions', lazy=True)

    def __repr__(self):
        return f'<Suggestion {self.id} by user {self.user_id}>'


# ── DailyVisit ────────────────────────────────────────────────────────────────
class DailyVisit(db.Model):
    """One row per unique session per day — lightweight unique visitor counter."""
    __tablename__ = 'daily_visits'

    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    date       = db.Column(db.Date, nullable=False)

    # Prevents counting the same session twice on the same day
    __table_args__ = (
        db.UniqueConstraint('session_id', 'date', name='uq_daily_session'),
    )


# ── Character ─────────────────────────────────────────────────────────────────
class Character(db.Model):
    """A character bio entry for the Meet them page — managed by admin."""
    __tablename__ = 'characters'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(50),  nullable=False)   # short display name: "Darrow"
    full_name      = db.Column(db.String(100), nullable=False)   # "Darrow of Lykos"
    color          = db.Column(db.String(30),  nullable=False)   # Society Color: "red", "gold"…
    bio            = db.Column(db.String(800), nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)    # stored in static/characters/
    display_order  = db.Column(db.Integer,     default=0)        # controls card sort order
    is_visible     = db.Column(db.Boolean,     default=True)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<Character {self.name} ({self.color})>'


# ── BanRecord ─────────────────────────────────────────────────────────────────
class BanRecord(db.Model):
    """Log of bans — used to audit and investigate violations."""
    __tablename__ = 'ban_records'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)  # for anonymous bans
    reason     = db.Column(db.String(500), nullable=False)
    banned_by  = db.Column(db.String(50), default='system')  # 'system' or admin username
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BanRecord {self.id}: {self.reason[:40]}>'
