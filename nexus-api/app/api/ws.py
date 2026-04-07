from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..auth import get_current_user_ws
from ..database import AsyncSessionLocal
import json

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws

    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)

    async def send_personal(self, user_id: str, message: dict):
        if user_id in self.active:
            await self.active[user_id].send_json(message)

manager = ConnectionManager()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    async with AsyncSessionLocal() as db:
        user = await get_current_user_ws(websocket, token, db)
        if not user:
            return
    await manager.connect(str(user.id), websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Ретрансляция E2EE сообщений
            if data.get("type") == "message":
                to = data.get("to")
                if to:
                    await manager.send_personal(to, data)
            # Обработка статуса "печатает", прочитано и т.д.
            elif data.get("type") == "typing":
                to = data.get("to")
                if to:
                    await manager.send_personal(to, data)
    except WebSocketDisconnect:
        manager.disconnect(str(user.id))
# Добавить в функцию websocket_endpoint после manager.connect
    # Периодически обновляем статус онлайн в Redis
    async def update_online_status():
        while True:
            await redis_client.setex(f"user_online:{user.id}", 300, "1")
            await asyncio.sleep(240)  # обновляем каждые 4 минуты
    asyncio.create_task(update_online_status())
    
async def send_reaction_notification(self, user_id: str, message_id: str, reaction: str, reactor_id: str):
    await self.send_personal(user_id, {
        "type": "reaction",
        "message_id": message_id,
        "user_id": reactor_id,
        "reaction": reaction
    })           
