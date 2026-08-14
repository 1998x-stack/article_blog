# Article Blog

A modern, secure, technically-styled blog built on **Flask** and **SQLite**, with
**FTS5 full-text search**, a normalized schema, safe Markdown rendering, tag
filtering, a protected admin area, and comment moderation.

The codebase is deliberately modular (app-factory + blueprints), dependency-light,
and fully test-driven, with a custom "field journal / code-scratch" visual identity.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration (.env)](#configuration-env)
- [Running](#running)
- [Seeding Content](#seeding-content)
- [Managing Content](#managing-content)
- [JSON Import](#json-import)
- [Project Layout](#project-layout)
- [Testing](#testing)
- [Security](#security)

---

## Features

- **Article authoring** — create, edit, and delete posts from a password-protected
  admin dashboard.
- **Full-text search** — SQLite **FTS5** across titles and content, with relevance
  ranking.
- **Tagging** — per-article tags, clickable chips, and dedicated tag pages.
- **Safe Markdown** — write in Markdown; rendered server-side and sanitized through
  a strict `bleach` allowlist (no raw, unescaped HTML).
- **Comments with moderation** — readers can leave comments, which are held in a
  pending queue until an admin approves, rejects, or deletes them.
- **Grid & list views** with correct, page-numbered pagination.
- **Bold design** — a distinctive "developer's notebook" aesthetic: JetBrains Mono
  display, warm ink palette, amber accent, dot-grid grain, responsive and accessible
  (visible focus, reduced-motion support).

## Tech Stack

- **Python 3.9+**
- **Flask** (app-factory + blueprints)
- **SQLite** via the standard `sqlite3` module, with **FTS5** full-text search
- **python-dotenv** for configuration
- **Markdown** + **bleach** for safe rendering
- **pytest** for testing

No ORM, no front-end build step, and no heavyweight framework — raw, explicit SQL
keeps behavior transparent.

---

## Getting Started

**Requirements:** Python 3.9+

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Configuration (.env)

Copy the example configuration into a local `.env` (git-ignored):

```bash
cp .env.example .env
```

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Flask session signing key (use a long random string) | dev fallback |
| `DATABASE` | Path to the SQLite database file | `blog.db` |
| `ADMIN_USERNAME` | Admin account username | `admin` |
| `ADMIN_PASSWORD` | Admin account password | if empty, a random one is generated and printed on first boot |

`.env` is read automatically by Flask (via `python-dotenv`) and is **never**
committed to version control.

## Running

```bash
flask --app app run --host 0.0.0.0 --port 8000
```

- **Site:** http://localhost:8000
- **Admin login:** http://localhost:8000/login

Log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` from your `.env` (or the
generated password shown on the first boot), then manage articles at
`/admin/articles` and comments at `/admin/comments`.

The database schema is created automatically on first startup.

## Seeding Content

The repository ships two idempotent seeding scripts:

```bash
# Starter set — 8 well-written technical posts (rebuilds blog.db)
python scripts/seed_professional.py

# A second batch — 7 more posts (merges into the existing DB, skips duplicates)
python scripts/seed_extra.py
```

Anything you author in the admin dashboard is persisted to `blog.db` and will not
be overwritten by these scripts (the professional seed intentionally replaces the
database; the **extra** seed only adds).

## Managing Content

| Action | How |
|--------|-----|
| Write a post | Log in → **Articles → New article** (Markdown + live preview) |
| Edit / delete | Dashboard → **Articles**, then Edit/Delete |
| Moderate comments | Dashboard → **Comments** (approve / reject / delete) |

## JSON Import

Bulk-import a JSON list of articles via an authenticated request to
`/admin/import_json`:

```bash
curl -X POST http://localhost:8000/admin/import_json \
  -H "Content-Type: application/json" \
  -b <session-cookie> \
  -d '[{"title":"My Post","content":"# Heading\\nbody","tags":"python,web","excerpt":"…"}]'
```

Each object requires `title` and `content`; `tags` may be a comma-separated string
or a list.

## Project Layout

```
app.py            App factory + entry point
config.py         Env-driven configuration
database.py       Schema, connection helpers, reset/seed
models.py         Data-access layer (articles, tags, comments, users, search)
render.py         Safe Markdown → HTML (bleach allowlist)
auth.py           Login/logout, admin seeding, CSRF/injection
csrf.py           CSRF token generation & validation
slug.py           URL slug helper
blueprints/       public · comments · admin · api
scripts/          seed_professional.py · seed_extra.py
static/           css/style.css · js/main.js
templates/        Jinja2 templates (public + admin) + _header.html partial
tests/            pytest suite
```

## Testing

```bash
pytest
```

The suite runs against a temporary SQLite database per test and never touches
`blog.db`. It covers the schema, the data layer, routing (public/admin), search,
tag filtering, comment moderation, authentication/CSRF, and Markdown sanitization.

## Security

- **Parameterized SQL** throughout (raw `sqlite3`, never string-interpolated input).
- **Password hashing** with Werkzeug (`pbkdf2:sha256`) — passwords are never stored
  or logged in plaintext.
- **CSRF protection** on every POST form; the admin API rejects missing tokens.
- **Markdown sanitization** — rendered content is filtered against an allowlist and
  dangerous protocols (`javascript:` etc.) are stripped.
- **Escaped comment content**, safe URL handling, and a hard session secret.
- **Admin routes** are login-protected; anonymous visitors don't see the admin link.

---

Built with SQLite, Flask, and purpose. Crafted as a developer's reading notebook.