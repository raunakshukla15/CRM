import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CustomerStatus(str, enum.Enum):
    LEAD = "Lead"
    ACTIVE = "Active"
    VIP = "VIP"
    CHURNED = "Churned"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    woocommerce_customer_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    billing_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    shipping_address: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    total_spend: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    lifetime_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    customer_status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=CustomerStatus.LEAD,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True
    )
    communication_logs: Mapped[list["CommunicationLog"]] = relationship(
        "CommunicationLog",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notes: Mapped[list["CustomerNote"]] = relationship(
        "CustomerNote",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_customers_status", "customer_status"),
        Index("ix_customers_total_spend", "total_spend"),
    )
