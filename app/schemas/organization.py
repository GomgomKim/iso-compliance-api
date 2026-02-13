from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.organization import ProfileType


class OrganizationBase(BaseModel):
    name: str
    profile_type: ProfileType = ProfileType.STARTUP


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    profile_type: Optional[ProfileType] = None


class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationStatsResponse(BaseModel):
    total_controls: int
    completed_controls: int
    in_progress_controls: int
    not_started_controls: int
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    total_documents: int
    expiring_documents: int
