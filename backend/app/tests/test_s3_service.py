"""
Unit tests for S3Service - file storage service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.storage.s3_service import S3Service


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 S3 client for testing"""
    mock_client = Mock()
    mock_client.head_bucket.return_value = {}  # Bucket exists
    mock_client.put_object.return_value = {"ETag": "test-etag"}
    mock_client.delete_object.return_value = {}
    mock_client.list_objects_v2.return_value = {"Contents": []}
    return mock_client


@pytest.fixture
def s3_service(mock_boto3_client):
    """Fixture for S3Service with mocked boto3 client"""
    with patch('boto3.client') as mock_boto3_client_func:
        mock_boto3_client_func.return_value = mock_boto3_client
        service = S3Service(
            bucket_name="test-bucket",
            region="us-east-1",
            endpoint_url="http://localhost:4566"
        )
        return service


class TestS3Service:
    """Test S3Service operations"""

    def test_initialization(self, s3_service):
        """Test S3Service initialization"""
        assert s3_service.bucket_name == "test-bucket"
        assert s3_service.region == "us-east-1"
        assert s3_service.endpoint_url == "http://localhost:4566"
        assert s3_service.s3_client is not None

    async def test_ensure_bucket_exists_success(self, s3_service, mock_boto3_client):
        """Test bucket exists check when bucket exists"""
        result = await s3_service.ensure_bucket_exists()
        
        assert result is True
        mock_boto3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")

    async def test_ensure_bucket_exists_create_new(self, s3_service, mock_boto3_client):
        """Test bucket creation when bucket doesn't exist"""
        # Mock bucket doesn't exist
        from botocore.exceptions import ClientError
        mock_boto3_client.head_bucket.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}}, 
            'HeadBucket'
        )
        
        result = await s3_service.ensure_bucket_exists()
        
        assert result is True
        mock_boto3_client.create_bucket.assert_called_once_with(Bucket="test-bucket")

    async def test_upload_menu_item_image_success(self, s3_service, mock_boto3_client):
        """Test successful menu item image upload"""
        file_data = b"fake image data"
        file_name = "test_image.png"
        restaurant_id = 1
        
        result = await s3_service.upload_menu_item_image(
            file_data=file_data,
            file_name=file_name,
            restaurant_id=restaurant_id
        )
        
        assert result["success"] is True
        assert result["original_name"] == file_name
        assert result["restaurant_id"] == restaurant_id
        assert result["s3_key"] == f"restaurants/{restaurant_id}/images/{file_name}"
        assert "s3_url" in result
        assert "file_id" in result
        
        # Verify S3 put_object was called correctly
        mock_boto3_client.put_object.assert_called_once()
        call_args = mock_boto3_client.put_object.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == f"restaurants/{restaurant_id}/images/{file_name}"
        assert call_args[1]["Body"] == file_data
        assert call_args[1]["ContentType"] == "image/png"

    async def test_upload_menu_item_image_invalid_type(self, s3_service, mock_boto3_client):
        """Test menu item image upload with invalid file type"""
        file_data = b"fake data"
        file_name = "test.txt"
        restaurant_id = 1
        
        result = await s3_service.upload_menu_item_image(
            file_data=file_data,
            file_name=file_name,
            restaurant_id=restaurant_id,
            content_type="text/plain"
        )
        
        assert result["success"] is False
        assert "Invalid file type" in result["error"]

    async def test_upload_file_success(self, s3_service, mock_boto3_client):
        """Test successful file upload"""
        file_data = b"fake file data"
        file_name = "test_document.pdf"
        restaurant_id = 1
        file_type = "documents"
        
        result = await s3_service.upload_file(
            file_data=file_data,
            file_name=file_name,
            restaurant_id=restaurant_id,
            file_type=file_type
        )
        
        assert result["success"] is True
        assert result["original_name"] == file_name
        assert result["restaurant_id"] == restaurant_id
        assert result["file_type"] == file_type
        assert result["s3_key"] == f"restaurants/{restaurant_id}/{file_type}/{file_name}"

    async def test_delete_file_success(self, s3_service, mock_boto3_client):
        """Test successful file deletion"""
        s3_key = "restaurants/1/images/test.png"
        
        result = await s3_service.delete_file(s3_key)
        
        assert result["success"] is True
        mock_boto3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=s3_key
        )

    async def test_get_file_url(self, s3_service):
        """Test file URL generation"""
        s3_key = "restaurants/1/images/test.png"
        
        # Test with endpoint URL (LocalStack/MinIO)
        url = await s3_service.get_file_url(s3_key)
        expected_url = f"{s3_service.endpoint_url}/test-bucket/{s3_key}"
        assert url == expected_url

    async def test_get_file_url_aws(self):
        """Test file URL generation for AWS S3"""
        with patch('boto3.client'):
            service = S3Service(
                bucket_name="test-bucket",
                region="us-east-1"
                # No endpoint_url for AWS
            )
            
            s3_key = "restaurants/1/images/test.png"
            url = await service.get_file_url(s3_key)
            expected_url = f"https://test-bucket.s3.us-east-1.amazonaws.com/{s3_key}"
            assert url == expected_url

    async def test_list_files_success(self, s3_service, mock_boto3_client):
        """Test successful file listing"""
        restaurant_id = 1
        file_type = "images"
        
        # Mock S3 response with files
        mock_files = [
            {
                "Key": f"restaurants/{restaurant_id}/images/image1.png",
                "Size": 1024,
                "LastModified": "2024-01-01T00:00:00Z"
            },
            {
                "Key": f"restaurants/{restaurant_id}/images/image2.jpg",
                "Size": 2048,
                "LastModified": "2024-01-02T00:00:00Z"
            }
        ]
        mock_boto3_client.list_objects_v2.return_value = {"Contents": mock_files}
        
        result = await s3_service.list_files(restaurant_id, file_type)
        
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["files"]) == 2
        assert "url" in result["files"][0]
        assert "key" in result["files"][0]

    async def test_list_files_empty(self, s3_service, mock_boto3_client):
        """Test file listing when no files exist"""
        restaurant_id = 1
        file_type = "images"
        
        # Mock empty S3 response
        mock_boto3_client.list_objects_v2.return_value = {}
        
        result = await s3_service.list_files(restaurant_id, file_type)
        
        assert result["success"] is True
        assert result["count"] == 0
        assert result["files"] == []

    async def test_error_handling_upload_failure(self, s3_service, mock_boto3_client):
        """Test error handling during upload failure"""
        # Mock S3 client to raise exception
        mock_boto3_client.put_object.side_effect = Exception("S3 upload failed")
        
        result = await s3_service.upload_menu_item_image(
            file_data=b"test",
            file_name="test.png",
            restaurant_id=1
        )
        
        assert result["success"] is False
        assert "Upload failed" in result["error"]

    async def test_error_handling_delete_failure(self, s3_service, mock_boto3_client):
        """Test error handling during delete failure"""
        # Mock S3 client to raise exception
        mock_boto3_client.delete_object.side_effect = Exception("S3 delete failed")
        
        result = await s3_service.delete_file("test-key")
        
        assert result["success"] is False
        assert "Delete failed" in result["error"]
