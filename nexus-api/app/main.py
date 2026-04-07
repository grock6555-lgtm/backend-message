from fastapi import FastAPI
from .api import users, chats, messages, files, calls, ws, prekeys
from .database import engine, Base
from .config import settings
from .api import stickers, reactions, contacts, invites
from .api import calls
app.include_router(calls.router)
app.include_router(stickers.router)
app.include_router(reactions.router)
app.include_router(contacts.router)
app.include_router(invites.router)

app = FastAPI(title="Nexus Chat API")

# Создание таблиц (если не созданы)
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(users.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(files.router)
app.include_router(calls.router)
app.include_router(ws.router)
app.include_router(prekeys.router)

@app.get("/health")
async def health():
    return {"status": "ok"}