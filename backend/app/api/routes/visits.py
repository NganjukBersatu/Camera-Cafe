from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models.visit import Visit
from app.models.customer import Customer
from app.schemas.visit import VisitCreate, VisitResponse, PaginatedVisits
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/visits", tags=["visits"])


@router.get("", response_model=PaginatedVisits)
def list_visits(
    customer_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = select(Visit)
    if customer_id:
        q = q.where(Visit.customer_id == customer_id)
    if date_from:
        try:
            start = datetime.fromisoformat(date_from)
            q = q.where(Visit.visited_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Format date_from tidak valid")
    if date_to:
        try:
            end = datetime.fromisoformat(date_to)
            q = q.where(Visit.visited_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Format date_to tidak valid")

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    visits = db.scalars(q.order_by(Visit.visited_at.desc()).offset((page - 1) * size).limit(size)).all()

    return PaginatedVisits(
        items=[VisitResponse.model_validate(v) for v in visits],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=VisitResponse, status_code=201)
def create_visit(body: VisitCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, body.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    visit = Visit(
        id=str(uuid.uuid4()),
        customer_id=body.customer_id,
        source=body.source,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return VisitResponse.model_validate(visit)
