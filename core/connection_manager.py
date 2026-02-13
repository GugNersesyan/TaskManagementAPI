from typing import Dict, List
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()

        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []

            self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast(self, message: str):
        async with self._lock:
            for connections in self.active_connections.values():
                for websocket in connections:
                    await websocket.send_text(message)

    async def send_personal_message(self, message: str, user_id: int):
        async with self._lock:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    await websocket.send_text(message)
