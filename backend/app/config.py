from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://crm_user:crm_password_123@127.0.0.1:5432/camera_cafe_crm"
    redis_url: str = "redis://127.0.0.1:6379/0"
    qdrant_url: str = "http://127.0.0.1:6333"
    mqtt_host: str = "127.0.0.1"
    mqtt_port: int = 1883

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    base_url: str = "http://localhost:8000"

settings = Settings()