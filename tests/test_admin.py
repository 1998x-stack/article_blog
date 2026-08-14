from models import create_article, create_comment


def _token(client):
    with client.session_transaction() as s:
        return s["_csrf_token"]


def test_dashboard(admin_client):
    r = admin_client.get("/admin")
    assert r.status_code == 200


def test_create_article(admin_client, app):
    r = admin_client.post("/admin/articles/new", data={
        "_csrf_token": _token(admin_client), "title": "New", "slug": "new",
        "content_md": "# hi", "excerpt": "e", "tags": "a,b"},
        follow_redirects=True)
    assert r.status_code == 200
    assert "New" in r.get_data(as_text=True)


def test_edit_article(admin_client, app, db_path):
    aid = create_article("Old", "old", "x", "e", [], db_path=db_path)
    admin_client.post(f"/admin/articles/{aid}/edit", data={
        "_csrf_token": _token(admin_client), "title": "New Title",
        "slug": "new-title", "content_md": "body", "excerpt": "e", "tags": ""},
        follow_redirects=True)
    r = admin_client.get("/article/new-title")
    assert "New Title" in r.get_data(as_text=True)


def test_delete_article(admin_client, db_path, client):
    aid = create_article("Temp", "temp", "x", "e", [], db_path=db_path)
    admin_client.post(f"/admin/articles/{aid}/delete",
                      data={"_csrf_token": _token(admin_client)},
                      follow_redirects=True)
    assert client.get("/article/temp").status_code == 404


def test_comment_action(admin_client, db_path):
    aid = create_article("C", "c", "x", "e", [], db_path=db_path)
    cid = create_comment(aid, "bob", "hi", db_path=db_path)
    admin_client.post(f"/admin/comments/{cid}/approve",
                      data={"_csrf_token": _token(admin_client)},
                      follow_redirects=True)
    from models import list_all_comments
    assert any(x["id"] == cid for x in list_all_comments(status="approved", db_path=db_path))


def test_import_json(admin_client, app, db_path):
    r = admin_client.post("/admin/import_json", json=[
        {"title": "Imported", "content": "body", "tags": "x"}
    ])
    assert r.status_code == 201
    from models import get_article_by_slug
    assert get_article_by_slug("imported", db_path=db_path) is not None