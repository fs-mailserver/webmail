import subprocess
import sys
from pathlib import Path

import httpx

from app.main import app
from app.models import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {
    "users",
    "accounts",
    "account_signatures",
    "folders",
    "threads",
    "messages",
    "attachments",
    "sender_blocklist_rules",
    "blocklist_apply_logs",
    "device_registrations",
}


def test_openapi_schema_is_valid() -> None:
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    paths = schema["paths"]
    for path in ("/api/v1/auth/login", "/api/v1/auth/me", "/api/v1/accounts", "/api/v1/users", "/api/v1/health"):
        assert path in paths, path
    account_read = schema["components"]["schemas"]["AccountRead"]["properties"]
    assert "password" not in account_read and "encrypted_password" not in account_read


async def test_liveness(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


async def test_cors_preflight(client: httpx.AsyncClient) -> None:
    response = await client.options(
        "/api/v1/auth/login",
        headers={"Origin": "https://webmail.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") == "https://webmail.example.com"
    evil = await client.options(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in evil.headers


def test_metadata_contains_all_spec_tables() -> None:
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_migration_renders_offline_sql() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE {table} " in result.stdout, table
    assert "GENERATED ALWAYS AS" in result.stdout
    assert "USING gin" in result.stdout


def test_migration_matches_models() -> None:
    """Fails if a model changed without regenerating the migration."""
    rendered = subprocess.run(
        [sys.executable, "scripts/render_initial_migration.py"], cwd=BACKEND_DIR, capture_output=True, text=True, check=True
    ).stdout
    committed = (BACKEND_DIR / "alembic/versions/20261112_0001_initial.py").read_text()
    assert rendered.strip() == committed.strip(), "Models drifted from the initial migration — add a new Alembic revision."


async def test_readiness_is_bounded_and_reports_degraded(client: httpx.AsyncClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import anyio

    from app.api.v1 import health

    class HangingRedis:
        async def ping(self) -> None:
            await anyio.sleep(60)

    class BrokenEngine:
        def connect(self):  # type: ignore[no-untyped-def]
            raise OSError("db down")

    monkeypatch.setattr(health, "CHECK_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(health, "get_redis", lambda: HangingRedis())
    monkeypatch.setattr(health, "get_engine", lambda: BrokenEngine())
    with anyio.fail_after(5):
        response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "error", "redis": "error"}
