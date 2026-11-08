"""Endpoints for app settings and Fritz!Box connection profiles (TR-064/SIP/VPN)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kartoffelfax.core.fritzbox.tr064_client import (
    TR064Client,
    TR064ConnectionError,
    TR064Credentials,
    TR064Error,
)
from kartoffelfax.db.repositories import connection_repository as repo

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
    transport: Literal["sip_t38", "sip_g711", "capi_tcp"] = "sip_t38"
    requires_vpn: bool = False
    vpn_interface: str | None = None


def _vpn_interface_up(interface: str) -> bool | None:
    """Linux-only check via sysfs; None where the state cannot be determined."""
    if not sys.platform.startswith("linux"):
        return None
    return (Path("/sys/class/net") / Path(interface).name).exists()


@router.get("/connections")
async def list_connections() -> list[dict[str, Any]]:
    return await repo.list_connections()


@router.post("/connections", status_code=201)
async def create_connection(payload: FritzboxConnectionIn) -> dict[str, Any]:
    return await repo.create_connection(payload.model_dump())


@router.post("/connections/{connection_id}/test")
async def test_connection(connection_id: int) -> dict[str, Any]:
    """Probes TR-064 reachability and, if requires_vpn, the WireGuard interface state."""
    conn = await repo.get_connection_public(connection_id)
    if conn is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    client = TR064Client(
        TR064Credentials(
            host=conn["host"],
            port=conn["tr064_port"],
            username=conn["tr064_username"],
            password=await repo.get_tr064_password(connection_id),
        )
    )
    result: dict[str, Any] = {"reachable": await client.is_reachable(), "device_info": None, "error": None}

    if conn["requires_vpn"] and conn["vpn_interface"]:
        result["vpn_interface_up"] = _vpn_interface_up(conn["vpn_interface"])

    if result["reachable"]:
        try:
            result["device_info"] = await client.get_device_info()
        except (TR064Error, TR064ConnectionError) as exc:
            result["error"] = str(exc)
    return result
