from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
import enum

from app.db.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.control import OrganizationControl
    from app.models.task import Task
    from app.models.document import Document


class ProfileType(str, enum.Enum):
    STARTUP = "startup"
    SME = "sme"
    MIDSIZE = "midsize"
    ENTERPRISE = "enterprise"


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization model representing a company using the platform."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_type: Mapped[ProfileType] = mapped_column(
        SQLEnum(ProfileType),
        default=ProfileType.STARTUP,
        nullable=False,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")
    controls: Mapped[List["OrganizationControl"]] = relationship(
        "OrganizationControl", back_populates="organization"
    )
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="organization")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="organization")
