import pytest
from unittest.mock import AsyncMock

from app.core.connection_manager import ConnectionManager


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect(self):
        manager = ConnectionManager()
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        
        await manager.connect(websocket, user_id=1)
        
        assert 1 in manager.active_connections
        assert websocket in manager.active_connections[1]
        websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple(self):
        manager = ConnectionManager()
        websocket1 = AsyncMock()
        websocket1.accept = AsyncMock()
        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        
        await manager.connect(websocket1, user_id=1)
        await manager.connect(websocket2, user_id=1)
        
        assert len(manager.active_connections[1]) == 2

    @pytest.mark.asyncio
    async def test_connect_different_users(self):
        manager = ConnectionManager()
        websocket1 = AsyncMock()
        websocket1.accept = AsyncMock()
        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        
        await manager.connect(websocket1, user_id=1)
        await manager.connect(websocket2, user_id=2)
        
        assert 1 in manager.active_connections
        assert 2 in manager.active_connections

    def test_disconnect(self):
        manager = ConnectionManager()
        websocket = AsyncMock()
        
        manager.active_connections[1] = [websocket]
        
        manager.disconnect(websocket, user_id=1)
        
        assert 1 not in manager.active_connections

    def test_disconnect_keeps_other_connections(self):
        manager = ConnectionManager()
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        
        manager.active_connections[1] = [websocket1, websocket2]
        
        manager.disconnect(websocket1, user_id=1)
        
        assert 1 in manager.active_connections
        assert websocket2 in manager.active_connections[1]

    @pytest.mark.asyncio
    async def test_broadcast(self):
        manager = ConnectionManager()
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()
        
        manager.active_connections[1] = [websocket1]
        manager.active_connections[2] = [websocket2]
        
        await manager.broadcast("test message")
        
        websocket1.send_text.assert_called_once_with("test message")
        websocket2.send_text.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_broadcast_empty(self):
        manager = ConnectionManager()
        
        await manager.broadcast("test message")

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        manager = ConnectionManager()
        websocket = AsyncMock()
        
        manager.active_connections[1] = [websocket]
        
        await manager.send_personal_message("personal message", user_id=1)
        
        websocket.send_text.assert_called_once_with("personal message")

    @pytest.mark.asyncio
    async def test_send_personal_message_user_not_found(self):
        manager = ConnectionManager()
        
        await manager.send_personal_message("message", user_id=999)
