from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class VisitCreate(BaseModel):
    customer_id: str
    source: Literal["manual"] = "manual"


class VisitResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    customer_id: str
    customer_name: str | None = None
    source: str
    recognition_event_id: str | None
    visited_at: datetime
    order_note: str | None = None  # ← tambah ini


class PaginatedVisits(BaseModel):
    items: list[VisitResponse]
    total: int
    page: int
    size: int