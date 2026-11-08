from __future__ import annotations

import sqlite3
from pathlib import Path

import httpx
import pytest
from kartoffelfax.api import routes_settings
from kartoffelfax.core import security
from kartoffelfax.core.fritzbox.tr064_client import TR064Client

from .test_tr064_client import DIGEST_CHALLENGE, GET_INFO_RESPONSE

PAYLOAD = {
    "name": "Zuhause",
    "host": "192.168.178.1",
    "tr064_username": "faxuser",
    "tr064_password": "tr064-Geheim-123",
    "sip_username": "620",
    "sip_password": "sip-Geheim-456",
}


def _mock_fritzbox(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    def factory(creds):
        return TR064Client(creds, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(routes_settings, "TR064Client", factory)


async def test_create_and_list_never_return_passwords(client: httpx.AsyncClient) -> None:
    created = (await client.post("/api/settings/connections", json=PAYLOAD)).json()
    listed = (await client.get("/api/settings/connections")).json()

    for body in (created, listed[0]):
        assert "tr064_password" not in body and "tr064_password_enc" not in body
        assert "sip_password" not in body and "sip_password_enc" not in body
        assert "Geheim" not in str(body)
        assert body["has_tr064_password"] is True
        assert body["has_sip_password"] is True
        assert body["tr064_username"] == "faxuser"


async def test_passwords_are_encrypted_at_rest(client: httpx.AsyncClient, tmp_path: Path) -> None:
    await client.post("/api/settings/connections", json=PAYLOAD)

    conn = sqlite3.connect(tmp_path / "test.db")
    try:
        tr064_enc, sip_enc = conn.execute(
            "SELECT tr064_password_enc, sip_password_enc FROM fritzbox_connections"
        ).fetchone()
    finally:
        conn.close()

    assert "tr064-Geheim-123" not in tr064_enc
    assert "sip-Geheim-456" not in sip_enc
    assert security.decrypt(tr064_enc) == "tr064-Geheim-123"
    assert security.decrypt(sip_enc) == "sip-Geheim-456"
    assert (tmp_path / "secret.key").stat().st_mode & 0o777 == 0o600


async def test_invalid_transport_rejected(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/settings/connections", json={**PAYLOAD, "transport": "carrier-pigeon"})
    assert resp.status_code == 422


async def test_connection_test_returns_device_info(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tr64desc.xml":
            return httpx.Response(200, text="<root/>")
        if "authorization" not in request.headers:
            return httpx.Response(401, headers={"WWW-Authenticate": DIGEST_CHALLENGE})
        return httpx.Response(200, text=GET_INFO_RESPONSE)

    _mock_fritzbox(monkeypatch, handler)
    conn_id = (await client.post("/api/settings/connections", json=PAYLOAD)).json()["id"]

    result = (await client.post(f"/api/settings/connections/{conn_id}/test")).json()

    assert result["reachable"] is True
    assert result["device_info"]["NewModelName"] == "FRITZ!Box 7590"
    assert result["error"] is None


async def test_connection_test_reports_unreachable_box(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    _mock_fritzbox(monkeypatch, handler)
    conn_id = (await client.post("/api/settings/connections", json=PAYLOAD)).json()["id"]

    result = (await client.post(f"/api/settings/connections/{conn_id}/test")).json()

    assert result["reachable"] is False
    assert result["device_info"] is None


async def test_connection_test_unknown_id_is_404(client: httpx.AsyncClient) -> None:
    assert (await client.post("/api/settings/connections/999/test")).status_code == 404
