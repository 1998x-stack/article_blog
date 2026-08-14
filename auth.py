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
        create_user(username, generate_password_hash(password, method="pbkdf2:sha256"), db_path=db)


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
    return render_template("admin/login.html")


@bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    return redirect(url_for("public.index"))