from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
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
def articles():
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