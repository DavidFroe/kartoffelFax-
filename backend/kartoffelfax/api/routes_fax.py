"""REST endpoints for fax messages (inbox/outbox/drafts/archive)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from kartoffelfax.schemas.fax import FaxFolder, FaxMessage, FaxMessageCreate

router = APIRouter(prefix="/api/fax", tags=["fax"])


@router.get("/{folder}", response_model=list[FaxMessage])
async def list_fax_messages(folder: FaxFolder) -> list[FaxMessage]:
    """List all fax messages in a given folder (inbox/outbox/drafts/archive/trash)."""
    raise NotImplementedError


@router.get("/message/{fax_id}", response_model=FaxMessage)
async def get_fax_message(fax_id: int) -> FaxMessage:
    raise NotImplementedError


@router.post("/send", response_model=FaxMessage, status_code=201)
async def send_fax(payload: FaxMessageCreate) -> FaxMessage:
    """Queue a fax for sending. Documents are merged to PDF, then dialed via SIP/T.38."""
    raise NotImplementedError


@router.post("/upload", status_code=201)
async def upload_document(file: UploadFile) -> dict[str, str]:
    """Drag & drop upload target; returns a stored_path to attach to a FaxMessageCreate."""
    raise NotImplementedError


@router.delete("/message/{fax_id}", status_code=204)
async def delete_fax_message(fax_id: int) -> None:
    raise NotImplementedError
