import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    recognition_event_id: Mapped[str | None] = mapped_column(String, nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    order_note: Mapped[str | None] = mapped_column(Text, nullable=True)  # ← tambah ini

    customer: Mapped["Customer"] = relationship(back_populates="visits")


from app.models.customer import Customer  # noqa: E402