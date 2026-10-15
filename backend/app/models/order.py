from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    woocommerce_order_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    fulfillment_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unfulfilled"
    )
    order_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    line_items: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")

    __table_args__ = (Index("ix_orders_status", "status"),)
