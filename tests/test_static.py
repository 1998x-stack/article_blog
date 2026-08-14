from models import create_article


def test_css_linked(client):
    assert "/static/css/style.css" in client.get("/").get_data(as_text=True)


def test_view_toggles(client):
    body = client.get("/").get_data(as_text=True)
    assert "view=grid" in body and "view=list" in body


def test_pagination_next_last(client, app, db_path):
    # seed > ARTICLES_PER_PAGE (6) so there are two pages
    for i in range(7):
        create_article(f"Article {i}", f"article-{i}", "x", "e", [], db_path=db_path)
    page1 = client.get("/?page=1").get_data(as_text=True)
    assert "Next" in page1
    page2 = client.get("/?page=2").get_data(as_text=True)
    assert "Next" not in page2  # last page has no forward link


def test_admin_nav_linked(admin_client):
    assert "/admin/articles" in admin_client.get("/admin").get_data(as_text=True)