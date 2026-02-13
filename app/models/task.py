from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional
from datetime import datetime
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.control import OrganizationControl
    from app.models.user import User
    from app.models.document import Document


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, UUIDMixin, TimestampMixin):
    """Task model representing work items for compliance."""
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.TODO,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recurring_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # RRULE format

    # Foreign keys
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("organization_controls.id"),
        nullable=True,
        index=True,
    )
    assignee_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="tasks")
    control: Mapped[Optional["OrganizationControl"]] = relationship(
        "OrganizationControl", back_populates="tasks"
    )
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="task")
