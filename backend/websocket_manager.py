import json
import logging
import asyncio
import time
from typing import Set, Dict, Any, List
from fastapi import WebSocket

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.controllers: Set[WebSocket] = set()
        self.receivers: Set[WebSocket] = set()
        self.receiver_info: Dict[WebSocket, Dict[str, Any]] = {}
        self.cast_version: int = 0
        self.cast_lock = asyncio.Lock()
        self.current_state: Dict[str, Any] = {
            "state": "STOPPED",
            "title": "Ready to cast",
            "url": "",
            "channel_id": None,
            "logo": "",
            "sources": [],
            "source_index": 0,
            "version": 0,
            "volume": 20,
            "muted": False,
            "duration": "00:00:00",
            "position": "00:00:00",
            "selected_tv_name": "Hisense VIDAA TV",
            "selected_tv_ip": "192.168.50.249"
        }

    def next_version(self) -> int:
        self.cast_version += 1
        return self.cast_version

    async def connect_controller(self, websocket: WebSocket):
        await websocket.accept()
        self.controllers.add(websocket)
        # Send current state immediately on connect
        await websocket.send_json({
            "type": "sync_state",
            "data": self.current_state
        })

    def disconnect_controller(self, websocket: WebSocket):
        self.controllers.discard(websocket)

    async def connect_receiver(self, websocket: WebSocket):
        await websocket.accept()
        self.receivers.add(websocket)
        host = websocket.client.host if websocket.client else "unknown"
        ua = websocket.headers.get("user-agent", "")
        self.receiver_info[websocket] = {
            "host": host,
            "user_agent": ua,
            "connected_at": time.time()
        }
        logger.info(f"TV Web Receiver connected from {host}. Total receivers: {len(self.receivers)}")
        # Send current playback state to receiver ONLY if URL exists, including full versioned payload
        if self.current_state.get("url"):
            await websocket.send_json({
                "type": "playback_command",
                "action": "play",
                "url": self.current_state["url"],
                "title": self.current_state.get("title", "Live Stream"),
                "channel_id": self.current_state.get("channel_id"),
                "logo": self.current_state.get("logo", ""),
                "sources": self.current_state.get("sources", []),
                "source_index": self.current_state.get("source_index", 0),
                "sources_total": len(self.current_state.get("sources", [])),
                "version": self.current_state.get("version", self.cast_version)
            })

    def disconnect_receiver(self, websocket: WebSocket):
        self.receivers.discard(websocket)
        self.receiver_info.pop(websocket, None)

    async def broadcast_to_controllers(self, event_type: str, data: Any):
        """Send message to all phone/web controllers."""
        message = {"type": event_type, "data": data}
        dead_sockets = set()
        for ws in self.controllers:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.add(ws)
        for dead in dead_sockets:
            self.controllers.discard(dead)

    async def send_to_receivers(self, action: str, data: Dict[str, Any]):
        """Send command to TV Web Receivers."""
        payload = {"type": "playback_command", "action": action, "version": self.cast_version, **data}
        dead_sockets = set()
        for ws in self.receivers:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)
        for dead in dead_sockets:
            self.receivers.discard(dead)
            self.receiver_info.pop(dead, None)

    def get_receivers_debug_info(self) -> List[Dict[str, Any]]:
        return list(self.receiver_info.values())

    def update_state(self, updates: Dict[str, Any]):
        self.current_state.update(updates)

ws_manager = ConnectionManager()
