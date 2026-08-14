from flask import Blueprint, render_template, request, abort, current_app
import models

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    view_type = request.args.get("view", "grid")
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    per = current_app.config["ARTICLES_PER_PAGE"]
    offset = (page - 1) * per
    articles = models.list_articles(per, offset)
    total = models.count_articles()
    total_pages = max(1, -(-total // per))
    lead_tags = []
    if page == 1 and articles:
        lead_tags = models.get_tags_for_article(articles[0]["id"])
    return render_template("index.html", articles=articles, view_type=view_type,
                           page=page, total=total, total_pages=total_pages,
                           tags=models.list_tags(), lead_tags=lead_tags)


@bp.route("/article/<slug>")
def article(slug):
    row = models.get_article_by_slug(slug)
    if row is None:
        abort(404)
    return render_template(
        "article.html",
        article=row,
        tags=models.get_tags_for_article(row["id"]),
        comments=models.list_comments(row["id"], status="approved"),
        rendered=models.render_markdown(row["content_md"]),
    )


@bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    results = models.search_articles(q, 20, 0) if q else []
    return render_template("search.html", q=q, results=results, total=len(results))


@bp.route("/tag/<name>")
def tag(name):
    per = current_app.config["ARTICLES_PER_PAGE"]
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    offset = (page - 1) * per
    articles = models.get_articles_by_tag(name, per, offset)
    total = models.count_articles_by_tag(name)
    total_pages = max(1, -(-total // per))
    return render_template("tag.html", tag=name, articles=articles,
                           page=page, total_pages=total_pages)