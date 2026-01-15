"""Storage abstraction for S3 and local filesystem."""

import logging
from pathlib import Path
from typing import Optional
from datetime import timedelta

try:
    import aioboto3
    from botocore.exceptions import ClientError, BotoCoreError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from fastapi import UploadFile
from core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Storage service with S3 support and local filesystem fallback."""
    
    def __init__(self):
        self.use_s3 = bool(settings.S3_BUCKET_NAME and S3_AVAILABLE)
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.local_path = Path(settings.LOCAL_STORAGE_PATH)
        
        if not self.use_s3:
            # Ensure local storage directory exists
            self.local_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using local storage at {self.local_path}")
        else:
            logger.info(f"Using S3 storage: bucket={self.bucket_name}, region={self.region}")
    
    async def upload_file(self, file: UploadFile, object_key: str) -> str:
        """
        Upload file to storage.
        
        Args:
            file: FastAPI UploadFile object
            object_key: S3 key or local file path
            
        Returns:
            The object key where the file was stored
        """
        try:
            if self.use_s3:
                return await self._upload_to_s3(file, object_key)
            else:
                return await self._upload_to_local(file, object_key)
        except Exception as e:
            logger.error(f"Failed to upload file {object_key}: {str(e)}")
            raise
    
    async def _upload_to_s3(self, file: UploadFile, object_key: str) -> str:
        """Upload file to S3."""
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset for potential retry
            
            # Upload with server-side encryption
            await s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ServerSideEncryption='AES256',
                ContentType=file.content_type or 'application/octet-stream'
            )
            
            logger.info(f"Uploaded {object_key} to S3")
            return object_key
    
    async def _upload_to_local(self, file: UploadFile, object_key: str) -> str:
        """Upload file to local filesystem."""
        # Create directory structure if needed
        file_path = self.local_path / object_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Uploaded {object_key} to local storage")
        return object_key
    
    async def download_file(self, object_key: str) -> bytes:
        """
        Download file from storage.
        
        Args:
            object_key: S3 key or local file path
            
        Returns:
            File content as bytes
        """
        try:
            if self.use_s3:
                return await self._download_from_s3(object_key)
            else:
                return await self._download_from_local(object_key)
        except Exception as e:
            logger.error(f"Failed to download file {object_key}: {str(e)}")
            raise
    
    async def _download_from_s3(self, object_key: str) -> bytes:
        """Download file from S3."""
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            try:
                response = await s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
                content = await response['Body'].read()
                return content
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'NoSuchKey':
                    raise FileNotFoundError(f"File not found: {object_key}")
                raise
    
    async def _download_from_local(self, object_key: str) -> bytes:
        """Download file from local filesystem."""
        file_path = self.local_path / object_key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {object_key}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, object_key: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            object_key: S3 key or local file path
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if self.use_s3:
                return await self._delete_from_s3(object_key)
            else:
                return await self._delete_from_local(object_key)
        except Exception as e:
            logger.error(f"Failed to delete file {object_key}: {str(e)}")
            return False
    
    async def _delete_from_s3(self, object_key: str) -> bool:
        """Delete file from S3."""
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            try:
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
                logger.info(f"Deleted {object_key} from S3")
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'NoSuchKey':
                    return False
                raise
    
    async def _delete_from_local(self, object_key: str) -> bool:
        """Delete file from local filesystem."""
        file_path = self.local_path / object_key
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        logger.info(f"Deleted {object_key} from local storage")
        return True
    
    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files with given prefix.
        
        Args:
            prefix: Prefix to filter files
            
        Returns:
            List of object keys
        """
        try:
            if self.use_s3:
                return await self._list_s3_files(prefix)
            else:
                return await self._list_local_files(prefix)
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []
    
    async def _list_s3_files(self, prefix: str) -> list[str]:
        """List files from S3."""
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            try:
                response = await s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                if 'Contents' not in response:
                    return []
                
                return [obj['Key'] for obj in response['Contents']]
            except ClientError as e:
                logger.error(f"S3 list error: {str(e)}")
                return []
    
    async def _list_local_files(self, prefix: str) -> list[str]:
        """List files from local filesystem."""
        prefix_path = self.local_path / prefix if prefix else self.local_path
        
        if not prefix_path.exists():
            return []
        
        files = []
        for file_path in prefix_path.rglob('*'):
            if file_path.is_file():
                # Get relative path from local_path
                rel_path = file_path.relative_to(self.local_path)
                files.append(str(rel_path))
        
        return files
    
    async def get_file_metadata(self, object_key: str) -> dict:
        """
        Get file metadata.
        
        Args:
            object_key: S3 key or local file path
            
        Returns:
            Dictionary with metadata (size, content_type, last_modified, etc.)
        """
        try:
            if self.use_s3:
                return await self._get_s3_metadata(object_key)
            else:
                return await self._get_local_metadata(object_key)
        except Exception as e:
            logger.error(f"Failed to get metadata for {object_key}: {str(e)}")
            raise
    
    async def _get_s3_metadata(self, object_key: str) -> dict:
        """Get metadata from S3."""
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            try:
                response = await s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
                
                return {
                    'size': response.get('ContentLength', 0),
                    'content_type': response.get('ContentType', 'application/octet-stream'),
                    'last_modified': response.get('LastModified'),
                    'etag': response.get('ETag', '').strip('"')
                }
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if error_code == 'NotFound':
                    raise FileNotFoundError(f"File not found: {object_key}")
                raise
    
    async def _get_local_metadata(self, object_key: str) -> dict:
        """Get metadata from local filesystem."""
        file_path = self.local_path / object_key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {object_key}")
        
        stat = file_path.stat()
        
        return {
            'size': stat.st_size,
            'content_type': 'application/octet-stream',  # Local files don't have content type
            'last_modified': stat.st_mtime,
            'etag': str(stat.st_mtime)
        }
    
    async def get_presigned_url(self, object_key: str, expiry_hours: int = 1) -> Optional[str]:
        """
        Generate presigned URL for file download (S3 only).
        
        Args:
            object_key: S3 key
            expiry_hours: URL expiry time in hours
            
        Returns:
            Presigned URL or None if using local storage
        """
        if not self.use_s3:
            return None
        
        session = aioboto3.Session()
        
        async with session.client(
            's3',
            region_name=self.region
        ) as s3_client:
            try:
                url = await s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': object_key
                    },
                    ExpiresIn=int(timedelta(hours=expiry_hours).total_seconds())
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {object_key}: {str(e)}")
                return None


# Global storage service instance
storage_service = StorageService()
