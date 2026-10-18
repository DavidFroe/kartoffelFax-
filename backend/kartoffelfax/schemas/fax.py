"""Pydantic models for fax messages, mirroring the `fax_messages` table."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class FaxDirection(StrEnum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class FaxFolder(StrEnum):
    INBOX = "inbox"
    OUTBOX = "outbox"
    DRAFTS = "drafts"
    ARCHIVE = "archive"
    TRASH = "trash"


class FaxStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    DIALING = "dialing"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class FaxMessageBase(BaseModel):
    fax_number: str
    subject: str | None = None
    contact_id: int | None = None


class FaxMessageCreate(FaxMessageBase):
    """Payload to create a new outgoing fax (draft or immediate send)."""

    source_file_paths: list[str] = []


class FaxMessage(FaxMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: FaxDirection
    folder: FaxFolder
    status: FaxStatus
    pdf_path: str | None = None
    thumbnail_path: str | None = None
    page_count: int | None = None
    duration_seconds: int | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime
    queued_at: datetime | None = None
    sent_at: datetime | None = None
    received_at: datetime | None = None
