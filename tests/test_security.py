from models import create_article


def test_csrf_missing_blocked(admin_client):
    r = admin_client.post("/admin/articles/new", data={"title": "x", "content_md": "y"})
    assert r.status_code == 400


def test_comment_requires_csrf(client, db_path):
    create_article("X", "x", "body", "e", [], db_path=db_path)
    r = client.post("/article/x/comments",
                    data={"author": "bob", "content": "hi"})
    assert r.status_code == 400


def test_public_has_no_admin_link_for_anon(client):
    assert "/admin" not in client.get("/").get_data(as_text=True)