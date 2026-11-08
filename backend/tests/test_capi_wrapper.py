from __future__ import annotations

import asyncio

import pytest
from kartoffelfax.core.fritzbox.capi_wrapper import CapiFaxWrapper, CapiNotAvailableError


async def _listening_port() -> tuple[asyncio.Server, int]:
    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


async def test_is_available_true_when_port_open() -> None:
    server, port = await _listening_port()
    async with server:
        assert await CapiFaxWrapper("127.0.0.1", port).is_available() is True


async def test_is_available_false_when_port_closed() -> None:
    server, port = await _listening_port()
    server.close()
    await server.wait_closed()
    assert await CapiFaxWrapper("127.0.0.1", port).is_available() is False


async def test_send_fax_reports_unreachable_endpoint() -> None:
    server, port = await _listening_port()
    server.close()
    await server.wait_closed()
    with pytest.raises(CapiNotAvailableError):
        await CapiFaxWrapper("127.0.0.1", port).send_fax("123", "x.tif")


async def test_send_fax_is_explicitly_unimplemented_even_if_reachable() -> None:
    server, port = await _listening_port()
    async with server:
        with pytest.raises(NotImplementedError, match="specification"):
            await CapiFaxWrapper("127.0.0.1", port).send_fax("123", "x.tif")
