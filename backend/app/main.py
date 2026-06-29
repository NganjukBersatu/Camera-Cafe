from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, customers, visits, enrollment, cameras, recognition, menu
import asyncio
import redis.asyncio as aioredis
import json

app = FastAPI(title="Camera Cafe CRM", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(customers.router)
app.include_router(visits.router)
app.include_router(enrollment.router)
app.include_router(cameras.router)
app.include_router(recognition.router)
app.include_router(menu.router)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client terhubung. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Client terputus. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


async def redis_subscriber():
    """Subscribe ke Redis channel dengan auto-reconnect."""
    print("Redis subscriber aktif — mendengarkan recognition_events...")
    while True:
        try:
            r = aioredis.from_url(
                settings.redis_url,
                socket_timeout=None,
                socket_connect_timeout=5,
            )
            pubsub = r.pubsub()
            await pubsub.subscribe("recognition_events")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        print("EVENT DARI REDIS: ", data)
                        await manager.broadcast(data)
                        print(f"Broadcast ke {len(manager.active_connections)} client")
                    except Exception as e:
                        print(f"Error broadcast: {e}")

        except Exception as e:
            print(f"Redis subscriber error: {e} — reconnect dalam 3 detik...")
            await asyncio.sleep(3)


@app.on_event("startup")
async def startup_event():
    app.state.redis_task = asyncio.create_task(redis_subscriber())
    print("Background Redis subscriber dimulai.")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "redis_task"):
        app.state.redis_task.cancel()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:

        await websocket.send_json({
            "event_type": "system_health",
            "health": {
                "api": "ok",
                "database": "ok",
                "redis": "ok",
                "qdrant": "ok",
                "mosquitto": "ok",
                "celery": "ok",
            }
        })

        while True:
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        print("WS ERROR:", e)
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Camera Cafe CRM"
    }


app.state.manager = manager