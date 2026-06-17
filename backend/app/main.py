from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, customers, visits, enrollment, cameras


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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    print("Origin:", websocket.headers.get("origin"))

    await websocket.accept()

    await websocket.send_json({
        "status": "connected"
    })

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        print("Client terputus")
@app.get("/")
async def root():

    return {
        "status": "ok",
        "service": "Camera Cafe CRM"
    }

app.state.manager = manager