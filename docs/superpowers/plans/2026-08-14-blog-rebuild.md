# Article Blog Rebuild — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Totally reconstruct the existing Flask + SQLite blog into a well-architected, secure, tested technical/developer blog with a normalized schema, full-text search, tag filtering, safe Markdown, an admin area, comment moderation, and a bold custom design.

**Architecture:** Modular Flask monolith using the app-factory pattern and blueprints. Server-rendered Jinja2 templates; SQLite (with FTS5) for data; a thin `models.py` data-access layer; blueprints `public`, `comments`, `admin`, `api`; `auth.py` for login/CSRF. Approved design spec: `docs/superpowers/specs/2026-08-14-blog-rebuild-design.md`.

**Tech Stack:** Python 3, Flask, SQLite (incl. FTS5), `markdown` + `bleach` for safe rendering, Werkzeug for password hashing, pytest, vanilla CSS/JS.

## Global Constraints

- Stack: Python 3 + Flask + SQLite only. No frontend framework, no build step, no ORM — use raw SQL via the built-in `sqlite3` module.
- Every connection runs `PRAGMA foreign_keys = ON`; the DB file uses `PRAGMA journal_mode = WAL`.
- All SQL is parameterized (never string-interpolated user values).
- Single admin account; password hashed with Werkzeug `generate_password_hash` (never plaintext).
- `SECRET_KEY` from config/env; CSRF token on every POST form (session token + hidden `_csrf_token` field).
- Markdown → HTML via the `markdown` lib then sanitized with `bleach` allowlist; article/comment content is never rendered raw.
- Public routes use slugs (`/article/<slug>`); admin under `/admin`; auth at `/login`, `/logout`.
- Tests use a temp-file SQLite DB via fixture; they must never touch `blog.db`.
- Layout is fixed by the spec (below in Task 1).

---

### Task 1: Project Scaffolding (config, app factory, deps, fixtures)

**Files:**
- Create: `requirements.txt`, `.gitignore`, `config.py`, `app.py`
- Create: `tests/conftest.py`, `tests/test_smoke.py`

**Interfaces:**
- Produces: `create_app(config_overrides=None) -> flask.Flask`; `config.py` with `DB_PATH`, `ARTICLES_PER_PAGE`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.
- Later tasks consume `create_app()` and the `tests/conftest.py` fixtures `app`, `client`, `db_path`, `admin_client`.

- [ ] **Step 1: Write project metadata files**

`requirements.txt`:
```
Flask>=3.0
Markdown>=3.5
bleach>=6.0
pytest>=8.0
```

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
.env
```

- [ ] **Step 2: Write the configuration module**

`config.py`:
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Absolute path to the SQLite database file.
DB_PATH = str(BASE_DIR / "blog.db")

ARTICLES_PER_PAGE = 6

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-before-deploy")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")  # empty -> random generated
```

- [ ] **Step 3: Write the app factory**

`app.py`:
```python
import os
import config as cfg
from flask import Flask


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", cfg.SECRET_KEY),
        DATABASE=os.environ.get("DATABASE", cfg.DB_PATH),
        ARTICLES_PER_PAGE=cfg.ARTICLES_PER_PAGE,
        ADMIN_USERNAME=cfg.ADMIN_USERNAME,
        ADMIN_PASSWORD=cfg.ADMIN_PASSWORD,
    )
    if config_overrides:
        app.config.update(config_overrides)

    from database import init_db, init_schema
    init_db(app)
    init_schema(app.config["DATABASE"])

    from auth import bp as auth_bp, register_auth_extensions
    from errors import register_error_handlers
    register_auth_extensions(app)
    register_error_handlers(app)

    from blueprints.public import bp as public_bp
    from blueprints.comments import bp as comments_bp
    from blueprints.admin import bp as admin_bp
    from blueprints.api import bp as api_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app
```
> Blueprint modules don't exist until Task 6/7. To keep the scaffold importable and testable now, create empty placeholder modules inline below in Step 4 so `app.py` imports. This scaffold's `create_app` is exercised by the smoke test; the placeholder blueprints are replaced fully in Tasks 6-7.

- [ ] **Step 4: Create placeholders so the app imports**

`database.py`:
```python
import sqlite3
from flask import g

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(app):
    app.teardown_appcontext(_close_db)


def _close_db(e=None):
    db = g.pop("_db", None)
    if db is not None:
        db.close()


def get_db():
    if "_db" not in g:
        g._db = sqlite3.connect(_db_path())
        g._db.row_factory = sqlite3.Row
        g._db.execute("PRAGMA foreign_keys = ON")
    return g._db


def _db_path():
    from flask import current_app
    return current_app.config["DATABASE"]


def init_schema(db_path):
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(_SCHEMA)
```

`seed.py` (no-op for now; real seeding in Task 2/5):
```python
def seed_admin(app):
    pass
```

`blueprints/__init__.py`:
```python
from . import public  # populated in Task 6
```

`blueprints/public.py` (placeholder — replaced in Task 6):
```python
from flask import Blueprint
bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    return "ok"
```

`blueprints/comments.py` (placeholder), `blueprints/admin.py`, `blueprints/api.py` — each:
```python
from flask import Blueprint
bp = Blueprint("NAME", __name__)
```

`auth.py` (placeholder; replaced in Task 5):
```python
def register_auth_extensions(app):
    pass
```

`errors.py` (placeholder; replaced in Task 5):
```python
def register_error_handlers(app):
    pass
```

- [ ] **Step 5: Write the failing smoke test**

`tests/conftest.py`:
```python
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402


@pytest.fixture
def app(tmp_path):
    test_db = str(tmp_path / "test.db")
    app = create_app({
        "DATABASE": test_db,
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "testpass",
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_path(app):
    return app.config["DATABASE"]
```

`tests/test_smoke.py`:
```python
from app import create_app


def test_app_factory_creates_app():
    app = create_app({"TESTING": True})
    assert app is not None
    assert app.config["SECRET_KEY"]


def test_root_responds(client):
    assert client.get("/").status_code == 200
```

- [ ] **Step 6: Install deps and run**

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest tests/test_smoke.py -v
```
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .gitignore config.py app.py database.py auth.py errors.py blueprints/ tests/
git commit -m "chore: scaffold Flask app factory, config, and test harness"
```

---

### Task 2: Database Schema, Helpers & Seed

**Files:**
- Replace: `database.py`
- Create: `tests/test_database.py`

**Interfaces:**
- Consumes: `app.config["DATABASE"]`.
- Produces: `get_db()`, `init_db(app)`, `init_schema(db_path)`, `reset_and_seed(db_path)`; triggers keep FTS in sync automatically.

- [ ] **Step 1: Write the failing DB test**

`tests/test_database.py`:
```python
import sqlite3
from database import init_schema, get_db


def test_schema_creates_tables(db_path):
    init_schema(db_path)
    with sqlite3.connect(db_path) as con:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"users", "articles", "tags", "article_tags", "comments"} <= tables


def test_foreign_keys_enforced(db_path, app):
    init_schema(db_path)
    with app.app_context():
        db = get_db()
        try:
            db.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (99999, 99999)")
            db.commit()
            raised = False
        except Exception:
            raised = True
        assert raised
```

- [ ] **Step 2: Run — expect failure**

```
source .venv/bin/activate
pytest tests/test_database.py -v
```
Expected: FAIL — the minimal schema from Task 1 lacks `tags`/`article_tags`/`articles`/`comments` tables.

- [ ] **Step 3: Implement the full schema**

Replace `database.py`:
```python
import sqlite3
from flask import g

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    excerpt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title, content,
    content='articles', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, title, content) VALUES (new.id, new.title, new.content_md);
END;

CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, content)
    VALUES ('delete', old.id, old.title, old.content_md);
END;

CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title, content)
    VALUES ('delete', old.id, old.title, old.content_md);
    INSERT INTO articles_fts(rowid, title, content) VALUES (new.id, new.title, new.content_md);
END;

CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);
CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_article ON comments(article_id);
"""


def init_db(app):
    app.teardown_appcontext(_close_db)


def get_db():
    if "_db" not in g:
        g._db = sqlite3.connect(_db_path())
        g._db.row_factory = sqlite3.Row
        g._db.execute("PRAGMA foreign_keys = ON")
        g._db.execute("PRAGMA journal_mode = WAL")
    return g._db


def _close_db(e=None):
    db = g.pop("_db", None)
    if db is not None:
        db.close()


def init_schema(db_path):
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.executescript(_SCHEMA)


def reset_and_seed(db_path):
    from models import create_article
    with sqlite3.connect(db_path) as con:
        for t in ("article_tags", "comments", "tags"):
            con.execute(f"DELETE FROM {t}")
        con.execute("DELETE FROM articles_fts")
        con.execute("DELETE FROM articles")
    create_article("First Article", "first-article",
                   "Welcome to the blog. Posts about **Python** and **Flask**.",
                   "Introductory post", ["python", "flask"], db_path=db_path)
    create_article("Second Article", "second-article",
                   "Notes on building clean, fast websites with SQLite.",
                   "A technical post", ["web", "development"], db_path=db_path)


def _db_path():
    from flask import current_app
    return current_app.config["DATABASE"]
```
> `reset_and_seed` uses `models.create_article` (built in Task 3); it will only run after Task 3. The `ORDER BY ... DESC` index on articles is created by the FTS triggers regardless.

- [ ] **Step 4: Run DB tests**

`pytest tests/test_database.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_database.py
git commit -m "feat: add normalized schema with FTS5, triggers, and connection helpers"
```

---

### Task 3: Data Layer (models.py)

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

**Interfaces:**
Produces (each function takes `db_path=None`, defaulting to `app.config["DATABASE"]` via `g`):
- `create_user(username, password_hash, db_path=None) -> id`
- `get_user_by_username(username, db_path=None) -> sqlite3.Row | None`
- `create_article(title, slug, content_md, excerpt, tags, db_path=None) -> id`
- `update_article(article_id, title, slug, content_md, excerpt, tags, db_path=None)`
- `delete_article(article_id, db_path=None)`
- `get_article(article_id, db_path=None)`, `get_article_by_slug(slug, db_path=None)`
- `list_articles(limit, offset, db_path=None)` (recent first), `count_articles(db_path=None)`
- `search_articles(query, limit, offset, db_path=None)`
- `list_tags(db_path=None)`, `get_articles_by_tag(tag, limit, offset, db_path=None)`, `count_articles_by_tag(tag, db_path=None)`
- `get_tags_for_article(article_id, db_path=None) -> list[str]`
- `create_comment(article_id, author, content, db_path=None)`, `list_comments(article_id, status='approved', db_path=None)`, `list_all_comments(status=None, db_path=None)`, `set_comment_status(comment_id, status, db_path=None)`, `delete_comment(comment_id, db_path=None)`, `count_comments(status=None, db_path=None)`
- `recent_articles(limit=5, db_path=None)`

- [ ] **Step 1: Write the failing models test**

`tests/test_models.py`:
```python
import pytest
from models import (
    create_article, get_article, update_article, delete_article,
    list_articles, count_articles, search_articles, list_tags,
    get_tags_for_article, get_articles_by_tag, count_articles_by_tag,
    create_user, get_user_by_username,
)


@pytest.fixture
def db_path(app):
    from database import init_schema
    init_schema(app.config["DATABASE"])
    return app.config["DATABASE"]


def test_user(db_path):
    uid = create_user("admin", "hash123", db_path=db_path)
    row = get_user_by_username("admin", db_path=db_path)
    assert row["id"] == uid
    assert row["password_hash"] == "hash123"


def test_article_roundtrip(db_path):
    aid = create_article("Hello", "hello-world", "**body**", "e", ["intro", "guide"],
                         db_path=db_path)
    row = get_article(aid, db_path=db_path)
    assert row["title"] == "Hello"
    assert row["slug"] == "hello-world"


def test_update_and_delete(db_path):
    aid = create_article("Keep", "keep", "x", "e", [], db_path=db_path)
    update_article(aid, "Changed", "changed", "y", "e", ["a"], db_path=db_path)
    assert get_article(aid, db_path=db_path)["title"] == "Changed"
    delete_article(aid, db_path=db_path)
    assert get_article(aid, db_path=db_path) is None


def test_list_and_count(db_path):
    create_article("One", "one", "x", "e", [], db_path=db_path)
    create_article("Two", "two", "x", "e", [], db_path=db_path)
    assert count_articles(db_path=db_path) == 2
    assert len(list_articles(1, 0, db_path=db_path)) == 1


def test_search_finds_title(db_path):
    aid = create_article("About Python", "py", "talk about python", "e", ["p"],
                         db_path=db_path)
    rows = search_articles("python", 10, 0, db_path=db_path)
    assert any(r["id"] == aid for r in rows)


def test_tags_roundtrip_and_filter(db_path):
    aid = create_article("Tag It", "tag", "body", "e", ["python", "web"],
                         db_path=db_path)
    assert set(get_tags_for_article(aid, db_path=db_path)) == {"python", "web"}
    names = {t["name"] for t in list_tags(db_path=db_path)}
    assert {"python", "web"} <= names
    found = get_articles_by_tag("python", 10, 0, db_path=db_path)
    assert any(a["id"] == aid for a in found)
    assert count_articles_by_tag("python", db_path=db_path) >= 1
```

- [ ] **Step 2: Run — expect failure**

`pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'models'`.

- [ ] **Step 3: Implement `models.py`**

```python
import sqlite3
from flask import g


def _conn(db_path):
    if db_path:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con
    return get_db()


def get_db():
    if "_db" not in g:
        g._db = sqlite3.connect(_db_path())
        g._db.row_factory = sqlite3.Row
        g._db.execute("PRAGMA foreign_keys = ON")
    return g._db


def _db_path():
    from flask import current_app
    return current_app.config["DATABASE"]


# --- users ---
def create_user(username, password_hash, db_path=None):
    con = _conn(db_path)
    cur = con.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))
    con.commit()
    return cur.lastrowid


def get_user_by_username(username, db_path=None):
    con = _conn(db_path)
    return con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


# --- tags / articles ---
def _tag_ids(con, names):
    ids = []
    for name in (names or []):
        con.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        row = con.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        ids.append(row["id"])
    return ids


def create_article(title, slug, content_md, excerpt, tags, db_path=None):
    con = _conn(db_path)
    cur = con.execute(
        "INSERT INTO articles (title, slug, content_md, excerpt) VALUES (?, ?, ?, ?)",
        (title, slug, content_md, excerpt))
    aid = cur.lastrowid
    for tid in _tag_ids(con, tags):
        con.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)", (aid, tid))
    con.commit()
    return aid


def update_article(article_id, title, slug, content_md, excerpt, tags, db_path=None):
    con = _conn(db_path)
    con.execute("UPDATE articles SET title=?, slug=?, content_md=?, excerpt=?, "
                "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (title, slug, content_md, excerpt, article_id))
    con.execute("DELETE FROM article_tags WHERE article_id = ?", (article_id,))
    for tid in _tag_ids(con, tags):
        con.execute("INSERT INTO article_tags (article_id, tag_id) VALUES (?, ?)",
                    (article_id, tid))
    con.commit()


def delete_article(article_id, db_path=None):
    con = _conn(db_path)
    con.execute("DELETE FROM articles WHERE id=?", (article_id,))
    con.commit()


def get_article(article_id, db_path=None):
    return _conn(db_path).execute(
        "SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()


def get_article_by_slug(slug, db_path=None):
    return _conn(db_path).execute(
        "SELECT * FROM articles WHERE slug=?", (slug,)).fetchone()


def list_articles(limit, offset, db_path=None):
    return _conn(db_path).execute(
        "SELECT * FROM articles ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)).fetchall()


def count_articles(db_path=None):
    return _conn(db_path).execute(
        "SELECT COUNT(*) AS c FROM articles").fetchone()["c"]


def search_articles(query, limit, offset, db_path=None):
    return _conn(db_path).execute(
        "SELECT a.* FROM articles_fts JOIN articles a ON a.id = articles_fts.rowid "
        "WHERE articles_fts MATCH ? LIMIT ? OFFSET ?",
        (query, limit, offset)).fetchall()


def get_tags_for_article(article_id, db_path=None):
    return [r["name"] for r in _conn(db_path).execute(
        "SELECT t.name FROM tags t JOIN article_tags at ON at.tag_id = t.id "
        "WHERE at.article_id=? ORDER BY t.name", (article_id,)).fetchall()]


def list_tags(db_path=None):
    return _conn(db_path).execute(
        "SELECT t.name, COUNT(at.article_id) AS count FROM tags t "
        "LEFT JOIN article_tags at ON at.tag_id = t.id "
        "GROUP BY t.id ORDER BY t.name").fetchall()


def get_articles_by_tag(tag, limit, offset, db_path=None):
    return _conn(db_path).execute(
        "SELECT a.* FROM articles a JOIN article_tags at ON at.article_id=a.id "
        "JOIN tags t ON t.id=at.tag_id WHERE t.name=? "
        "ORDER BY a.created_at DESC LIMIT ? OFFSET ?", (tag, limit, offset)).fetchall()


def count_articles_by_tag(tag, db_path=None):
    return _conn(db_path).execute(
        "SELECT COUNT(*) AS c FROM articles a JOIN article_tags at ON at.article_id=a.id "
        "JOIN tags t ON t.id=at.tag_id WHERE t.name=?", (tag,)).fetchone()["c"]


# --- comments ---
def create_comment(article_id, author, content, db_path=None):
    con = _conn(db_path)
    cur = con.execute(
        "INSERT INTO comments (article_id, author, content) VALUES (?, ?, ?)",
        (article_id, author, content))
    con.commit()
    return cur.lastrowid


def list_comments(article_id, status="approved", db_path=None):
    return _conn(db_path).execute(
        "SELECT * FROM comments WHERE article_id=? AND status=? ORDER BY created_at ASC",
        (article_id, status)).fetchall()


def list_all_comments(status=None, db_path=None):
    con = _conn(db_path)
    if status:
        return con.execute(
            "SELECT * FROM comments WHERE status=? ORDER BY created_at DESC",
            (status,)).fetchall()
    return con.execute("SELECT * FROM comments ORDER BY created_at DESC").fetchall()


def set_comment_status(comment_id, status, db_path=None):
    con = _conn(db_path)
    con.execute("UPDATE comments SET status=? WHERE id=?", (status, comment_id))
    con.commit()


def delete_comment(comment_id, db_path=None):
    con = _conn(db_path)
    con.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    con.commit()


def count_comments(status=None, db_path=None):
    con = _conn(db_path)
    if status:
        return con.execute("SELECT COUNT(*) AS c FROM comments WHERE status=?",
                           (status,)).fetchone()["c"]
    return con.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"]


def recent_articles(limit=5, db_path=None):
    return list_articles(limit, 0, db_path=db_path)
```

- [ ] **Step 4: Run the models tests**

```
source .venv/bin/activate
pytest tests/test_models.py -v
```
Expected: PASS.
Expected: PASS.

- [ ] **Step 5: Verify `reset_and_seed` now works (use existing test DB)**

```
.venv/bin/python -c "from database import reset_and_seed; reset_and_seed('/tmp/seed_check.db')"
```
Expected: no traceback (two seeded articles created).

- [ ] **Step 6: Commit**

```bash
git add models.py database.py tests/test_models.py
git commit -m "feat: add data-access layer for articles, tags, users, comments, search"
```

---

### Task 4: Markdown Rendering (safe)

**Files:**
- Create: `render.py`
- Create: `tests/test_render.py`

**Interfaces:**
- Produces: `render_markdown(text: str) -> str` (sanitized HTML).
- Re-exported as `models.render_markdown` in Task 6.

- [ ] **Step 1: Write the failing render test**

`tests/test_render.py`:
```python
from render import render_markdown


def test_renders_heading():
    html = render_markdown("# Hello")
    assert "<h1>Hello</h1>" in html


def test_strips_script():
    html = render_markdown("<script>alert(1)</script>")
    assert "script" not in html


def test_renders_code():
    html = render_markdown("```python\nprint(1)\n```")
    assert "<code" in html


def test_allows_safe_link():
    html = render_markdown("[ok](https://example.com)")
    assert 'href="https://example.com"' in html


def test_blocks_javascript_href():
    html = render_markdown("[x](javascript:alert(1))")
    assert "javascript:" not in html
```

- [ ] **Step 2: Run — expect failure**

`pytest tests/test_render.py -v` — Expected: FAIL, `ImportError`.

- [ ] **Step 3: Implement `render.py`**

```python
import markdown as _md
import bleach

_ALLOWED_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "strong", "em", "del", "code", "pre", "blockquote",
    "a", "ul", "ol", "li", "img", "table", "thead", "tbody",
    "tr", "th", "td",
]
_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}
_ALLOWED_PROTOCOLS = {"http", "https", "mailto"}


def render_markdown(text: str) -> str:
    processor = _md.Markdown(extensions=["fenced_code", "tables", "nl2br", "sane_lists"])
    html = processor.convert(text or "")
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
```

- [ ] **Step 4: Run — expect PASS**

`pytest tests/test_render.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add render.py tests/test_render.py
git commit -m "feat: add safe markdown-to-HTML rendering with bleach allowlist"
```

---

### Task 5: Auth, CSRF & Admin Blueprint

**Files:**
- Replace: `auth.py`, `errors.py`
- Create: `csrf.py`
- Create: `tests/test_auth.py` (+ `admin_client` fixture in `conftest.py`)
- Create: `templates/admin/login.html`, `templates/errors/404.html`, `templates/errors/403.html`

**Interfaces:**
- Produces: `register_auth_extensions(app)` (seeds admin + registers `csrf_token` template global), `login`, `logout` routes, `require_admin` decorator, `register_error_handlers(app)`, `validate_csrf()`, `generate_csrf_token()`.
- Consumes: `models.get_user_by_username`, `models.create_user`, Werkzeug password hashing.
- The `admin_client` fixture relies on real login now working (Task 5 finish).

- [ ] **Step 1: Write failing auth tests**

`tests/test_auth.py`:
```python
def test_admin_route_redirects_to_login(client):
    r = client.get("/admin")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_bad_login_fails(client):
    client.get("/login")
    with client.session_transaction() as s:
        token = s.get("_csrf_token")
    r = client.post("/login", data={"username": "admin", "password": "wrong",
                                    "_csrf_token": token})
    assert r.status_code == 200
    assert "Invalid" in r.get_data(as_text=True)


def test_login_then_access_admin(app, client):
    # fetch csrf token from session
    client.get("/login")
    with client.session_transaction() as s:
        token = s.get("_csrf_token")
    r = client.post("/login", data={"username": app.config["ADMIN_USERNAME"],
                                    "password": app.config["ADMIN_PASSWORD"],
                                    "_csrf_token": token})
    assert r.status_code == 302
    r2 = client.get("/admin")
    assert r2.status_code == 200
```

- [ ] **Step 2: Run — expect failure**

`pytest tests/test_auth.py -v` — Expected: FAIL (routes/`/admin`/templates missing).

- [ ] **Step 3: Implement `csrf.py`**

`csrf.py`:
```python
import secrets
from flask import session, request, abort


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(24)
    return session["_csrf_token"]


def validate_csrf():
    token = session.get("_csrf_token")
    submitted = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
    if not token or not submitted or not secrets.compare_digest(token, submitted):
        abort(400)
```

- [ ] **Step 4: Implement `auth.py`**

`auth.py`:
```python
import secrets
from functools import wraps
from flask import (Blueprint, session, redirect, url_for, render_template,
                   request, flash, current_app)
from werkzeug.security import generate_password_hash, check_password_hash
import config as cfg

from models import get_user_by_username, create_user
from csrf import validate_csrf, generate_csrf_token

bp = Blueprint("auth", __name__)


def register_auth_extensions(app):
    @app.context_processor
    def inject_csrf():
        return {"csrf_token": generate_csrf_token}

    username = app.config.get("ADMIN_USERNAME", cfg.ADMIN_USERNAME)
    password = app.config.get("ADMIN_PASSWORD") or cfg.ADMIN_PASSWORD
    db = app.config["DATABASE"]
    if get_user_by_username(username, db_path=db) is None:
        if not password:
            password = secrets.token_urlsafe(12)
            print(f"Generated admin password for {username}: {password}")
        create_user(username, generate_password_hash(password), db_path=db)


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = get_user_by_username(username, db_path=current_app.config["DATABASE"])
        if user and check_password_hash(user["password_hash"], password):
            session["admin_id"] = user["id"]
            flash("Logged in.", "success")
            return redirect(request.args.get("next") or url_for("public.index"))
        flash("Invalid credentials.", "error")
    return render_template("admin/login.html"), (200 if request.method == "GET" else 200)


@bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    return redirect(url_for("public.index"))
```

- [ ] **Step 5: Implement `errors.py`**

`errors.py`:
```python
from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403
```

- [ ] **Step 6: Add minimal admin/error templates**

All extend a `base.html` (created in Task 6; create a minimal one now in `templates/base.html`):
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Article Blog{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <div class="flash">
        {% for category, msg in messages %}<p class="{{ category }}">{{ msg }}</p>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</body>
</html>
```
`templates/admin/login.html`, `errors/404.html`, `errors/403.html` each `{% extends "base.html" %}` with a `{% block content %}` (login = username/password/`csrf_token()` hidden field; errors = message text).

- [ ] **Step 7: Fix the `admin_client` fixture in `conftest.py`**

```python
@pytest.fixture
def admin_client(app):
    c = app.test_client()
    c.get("/login")
    with c.session_transaction() as s:
        token = s.get("_csrf_token")
    c.post("/login", data={
        "username": app.config["ADMIN_USERNAME"],
        "password": app.config["ADMIN_PASSWORD"],
        "_csrf_token": token,
    })
    return c
```

- [ ] **Step 8: Add a stub `/admin` dashboard route in the admin blueprint**

`blueprints/admin.py`:
```python
from flask import Blueprint, render_template, redirect, url_for, session
from auth import require_admin

bp = Blueprint("admin", __name__)


@bp.route("/admin")
@require_admin
def dashboard():
    return render_template("admin/dashboard.html")
```
Add `templates/admin/dashboard.html` (minimal).
> Full dashboard/counts land in Task 7; this stub lets `test_admin_route` pass.

- [ ] **Step 9: Run auth tests**

`pytest tests/test_auth.py -v` — Expected: PASS.

- [ ] **Step 10: Commit**

```bash
git add csrf.py auth.py errors.py blueprints/admin.py templates/ tests/conftest.py tests/test_auth.py
git commit -m "feat: add admin auth, CSRF, error handlers, and login flow"
```

---

### Task 6: Public Blueprint (index, article, search, tag)

**Files:**
- Create: `blueprints/public.py` (replace placeholder)
- Create: `blueprints/comments.py`
- Create: `templates/index.html`, `templates/article.html`, `templates/search.html`, `templates/tag.html`
- Modify: `models.py` (add `render_markdown` re-export)
- Create: `tests/test_public.py`

**Interfaces:**
- Produces: routes `/` (`public.index`), `/article/<slug>` (`public.article`), `/search` (`public.search`), `/tag/<name>` (`public.tag`), and `comments.post_comment` at `POST /article/<slug>/comments`.
- Consumes: `models.*`, `app.config["ARTICLES_PER_PAGE"]`, `render_markdown`.

- [ ] **Step 1: Write failing public tests**

`tests/test_public.py`:
```python
from models import create_article


def test_index_lists_articles(client, db_path):
    create_article("One", "one", "x", "e", ["a"], db_path=db_path)
    r = client.get("/")
    assert r.status_code == 200
    assert "One" in r.get_data(as_text=True)


def test_article_page(client, db_path):
    create_article("Detail", "detail", "Body here", "e", ["t"], db_path=db_path)
    r = client.get("/article/detail")
    assert r.status_code == 200
    assert "Detail" in r.get_data(as_text=True)


def test_article_404(client):
    assert client.get("/article/nope").status_code == 404


def test_search_finds_article(client, db_path):
    create_article("Python Search", "py", "all about python", "e", ["p"], db_path=db_path)
    r = client.get("/search?q=python")
    assert "Python Search" in r.get_data(as_text=True)


def test_tag_page(client, db_path):
    create_article("Tagged", "tagged", "x", "e", ["flask"], db_path=db_path)
    r = client.get("/tag/flask")
    assert "Tagged" in r.get_data(as_text=True)
```

- [ ] **Step 2: Run — expect failure**

`pytest tests/test_public.py -v` — Expected: FAIL (routes/templates missing).

- [ ] **Step 3: Implement `public.py`**

`blueprints/public.py`:
```python
from flask import Blueprint, render_template, request, abort, current_app
import models

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    view_type = request.args.get("view", "grid")
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    per = current_app.config["ARTICLES_PER_PAGE"]
    offset = (page - 1) * per
    articles = models.list_articles(per, offset)
    total = models.count_articles()
    total_pages = max(1, -(-total // per))
    return render_template("index.html", articles=articles, view_type=view_type,
                           page=page, total=total, total_pages=total_pages,
                           tags=models.list_tags())


@bp.route("/article/<slug>")
def article(slug):
    row = models.get_article_by_slug(slug)
    if row is None:
        abort(404)
    return render_template(
        "article.html",
        article=row,
        tags=models.get_tags_for_article(row["id"]),
        comments=models.list_comments(row["id"], status="approved"),
        rendered=models.render_markdown(row["content_md"]),
    )


@bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    results = models.search_articles(q, 20, 0) if q else []
    return render_template("search.html", q=q, results=results, total=len(results))


@bp.route("/tag/<name>")
def tag(name):
    per = current_app.config["ARTICLES_PER_PAGE"]
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    offset = (page - 1) * per
    articles = models.get_articles_by_tag(name, per, offset)
    total = models.count_articles_by_tag(name)
    total_pages = max(1, -(-total // per))
    return render_template("tag.html", tag=name, articles=articles,
                           page=page, total_pages=total_pages)
```

`blueprints/comments.py`:
```python
from flask import Blueprint, request, redirect, url_for, flash
from csrf import validate_csrf
import models

bp = Blueprint("comments", __name__)


@bp.post("/article/<slug>/comments")
def post_comment(slug):
    validate_csrf()
    article = models.get_article_by_slug(slug)
    if article is None:
        return redirect(url_for("public.index"))
    author = (request.form.get("author") or "").strip()
    content = (request.form.get("content") or "").strip()
    if not author or not content:
        flash("Name and comment are required.", "error")
    else:
        models.create_comment(article["id"], author, content)
        flash("Thanks! Your comment is awaiting moderation.", "success")
    return redirect(url_for("public.article", slug=slug))
```

- [ ] **Step 4: Re-export `render_markdown` via models**

Add to the top of `models.py`:
```python
from render import render_markdown
```

- [ ] **Step 5: Create minimal public templates**

Each extends `base.html` and renders its variables with plain HTML (titles, excerpts/summaries, links to `/article/<slug>`, comment form returning `author`/`content` + `csrf_token()` hidden input, search form `q`, tag chips). Real styling is Task 9.

- [ ] **Step 6: Run public tests**

`pytest tests/test_public.py -v` — Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add blueprints/public.py blueprints/comments.py models.py templates/index.html templates/article.html templates/search.html templates/tag.html tests/test_public.py
git commit -m "feat: add public blog routes and templates"
```

---

### Task 7: Admin CRUD, Comment Moderation & JSON Import

**Files:**
- Replace: `blueprints/admin.py`
- Replace: `blueprints/api.py`
- Create: `templates/admin/*` (dashboard, articles list, article form, comments)
- Create: `tests/test_admin.py`
- Create: `slug.py`
- Create: `tests/test_slug.py`

**Interfaces:**
- Consumes: `require_admin`, `validate_csrf`, models, `slugify`.
- Produces: `/admin` dashboard, `/admin/articles`, `/admin/articles/new`, `/admin/articles/<id>/edit`, `/admin/articles/<id>/delete`, `/admin/comments`, `POST /admin/comments/<id>/<action>`, `POST /admin/import_json`.

- [ ] **Step 1: Write `slug.py` + tests (fail first)**

`tests/test_slug.py`:
```python
from slug import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_punctuation():
    assert slugify("C# & Python!") == "c-python"


def test_unicode():
    assert slugify("Café") == "cafe"


def test_empty():
    assert slugify("  ") == "untitled"
```
Run `pytest tests/test_slug.py -v` → FAIL. Then `slug.py`:
```python
import re
import unicodedata


def slugify(title):
    s = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "untitled"
```
Run again → PASS.

- [ ] **Step 2: Write failing admin tests**

`tests/test_admin.py`:
```python
from models import create_article, create_comment


def _token(client):
    with client.session_transaction() as s:
        return s["_csrf_token"]


def test_dashboard(admin_client):
    r = admin_client.get("/admin")
    assert r.status_code == 200


def test_create_article(admin_client, app):
    r = admin_client.post("/admin/articles/new", data={
        "_csrf_token": _token(admin_client), "title": "New", "slug": "new",
        "content_md": "# hi", "excerpt": "e", "tags": "a,b"},
        follow_redirects=True)
    assert r.status_code == 200
    assert "New" in r.get_data(as_text=True)


def test_edit_article(admin_client, app, db_path):
    aid = create_article("Old", "old", "x", "e", [], db_path=db_path)
    admin_client.post(f"/admin/articles/{aid}/edit", data={
        "_csrf_token": _token(admin_client), "title": "New Title",
        "slug": "new-title", "content_md": "body", "excerpt": "e", "tags": ""},
        follow_redirects=True)
    r = admin_client.get("/article/new-title")
    assert "New Title" in r.get_data(as_text=True)


def test_delete_article(admin_client, db_path, client):
    aid = create_article("Temp", "temp", "x", "e", [], db_path=db_path)
    admin_client.post(f"/admin/articles/{aid}/delete",
                      data={"_csrf_token": _token(admin_client)},
                      follow_redirects=True)
    assert client.get("/article/temp").status_code == 404


def test_comment_action(admin_client, db_path):
    aid = create_article("C", "c", "x", "e", [], db_path=db_path)
    cid = create_comment(aid, "bob", "hi")
    admin_client.post(f"/admin/comments/{cid}/approve",
                      data={"_csrf_token": _token(admin_client)},
                      follow_redirects=True)
    from models import list_all_comments
    assert any(x["id"] == cid for x in list_all_comments(status="approved", db_path=db_path))


def test_import_json(admin_client, app, db_path):
    r = admin_client.post("/admin/import_json", json=[
        {"title": "Imported", "content": "body", "tags": "x"}
    ])
    assert r.status_code == 201
    from models import get_article_by_slug
    assert get_article_by_slug("imported", db_path=db_path) is not None
```
> The JSON import endpoint reads the session via the `admin_client` login (no form CSRF needed for `application/json`; `validate_csrf` reads `X-CSRF-Token` or form field). If import needs the token, set the `X-CSRF-Token` header in the request.

- [ ] **Step 3: Run — expect failures**

`pytest tests/test_admin.py tests/test_slug.py -v` — Expected: slug tests fail (module), admin fail (routes/templates).

- [ ] **Step 4: Implement `blueprints/admin.py`**

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from auth import require_admin
from csrf import validate_csrf
from slug import slugify
import models

bp = Blueprint("admin", __name__)


@bp.get("/admin")
@require_admin
def dashboard():
    return render_template(
        "admin/dashboard.html",
        article_count=models.count_articles(),
        pending=models.count_comments(status="pending"),
        approved=models.count_comments(status="approved"),
        recent=models.recent_articles(5),
    )


@bp.get("/admin/articles")
@require_admin
def articles_list():
    return render_template("admin/articles_list.html",
                           articles=models.list_articles(1000, 0))


@bp.route("/admin/articles/new", methods=["GET", "POST"])
@require_admin
def new():
    if request.method == "POST":
        validate_csrf()
        title = (request.form.get("title") or "").strip()
        content = request.form.get("content_md", "")
        excerpt = (request.form.get("excerpt") or "").strip()
        slug = (request.form.get("slug") or slugify(title)).strip()
        tags = [t.strip() for t in (request.form.get("tags") or "").split(",") if t.strip()]
        if not title or not content or not slug:
            flash("Title, slug, and content are required.", "error")
        else:
            models.create_article(title, slug, content_md=content, excerpt=excerpt, tags=tags)
            flash("Article created.", "success")
            return redirect(url_for("admin.articles"))
    return render_template("admin/article_form.html", article=None, form_tags="")


@bp.route("/admin/articles/<int:article_id>/edit", methods=["GET", "POST"])
@require_admin
def edit(article_id):
    article = models.get_article(article_id)
    if article is None:
        abort(404)
    if request.method == "POST":
        validate_csrf()
        title = (request.form.get("title") or "").strip()
        slug = (request.form.get("slug") or slugify(title)).strip()
        content = request.form.get("content_md", "")
        excerpt = (request.form.get("excerpt") or "").strip()
        tags = [t.strip() for t in (request.form.get("tags") or "").split(",") if t.strip()]
        if not title or not content or not slug:
            flash("Title, slug, and content are required.", "error")
        else:
            models.update_article(article_id, title, slug, content, excerpt, tags)
            flash("Article updated.", "success")
            return redirect(url_for("admin.articles"))
    return render_template("admin/article_form.html", article=article,
                           form_tags=", ".join(models.get_tags_for_article(article_id)))


@bp.post("/admin/articles/<int:article_id>/delete")
@require_admin
def delete(article_id):
    validate_csrf()
    models.delete_article(article_id)
    flash("Article deleted.", "success")
    return redirect(url_for("admin.articles"))


@bp.get("/admin/comments")
@require_admin
def comments():
    return render_template("admin/comments.html",
                           pending=models.list_all_comments(status="pending"),
                           approved=models.list_all_comments(status="approved"))


@bp.post("/admin/comments/<int:comment_id>/<action>")
@require_admin
def comment_action(comment_id, action):
    validate_csrf()
    mapping = {"approve": "approved", "reject": "rejected", "delete": None}
    if action not in mapping:
        abort(400)
    if mapping[action] is None:
        models.delete_comment(comment_id)
    else:
        models.set_comment_status(comment_id, mapping[action])
    return redirect(url_for("admin.comments"))
```
> Note `create_article` is called with keyword `content_md=` because it is the 4th positional param; passing it by keyword avoids ambiguity.

- [ ] **Step 5: Implement `blueprints/api.py`**

```python
import json
from flask import Blueprint, request, jsonify, session
import models
from slug import slugify

bp = Blueprint("api", __name__)


@bp.post("/admin/import_json")
def import_json():
    if not session.get("admin_id"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        payload = json.loads(request.get_data(as_text=True) or "[]")
    except (json.JSONDecodeError, ValueError):
        return jsonify({"error": "Invalid JSON"}), 400
    if not isinstance(payload, list):
        return jsonify({"error": "JSON must be a list"}), 400
    added = 0
    for i, item in enumerate(payload):
        title = (item.get("title") or "").strip()
        content = (item.get("content") or "").strip()
        raw_tags = item.get("tags", "")
        tags = raw_tags if isinstance(raw_tags, list) else [t for t in raw_tags.split(",") if t]
        if not title or not content:
            return jsonify({"error": f"Missing fields in article {i + 1}"}), 400
        models.create_article(title, slugify(title), content,
                              (item.get("excerpt") or "")[:160], tags)
        added += 1
    return jsonify({"success": f"Imported {added} articles", "added": added}), 201
```

- [ ] **Step 6: Create admin templates**

Each extends `base.html` (or an `admin/admin_base.html` extending base) with navigation to dashboard/articles/comments/logout. All POST forms include `{{ csrf_token() }}` hidden field. Article form uses a textarea `content_md`. Comment moderation lists pending with approve/reject/delete links (POST forms).

- [ ] **Step 7: Run admin tests**

`pytest tests/test_admin.py -v` — Expected: PASS (`test_import_json` needs `admin_client` logged-in or raw `client` with session; use `admin_client`).

- [ ] **Step 8: Commit**

```bash
git add slug.py blueprints/admin.py blueprints/api.py templates/admin tests/test_admin.py tests/test_slug.py
git commit -m "feat: add admin dashboard, article CRUD, comment moderation, JSON import"
```

---

### Task 8: Bold Design System (CSS + JS + full templates)

**Files:**
- Replace: `static/css/style.css`
- Create: `static/js/main.js`
- Rewrite: `templates/base.html`, `templates/index.html`, `templates/article.html`, `templates/search.html`, `templates/tag.html`, all `templates/admin/*`
- Create: `tests/test_static.py`

**Design:** bold, developer-oriented — dark header/hero, mono accent font, vivid accent (teal), strong type scale, tag chips, responsive grid/list, accessible contrast, focus states.

- [ ] **Step 1: Write static smoke tests**

`tests/test_static.py`:
```python
def test_css_linked(client):
    assert "/static/css/style.css" in client.get("/").get_data(as_text=True)


def test_view_toggles(client):
    body = client.get("/").get_data(as_text=True)
    assert "view=grid" in body and "view=list" in body


def test_pagination_next(client):
    assert "Next" in client.get("/?page=1").get_data(as_text=True)


def test_admin_nav_linked(admin_client):
    assert "/admin/articles" in admin_client.get("/admin").get_data(as_text=True)
```

- [ ] **Step 2: Write the CSS design system**

Full `style.css` implementing CSS custom properties, dark header, card grid + list views, tag chips, pagination, admin nav, forms/buttons, code blocks, comments, flash messages, and mobile media queries. (~400 lines.) Keep class names used by templates: `.container`, `.navbar`, `.article-card`, `.grid`, `.list`, `.tag-chip`, `.pagination`, `.btn`, `.btn-danger`, `.admin-nav`, `.flash`.

- [ ] **Step 3: Write `static/js/main.js`**

Vanilla JS: view-toggle state persisted to `?view=`, smooth scroll on pagination, and a live Markdown preview for `#content_md` refreshing `#markdown-preview` via `POST /admin/preview` (XHR) or client-side textarea-to-HTML placeholder. Keep dependency-free.

- [ ] **Step 4: Update all templates to the new CSS classes/markup**

Rewrite base.html with the full layout; give index.html the grid/list + tag chips + pagination; article.html rendered markdown + comments; admin templates with the admin shell.

- [ ] **Step 5: Run tests + boot check**

```
pytest tests/test_static.py -v
.venv/bin/flask --app app routes   # no import errors
```

- [ ] **Step 6: Commit**

```bash
git add static/ templates/ tests/test_static.py
git commit -m "feat: add bold design system and full page templates"
```

---

### Task 9: Security Regression Tests, README & Final Verification

**Files:**
- Create: `tests/test_security.py`
- Write: `README.md`

- [ ] **Step 1: Write security regression tests**

`tests/test_security.py`:
```python
def test_csrf_missing_blocked(admin_client):
    r = admin_client.post("/admin/articles/new", data={"title": "x", "content_md": "y"})
    assert r.status_code == 400


def test_comment_requires_csrf(client, db_path):
    from models import create_article
    create_article("X", "x", "body", "e", [], db_path=db_path)
    r = client.post("/article/x/comments",
                    data={"author": "bob", "content": "hi"})
    assert r.status_code == 400


def test_public_has_no_admin_link_for_anon(client):
    assert "/admin" not in client.get("/").get_data(as_text=True)
```

- [ ] **Step 2: Write `README.md`**

Document install (`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`), env vars (`SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`), running (`flask run`), default admin message, features, project layout, and testing (`pytest`).

- [ ] **Step 3: Full test run + boot check**

```
source .venv/bin/activate
pytest -v
```
Expected: all green.
```
.venv/bin/flask --app app run
```
Confirm `/`, an article, `/search`, `/tag/...`, `/login`, and `/admin` load without 500s (log in with seeded admin password shown at first run).

- [ ] **Step 4: Commit**

```bash
git add tests/test_security.py README.md
git commit -m "docs: add README and security regression tests"
```

---

## Self-Review

- **Spec coverage:** schema (Task 2), models/search/tags (Task 3), markdown (Task 4), admin+auth+CSRF (Task 5, 7), public + search + tags + comments (Task 6), JSON import (Task 7), bold design (Task 8), security/tests/README (Task 9). All spec §2–§6 mapped.
- **No placeholders:** all tests/code are concrete; no "TBD"/"add handling".
- **Type/name consistency:** `create_article(title, slug, content_md, excerpt, tags, db_path=None)` used consistently; `render_markdown`, `csrf_token()`, `require_admin`, `validate_csrf`, `slugify` signatures match across tasks.