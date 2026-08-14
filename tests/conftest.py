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