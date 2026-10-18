"""TR-064 SOAP client for Fritz!Box: device info, call monitoring, WAN/VPN status.

Works over a plain LAN connection or a WireGuard tunnel transparently, since it
only needs an IP/port reachable from this host (VPN-side Fritz!Box IP, e.g.
192.168.178.1 over wg0, or the LAN IP directly).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class TR064Credentials:
    host: str
    port: int = 49000
    username: str | None = None
    password: str | None = None


class TR064ConnectionError(RuntimeError):
    """Raised when the Fritz!Box is unreachable (e.g. VPN tunnel down)."""


class TR064Client:
    """Minimal async TR-064 client, built on top of httpx + SOAP envelopes."""

    def __init__(self, credentials: TR064Credentials, timeout: float = 5.0) -> None:
        self._creds = credentials
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return f"http://{self._creds.host}:{self._creds.port}"

    async def is_reachable(self) -> bool:
        """Quick reachability probe, used by /api/settings/connections/{id}/test."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.base_url}/tr64desc.xml")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError):
            return False

    async def get_device_info(self) -> dict[str, str]:
        """Calls GetInfo on urn:dslforum-org:service:DeviceInfo:1."""
        raise NotImplementedError("TODO: build SOAP envelope + auth digest, parse response")
