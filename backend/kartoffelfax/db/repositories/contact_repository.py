"""SQL access for the `contacts` table."""
from __future__ import annotations

from typing import Any

from kartoffelfax.db.database import get_connection

_UPDATABLE = {
    "display_name", "company", "fax_number", "phone_number", "email",
    "street", "postal_code", "city", "country", "notes",
}  # fmt: skip


async def list_contacts(query: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM contacts"
    params: tuple[str, ...] = ()
    if query:
        like = f"%{query}%"
        sql += " WHERE display_name LIKE ? OR fax_number LIKE ?"
        params = (like, like)
    sql += " ORDER BY display_name COLLATE NOCASE, id"
    async with get_connection() as db:
        cursor = await db.execute(sql, params)
        return [dict(row) for row in await cursor.fetchall()]


async def get_contact(contact_id: int) -> dict[str, Any] | None:
    async with get_connection() as db:
        cursor = await db.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_contact(data: dict[str, Any]) -> dict[str, Any]:
    columns = [c for c in data if c in _UPDATABLE]
    placeholders = ", ".join("?" for _ in columns)
    async with get_connection() as db:
        cursor = await db.execute(
            f"INSERT INTO contacts ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(data[c] for c in columns),
        )
        await db.commit()
        contact_id = cursor.lastrowid
    created = await get_contact(contact_id)  # type: ignore[arg-type]
    assert created is not None
    return created


async def update_contact(contact_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    columns = [c for c in data if c in _UPDATABLE]
    if columns:
        assignments = ", ".join(f"{c} = ?" for c in columns)
        async with get_connection() as db:
            cursor = await db.execute(
                f"UPDATE contacts SET {assignments}, "
                "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = ?",
                (*(data[c] for c in columns), contact_id),
            )
            await db.commit()
            if cursor.rowcount == 0:
                return None
    return await get_contact(contact_id)


async def delete_contact(contact_id: int) -> bool:
    async with get_connection() as db:
        cursor = await db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        await db.commit()
        return cursor.rowcount > 0
