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