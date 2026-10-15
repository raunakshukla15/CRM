from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.customer_note import CustomerNote
from app.models.order import Order
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
    NoteCreate,
    NoteResponse,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerListResponse)
def list_customers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: CustomerStatus | None = Query(default=None),
    min_spend: Decimal | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, description="Search email / name / phone"),
    order_status: str | None = Query(
        default=None, description="Only customers having an order with this status"
    ),
):
    query = select(Customer)
    count_q = select(func.count()).select_from(Customer)

    filters = []
    if status is not None:
        filters.append(Customer.customer_status == status)
    if min_spend is not None:
        filters.append(Customer.total_spend >= min_spend)
    if search:
        like = f"%{search}%"
        filters.append(
            (Customer.email.like(like))
            | (Customer.first_name.like(like))
            | (Customer.last_name.like(like))
            | (Customer.phone.like(like))
        )
    if order_status:
        sub = select(Order.customer_id).where(Order.status == order_status).distinct()
        filters.append(Customer.id.in_(sub))
    if filters:
        query = query.where(*filters)
        count_q = count_q.where(*filters)

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(
            query.order_by(Customer.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(Customer).where(Customer.email == email)):
        raise HTTPException(status_code=409, detail="A customer with this email already exists")
    customer = Customer(
        email=email,
        first_name=body.first_name or "",
        last_name=body.last_name or "",
        phone=body.phone,
        billing_address=body.billing_address,
        shipping_address=body.shipping_address,
        customer_status=CustomerStatus.LEAD,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, body: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        email = data["email"].strip().lower()
        clash = db.scalar(select(Customer).where(Customer.email == email, Customer.id != customer_id))
        if clash:
            raise HTTPException(status_code=409, detail="Another customer uses this email")
        data["email"] = email
    for key, value in data.items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.scalar(
        select(Customer)
        .where(Customer.id == customer_id)
        .options(
            selectinload(Customer.orders),
            selectinload(Customer.communication_logs),
            selectinload(Customer.notes),
            selectinload(Customer.interactions),
            selectinload(Customer.followups),
        )
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/{customer_id}/notes", response_model=NoteResponse, status_code=201)
def add_customer_note(customer_id: int, body: NoteCreate, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    note = CustomerNote(
        customer_id=customer.id, note=body.note, created_by=body.created_by
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{customer_id}/notes", response_model=list[NoteResponse])
def list_customer_notes(customer_id: int, db: Session = Depends(get_db)):
    if db.get(Customer, customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return list(
        db.scalars(
            select(CustomerNote)
            .where(CustomerNote.customer_id == customer_id)
            .order_by(CustomerNote.id.desc())
        ).all()
    )
