from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.control import OrganizationControl
    from app.models.task import Task
    from app.models.user import User


class Document(Base, UUIDMixin, TimestampMixin):
    """Document model representing uploaded evidence files."""
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)  # S3/R2 key
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=True,
        index=True,
    )
    uploaded_by_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="documents")
    control: Mapped[Optional["OrganizationControl"]] = relationship(
        "OrganizationControl", back_populates="documents"
    )
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="documents")
    uploaded_by: Mapped["User"] = relationship("User", back_populates="uploaded_documents")
