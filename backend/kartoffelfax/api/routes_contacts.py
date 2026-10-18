"""REST endpoints for the contact/phonebook, plus legacy .srl import."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile

from kartoffelfax.schemas.contact import Contact, ContactCreate, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
async def list_contacts(query: str | None = None) -> list[Contact]:
    raise NotImplementedError


@router.post("", response_model=Contact, status_code=201)
async def create_contact(payload: ContactCreate) -> Contact:
    raise NotImplementedError


@router.patch("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: int, payload: ContactUpdate) -> Contact:
    raise NotImplementedError


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: int) -> None:
    raise NotImplementedError


@router.post("/import/srl", status_code=202)
async def import_srl_phonebook(file: UploadFile) -> dict[str, int]:
    """Import an AVM Fritz!fax .srl phonebook export, returns an import_jobs id."""
    raise NotImplementedError
