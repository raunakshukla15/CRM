"""Singleton row tracking the last WooCommerce sync (id always 1)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False, default=1)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")
    customers_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
