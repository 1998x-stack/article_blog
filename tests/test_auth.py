def test_admin_route_redirects_to_login(client):
    r = client.get("/admin")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_bad_login_fails(client):
    client.get("/login")
    with client.session_transaction() as s:
        token = s.get("_csrf_token")
    r = client.post("/login", data={"username": "admin", "password": "wrong",
                                    "_csrf_token": token})
    assert r.status_code == 200
    assert "Invalid" in r.get_data(as_text=True)


def test_login_then_access_admin(app, client):
    client.get("/login")
    with client.session_transaction() as s:
        token = s.get("_csrf_token")
    r = client.post("/login", data={"username": app.config["ADMIN_USERNAME"],
                                    "password": app.config["ADMIN_PASSWORD"],
                                    "_csrf_token": token})
    assert r.status_code == 302
    r2 = client.get("/admin")
    assert r2.status_code == 200