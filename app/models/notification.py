from sqlalchemy import String, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class NotificationType(str, enum.Enum):
    DEADLINE_APPROACHING = "deadline_approaching"  # D-30, D-7
    DEADLINE_TODAY = "deadline_today"  # D-day
    DEADLINE_OVERDUE = "deadline_overdue"  # D+1~
    TASK_ASSIGNED = "task_assigned"
    DOCUMENT_EXPIRING = "document_expiring"
    CONTROL_STATUS_CHANGED = "control_status_changed"


class Notification(Base, UUIDMixin, TimestampMixin):
    """Notification model for user alerts."""
    __tablename__ = "notifications"

    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    # Optional reference to related entity
    related_task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=True,
    )
    related_document_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("documents.id"),
        nullable=True,
    )
