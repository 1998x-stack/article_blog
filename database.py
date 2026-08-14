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