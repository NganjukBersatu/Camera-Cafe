from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models.recognition import RecognitionEvent
from app.schemas.recognition import RecognitionEventResponse, PaginatedRecognitionEvents

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.get("", response_model=PaginatedRecognitionEvents)
def list_recognition_events(
    camera_id: str | None = Query(None),
    customer_id: str | None = Query(None),
    matched: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = select(RecognitionEvent)
    if camera_id:
        q = q.where(RecognitionEvent.camera_id == camera_id)
    if customer_id:
        q = q.where(RecognitionEvent.customer_id == customer_id)
    if matched is not None:
        q = q.where(RecognitionEvent.matched == matched)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    events = db.scalars(
        q.order_by(RecognitionEvent.detected_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return PaginatedRecognitionEvents(
        items=[RecognitionEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{event_id}", response_model=RecognitionEventResponse)
def get_recognition_event(event_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    event = db.get(RecognitionEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event tidak ditemukan")
    return RecognitionEventResponse.model_validate(event)