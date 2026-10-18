"""SIP/VoIP client acting as an IP-phone registered against the Fritz!Box,
used to place outgoing fax calls over T.38 (preferred) or G.711 fallback,
and to answer incoming fax calls for the inbox.

This intentionally avoids the legacy CAPI driver stack; the Fritz!Box exposes
a standard SIP registrar (Telefonie > Telefoniegeraete > Faxgeraet) that works
identically whether reached on the LAN or across a WireGuard tunnel.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FaxTransport(StrEnum):
    T38 = "sip_t38"
    G711 = "sip_g711"


@dataclass(slots=True)
class SIPCredentials:
    host: str
    port: int = 5060
    username: str = ""
    password: str = ""


class SIPFaxError(RuntimeError):
    """Raised on registration failure, call setup failure, or T.38 negotiation failure."""


class SIPFaxClient:
    """Wraps a SIP stack (e.g. pjsua2 or a custom asyncio SIP implementation).

    Lifecycle for sending: register() -> invite(fax_number) -> negotiate T.38 ->
    stream the TIFF/G3 fax data -> hangup(). Each step emits a status event that
    the API layer forwards over the /ws/status WebSocket.
    """

    def __init__(self, credentials: SIPCredentials, transport: FaxTransport = FaxTransport.T38) -> None:
        self._creds = credentials
        self._transport = transport

    async def register(self) -> None:
        raise NotImplementedError

    async def send_fax(self, fax_number: str, g3_path: str) -> None:
        """Dials out and transmits a G3/TIFF-encoded fax document."""
        raise NotImplementedError

    async def listen_for_incoming(self) -> None:
        """Runs as a background task; answers incoming calls and saves received faxes."""
        raise NotImplementedError
