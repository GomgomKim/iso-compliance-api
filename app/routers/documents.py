from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    PresignedUploadResponse,
    PresignedDownloadResponse,
)
from app.core.security import get_current_user
from app.services.storage import get_storage_service, StorageService

router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    control_id: Optional[str] = None,
    task_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the organization."""
    org_id = current_user["organization_id"]

    query = (
        select(Document)
        .options(selectinload(Document.uploaded_by))
        .where(Document.organization_id == org_id)
    )

    if control_id:
        query = query.where(Document.control_id == control_id)

    if task_id:
        query = query.where(Document.task_id == task_id)

    if search:
        query = query.where(
            Document.name.ilike(f"%{search}%")
            | Document.description.ilike(f"%{search}%")
        )

    result = await db.execute(query.order_by(Document.created_at.desc()))
    documents = result.scalars().all()

    total_size = sum(doc.file_size for doc in documents)

    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        total_size=total_size,
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    control_id: Optional[str] = Form(None),
    task_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a document directly."""
    org_id = current_user["organization_id"]

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Generate file key
    file_key = storage.generate_file_key(
        organization_id=org_id,
        filename=file.filename or "unknown",
    )

    # Upload to storage
    await storage.upload_file(
        file_content=content,
        file_key=file_key,
        content_type=file.content_type or "application/octet-stream",
    )

    # Create document record
    document = Document(
        name=name or file.filename or "Untitled",
        description=description,
        file_key=file_key,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        organization_id=org_id,
        control_id=control_id,
        task_id=task_id,
        uploaded_by_id=current_user["user_id"],
    )
    db.add(document)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.uploaded_by))
        .where(Document.id == document.id)
    )

    return DocumentUploadResponse(document=result.scalar_one())


@router.post("/presigned-upload", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(
    filename: str,
    content_type: str,
    current_user: dict = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Get a presigned URL for direct upload to S3/R2."""
    org_id = current_user["organization_id"]

    file_key = storage.generate_file_key(
        organization_id=org_id,
        filename=filename,
    )

    upload_url = await storage.get_presigned_upload_url(
        file_key=file_key,
        content_type=content_type,
        expires_in=3600,
    )

    return PresignedUploadResponse(
        upload_url=upload_url,
        file_key=file_key,
        expires_in=3600,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.uploaded_by))
        .where(
            Document.id == document_id,
            Document.organization_id == current_user["organization_id"],
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get("/{document_id}/download", response_model=PresignedDownloadResponse)
async def get_document_download_url(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Get a presigned URL for downloading a document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == current_user["organization_id"],
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    download_url = await storage.get_presigned_download_url(
        file_key=document.file_key,
        filename=document.name,
        expires_in=3600,
    )

    return PresignedDownloadResponse(
        download_url=download_url,
        expires_in=3600,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    request: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.uploaded_by))
        .where(
            Document.id == document_id,
            Document.organization_id == current_user["organization_id"],
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    await db.flush()
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete a document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == current_user["organization_id"],
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete from storage
    await storage.delete_file(document.file_key)

    # Delete from database
    await db.delete(document)

    return {"message": "Document deleted successfully"}
