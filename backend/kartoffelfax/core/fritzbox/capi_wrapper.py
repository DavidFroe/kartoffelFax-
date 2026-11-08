"""Optional fallback: CAPI-over-TCP wrapper for local Windows installations
that still rely on a CAPI-compatible fax driver, instead of the SIP/T.38 path.

Not needed for the primary VPN/remote use case; kept isolated so it can be
omitted entirely from Linux/Flatpak builds.

Only endpoint reachability is implemented. No public specification of the
remote-CAPI wire protocol (or of its authentication) was found, so
`send_fax` is deliberately left unimplemented rather than guessed.
"""
from __future__ import annotations

import asyncio


class CapiNotAvailableError(RuntimeError):
    """Raised when no CAPI-over-TCP endpoint is configured or reachable."""


class CapiFaxWrapper:
    def __init__(self, host: str, port: int = 2662, timeout: float = 3.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout

    async def is_available(self) -> bool:
        """True if a TCP connection to the configured endpoint can be opened."""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), self._timeout
            )
        except (OSError, TimeoutError):
            return False
        writer.close()
        await writer.wait_closed()
        return True

    async def send_fax(self, fax_number: str, g3_path: str) -> None:
        if not await self.is_available():
            raise CapiNotAvailableError(f"No CAPI endpoint reachable at {self._host}:{self._port}")
        raise NotImplementedError(
            "Remote-CAPI wire protocol is not implemented: no public specification was available"
        )
