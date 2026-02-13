from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.task import Task
    from app.models.document import Document
    from app.models.activity import Activity


class UserRole(str, enum.Enum):
    ADMIN = "admin"  # ISO 담당자
    MANAGER = "manager"  # 부서 관리자
    MEMBER = "member"  # 일반 담당자


class User(Base, UUIDMixin, TimestampMixin):
    """User model representing a user of the platform."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.MEMBER,
        nullable=False,
    )
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    assigned_tasks: Mapped[List["Task"]] = relationship("Task", back_populates="assignee")
    uploaded_documents: Mapped[List["Document"]] = relationship("Document", back_populates="uploaded_by")
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="user")
