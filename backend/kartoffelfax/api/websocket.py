"""WebSocket hub for live fax status updates (dialing, T.38 progress, VPN state)."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        payload = json.dumps(event)
        for client in self._clients:
            try:
                await client.send_text(payload)
            except Exception:
                stale.append(client)
        for client in stale:
            self.disconnect(client)


manager = ConnectionManager()


@router.websocket("/ws/status")
async def status_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # client doesn't send anything meaningful yet
    except WebSocketDisconnect:
        manager.disconnect(websocket)
