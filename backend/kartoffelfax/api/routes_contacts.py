"""REST endpoints for the contact/phonebook, plus legacy .srl import."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from kartoffelfax.db.repositories import contact_repository as repo
from kartoffelfax.schemas.contact import Contact, ContactCreate, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=list[Contact])
async def list_contacts(query: str | None = None) -> list[Contact]:
    return [Contact.model_validate(row) for row in await repo.list_contacts(query)]


@router.post("", response_model=Contact, status_code=201)
async def create_contact(payload: ContactCreate) -> Contact:
    return Contact.model_validate(await repo.create_contact(payload.model_dump()))


@router.patch("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: int, payload: ContactUpdate) -> Contact:
    row = await repo.update_contact(contact_id, payload.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact.model_validate(row)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: int) -> None:
    if not await repo.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")


@router.post("/import/srl", status_code=202)
async def import_srl_phonebook(file: UploadFile) -> dict[str, int]:
    """Import an AVM Fritz!fax .srl phonebook export, returns an import_jobs id."""
    raise NotImplementedError
