"""SQL access for `fax_messages`, `fax_source_files` and `fax_events`."""
from __future__ import annotations

from typing import Any

from kartoffelfax.db.database import get_connection


async def list_by_folder(folder: str) -> list[dict[str, Any]]:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM fax_messages WHERE folder = ? ORDER BY created_at DESC, id DESC",
            (folder,),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_message(fax_id: int) -> dict[str, Any] | None:
    async with get_connection() as db:
        cursor = await db.execute("SELECT * FROM fax_messages WHERE id = ?", (fax_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_queued_outgoing(
    fax_number: str,
    subject: str | None,
    contact_id: int | None,
    sources: list[dict[str, str | None]],
) -> dict[str, Any]:
    """Insert an outgoing fax as queued/outbox together with its source files."""
    async with get_connection() as db:
        cursor = await db.execute(
            "INSERT INTO fax_messages "
            "(direction, folder, status, contact_id, fax_number, subject, queued_at) "
            "VALUES ('outgoing', 'outbox', 'queued', ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
            (contact_id, fax_number, subject),
        )
        fax_id = cursor.lastrowid
        for order, source in enumerate(sources):
            await db.execute(
                "INSERT INTO fax_source_files "
                "(fax_message_id, original_name, stored_path, mime_type, sort_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (fax_id, source["original_name"], source["stored_path"], source["mime_type"], order),
            )
        await db.execute(
            "INSERT INTO fax_events (fax_message_id, event_type) VALUES (?, 'queued')", (fax_id,)
        )
        await db.commit()
    created = await get_message(fax_id)  # type: ignore[arg-type]
    assert created is not None
    return created


async def list_source_files(fax_id: int) -> list[dict[str, Any]]:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM fax_source_files WHERE fax_message_id = ? ORDER BY sort_order", (fax_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def contact_exists(contact_id: int) -> bool:
    async with get_connection() as db:
        cursor = await db.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
        return await cursor.fetchone() is not None


async def delete_message(fax_id: int) -> bool:
    async with get_connection() as db:
        cursor = await db.execute("DELETE FROM fax_messages WHERE id = ?", (fax_id,))
        await db.commit()
        return cursor.rowcount > 0


async def list_events(fax_id: int) -> list[dict[str, Any]]:
    async with get_connection() as db:
        cursor = await db.execute(
            "SELECT id, event_type, detail, created_at FROM fax_events "
            "WHERE fax_message_id = ? ORDER BY id",
            (fax_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]
