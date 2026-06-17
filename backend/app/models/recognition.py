import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecognitionEvent(Base):
    __tablename__ = "recognition_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    frame_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
