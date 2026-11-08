from __future__ import annotations

import httpx


async def _create(client: httpx.AsyncClient, name: str, fax: str | None = None) -> dict:
    resp = await client.post("/api/contacts", json={"display_name": name, "fax_number": fax})
    assert resp.status_code == 201
    return resp.json()


async def test_create_and_get_in_list(client: httpx.AsyncClient) -> None:
    created = await _create(client, "Praxis Dr. Meier", "+49301234567")
    assert created["id"] > 0
    assert created["country"] == "DE"

    listed = (await client.get("/api/contacts")).json()
    assert [c["display_name"] for c in listed] == ["Praxis Dr. Meier"]


async def test_list_query_filters_name_and_fax(client: httpx.AsyncClient) -> None:
    await _create(client, "Alpha GmbH", "111")
    await _create(client, "Beta AG", "222")

    by_name = (await client.get("/api/contacts", params={"query": "alph"})).json()
    assert [c["display_name"] for c in by_name] == ["Alpha GmbH"]

    by_fax = (await client.get("/api/contacts", params={"query": "222"})).json()
    assert [c["display_name"] for c in by_fax] == ["Beta AG"]

    assert len((await client.get("/api/contacts")).json()) == 2


async def test_update_changes_only_given_fields(client: httpx.AsyncClient) -> None:
    created = await _create(client, "Alt", "123")
    resp = await client.patch(f"/api/contacts/{created['id']}", json={"display_name": "Neu"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == "Neu"
    assert body["fax_number"] == "123"
    assert body["country"] == "DE"


async def test_delete_removes_contact(client: httpx.AsyncClient) -> None:
    created = await _create(client, "Weg")
    assert (await client.delete(f"/api/contacts/{created['id']}")).status_code == 204
    assert (await client.get("/api/contacts")).json() == []


async def test_missing_contact_returns_404(client: httpx.AsyncClient) -> None:
    assert (await client.patch("/api/contacts/999", json={"display_name": "x"})).status_code == 404
    assert (await client.delete("/api/contacts/999")).status_code == 404
