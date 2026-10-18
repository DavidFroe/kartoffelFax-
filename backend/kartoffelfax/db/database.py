"""SQLite connection handling and schema bootstrap (async via aiosqlite)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import resources
from typing import AsyncIterator

import aiosqlite

from kartoffelfax.config import settings

_SCHEMA_VERSION = "0001_initial"


async def init_db() -> None:
    settings.ensure_directories()
    db_path = settings.resolved_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = resources.files("kartoffelfax.db").joinpath("schema.sql").read_text(encoding="utf-8")

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(schema_sql)
        await db.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            (_SCHEMA_VERSION,),
        )
        await db.commit()


@asynccontextmanager
async def get_connection() -> AsyncIterator[aiosqlite.Connection]:
    db_path = settings.resolved_database_path()
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
    finally:
        await db.close()
