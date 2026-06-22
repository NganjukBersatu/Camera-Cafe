from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models.customer import Customer, CustomerFace
from app.models.visit import Visit
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerFaceResponse,
    PaginatedCustomers,
)
from app.schemas.visit import VisitResponse, PaginatedVisits
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=PaginatedCustomers)
def list_customers(
    search: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = select(Customer)
    if search:
        q = q.where(Customer.name.ilike(f"%{search}%"))
    if status == "active":
        q = q.where(Customer.is_active.is_(True))
    elif status == "inactive":
        q = q.where(Customer.is_active.is_(False))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    customers = db.scalars(q.offset((page - 1) * size).limit(size)).all()

    return PaginatedCustomers(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(
        id=str(uuid.uuid4()),
        name=body.name,
        contact=body.contact,
        notes=body.notes,
        preferences=body.preferences,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: str, body: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    customer.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}/faces", response_model=list[CustomerFaceResponse])
def get_faces(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    return [CustomerFaceResponse.model_validate(f) for f in customer.faces]


@router.delete("/{customer_id}/faces/{face_id}", status_code=204)
def delete_face(customer_id: str, face_id: str, db: Session = Depends(get_db)):
    face = db.scalar(
        select(CustomerFace).where(
            CustomerFace.id == face_id,
            CustomerFace.customer_id == customer_id,
        )
    )
    if not face:
        raise HTTPException(status_code=404, detail="Face tidak ditemukan")
    db.delete(face)
    db.commit()


@router.get("/{customer_id}/visits", response_model=PaginatedVisits)
def get_customer_visits(
    customer_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
    q = select(Visit).where(Visit.customer_id == customer_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    visits = db.scalars(q.order_by(Visit.visited_at.desc()).offset((page - 1) * size).limit(size)).all()
    return PaginatedVisits(
        items=[VisitResponse.model_validate(v) for v in visits],
        total=total,
        page=page,
        size=size,
    )
