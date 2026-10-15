from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession, selectinload

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.customer import Customer, CustomerStatus
from app.models.customer_note import CustomerNote
from app.models.order import Order
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
    NoteCreate,
    NoteResponse,
)
from app.services.activity import log_activity

router = APIRouter(prefix="/customers", tags=["customers"])


def _owned_customer_or_404(db: DBSession, customer_id: int, user_id: int) -> Customer:
    customer = db.scalar(
        select(Customer).where(Customer.id == customer_id, Customer.owner_id == user_id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("", response_model=CustomerListResponse)
def list_customers(
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: CustomerStatus | None = Query(default=None),
    min_spend: Decimal | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, description="Search email / name / phone"),
    order_status: str | None = Query(
        default=None, description="Only customers having an order with this status"
    ),
    sort: str = Query(default="newest", description="newest|spend|name"),
):
    filters = [Customer.owner_id == user.id]
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
            | (Customer.company.like(like))
        )
    if order_status:
        sub = (
            select(Order.customer_id)
            .where(Order.status == order_status, Order.owner_id == user.id)
            .distinct()
        )
        filters.append(Customer.id.in_(sub))

    query = select(Customer).where(*filters)
    count_q = select(func.count()).select_from(Customer).where(*filters)

    if sort == "spend":
        query = query.order_by(Customer.total_spend.desc())
    elif sort == "name":
        query = query.order_by(Customer.first_name.asc(), Customer.last_name.asc())
    else:
        query = query.order_by(Customer.id.desc())

    total = db.scalar(count_q) or 0
    items = list(
        db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    body: CustomerCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    email = body.email.strip().lower()
    if db.scalar(select(Customer).where(Customer.owner_id == user.id, Customer.email == email)):
        raise HTTPException(status_code=409, detail="You already have a customer with this email.")
    customer = Customer(
        owner_id=user.id,
        email=email,
        first_name=body.first_name or "",
        last_name=body.last_name or "",
        phone=body.phone,
        company=body.company,
        billing_address=body.billing_address,
        shipping_address=body.shipping_address,
        profile_notes=body.profile_notes,
        customer_status=CustomerStatus.LEAD,
    )
    db.add(customer)
    db.flush()
    log_activity(db, "customer.created", f"Customer {email} created.",
                 user_id=user.id, entity_type="customer", entity_id=customer.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    customer = _owned_customer_or_404(db, customer_id, user.id)
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        email = data["email"].strip().lower()
        clash = db.scalar(
            select(Customer).where(
                Customer.owner_id == user.id, Customer.email == email, Customer.id != customer_id
            )
        )
        if clash:
            raise HTTPException(status_code=409, detail="Another customer uses this email")
        data["email"] = email
    for key, value in data.items():
        setattr(customer, key, value)
    log_activity(db, "customer.updated", f"Customer {customer.email} updated.",
                 user_id=user.id, entity_type="customer", entity_id=customer.id,
                 ip=get_client_ip(request))
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    customer = _owned_customer_or_404(db, customer_id, user.id)
    email = customer.email
    db.delete(customer)  # cascades orders, notes, interactions, followups, comm logs
    log_activity(db, "customer.deleted", f"Customer {email} deleted with related records.",
                 user_id=user.id, entity_type="customer", entity_id=customer_id,
                 ip=get_client_ip(request))
    db.commit()
    return {"ok": True}


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: int,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    customer = db.scalar(
        select(Customer)
        .where(Customer.id == customer_id, Customer.owner_id == user.id)
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
def add_customer_note(
    customer_id: int,
    body: NoteCreate,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    customer = _owned_customer_or_404(db, customer_id, user.id)
    note = CustomerNote(
        owner_id=user.id, customer_id=customer.id, note=body.note, created_by=body.created_by
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{customer_id}/notes", response_model=list[NoteResponse])
def list_customer_notes(
    customer_id: int,
    user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    _owned_customer_or_404(db, customer_id, user.id)
    return list(
        db.scalars(
            select(CustomerNote)
            .where(CustomerNote.customer_id == customer_id)
            .order_by(CustomerNote.id.desc())
        ).all()
    )
