from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskWithDdayResponse,
)
from app.core.security import get_current_user

router = APIRouter()


def calculate_dday(due_date: Optional[datetime]) -> tuple[Optional[str], bool]:
    """Calculate D-day string and overdue status."""
    if not due_date:
        return None, False

    now = datetime.now(timezone.utc)
    due = due_date.replace(tzinfo=timezone.utc) if due_date.tzinfo is None else due_date

    # Reset time for comparison
    now_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    due_date_only = due.replace(hour=0, minute=0, second=0, microsecond=0)

    diff = (due_date_only - now_date).days

    if diff == 0:
        return "D-Day", False
    elif diff > 0:
        return f"D-{diff}", False
    else:
        return f"D+{abs(diff)}", True


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    control_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    overdue_only: bool = False,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks for the organization."""
    org_id = current_user["organization_id"]
    now = datetime.now(timezone.utc)

    query = (
        select(Task)
        .options(selectinload(Task.assignee))
        .where(Task.organization_id == org_id)
    )

    if status:
        query = query.where(Task.status == status)

    if priority:
        query = query.where(Task.priority == priority)

    if control_id:
        query = query.where(Task.control_id == control_id)

    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)

    if overdue_only:
        query = query.where(Task.due_date < now, Task.status != TaskStatus.DONE)

    if search:
        query = query.where(
            Task.title.ilike(f"%{search}%") | Task.description.ilike(f"%{search}%")
        )

    result = await db.execute(query.order_by(Task.due_date.asc().nullslast()))
    tasks = result.scalars().all()

    # Calculate stats
    by_status = {}
    by_priority = {}
    overdue_count = 0

    for task in tasks:
        # By status
        status_key = task.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1

        # By priority
        priority_key = task.priority.value
        by_priority[priority_key] = by_priority.get(priority_key, 0) + 1

        # Overdue
        if task.due_date and task.due_date < now and task.status != TaskStatus.DONE:
            overdue_count += 1

    return TaskListResponse(
        tasks=tasks,
        total=len(tasks),
        by_status=by_status,
        by_priority=by_priority,
        overdue_count=overdue_count,
    )


@router.get("/upcoming", response_model=List[TaskWithDdayResponse])
async def list_upcoming_tasks(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List upcoming tasks within the specified number of days."""
    org_id = current_user["organization_id"]
    now = datetime.now(timezone.utc)
    from datetime import timedelta

    future = now + timedelta(days=days)

    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
        .where(
            Task.organization_id == org_id,
            Task.status != TaskStatus.DONE,
            Task.due_date.isnot(None),
            Task.due_date <= future,
        )
        .order_by(Task.due_date.asc())
    )
    tasks = result.scalars().all()

    # Add D-day info
    tasks_with_dday = []
    for task in tasks:
        dday, is_overdue = calculate_dday(task.due_date)
        task_dict = TaskWithDdayResponse.model_validate(task)
        task_dict.dday = dday
        task_dict.is_overdue = is_overdue
        tasks_with_dday.append(task_dict)

    return tasks_with_dday


@router.post("/", response_model=TaskResponse)
async def create_task(
    request: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    task = Task(
        **request.model_dump(),
        organization_id=current_user["organization_id"],
    )
    db.add(task)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
        .where(Task.id == task.id)
    )
    return result.scalar_one()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task."""
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
        .where(
            Task.id == task_id,
            Task.organization_id == current_user["organization_id"],
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.assignee))
        .where(
            Task.id == task_id,
            Task.organization_id == current_user["organization_id"],
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == current_user["organization_id"],
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    await db.delete(task)
    return {"message": "Task deleted successfully"}
