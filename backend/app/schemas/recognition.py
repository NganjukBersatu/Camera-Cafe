from pydantic import BaseModel
from datetime import datetime

class RecognitionEventResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    camera_id: str
    customer_id: str | None
    similarity: float
    matched: bool
    frame_path: str | None
    detected_at: datetime

class PaginatedRecognitionEvents(BaseModel):
    items: list[RecognitionEventResponse]
    total: int
    page: int
    size: int