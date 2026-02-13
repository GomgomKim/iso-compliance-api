from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, Any
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ActivityType(str, enum.Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    CONTROL_STATUS_CHANGED = "control_status_changed"
    USER_INVITED = "user_invited"
    USER_REMOVED = "user_removed"


class Activity(Base, UUIDMixin, TimestampMixin):
    """Activity log model for tracking user actions."""
    __tablename__ = "activities"

    type: Mapped[ActivityType] = mapped_column(SQLEnum(ActivityType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities")
