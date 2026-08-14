from models import create_article


def test_index_lists_articles(client, db_path):
    create_article("One", "one", "x", "e", ["a"], db_path=db_path)
    r = client.get("/")
    assert r.status_code == 200
    assert "One" in r.get_data(as_text=True)


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