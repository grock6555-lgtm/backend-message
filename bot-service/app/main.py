from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api import endpoints
from .redis_listener import listen_to_redis
from .api import auth, users, chats, messages, files, calls, ws, prekeys
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(listen_to_redis())
    yield
    task.cancel()

app = FastAPI(title="Nexus Chat Bot Service", lifespan=lifespan)
app.include_router(endpoints.router)
app.include_router(auth.router)