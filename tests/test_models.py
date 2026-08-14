import pytest
from models import (
    create_article, get_article, update_article, delete_article,
    list_articles, count_articles, search_articles, list_tags,
    get_tags_for_article, get_articles_by_tag, count_articles_by_tag,
    create_user, get_user_by_username,
)


@pytest.fixture
def db_path(app):
    from database import init_schema
    init_schema(app.config["DATABASE"])
    return app.config["DATABASE"]


def test_user(db_path):
    uid = create_user("tester", "hash123", db_path=db_path)
    row = get_user_by_username("tester", db_path=db_path)
    assert row["id"] == uid
    assert row["password_hash"] == "hash123"


def test_article_roundtrip(db_path):
    aid = create_article("Hello", "hello-world", "**body**", "e", ["intro", "guide"],
                         db_path=db_path)
    row = get_article(aid, db_path=db_path)
    assert row["title"] == "Hello"
    assert row["slug"] == "hello-world"


def test_update_and_delete(db_path):
    aid = create_article("Keep", "keep", "x", "e", [], db_path=db_path)
    update_article(aid, "Changed", "changed", "y", "e", ["a"], db_path=db_path)
    assert get_article(aid, db_path=db_path)["title"] == "Changed"
    delete_article(aid, db_path=db_path)
    assert get_article(aid, db_path=db_path) is None


def test_list_and_count(db_path):
    create_article("One", "one", "x", "e", [], db_path=db_path)
    create_article("Two", "two", "x", "e", [], db_path=db_path)
    assert count_articles(db_path=db_path) == 2
    assert len(list_articles(1, 0, db_path=db_path)) == 1


def test_search_finds_title(db_path):
    aid = create_article("About Python", "py", "talk about python", "e", ["p"],
                         db_path=db_path)
    rows = search_articles("python", 10, 0, db_path=db_path)
    assert any(r["id"] == aid for r in rows)


def test_tags_roundtrip_and_filter(db_path):
    aid = create_article("Tag It", "tag", "body", "e", ["python", "web"],
                         db_path=db_path)
    assert set(get_tags_for_article(aid, db_path=db_path)) == {"python", "web"}
    names = {t["name"] for t in list_tags(db_path=db_path)}
    assert {"python", "web"} <= names
    found = get_articles_by_tag("python", 10, 0, db_path=db_path)
    assert any(a["id"] == aid for a in found)
    assert count_articles_by_tag("python", db_path=db_path) >= 1