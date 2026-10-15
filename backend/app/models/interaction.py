from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Interaction(Base):
    """Manual communication record: calls, emails, meetings, notes."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False, default="note")
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="logged")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="admin")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="interactions")
