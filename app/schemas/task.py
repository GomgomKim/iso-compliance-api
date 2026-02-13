from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    recurring_rule: Optional[str] = None


class TaskCreate(TaskBase):
    control_id: Optional[str] = None
    assignee_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    control_id: Optional[str] = None
    assignee_id: Optional[str] = None
    recurring_rule: Optional[str] = None


class AssigneeResponse(BaseModel):
    id: str
    name: Optional[str]
    email: str

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    id: str
    organization_id: str
    control_id: Optional[str]
    assignee_id: Optional[str]
    assignee: Optional[AssigneeResponse]
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    overdue_count: int


class TaskWithDdayResponse(TaskResponse):
    dday: Optional[str] = None  # e.g., "D-7", "D-Day", "D+3"
    is_overdue: bool = False
