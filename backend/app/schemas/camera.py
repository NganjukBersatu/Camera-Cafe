from pydantic import BaseModel
from datetime import datetime

class CameraCreate(BaseModel):
    name: str
    role: str
    rtsp_url: str
    capture_interval_ms: int = 1000

class CameraUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    rtsp_url: str | None = None
    capture_interval_ms: int | None = None
    is_active: bool | None = None

class CameraResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    name: str
    role: str
    rtsp_url: str
    capture_interval_ms: int = 1000
    is_active: bool = True
    last_frame_at: datetime | None = None
    created_at: datetime

class PaginatedCameras(BaseModel):
    items: list[CameraResponse]
    total: int
    page: int
    size: int