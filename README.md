# Article Blog

A modern, secure, technically-styled blog rebuilt from scratch on **Flask + SQLite** (with FTS5 full-text search). Includes a normalized database schema, safe Markdown rendering, tag filtering, search, a cookies-session admin area, and comment moderation.

## Features

- **Articles** — create, edit, and delete from a protected admin dashboard (no more manual JSON import required, though it's kept for bulk loading).
- **Search** — full-text search (SQLite FTS5) across titles and content.
- **Tags** — tag chips on the homepage and dedicated tag pages.
- **Markdown** — write in Markdown; rendered server-side and sanitized with a `bleach` allowlist (no raw, unescaped HTML).
- **Comments** — readers can comment; new comments are held for admin **moderation** (approve / reject / delete).
- **Grid & list views** with working pagination (page numbers, correct next/last behavior).
- **Bold developer-oriented design** — JetBrains Mono display, warm ink palette, amber accent, responsive, accessible.

## Requirements

- Python 3.9+
- Dependencies installed via pip (see below)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration (environment variables)

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Flask session key | random dev key (**set in production**) |
| `DATABASE` | Path to the SQLite database file | `blog.db` |
| `ADMIN_USERNAME` | Admin account username | `admin` |
| `ADMIN_PASSWORD` | Admin account password | if empty, a random one is generated and printed at first run |

## Running

```bash
flask run
```

- Public site: http://localhost:5000/
- Admin login: http://localhost:5000/login
  - Log in with the **admin username/password** (from env, or the generated password shown on the first boot).
  - After logging in, manage articles at `/admin/articles` and comments at `/admin/comments`.

On first startup the database schema is created automatically and two sample articles are seeded. Use `reset_and_seed()` from `database.py` to re-seed sample content:

```bash
python -c "from database import reset_and_seed; reset_and_seed('blog.db')"
```

## Bulk-importing articles (JSON)

POST an authenticated request to `/admin/import_json` with a JSON array of objects `{ "title", "content", "tags", "excerpt" }`:

```bash
curl -X POST http://localhost:5000/admin/import_json \
  -H "Content-Type: application/json" \
  -b <session-cookie> \
  -d '[{"title":"My Post","content":"# Heading\nbody text","tags":"python,web"}]'
```

## Project layout

```
app.py            Flask app factory + entry point
config.py         configuration (env-driven)
database.py       schema, connection helpers, seed
models.py         data-access layer (articles, tags, comments, users, search)
render.py         safe Markdown → HTML (bleach allowlist)
auth.py           login/logout, admin seeding, CSRF/helper injection
csrf.py           CSRF token generation & validation
slug.py           URL slug helper
blueprints/       public, comments, admin, api
static/css        style.css  (design system)
static/js         main.js
templates/        Jinja2 templates (public + admin)
tests/            pytest suite
```

## Testing

```bash
pytest
```

Tests run against a temporary SQLite database per-test and never touch `blog.db`.

## Security

- Parameterized SQL (SQLAlchemy-free, raw `sqlite3`) throughout.
- Passwords hashed with Werkzeug (`pbkdf2:sha256`).
- CSRF tokens on every POST form; the admin API rejects missing tokens.
- Markdown sanitized; comment content escaped; `javascript:` and dangerous protocols stripped.
- Admin routes protected; anonymous visitors don't see the admin link.