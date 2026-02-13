from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.database import get_db
from app.models.control import Control, OrganizationControl, ControlStatus
from app.schemas.control import (
    OrganizationControlResponse,
    OrganizationControlUpdate,
    ControlListResponse,
    ControlCategoryResponse,
)
from app.core.security import get_current_user

router = APIRouter()


@router.get("/", response_model=ControlListResponse)
async def list_controls(
    status: Optional[ControlStatus] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all controls for the organization."""
    org_id = current_user["organization_id"]

    query = (
        select(OrganizationControl)
        .options(selectinload(OrganizationControl.control))
        .where(OrganizationControl.organization_id == org_id)
    )

    if status:
        query = query.where(OrganizationControl.status == status)

    if category:
        query = query.join(Control).where(Control.category == category)

    if search:
        query = query.join(Control).where(
            Control.name_ko.ilike(f"%{search}%")
            | Control.name_en.ilike(f"%{search}%")
            | Control.control_id.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    controls = result.scalars().all()

    # Calculate stats by status
    by_status = {}
    for ctrl in controls:
        status_key = ctrl.status.value
        by_status[status_key] = by_status.get(status_key, 0) + 1

    # Calculate stats by category
    by_category = {}
    for ctrl in controls:
        cat_key = ctrl.control.category
        by_category[cat_key] = by_category.get(cat_key, 0) + 1

    return ControlListResponse(
        controls=controls,
        total=len(controls),
        by_status=by_status,
        by_category=by_category,
    )


@router.get("/categories", response_model=List[ControlCategoryResponse])
async def list_controls_by_category(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List controls grouped by category."""
    org_id = current_user["organization_id"]

    result = await db.execute(
        select(OrganizationControl)
        .options(selectinload(OrganizationControl.control))
        .where(OrganizationControl.organization_id == org_id)
    )
    controls = result.scalars().all()

    # Group by category
    categories = {}
    for ctrl in controls:
        cat = ctrl.control.category
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "category_name_en": ctrl.control.category_name_en,
                "category_name_ko": ctrl.control.category_name_ko,
                "controls": [],
                "completed": 0,
            }
        categories[cat]["controls"].append(ctrl)
        if ctrl.status == ControlStatus.COMPLETED:
            categories[cat]["completed"] += 1

    return [
        ControlCategoryResponse(
            category=data["category"],
            category_name_en=data["category_name_en"],
            category_name_ko=data["category_name_ko"],
            controls=data["controls"],
            total=len(data["controls"]),
            completed=data["completed"],
        )
        for data in sorted(categories.values(), key=lambda x: x["category"])
    ]


@router.get("/{control_id}", response_model=OrganizationControlResponse)
async def get_control(
    control_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific control."""
    result = await db.execute(
        select(OrganizationControl)
        .options(selectinload(OrganizationControl.control))
        .where(
            OrganizationControl.id == control_id,
            OrganizationControl.organization_id == current_user["organization_id"],
        )
    )
    control = result.scalar_one_or_none()

    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found",
        )

    return control


@router.patch("/{control_id}", response_model=OrganizationControlResponse)
async def update_control(
    control_id: str,
    request: OrganizationControlUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a control status."""
    result = await db.execute(
        select(OrganizationControl)
        .options(selectinload(OrganizationControl.control))
        .where(
            OrganizationControl.id == control_id,
            OrganizationControl.organization_id == current_user["organization_id"],
        )
    )
    control = result.scalar_one_or_none()

    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(control, field, value)

    await db.flush()
    return control
