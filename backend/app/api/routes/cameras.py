from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from websockets import route
from app.database import get_db
from app.models.camera import CameraSource
from app.schemas.camera import (CameraCreate, CameraUpdate, CameraResponse, PaginatedCameras)
import uuid

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.get("", response_model=PaginatedCameras)
def list_cameras(
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = select(CameraSource)
    if role:
        q = q.where(CameraSource.role == role)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    cameras = db.scalars(q.offset((page - 1) * size).limit(size)).all()

    return PaginatedCameras(
        items=[CameraResponse.model_validate(c) for c in cameras],
        total=total,
        page=page,
        size=size,
    )

@router.post("", response_model=CameraResponse, status_code=201)
def create_camera(body: CameraCreate, db: Session = Depends(get_db)):
    camera = CameraSource(
        id=str(uuid.uuid4()),
        name=body.name,
        role=body.role,
        rtsp_url=body.rtsp_url,
        capture_interval_ms=body.capture_interval_ms,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return CameraResponse.model_validate(camera)

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = db.get(CameraSource, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera tidak ditemukan")
    return CameraResponse.model_validate(camera)

@router.patch("/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: str, body: CameraUpdate, db: Session = Depends(get_db)):
    camera = db.get(CameraSource, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera tidak ditemukan")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)
    db.commit()
    db.refresh(camera)
    return CameraResponse.model_validate(camera)

@router.delete("/{camera_id}", status_code=204)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = db.get(CameraSource, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera tidak ditemukan")
    db.delete(camera)
    db.commit()