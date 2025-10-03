"""
S3 Service for file storage - handles menu item images and other file uploads
"""

import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

try:
    from botocore.exceptions import ClientError
except ImportError:
    # For testing when boto3 is not available
    class ClientError(Exception):
        def __init__(self, response, operation):
            self.response = response
            super().__init__(f"ClientError: {response}")

logger = logging.getLogger(__name__)


class S3Service:
    """
    AWS S3 file storage service for menu item images and other uploads
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", endpoint_url: str = None):
        """
        Initialize S3 service
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint URL (for LocalStack, MinIO, etc.)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.endpoint_url = endpoint_url
        
        # Initialize boto3 S3 client
        try:
            import boto3
            
            client_kwargs = {'region_name': region}
            if endpoint_url:
                client_kwargs['endpoint_url'] = endpoint_url
                
            self.s3_client = boto3.client('s3', **client_kwargs)
            
            logger.info(f"S3 service initialized - Bucket: {bucket_name}, Region: {region}")
            if endpoint_url:
                logger.info(f"Custom endpoint: {endpoint_url}")
                
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    async def ensure_bucket_exists(self) -> bool:
        """
        Ensure the S3 bucket exists, create if it doesn't
        
        Returns:
            bool: True if bucket exists or was created successfully
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' exists")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    # Create bucket
                    if self.region == "us-east-1":
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Created S3 bucket '{self.bucket_name}' in region '{self.region}'")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to create S3 bucket '{self.bucket_name}': {e}")
                    return False
                
        except Exception as e:
            logger.error(f"Error checking S3 bucket '{self.bucket_name}': {e}")
            return False
    
    async def upload_menu_item_image(
        self, 
        file_data: bytes, 
        file_name: str, 
        restaurant_id: int,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a menu item image to S3
        
        Args:
            file_data: Image file data
            file_name: Original file name
            restaurant_id: Restaurant ID for organization
            content_type: MIME type (auto-detected if not provided)
            
        Returns:
            Dict with upload result including S3 URL and key
        """
        try:
            # Ensure bucket exists
            await self.ensure_bucket_exists()
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = 'image/png'  # Default fallback
            
            # Validate content type
            if not content_type.startswith('image/'):
                return {
                    "success": False,
                    "error": f"Invalid file type: {content_type}. Only images are allowed."
                }
            
            # Generate unique file ID for metadata
            file_id = str(uuid.uuid4())
            
            # Create organized S3 key structure for menu item images
            s3_key = f"restaurants/{restaurant_id}/images/{file_name}"
            
            # Upload to S3
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    "original_name": file_name,
                    "file_id": file_id,
                    "restaurant_id": str(restaurant_id),
                    "upload_type": "menu_item_image"
                }
            )
            
            # Generate S3 URL
            if self.endpoint_url:
                # For LocalStack/MinIO
                s3_url = f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                # For AWS S3
                s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            # Return success result
            result = {
                "success": True,
                "file_id": file_id,
                "original_name": file_name,
                "content_type": content_type,
                "size": len(file_data),
                "s3_key": s3_key,
                "s3_url": s3_url,
                "uploaded_at": datetime.now().isoformat(),
                "restaurant_id": restaurant_id
            }
            
            logger.info(f"Successfully uploaded menu item image: {file_name} to {s3_key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload menu item image {file_name}: {e}")
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def upload_file(
        self, 
        file_data: bytes, 
        file_name: str, 
        restaurant_id: int,
        file_type: str = "general",
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload any file to S3 with organized structure
        
        Args:
            file_data: File data
            file_name: Original file name
            restaurant_id: Restaurant ID for organization
            file_type: Type of file (images, audio, documents, etc.)
            content_type: MIME type (auto-detected if not provided)
            
        Returns:
            Dict with upload result
        """
        try:
            # Ensure bucket exists
            await self.ensure_bucket_exists()
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = 'application/octet-stream'  # Default fallback
            
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Create organized S3 key structure
            s3_key = f"restaurants/{restaurant_id}/{file_type}/{file_name}"
            
            # Upload to S3
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    "original_name": file_name,
                    "file_id": file_id,
                    "restaurant_id": str(restaurant_id),
                    "upload_type": file_type
                }
            )
            
            # Generate S3 URL
            if self.endpoint_url:
                s3_url = f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            # Return success result
            result = {
                "success": True,
                "file_id": file_id,
                "original_name": file_name,
                "content_type": content_type,
                "size": len(file_data),
                "s3_key": s3_key,
                "s3_url": s3_url,
                "uploaded_at": datetime.now().isoformat(),
                "restaurant_id": restaurant_id,
                "file_type": file_type
            }
            
            logger.info(f"Successfully uploaded file: {file_name} to {s3_key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_name}: {e}")
            return {
                "success": False,
                "error": f"Upload failed: {str(e)}"
            }
    
    async def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete a file from S3
        
        Args:
            s3_key: S3 key of the file to delete
            
        Returns:
            Dict with deletion result
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return {
                "success": True,
                "message": f"File deleted successfully: {s3_key}"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete file {s3_key}: {e}")
            return {
                "success": False,
                "error": f"Delete failed: {str(e)}"
            }
    
    async def get_file_url(self, s3_key: str) -> str:
        """
        Get the public URL for an S3 object
        
        Args:
            s3_key: S3 key of the file
            
        Returns:
            str: Public URL of the file
        """
        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
        else:
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
    
    async def list_files(self, restaurant_id: int, file_type: str = "images") -> Dict[str, Any]:
        """
        List files for a restaurant and file type
        
        Args:
            restaurant_id: Restaurant ID
            file_type: Type of files to list (images, audio, etc.)
            
        Returns:
            Dict with list of files
        """
        try:
            prefix = f"restaurants/{restaurant_id}/{file_type}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_url = await self.get_file_url(obj['Key'])
                    # Handle LastModified - it might be a datetime object or string
                    last_modified = obj['LastModified']
                    if hasattr(last_modified, 'isoformat'):
                        last_modified = last_modified.isoformat()
                    elif isinstance(last_modified, str):
                        last_modified = last_modified  # Already a string
                    else:
                        last_modified = str(last_modified)
                    
                    files.append({
                        "key": obj['Key'],
                        "url": file_url,
                        "size": obj['Size'],
                        "last_modified": last_modified
                    })
            
            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
            
        except Exception as e:
            logger.error(f"Failed to list files for restaurant {restaurant_id}: {e}")
            return {
                "success": False,
                "error": f"List failed: {str(e)}",
                "files": [],
                "count": 0
            }