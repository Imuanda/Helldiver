# Red Rising

## What is this project about
After reading Red Rising Saga, I have decided to build a web app inspired by the book.
So here what I wanna build:
- A web app that renders and displays powerful quotes from the book and saves them
- Work in the backend to build a safe and easy to navigate web application with the precision and knowledge of an architect
- Work on the different layers of the project since the front end with the quote is just a pretty face of a masterpiece in the backend

This is a practice project to learn how to code with AI, so take the time needed to complete it the right way
and also take the time to teach me how to effectively use AI to code through this project.


---

## Tech Stack

- **Backend**: Flask (Python) — lightweight, beginner-friendly, pairs naturally with HTML/CSS/JS
- **Frontend**: Plain HTML, CSS, JavaScript — no frameworks
- **Database**: SQLite (via Flask-SQLAlchemy) — simple file-based database, no server needed
- **Auth**: Flask-Login — handles sign-up, login, and session management
- **Virtual Environment**: Already created at `redrising/redrising/` — always activate it before installing anything


---

## Steps

### Step 1 — Frontend: Landing Page & Main Layout [DONE]
- Create a minimalistic but beautiful and visually striking frontend
- The landing screen is a **star and planet map** of the Red Rising universe
- At the center of the map: **Cassius au Bellona's last words from Lightbringer** (exact quote TBD — must be verified before use)
- Clicking the screen zooms the camera into **Mars**, transitioning into the actual app
- Add a **vertical sidebar/toolbar** that can be toggled in and out:
  - **Home** button — navigates to the home quote view
  - **Colors** button — a dropdown that lists all the Colors of the Society (see Colors section below)
- The **Home** body shows a single quote card containing:
  - The quote text
  - Who said it
  - Book title, chapter, and page number as metadata
  - A space for comments
  - Like and reaction buttons
  - *(Comments, likes, and reactions require login — see Auth)*

### Step 2 — Colors Pages [DONE]
Colors are the caste system of the Society in Red Rising. They are split into two groups:

**Dedicated Pages** (most prominent in the story — full description + quote cards):
| Color | Role in the Society |
|-------|-------------------|
| Gold | The ruling class — emperors, warlords, politicians |
| Red | Miners, the lowest caste — Darrow's color, the heart of the story |
| Obsidian | Elite warriors — Sevro, Ragnar |
| Gray | Soldiers and police — appear constantly throughout |
| Silver | Financiers and merchants — Quicksilver |
| Pink | Companions — enslaved class, carries heavy social weight |
| Blue | Pilots and navigators — Roque au Fabii |

Each dedicated Color page has:
- A description of the Color's role within the Society at the top
- Quote cards below (quote, speaker, book/chapter/page metadata)

**"Others" Section** (remaining colors — description only, no dedicated quote pages):
White, Copper, Orange, Green, Violet, Yellow, Bronze, Tan
These colors still appear in the sidebar under Colors > Others so visitors can learn about them.

### Step 3 — Quote System & Validation [DONE]
Quotes come from three sources:
1. **AI-sourced**: Found by Claude — focused on life lessons and influential lines from the 6 books
2. **Owner-added**: Submitted by the project owner (can request Claude to add them or use a submission form — to be built)
3. **User-submitted**: Submitted by logged-in visitors through the app

**All quotes go through validation regardless of source.**

Validation rules:
- The quote must be traceable to an actual moment in one of the 6 books
- Paraphrases, misattributions, or hallucinations are rejected
- Rejected quotes are logged in `flagged_quotes.json` (see below)

`flagged_quotes.json` entry structure:
```json
{
  "quote": "The exact text that was submitted",
  "source_claimed": "Book title, Chapter X",
  "status": "Invalid",
  "reason": "Could not be verified — likely a paraphrase or hallucination"
}
```
This file is added to `.gitignore` — it is a log, not source code.

Quotes are categorized by the **Color of the character who said them**.
User-submitted quotes appear on the Color page matching the character's Color.

### Step 4 — Authentication & Interactions [DONE]

**Who needs to be logged in:**
- Quote submission — requires login (accountability for content added to the DB)
- Comments and likes/reactions — NO login required (low friction, more engagement)

**Anonymous interactions (no account needed):**
- Tracked by session cookie (assigned on first visit, invisible to the user)
- One reaction per session per quote — prevents spam without requiring login
- Anonymous commenters get a random Red Rising-inspired name assigned per session
  (consistent for the whole session — same name on every comment until session expires)

**Registered users:**
- Required only to submit a quote
- Sign up with email + password
- Username is free choice — but the signup page informs users of options:
  character names from the books, roles (Knight, Howler, Lancer, Praetor, etc.),
  places, or anything else they want. No forced format — just inspiration.
- Username is what appears publicly — email is never shown

**Quote submission form (new sidebar section: "Submit a Quote"):**
- Field 1: The quote (text)
- Field 2: Name of the speaker/author
- Field 3: Book title (dropdown — only the 6 valid books)
- Field 4: Their perspective (optional — "Why do you like this quote?")
- On submit:
  - AI looks up the speaker's Society Color using a known characters table
  - If speaker is unknown, user selects the Color from a dropdown
  - Quote + color + metadata goes through validation.py
  - Saved as 'pending' for owner review before going live
  - Perspective (if provided) is saved with the quote

**Quote card update — Perspective section:**
- If a quote has a perspective attached, the card expands to show it
- Label: "Why I love this quote" (or similar)
- If no perspective, the card stays exactly as it is now — no empty space

**Anonymous username pool:**
A curated list of Red Rising-inspired names (places, minor characters, terms from the books)
assigned randomly to anonymous commenters per session.
Examples: Stoneside, Lykos, Tyche, Deepmine, Laureltide, Hookpoint, Caldwell, Sunborn

**Content rules — applied to ALL submitted content (quotes, comments, perspectives, usernames):**
- Profanity, bullying, harassment, or hate speech → content is blocked, user is banned
- Repeated violations from the same account or session are logged and the author is banned
- A ban silently blocks the user — no content goes through, no explanation shown (prevents workarounds)

**Character limits — standard sizes to protect layout and keep content focused:**
| Field            | Min | Max  |
|------------------|-----|------|
| Username         | 3   | 30   |
| Quote text       | 20  | 600  |
| Speaker/Author   | 2   | 100  |
| Perspective      | 0   | 400  |
| Comment          | 1   | 500  |

**Input sanitization — applied at the point of every form submission:**
- Strip leading/trailing whitespace
- Escape HTML characters to prevent XSS (cross-site scripting)
- Enforce character limits server-side (not just in the browser)
- Profanity filter runs before saving to the database
- Note: deeper security hardening (CSRF, rate limiting, injection audits) is dedicated Step 5

**Privacy principle:** Keep everyone safe and anonymous.
Email is never shown publicly. Usernames are the only public identity.

Build auth with Flask-Login. Session-based. No social login for now.

### Step 4b — Responsiveness [part of Step 4]
Every screen must work on any device size (phone, tablet, desktop).
Key areas: landing planet map scales on mobile (outer planets hidden, Mars stays centered),
quote card padding reduces on small screens, color page description stacks cleanly,
sidebar overlays correctly on mobile. Test at 375px (iPhone SE), 768px (iPad), 1440px (desktop).

### Step 5 — Security, Safety & PWA Foundation [DONE]
**Idempotency:**
- Disable submit/post buttons immediately on first click (client-side, prevents double-tap)
- Server-side duplicate check: reject quotes with matching text+speaker+book already in DB
- Comment submission: debounce on client + server ignores identical text from same session within 10s

**Blast radius / resilience:**
- Add graceful 404 and 500 error pages (no raw Flask tracebacks exposed to users)
- Wrap all DB operations in try/except so one bad query doesn't crash the whole request
- Disable Flask debug mode before any production deployment
- SQLite is fine for this scale — note that moving to PostgreSQL is the path if traffic grows

**Security hardening:**
- CSRF protection on all forms (Flask-WTF tokens)
- Rate limiting on comments, reactions, submissions (Flask-Limiter)
- Full XSS audit — verify all user content is escaped before rendering
- SQL injection review (SQLAlchemy parameterizes queries, but verify no raw SQL)
- Security headers (Content-Security-Policy, X-Frame-Options, HSTS, etc.)
- Ban system review and testing

**PWA & App Store foundation:**
The goal is to eventually submit to iOS App Store and Google Play.
The most practical path is a Progressive Web App (PWA) wrapped with Capacitor.
Requirements to add in this step:
- manifest.json — app name, icons, theme color, display mode (standalone)
- Service worker — offline support and asset caching
- Apple meta tags (apple-mobile-web-app-capable, apple-mobile-web-app-status-bar-style)
- HTTPS is mandatory in production for both PWA and app stores
- App icons at required sizes (iOS: 180x180, Android: 512x512, etc.)
- Privacy policy page (required by both stores — we collect emails)
Note: Capacitor wrapping and actual store submission are a separate phase after this.
A dedicated pass to harden the app before it could ever go public.
- CSRF protection on all forms (Flask-WTF tokens)
- Rate limiting on comments, reactions, and quote submissions (Flask-Limiter)
- Full XSS audit — verify all user content is escaped before rendering
- SQL injection review (SQLAlchemy parameterizes queries, but verify nothing uses raw SQL)
- Security headers (Content-Security-Policy, X-Frame-Options, etc.)
- IP/session-based ban system review and testing
- Review all routes that accept user input

### Step 6 — Final Cleanup & Deployment Prep [DONE]
- `requirements.txt` generated from venv (29 packages)
- `Procfile` — gunicorn entry point for Render
- `runtime.txt` — Python 3.8.3
- `render.yaml` — full Render deployment config with persistent disk
- Admin panel built at `/admin` — dashboard, pending queue, add quote, user management
- `make_admin.py` — one-time script to promote an account to admin
- `OWNER_GUIDE.md` — private operational guide (in .gitignore, never committed)
- SECRET_KEY and DATABASE_PATH now read from environment variables
- `.gitignore` final audit complete


---

## Restrictions
- Never touch any folder outside of this project
- Do not modify anything outside of this project
- Only operate inside the `redrising/` project folder
- Ask before deleting anything — explain what it is and why it needs to go
- Before committing any change to `.gitignore`, show the full current file contents first so nothing is accidentally removed or exposed
- All log files and sensitive files (e.g. `flagged_quotes.json`, `.env`, database files) must be added to `.gitignore`


---

## Additional Context

See `PRIVATE_WORKBOOK.md` for supplementary operational context. (Gitignored — local only.)


---

## Database Access Policy — Strict Guardrails for Claude

The database contains real user data: emails, usernames, passwords (hashed), comments, and session IDs.
This data belongs to the users and must be treated with maximum caution.

### What Claude is NEVER allowed to do without explicit owner authorization:

- Write, suggest, or run any query that **deletes user records** (`DELETE FROM users`)
- Write, suggest, or run any query that **modifies a user's email or password**
- Write any script that **bulk-modifies or bulk-deletes** rows in any table
- **Read or display** any user's personal data (email, session ID) beyond what's necessary for the immediate task
- Make any **direct change to the live database** — all database changes go through the app's own routes and admin panel

### Before touching ANYTHING database-related, Claude must state:

1. **WHAT** — exactly which table, which columns, and how many rows will be affected
2. **WHY** — the reason this change is needed
3. **WHO requested it** — the owner must have explicitly asked for this in the current conversation

If the request did not come directly and clearly from the owner in this session, Claude must ask for confirmation before proceeding.

### What is approved without special authorization (normal development work):
- Adding new columns or tables via `models.py` (schema changes, not data changes)
- Reading data to display it in templates or the admin panel
- Changes to the `quotes` table for adding/approving/rejecting quotes — this is the core function
- Changes to the `ban_records` table when the owner explicitly requests a ban action

### What always requires a clear "yes, do it" from the owner:
- Any deletion of user accounts or their associated data
- Any modification of user emails, usernames, or password hashes
- Any bulk operation that touches more than one user's records at once
- Running raw SQL against the database outside of normal app operations

When in doubt, stop and ask. The cost of asking is low. The cost of modifying someone's personal data without authorization is not.


---

## Conventions
- Break the project into small files that each serve one specific purpose — never write the whole project in one file
- Add short, clear comments to every piece of code — one line is fine, but write them like explaining to a 5-year-old
- Install all dependencies only inside the virtual environment — never globally
- Follow the steps in order and mark each one `[DONE]` when complete so future sessions know where to continue
- When a new session starts, read this file first and check which steps are marked `[DONE]` before doing anything
- Never start a completed step over — if files from that step already exist and the step is marked `[DONE]`, move on
- When the user adds instructions for a new step, continue from that step only
- **Every new feature must be built on its own branch** — `git checkout -b feature/name` before starting any new feature work. Merge to main when tested.
- **Update OWNER_GUIDE.md** for every new feature or framework added — short explanation, one or two lines max per entry
- **Always add new frameworks/libraries to the Tools section of OWNER_GUIDE.md** with a one-line description


---

## Future Features (backlog — to be built in future sessions)

These are confirmed ideas the owner wants to add. Build each on its own feature branch.

### Planned features:
- **Character Bios** — a dedicated section (accessible from the sidebar) with short bios of main Red Rising characters: Darrow, Sevro, Cassius, Virginia, Ragnar, Lysander, Orion, etc. Each bio: name, Color, role in the saga, key quote
- **Ambient Music** — optional background music (Red Rising-themed/cinematic) on the home page when reading quotes. User can toggle it on/off. Must not autoplay (browser policy)
- **User Profile Page** — `/profile/<username>` showing quotes they've submitted and their account details
- **Quote Search** — search bar to find quotes by keyword, speaker, or book
- **Quote Pagination** — once color pages have many quotes, paginate them (10 per page)
- **Email Verification** — confirm email on signup before account is active
- **Password Reset** — forgot password flow via email
- **Admin Notifications** — email alert to owner when a new quote or suggestion is submitted
- **Report Button** — let users flag comments for admin review
- **Capacitor Wrapping** — wrap the PWA for iOS/Android app store submission


---

## Fact-Check Queue
Items confirmed incorrect by the owner — to be fixed before final release:
- **Obsidian page**: Description references Sevro as "born of a Gold father and an Obsidian mother" — incorrect. Sevro's mother Bryn was a **Red**, making him half Gold, half Red. Also remove Sevro from the Obsidian description entirely.
- **Blue page**: Description references Roque au Fabii as a Blue admiral — incorrect. Roque was a **Gold**. The correct Blue to reference is **Orion xe Aquarii**, Darrow's pilot and admiral aboard the Morning Star.


---

## Workflow — How We Build Step by Step
Claude starts each new session with no memory of the previous one. To avoid repeating completed work:
1. Each finished step is marked `[DONE]` in this file
2. Claude reads this file at the start of every session to find the first step that is NOT `[DONE]`
3. The user can also say "we finished Step X, continue from Step Y" to be safe
4. Claude saves progress notes in its memory system between sessions

This means it is safe to add new steps to this file at any time — Claude will not restart from the top
as long as completed steps are marked `[DONE]`.


---

## Role & Skills
When working on this project, Claude operates as a **senior front-end developer with strong design instincts**.
Design philosophy: modern, minimalistic, visually striking, and beautiful — every screen should feel intentional.
Backend work is approached with the precision of a software architect — clean structure, small focused files, nothing bloated.


---

## Tools Used in This Project
*(To be filled in as we build — listed here per convention)*
- **Flask** — Python web framework that runs the backend server
- **Flask-SQLAlchemy** — connects Flask to the SQLite database so we can store and retrieve quotes
- **Flask-Login** — handles user accounts, sign-up, login, and keeping users logged in
- **SQLite** — a simple file-based database built into Python, no separate server needed
- **HTML/CSS/JS** — the frontend: structure, styling, and interactivity in the browser
- **Jinja2** — Flask's built-in templating engine that lets us inject Python data into HTML pages
- *(More tools will be added here as they are introduced)*
