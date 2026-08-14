from models import create_article


def test_index_lists_articles(client, db_path):
    create_article("One", "one", "x", "e", ["a"], db_path=db_path)
    r = client.get("/")
    assert r.status_code == 200
    assert "One" in r.get_data(as_text=True)


def test_homepage_shows_lead_once_and_hero_tags(client, db_path):
    create_article("Lead Post", "lead", "x", "e", ["alpha"], db_path=db_path)
    create_article("Other Post", "other", "x", "e", ["beta"], db_path=db_path)
    body = client.get("/").get_data(as_text=True)
    # hero shows the lead once; it must NOT be duplicated in the grid below
    assert body.count("Lead Post") == 1
    # hero renders the lead's own tag chips
    assert "<a class=\"tag-chip\"" in body
    assert "alpha" in body


def test_article_page(client, db_path):
    create_article("Detail", "detail", "Body here", "e", ["t"], db_path=db_path)
    r = client.get("/article/detail")
    assert r.status_code == 200
    assert "Detail" in r.get_data(as_text=True)


def test_article_404(client):
    assert client.get("/article/nope").status_code == 404


def test_search_finds_article(client, db_path):
    create_article("Python Search", "py", "all about python", "e", ["p"], db_path=db_path)
    r = client.get("/search?q=python")
    assert "Python Search" in r.get_data(as_text=True)


def test_tag_page(client, db_path):
    create_article("Tagged", "tagged", "x", "e", ["flask"], db_path=db_path)
    r = client.get("/tag/flask")
    assert "Tagged" in r.get_data(as_text=True)