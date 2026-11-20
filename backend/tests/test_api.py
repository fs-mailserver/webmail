import httpx

from app.core.crypto import decrypt_mailbox_password
from app.models import Account, User
from tests.conftest import TEST_PASSWORD, FakeSession, auth_headers, make_user


async def test_login_success_and_me(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    fake_session.put(make_user("alice@example.com"))
    response = await client.post("/api/v1/auth/login", json={"email": " Alice@Example.com ", "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer" and body["expires_in"] > 0

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"
    assert "hashed_password" not in me.json()


async def test_login_failures_are_indistinguishable(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    fake_session.put(make_user("bob@example.com"))
    fake_session.put(make_user("off@example.com", is_active=False))
    attempts = [
        {"email": "bob@example.com", "password": "wrong"},
        {"email": "ghost@example.com", "password": TEST_PASSWORD},
        {"email": "off@example.com", "password": TEST_PASSWORD},
    ]
    for payload in attempts:
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password."}


async def test_me_requires_valid_token(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    bad = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401
    assert bad.headers["www-authenticate"] == "Bearer"


async def test_deactivated_user_token_rejected(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    user = fake_session.put(make_user())
    headers = auth_headers(user)
    user.is_active = False
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


async def test_change_password(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    user = fake_session.put(make_user())
    headers = auth_headers(user)
    wrong = await client.post(
        "/api/v1/auth/change-password", headers=headers, json={"current_password": "nope", "new_password": "new-password-123"}
    )
    assert wrong.status_code == 400
    ok = await client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": TEST_PASSWORD, "new_password": "new-password-123"},
    )
    assert ok.status_code == 204
    login = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "new-password-123"})
    assert login.status_code == 200


async def test_users_endpoints_are_admin_only(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    user = fake_session.put(make_user())
    admin = fake_session.put(make_user("admin@example.com", role="admin"))
    assert (await client.get("/api/v1/users", headers=auth_headers(user))).status_code == 403

    created = await client.post(
        "/api/v1/users",
        headers=auth_headers(admin),
        json={"email": "New@Example.com", "password": "a-strong-password", "role": "user"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["email"] == "new@example.com"

    weak = await client.post("/api/v1/users", headers=auth_headers(admin), json={"email": "x@example.com", "password": "short"})
    assert weak.status_code == 422

    self_demote = await client.patch(f"/api/v1/users/{admin.id}", headers=auth_headers(admin), json={"role": "user"})
    assert self_demote.status_code == 400


async def test_account_create_encrypts_password_and_hides_it(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    admin = fake_session.put(make_user("admin@example.com", role="admin"))
    owner = fake_session.put(make_user("owner@example.com"))
    response = await client.post(
        "/api/v1/accounts",
        headers=auth_headers(admin),
        json={"email": "Info@example.com", "password": "imap-secret", "user_id": str(owner.id), "color_code": "#22c55e"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "info@example.com"
    assert body["user_id"] == str(owner.id)
    assert "password" not in body and "encrypted_password" not in body
    assert "imap-secret" not in response.text

    stored = next(obj for (kind, _), obj in fake_session.objects.items() if kind is Account)
    assert stored.encrypted_password.startswith("fernet:v1:")
    assert decrypt_mailbox_password(stored.encrypted_password) == "imap-secret"


async def test_account_isolation_between_users(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    alice = fake_session.put(make_user("alice@example.com"))
    mallory = fake_session.put(make_user("mallory@example.com"))
    account = Account(
        user_id=alice.id,
        email="alice@example.com",
        color_code="#3b82f6",
        imap_host="mailserver",
        imap_port=993,
        imap_use_ssl=True,
        smtp_host="mailserver",
        smtp_port=587,
        smtp_use_tls=True,
        encrypted_password="fernet:v1:x",
    )
    fake_session.add(account)

    own = await client.get("/api/v1/accounts", headers=auth_headers(alice))
    assert [a["email"] for a in own.json()] == ["alice@example.com"]
    assert (await client.get("/api/v1/accounts", headers=auth_headers(mallory))).json() == []
    assert (await client.get(f"/api/v1/accounts/{account.id}", headers=auth_headers(mallory))).status_code == 404

    cosmetic = await client.patch(f"/api/v1/accounts/{account.id}", headers=auth_headers(alice), json={"color_code": "#f97316"})
    assert cosmetic.status_code == 200 and cosmetic.json()["color_code"] == "#f97316"
    forbidden = await client.patch(f"/api/v1/accounts/{account.id}", headers=auth_headers(alice), json={"imap_host": "evil.example"})
    assert forbidden.status_code == 403
    assert (await client.delete(f"/api/v1/accounts/{account.id}", headers=auth_headers(alice))).status_code == 403


async def test_account_validation(client: httpx.AsyncClient, fake_session: FakeSession) -> None:
    admin: User = fake_session.put(make_user("admin@example.com", role="admin"))
    bad = await client.post(
        "/api/v1/accounts",
        headers=auth_headers(admin),
        json={"email": "a@b.hr", "password": "x", "color_code": "green", "imap_port": 70000},
    )
    assert bad.status_code == 422
