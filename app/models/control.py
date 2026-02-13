from sqlalchemy import String, Boolean, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.task import Task
    from app.models.document import Document


class ControlStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    REVIEW_PENDING = "review_pending"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


class Control(Base, UUIDMixin):
    """Master list of ISO 27001 Annex A controls."""
    __tablename__ = "controls"

    control_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(255), nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ko: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "A.5", "A.6"
    category_name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    category_name_ko: Mapped[str] = mapped_column(String(255), nullable=False)


class OrganizationControl(Base, UUIDMixin, TimestampMixin):
    """Organization-specific control status and configuration."""
    __tablename__ = "organization_controls"

    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("controls.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[ControlStatus] = mapped_column(
        SQLEnum(ControlStatus),
        default=ControlStatus.NOT_STARTED,
        nullable=False,
    )
    is_applicable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="controls")
    control: Mapped["Control"] = relationship("Control")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="control")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="control")

    __table_args__ = (
        UniqueConstraint("organization_id", "control_id", name="uq_org_control"),
    )
