from pydantic import BaseModel
from datetime import datetime


class CustomerCreate(BaseModel):
    name: str
    contact: str | None = None
    notes: str | None = None
    preferences: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    contact: str | None = None
    notes: str | None = None
    preferences: str | None = None
    is_active: bool | None = None


class CustomerFaceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    customer_id: str
    preview_path: str | None
    created_at: datetime


class CustomerResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    contact: str | None
    notes: str | None
    preferences: str | None
    is_active: bool
    face_count: int = 0
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, **kwargs):  # type: ignore[override]
        instance = super().model_validate(obj, **kwargs)
        instance.face_count = len(obj.faces) if hasattr(obj, "faces") else 0
        return instance


class PaginatedCustomers(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    size: int
