from __future__ import annotations

import sqlite3
from pathlib import Path

import httpx


async def _upload(client: httpx.AsyncClient, name: str = "brief.pdf", data: bytes = b"%PDF-1.4 test") -> dict:
    resp = await client.post("/api/fax/upload", files={"file": (name, data, "application/pdf")})
    assert resp.status_code == 201
    return resp.json()


async def test_upload_stores_file_under_uploads(client: httpx.AsyncClient, tmp_path: Path) -> None:
    body = await _upload(client, data=b"hello")
    assert body["stored_path"].startswith("uploads/")
    assert body["mime_type"] == "application/pdf"
    assert (tmp_path / body["stored_path"]).read_bytes() == b"hello"


async def test_upload_sanitises_filename(client: httpx.AsyncClient, tmp_path: Path) -> None:
    body = await _upload(client, name="../../evil name.pdf")
    assert (tmp_path / body["stored_path"]).resolve().parent == (tmp_path / "uploads").resolve()
    assert "/" not in body["original_name"]


async def test_send_queues_in_outbox_with_sources(client: httpx.AsyncClient, tmp_path: Path) -> None:
    upload = await _upload(client)
    resp = await client.post(
        "/api/fax/send",
        json={"fax_number": "+49301234567", "subject": "Test", "source_file_paths": [upload["stored_path"]]},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "queued"
    assert body["folder"] == "outbox"
    assert body["direction"] == "outgoing"
    assert body["queued_at"] is not None

    conn = sqlite3.connect(tmp_path / "test.db")
    try:
        rows = conn.execute(
            "SELECT original_name, stored_path, mime_type FROM fax_source_files WHERE fax_message_id = ?",
            (body["id"],),
        ).fetchall()
    finally:
        conn.close()
    assert rows == [("brief.pdf", upload["stored_path"], "application/pdf")]


async def test_send_rejects_unknown_or_escaping_paths(client: httpx.AsyncClient) -> None:
    for bad in ("uploads/missing.pdf", "../outside.pdf"):
        resp = await client.post("/api/fax/send", json={"fax_number": "1", "source_file_paths": [bad]})
        assert resp.status_code == 400


async def test_send_rejects_unknown_contact(client: httpx.AsyncClient) -> None:
    resp = await client.post("/api/fax/send", json={"fax_number": "1", "contact_id": 42})
    assert resp.status_code == 400


async def test_list_get_delete(client: httpx.AsyncClient) -> None:
    first = (await client.post("/api/fax/send", json={"fax_number": "111"})).json()
    second = (await client.post("/api/fax/send", json={"fax_number": "222"})).json()

    outbox = (await client.get("/api/fax/outbox")).json()
    assert {m["id"] for m in outbox} == {first["id"], second["id"]}
    assert (await client.get("/api/fax/inbox")).json() == []

    got = await client.get(f"/api/fax/message/{first['id']}")
    assert got.status_code == 200
    assert got.json()["fax_number"] == "111"

    assert (await client.delete(f"/api/fax/message/{first['id']}")).status_code == 204
    assert (await client.get(f"/api/fax/message/{first['id']}")).status_code == 404


async def test_missing_message_returns_404(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/fax/message/999")).status_code == 404
    assert (await client.delete("/api/fax/message/999")).status_code == 404
