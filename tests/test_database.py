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