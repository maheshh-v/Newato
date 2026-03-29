"""
ARIA WebSocket Broadcaster
Manages all active WebSocket connections and broadcasts events to them.
"""
import json
import time
from typing import Any
from fastapi import WebSocket
from utils.logger import get_logger

logger = get_logger("aria.broadcaster")


class Broadcaster:
    """Manages connected WebSocket clients and broadcasts events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("WS client connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WS client disconnected", total=len(self._connections))

    async def broadcast(self, event_type: str, task_id: str, data: dict[str, Any]) -> None:
        """Send an event to all connected clients."""
        envelope = {
            "task_id": task_id,
            "event_type": event_type,
            "timestamp": int(time.time() * 1000),
            "data": data,
        }
        message = json.dumps(envelope)
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning("WS send failed, removing client", error=str(e))
                dead.add(ws)
        self._connections -= dead

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Singleton instance
broadcaster = Broadcaster()
