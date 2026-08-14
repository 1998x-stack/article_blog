"""Production WSGI entry point (used by gunicorn via `wsgi:app`)."""
from app import create_app

app = create_app()