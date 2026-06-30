from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models.menu import MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse, PaginatedMenuItems
from app.config import settings
from pathlib import Path
import uuid
import shutil
import os

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=PaginatedMenuItems)
def list_menu(
    category: str | None = Query(None),
    available_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = select(MenuItem)
    if category:
        q = q.where(MenuItem.category == category)
    if available_only:
        q = q.where(MenuItem.is_available.is_(True))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(q.order_by(MenuItem.category, MenuItem.name).offset((page - 1) * size).limit(size)).all()

    result = []
    for item in items:
        image_url = None
        if item.image_path:
            image_url = f"{settings.base_url}/static/{item.image_path}"
        result.append(MenuItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            price=item.price,
            category=item.category,
            image_path=item.image_path,
            image_url=image_url,
            is_available=item.is_available,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ))

    return PaginatedMenuItems(items=result, total=total, page=page, size=size)


@router.post("", response_model=MenuItemResponse, status_code=201)
def create_menu_item(body: MenuItemCreate, db: Session = Depends(get_db)):
    item = MenuItem(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        price=body.price,
        category=body.category,
        is_available=body.is_available,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return MenuItemResponse(
        id=item.id, name=item.name, description=item.description,
        price=item.price, category=item.category, image_path=item.image_path,
        image_url=None, is_available=item.is_available,
        created_at=item.created_at, updated_at=item.updated_at,
    )


@router.patch("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(item_id: str, body: MenuItemUpdate, db: Session = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    image_url = f"{settings.base_url}/static/{item.image_path}" if item.image_path else None
    return MenuItemResponse(
        id=item.id, name=item.name, description=item.description,
        price=item.price, category=item.category, image_path=item.image_path,
        image_url=image_url, is_available=item.is_available,
        created_at=item.created_at, updated_at=item.updated_at,
    )


@router.delete("/{item_id}", status_code=204)
def delete_menu_item(item_id: str, db: Session = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")
    db.delete(item)
    db.commit()


@router.post("/{item_id}/image", response_model=MenuItemResponse)
async def upload_menu_image(
    item_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")

    upload_dir = Path("static") / "menu"
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    filename = f"{item_id}{ext}"
    filepath = upload_dir / filename

    with open(filepath, "wb") as buffet:
        shutil.copyfileobj(file.file, buffet)

    item.image_path = f"menu/{filename}"

    db.commit()
    db.refresh(item)

    image_url = f"{settings.base_url}/static/menu/{filename}"

    return MenuItemResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        image_path=item.image_path,
        image_url=image_url,
        is_available=item.is_available,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )