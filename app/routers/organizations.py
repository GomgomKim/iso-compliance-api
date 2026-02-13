from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.organization import Organization
from app.models.control import OrganizationControl, ControlStatus
from app.models.task import Task, TaskStatus
from app.models.document import Document
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationStatsResponse,
)
from app.core.security import get_current_user

router = APIRouter()


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current organization information."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user["organization_id"])
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.patch("/current", response_model=OrganizationResponse)
async def update_organization(
    request: OrganizationUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current organization (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update organization",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == current_user["organization_id"])
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.flush()
    return organization


@router.get("/current/stats", response_model=OrganizationStatsResponse)
async def get_organization_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization statistics."""
    org_id = current_user["organization_id"]
    now = datetime.now(timezone.utc)

    # Control stats
    control_stats = await db.execute(
        select(
            func.count(OrganizationControl.id).label("total"),
            func.sum(
                func.if_(OrganizationControl.status == ControlStatus.COMPLETED, 1, 0)
            ).label("completed"),
            func.sum(
                func.if_(OrganizationControl.status == ControlStatus.IN_PROGRESS, 1, 0)
            ).label("in_progress"),
            func.sum(
                func.if_(OrganizationControl.status == ControlStatus.NOT_STARTED, 1, 0)
            ).label("not_started"),
        ).where(OrganizationControl.organization_id == org_id)
    )
    control_row = control_stats.one()

    # Task stats
    task_stats = await db.execute(
        select(
            func.count(Task.id).label("total"),
            func.sum(func.if_(Task.status == TaskStatus.DONE, 1, 0)).label("completed"),
        ).where(Task.organization_id == org_id)
    )
    task_row = task_stats.one()

    # Overdue tasks
    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.organization_id == org_id,
            Task.status != TaskStatus.DONE,
            Task.due_date < now,
        )
    )
    overdue_count = overdue_result.scalar() or 0

    # Document stats
    doc_stats = await db.execute(
        select(func.count(Document.id).label("total")).where(
            Document.organization_id == org_id
        )
    )
    doc_row = doc_stats.one()

    # Expiring documents (within 30 days)
    from datetime import timedelta

    expiring_result = await db.execute(
        select(func.count(Document.id)).where(
            Document.organization_id == org_id,
            Document.expires_at.isnot(None),
            Document.expires_at <= now + timedelta(days=30),
        )
    )
    expiring_count = expiring_result.scalar() or 0

    return OrganizationStatsResponse(
        total_controls=control_row.total or 0,
        completed_controls=control_row.completed or 0,
        in_progress_controls=control_row.in_progress or 0,
        not_started_controls=control_row.not_started or 0,
        total_tasks=task_row.total or 0,
        completed_tasks=task_row.completed or 0,
        overdue_tasks=overdue_count,
        total_documents=doc_row.total or 0,
        expiring_documents=expiring_count,
    )
