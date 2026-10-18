"""Smoke test: schema.sql applies cleanly and expected tables exist."""
from __future__ import annotations

import sqlite3
from importlib import resources


def test_schema_applies_cleanly() -> None:
    schema_sql = resources.files("kartoffelfax.db").joinpath("schema.sql").read_text(encoding="utf-8")

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()

    expected = {
        "contacts",
        "fritzbox_connections",
        "fax_messages",
        "fax_source_files",
        "fax_events",
        "import_jobs",
        "settings",
        "schema_migrations",
    }
    assert expected.issubset(tables)
