"""SQL access for `fritzbox_connections`; credentials are encrypted before storage."""
from __future__ import annotations

from typing import Any

from kartoffelfax.core.security import decrypt, encrypt
from kartoffelfax.db.database import get_connection

_PUBLIC_COLUMNS = (
    "id, name, host, tr064_port, tr064_username, sip_username, sip_port, transport, "
    "is_default, requires_vpn, vpn_interface, created_at, updated_at, "
    "tr064_password_enc IS NOT NULL AS has_tr064_password, "
    "sip_password_enc IS NOT NULL AS has_sip_password"
)


def _public(row: Any) -> dict[str, Any]:
    data = dict(row)
    for key in ("is_default", "requires_vpn", "has_tr064_password", "has_sip_password"):
        data[key] = bool(data[key])
    return data


async def list_connections() -> list[dict[str, Any]]:
    async with get_connection() as db:
        cursor = await db.execute(f"SELECT {_PUBLIC_COLUMNS} FROM fritzbox_connections ORDER BY id")
        return [_public(row) for row in await cursor.fetchall()]


async def get_connection_public(connection_id: int) -> dict[str, Any] | None:
    async with get_connection() as db:
        cursor = await db.execute(
            f"SELECT {_PUBLIC_COLUMNS} FROM fritzbox_connections WHERE id = ?", (connection_id,)
        )
        row = await cursor.fetchone()
        return _public(row) if row else None


async def get_tr064_password(connection_id: int) -> str | None:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT tr064_password_enc FROM fritzbox_connections WHERE id = ?", (connection_id,)
        )
        row = await cursor.fetchone()
    if row is None or row["tr064_password_enc"] is None:
        return None
    return decrypt(row["tr064_password_enc"])


async def create_connection(data: dict[str, Any]) -> dict[str, Any]:
    tr064_password = data.get("tr064_password")
    sip_password = data.get("sip_password")
    async with get_connection() as db:
        cursor = await db.execute(
            "INSERT INTO fritzbox_connections (name, host, tr064_port, tr064_username, "
            "tr064_password_enc, sip_username, sip_password_enc, sip_port, transport, "
            "requires_vpn, vpn_interface) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data["name"],
                data["host"],
                data["tr064_port"],
                data.get("tr064_username"),
                encrypt(tr064_password) if tr064_password else None,
                data.get("sip_username"),
                encrypt(sip_password) if sip_password else None,
                data["sip_port"],
                data["transport"],
                int(data["requires_vpn"]),
                data.get("vpn_interface"),
            ),
        )
        await db.commit()
        connection_id = cursor.lastrowid
    created = await get_connection_public(connection_id)  # type: ignore[arg-type]
    assert created is not None
    return created
