"""Pydantic models for contacts, mirroring the `contacts` table."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    display_name: str
    company: str | None = None
    fax_number: str | None = None
    phone_number: str | None = None
    email: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str = "DE"
    notes: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    display_name: str | None = None  # all fields optional on update


class Contact(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    legacy_srl_id: str | None = None
    created_at: datetime
    updated_at: datetime
