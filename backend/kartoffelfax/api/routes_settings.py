"""Endpoints for app settings and Fritz!Box connection profiles (TR-064/SIP/VPN)."""
from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter(prefix="/api/settings", tags=["settings"])


class FritzboxConnectionIn(BaseModel):
    name: str
    host: str
    tr064_port: int = 49000
    tr064_username: str | None = None
    tr064_password: str | None = None  # encrypted before storage, never returned as-is
    sip_username: str | None = None
    sip_password: str | None = None
    sip_port: int = 5060
    transport: str = "sip_t38"
    requires_vpn: bool = False
    vpn_interface: str | None = None


@router.get("/connections")
async def list_connections() -> list[dict]:
    raise NotImplementedError


@router.post("/connections", status_code=201)
async def create_connection(payload: FritzboxConnectionIn) -> dict:
    raise NotImplementedError


@router.post("/connections/{connection_id}/test")
async def test_connection(connection_id: int) -> dict:
    """Probes TR-064 reachability and, if requires_vpn, the WireGuard interface state."""
    raise NotImplementedError
