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