from app import create_app


def test_app_factory_creates_app():
    app = create_app({"TESTING": True})
    assert app is not None
    assert app.config["SECRET_KEY"]


def test_root_responds(client):
    assert client.get("/").status_code == 200