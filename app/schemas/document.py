from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DocumentBase(BaseModel):
    name: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class DocumentCreate(DocumentBase):
    control_id: Optional[str] = None
    task_id: Optional[str] = None


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    control_id: Optional[str] = None
    task_id: Optional[str] = None


class UploaderResponse(BaseModel):
    id: str
    name: Optional[str]
    email: str

    class Config:
        from_attributes = True


class DocumentResponse(DocumentBase):
    id: str
    file_key: str
    file_size: int
    mime_type: str
    version: int
    organization_id: str
    control_id: Optional[str]
    task_id: Optional[str]
    uploaded_by_id: str
    uploaded_by: UploaderResponse
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    total_size: int


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    upload_url: Optional[str] = None  # For direct upload


class PresignedUploadResponse(BaseModel):
    upload_url: str
    file_key: str
    expires_in: int


class PresignedDownloadResponse(BaseModel):
    download_url: str
    expires_in: int
