import boto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for handling file storage with S3/R2."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            config = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_REGION,
            }
            if settings.S3_ENDPOINT_URL:
                config["endpoint_url"] = settings.S3_ENDPOINT_URL

            self._client = boto3.client("s3", **config)
        return self._client

    def generate_file_key(
        self,
        organization_id: str,
        filename: str,
        folder: str = "documents",
    ) -> str:
        """Generate a unique file key for S3."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
        safe_filename = f"{timestamp}_{unique_id}.{extension}" if extension else f"{timestamp}_{unique_id}"

        return f"{organization_id}/{folder}/{safe_filename}"

    async def upload_file(
        self,
        file_content: bytes,
        file_key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload a file to S3/R2."""
        try:
            extra_args = {"ContentType": content_type}
            if metadata:
                extra_args["Metadata"] = metadata

            self.client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_key,
                Body=file_content,
                **extra_args,
            )

            logger.info(f"File uploaded successfully: {file_key}")
            return file_key
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def get_presigned_upload_url(
        self,
        file_key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for direct upload."""
        try:
            url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": file_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise

    async def get_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None,
    ) -> str:
        """Generate a presigned URL for download."""
        try:
            params = {
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": file_key,
            }
            if filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

            url = self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise

    async def delete_file(self, file_key: str) -> bool:
        """Delete a file from S3/R2."""
        try:
            self.client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_key,
            )
            logger.info(f"File deleted successfully: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    async def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in S3/R2."""
        try:
            self.client.head_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_key,
            )
            return True
        except ClientError:
            return False


# Singleton instance
storage_service = StorageService()


def get_storage_service() -> StorageService:
    return storage_service
