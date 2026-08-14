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