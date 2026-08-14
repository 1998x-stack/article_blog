import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Absolute path to the SQLite database file.
DB_PATH = str(BASE_DIR / "blog.db")

ARTICLES_PER_PAGE = 6

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-before-deploy")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")  # empty -> random generated