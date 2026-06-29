from pydantic import BaseModel
from datetime import datetime


class MenuItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    is_available: bool | None = None


class MenuItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: str | None
    price: float
    category: str | None
    image_path: str | None
    image_url: str | None = None
    is_available: bool
    created_at: datetime
    updated_at: datetime


class PaginatedMenuItems(BaseModel):
    items: list[MenuItemResponse]
    total: int
    page: int
    size: int