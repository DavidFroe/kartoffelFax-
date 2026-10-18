"""Optional fallback: CAPI-over-TCP wrapper for local Windows installations
that still rely on a CAPI-compatible fax driver, instead of the SIP/T.38 path.

Not needed for the primary VPN/remote use case; kept isolated so it can be
omitted entirely from Linux/Flatpak builds.
"""
from __future__ import annotations


class CapiNotAvailableError(RuntimeError):
    """Raised when no CAPI-over-TCP endpoint is configured or reachable."""


class CapiFaxWrapper:
    def __init__(self, host: str, port: int = 2662) -> None:
        self._host = host
        self._port = port

    async def send_fax(self, fax_number: str, g3_path: str) -> None:
        raise NotImplementedError("CAPI-over-TCP fallback not yet implemented")
