"""
WebSocket Connection Manager
=============================
Manages WebSocket connections for real-time updates.

Channels:
  - "ledger"           → all clients watching the Transparent Ledger
  - "donor:{user_id}"  → per-donor updates (donation confirmed, students funded)
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Thread-safe WebSocket connection manager with channel-based broadcasting."""

    def __init__(self):
        # channel_name → set of active WebSocket connections
        self._channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """Accept a WebSocket and subscribe it to a channel."""
        await websocket.accept()
        if channel not in self._channels:
            self._channels[channel] = set()
        self._channels[channel].add(websocket)
        logger.info("WS connected: channel=%s (total=%d)", channel, len(self._channels[channel]))

    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket from a channel."""
        if channel in self._channels:
            self._channels[channel].discard(websocket)
            if not self._channels[channel]:
                del self._channels[channel]
            logger.info("WS disconnected: channel=%s", channel)

    async def broadcast(self, channel: str, data: dict):
        """Send a JSON message to all connections in a channel."""
        if channel not in self._channels:
            return

        dead_connections = set()
        message = json.dumps(data)

        for ws in self._channels[channel]:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self._channels[channel].discard(ws)

    async def broadcast_to_all_ledger(self, data: dict):
        """Broadcast to the global ledger channel."""
        await self.broadcast("ledger", data)

    async def broadcast_to_donor(self, user_id: str, data: dict):
        """Broadcast to a specific donor's channel."""
        await self.broadcast(f"donor:{user_id}", data)

    async def broadcast_transaction(self, tx_data: dict, donor_user_id: str = None):
        """
        Broadcast a new transaction to:
        1. The global ledger channel (always)
        2. The specific donor channel (if donor_user_id provided)
        """
        event_payload = {
            "type": "new_transaction",
            "data": tx_data,
        }
        await self.broadcast_to_all_ledger(event_payload)

        if donor_user_id:
            await self.broadcast_to_donor(donor_user_id, event_payload)

    async def broadcast_verification(self, student_user_id: str, result: dict):
        """Broadcast a verification event."""
        event_payload = {
            "type": "verification_update",
            "data": result,
        }
        # Broadcast to ledger so all watchers see verification activity
        await self.broadcast_to_all_ledger(event_payload)


# Global singleton — imported by main.py and event_listener.py
ws_manager = ConnectionManager()
