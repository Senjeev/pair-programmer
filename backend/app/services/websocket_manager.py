from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self.latest_code: Dict[str, str] = {}

    def set_code(self, room_id: str, code: str):
        self.latest_code[room_id] = code

    def get_code(self, room_id: str) -> Optional[str]:
        return self.latest_code.get(room_id)

    def _get_lock(self, room_id: str) -> asyncio.Lock:
        if room_id not in self._locks:
            self._locks[room_id] = asyncio.Lock()
        return self._locks[room_id]

    async def connect(self, room_id: str, websocket: WebSocket, username: str):
        try:
            await websocket.accept()
            async with self._get_lock(room_id):
                self.active_connections.setdefault(room_id, []).append({
                    "socket": websocket,
                    "username": username,
                    "typing": False
                })
        except Exception:
            logger.exception("Failed to connect websocket")
            try:
                await websocket.close()
            except Exception:
                pass

    async def disconnect(self, room_id: str, websocket: WebSocket):

        try:
            async with self._get_lock(room_id):
                if room_id not in self.active_connections:
                    return

                self.active_connections[room_id] = [
                    c for c in self.active_connections[room_id] 
                    if c["socket"] != websocket
                ]
                if not self.active_connections[room_id]:
                    self.active_connections.pop(room_id, None)
                    self._locks.pop(room_id, None)
                    self.latest_code.pop(room_id, None)
        except Exception:
            logger.exception("Error during websocket disconnect")

        try:
            await websocket.close()
        except Exception:
            pass

    async def _safe_send(self, socket: WebSocket, data: str) -> bool:
        try:
            await socket.send_text(data)
            return True
        except Exception:
            return False

    async def broadcast_code(self, room_id: str, code: str, sender_socket: WebSocket):
        self.latest_code[room_id] = code
        try:
            async with self._get_lock(room_id):
                if room_id not in self.active_connections:
                    return
 
                connections = self.active_connections[room_id]
                sender = next((c["username"] for c in connections if c["socket"] == sender_socket), "Unknown")
     
                sockets = [c["socket"] for c in connections]
        except Exception:
            logger.exception("Failed to prepare broadcast")
            return

        message = json.dumps({"type": "CODE_UPDATE", "code": code, "sender": sender})
        
        dead_sockets = []
        for socket in sockets:
            if socket == sender_socket:
                continue
            
            if not await self._safe_send(socket, message):
                dead_sockets.append(socket)
        
        if dead_sockets:
            await self.remove_dead_sockets(room_id, dead_sockets)

    async def broadcast_typing(self, room_id: str, sender_socket: WebSocket, typing: bool):
        try:
            async with self._get_lock(room_id):
                for conn in self.active_connections.get(room_id, []):
                    if conn["socket"] == sender_socket:
                        conn["typing"] = typing
                        break
        except Exception:
            pass

    async def remove_dead_sockets(self, room_id: str, dead_sockets: list):
        try:
            async with self._get_lock(room_id):
                if room_id not in self.active_connections:
                    return

                self.active_connections[room_id] = [
                    c for c in self.active_connections[room_id]
                    if c["socket"] not in dead_sockets
                ]

                if not self.active_connections[room_id]:
                    self.active_connections.pop(room_id, None)
                    self._locks.pop(room_id, None)
                    self.latest_code.pop(room_id, None)
        except Exception:
            logger.exception("Failed to remove dead sockets")

manager_instance = ConnectionManager()

def get_manager() -> ConnectionManager:
    return manager_instance