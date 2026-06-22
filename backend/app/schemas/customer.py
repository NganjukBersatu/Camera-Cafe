from datetime import datetime
from pydantic import BaseModel


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
    id: str
    name: str
    contact: str | None
    notes: str | None
    preferences: str | None
    status: str
    face_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, **kwargs):  # type: ignore[override]
        return cls(
            id=obj.id,
            name=obj.name,
            contact=obj.contact,
            notes=obj.notes,
            preferences=obj.preferences,
            status="active" if obj.is_active else "inactive",
            face_count=len(obj.faces) if hasattr(obj, "faces") else 0,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class PaginatedCustomers(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    size: int