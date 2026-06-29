from fastapi import APIRouter, Depends, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from websockets import route
from app.database import get_db
from app.models.camera import CameraSource
from app.schemas.camera import (CameraCreate, CameraUpdate, CameraResponse, PaginatedCameras)
from fastapi.responses import StreamingResponse, Response
import redis
import base64
import time
from app.config import settings
import uuid
import io

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

@router.get("/stream/live")
def stream_camera():
    def generate():
        r = redis.from_url(settings.redis_url)
        while True:
            frame_b64 = r.get("latest_frame")
            if frame_b64:
                frame_bytes = base64.b64decode(frame_b64)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            time.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/stream/snapshot")
def snapshot():
    r = redis.from_url(settings.redis_url)
    frame_b64 = r.get("latest_frame")
    if not frame_b64:
        raise HTTPException(status_code=503, detail="Tidak ada frame tersedia")
    frame_bytes = base64.b64decode(frame_b64)
    return Response(content=frame_bytes, media_type="image/jpeg")

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