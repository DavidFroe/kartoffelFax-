"""Imports historical AVM Fritz!fax message databases (export .db/.mdb dumps)
into the `fax_messages` / `contacts` tables, tagging rows via `legacy_import_id`
/ `legacy_srl_id` so re-running an import is idempotent.
"""
from __future__ import annotations

from pathlib import Path


async def import_legacy_database(source_path: Path, import_job_id: int) -> None:
    """Reads the legacy export and upserts contacts/fax_messages.

    Expected to dispatch on file extension/content to the correct reader
    (e.g. pyodbc/mdbtools for .mdb, sqlite3 for already-converted .db dumps).
    """
    raise NotImplementedError
