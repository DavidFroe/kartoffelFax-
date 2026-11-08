"""REST endpoints for fax messages (inbox/outbox/drafts/archive)."""
from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from kartoffelfax.config import settings
from kartoffelfax.db.repositories import fax_repository as repo
from kartoffelfax.schemas.fax import FaxFolder, FaxMessage, FaxMessageCreate

router = APIRouter(prefix="/api/fax", tags=["fax"])

_UUID_PREFIX = re.compile(r"^[0-9a-f]{32}_")


def _resolve_upload(stored_path: str) -> Path:
    uploads = (settings.data_dir / settings.uploads_dir).resolve()
    candidate = (settings.data_dir / stored_path).resolve()
    if not candidate.is_relative_to(uploads) or not candidate.is_file():
        raise HTTPException(status_code=400, detail=f"Unknown uploaded file: {stored_path}")
    return candidate


@router.get("/{folder}", response_model=list[FaxMessage])
async def list_fax_messages(folder: FaxFolder) -> list[FaxMessage]:
    """List all fax messages in a given folder (inbox/outbox/drafts/archive/trash)."""
    return [FaxMessage.model_validate(row) for row in await repo.list_by_folder(folder.value)]


@router.get("/message/{fax_id}", response_model=FaxMessage)
async def get_fax_message(fax_id: int) -> FaxMessage:
    row = await repo.get_message(fax_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Fax message not found")
    return FaxMessage.model_validate(row)


@router.get("/message/{fax_id}/events")
async def get_fax_events(fax_id: int) -> list[dict[str, Any]]:
    if await repo.get_message(fax_id) is None:
        raise HTTPException(status_code=404, detail="Fax message not found")
    return await repo.list_events(fax_id)


@router.get("/message/{fax_id}/pdf")
async def get_fax_pdf(fax_id: int) -> FileResponse:
    row = await repo.get_message(fax_id)
    if row is None or not row["pdf_path"]:
        raise HTTPException(status_code=404, detail="No PDF available")
    data_dir = settings.data_dir.resolve()
    path = (data_dir / row["pdf_path"]).resolve()
    if not path.is_relative_to(data_dir) or not path.is_file():
        raise HTTPException(status_code=404, detail="No PDF available")
    return FileResponse(path, media_type="application/pdf")


@router.post("/send", response_model=FaxMessage, status_code=201)
async def send_fax(payload: FaxMessageCreate) -> FaxMessage:
    """Queue a fax in the outbox. Actual transmission is not wired up yet."""
    if payload.contact_id is not None and not await repo.contact_exists(payload.contact_id):
        raise HTTPException(status_code=400, detail="Unknown contact_id")

    sources: list[dict[str, str | None]] = []
    for stored_path in payload.source_file_paths:
        resolved = _resolve_upload(stored_path)
        sources.append(
            {
                "original_name": _UUID_PREFIX.sub("", resolved.name),
                "stored_path": stored_path,
                "mime_type": mimetypes.guess_type(resolved.name)[0],
            }
        )

    row = await repo.create_queued_outgoing(
        payload.fax_number, payload.subject, payload.contact_id, sources
    )
    return FaxMessage.model_validate(row)


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile) -> dict[str, str]:
    """Drag & drop upload target; returns a stored_path to attach to a FaxMessageCreate."""
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename or "upload").name) or "upload"
    uploads = settings.data_dir / settings.uploads_dir
    uploads.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    (uploads / stored_name).write_bytes(await file.read())
    return {
        "stored_path": f"{settings.uploads_dir}/{stored_name}",
        "original_name": safe_name,
        "mime_type": file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
    }


@router.delete("/message/{fax_id}", status_code=204)
async def delete_fax_message(fax_id: int) -> None:
    if not await repo.delete_message(fax_id):
        raise HTTPException(status_code=404, detail="Fax message not found")
