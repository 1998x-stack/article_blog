# Article Blog Rebuild — Design Specification

**Date:** 2026-08-14
**Status:** Approved
**Stack:** Python 3 + Flask + SQLite (no frontend framework)

## 1. Overview

Totally reconstruct and improve the existing `article_blog` project — a small Flask + SQLite blog — into a well-architected, feature-rich technical/developer blog. Improvements cover the backend (modular, secure, tested), the database (normalized schema + full-text search), and the frontend (bold, distinctive, developer-oriented design).

Approach chosen: **Modular Flask monolith with server-rendered Jinja2 templates** (Approach 1). No separate frontend framework or build step.

## 2. Architecture

Modular Flask monolith using the app-factory pattern and blueprints.

```
article_blog/
├── app.py                      # app factory + entry point
├── config.py                   # configuration (DB path, secret key, per-page, etc.)
├── database.py                 # connection helpers + schema init + seed
├── auth.py                     # login/logout, session handling, decorators
├── models.py                   # thin data-access layer (CRUD per entity)
├── markdown.py                 # safe Markdown → HTML rendering
├── blueprints/
│   ├── public.py               # index, article view, search, tag pages
│   ├── comments.py             # public comment submission
│   ├── admin.py                # dashboard, article CRUD, comment moderation
│   └── api.py                  # JSON import endpoint (improved)
├── templates/                  # base, public, admin layouts
├── static/                     # CSS design system, JS
└── tests/                      # pytest
```

Design principles:
- App factory so tests can create isolated app instances.
- Blueprints isolate responsibilities; they communicate only through `models.py`.
- `require_admin` decorator (via `auth.py`) protects admin routes.
- Seed data so the site is non-empty on first launch.

## 3. Database Schema (normalized SQLite)

```sql
users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

articles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    excerpt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

tags(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)

article_tags(
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
)

comments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Supporting details:
- **FTS5 virtual table** (`articles_fts`) for full-text search over title + content, kept in sync on insert/update.
- Indexes on `articles.slug`, `articles.created_at`, `comments.article_id`.
- `PRAGMA foreign_keys = ON` and WAL mode enabled on each connection.
- `slug` auto-generated from title (unique, URL-safe), editable in admin.

## 4. Public Frontend

**Design:** bold, distinctive, developer-oriented. Strong opinionated typography (display/mono accent + clean sans), vivid accent palette with dark hero/header, strong contrast, cards with personality and clear hierarchy, responsive, accessible.

Pages:
- **Home** — paginated article grid/list (most recent first), tag filter chips, polished pagination with page numbers and correct next/last behavior.
- **Article page** — rendered Markdown (styled code blocks, links, images, blockquotes, tables), meta (date, tags → clickable), comments section.
- **Search** — FTS results with match highlighting.
- **Tag pages** — all articles for a tag.

Markdown rendered server-side with a **safe allowlist** (headings, paragraphs, code, lists, links, blockquotes, images, emphasis, tables) — no raw unsanitized HTML.

## 5. Admin Area & Auth

- Single admin account seeded on first run. Credentials from env (`ADMIN_USERNAME`, `ADMIN_PASSWORD`); if absent, a random password is generated and printed to console/logs on first run.
- Session auth, hashed password, CSRF protection on all forms.
- `require_admin` decorator on all admin routes.
- **Dashboard**: overview counts (articles, pending comments), recent articles.
- **Articles**: list with edit/delete; create/edit form with Markdown + live preview; tag add/remove; auto slug (editable).
- **Comments**: moderation queue (approve / reject / delete), view approved.
- **Import**: improved JSON import (file upload or raw body) with field validation and clear errors.

## 6. Error Handling, Security, Testing

**Error handling:** branded 404 and 403 pages; graceful empty states; JSON error responses for API.

**Security:** parameterized SQL everywhere; CSRF on all POST forms; session secret from config/env (no default); password hashing; Markdown sanitization (XSS); escaped comment content; safe URL handling; protected import endpoint.

**Testing (pytest):**
- DB layer: CRUD, tag filtering, search.
- Routes: index, article, search, admin CRUD, comment posting + moderation.
- Auth: login required, wrong password.
- Markdown render/sanitization.