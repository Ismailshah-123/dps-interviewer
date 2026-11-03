ADMIN = {"email": "admin@dps.example.com", "password": "TestPassword123!"}


async def test_refresh_cookie_is_httponly_and_rotates(client):
    r = await client.post("/api/v1/auth/login", json=ADMIN)
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "dps_refresh=" in cookie and "httponly" in cookie and "samesite=strict" in cookie and "path=/api/v1/auth" in cookie
    first = client.cookies.get("dps_refresh")

    # Cookie alone (no body) is enough to refresh, and the token rotates.
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 200, r.text
    second = client.cookies.get("dps_refresh")
    assert second and second != first

    # Replaying the old refresh token is rejected.
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert r.status_code == 401


async def test_logout_revokes_refresh_session(client):
    r = await client.post("/api/v1/auth/login", json=ADMIN)
    token = r.json()["refresh_token"]
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert r.status_code == 401


async def test_refresh_without_any_token_is_rejected(client):
    client.cookies.clear()
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 401
