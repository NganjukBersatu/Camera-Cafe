from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.config import settings
import redis as redis_lib
import socket

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/health/dependencies")
def health_dependencies():
    result = {
        "api": "ok",
        "database": "unknown",
        "redis": "unknown",
        "qdrant": "unknown",
        "mosquitto": "unknown",
        "celery": "unknown",
    }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["database"] = "ok"
    except Exception:
        result["database"] = "error"

    try:
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        result["redis"] = "ok"
    except Exception:
        result["redis"] = "error"

    try:
        import httpx
        res = httpx.get(f"{settings.qdrant_url}/health", timeout=2)
        result["qdrant"] = "ok" if res.status_code == 200 else "error"
    except Exception:
        result["qdrant"] = "error"
    
    try:
        sock = socket.create_connection((settings.mqtt_host, settings.mqtt_port), timeout=2)
        sock.close()
        result["mosquitto"] = "ok"
    except Exception:
        result["mosquitto"] = "error"

    return result