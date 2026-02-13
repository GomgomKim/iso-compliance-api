from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.control import ControlStatus


class ControlBase(BaseModel):
    control_id: str
    name_en: str
    name_ko: str
    description_en: Optional[str] = None
    description_ko: Optional[str] = None
    category: str
    category_name_en: str
    category_name_ko: str


class ControlResponse(ControlBase):
    id: str

    class Config:
        from_attributes = True


class OrganizationControlBase(BaseModel):
    status: ControlStatus = ControlStatus.NOT_STARTED
    is_applicable: bool = True
    notes: Optional[str] = None


class OrganizationControlUpdate(BaseModel):
    status: Optional[ControlStatus] = None
    is_applicable: Optional[bool] = None
    notes: Optional[str] = None


class OrganizationControlResponse(OrganizationControlBase):
    id: str
    organization_id: str
    control_id: str
    control: ControlResponse
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    document_count: int = 0

    class Config:
        from_attributes = True


class ControlListResponse(BaseModel):
    controls: List[OrganizationControlResponse]
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]


class ControlCategoryResponse(BaseModel):
    category: str
    category_name_en: str
    category_name_ko: str
    controls: List[OrganizationControlResponse]
    total: int
    completed: int
