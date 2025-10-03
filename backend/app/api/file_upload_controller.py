"""
File Upload API Controller - handles file uploads for menu items and other assets
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.storage.s3_service import S3Service

router = APIRouter(prefix="/api/admin/upload", tags=["admin-upload"])


@router.post("/image", status_code=status.HTTP_201_CREATED)
@inject
async def upload_menu_item_image(
    file: UploadFile = File(...),
    restaurant_id: int = Form(...),
    s3_service: S3Service = Depends(Provide[Container.s3_service])
) -> Dict[str, Any]:
    """
    Upload a menu item image
    
    Args:
        file: Image file to upload
        restaurant_id: Restaurant ID for organization
        s3_service: Injected S3 service
        
    Returns:
        Upload result with S3 URL and metadata
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed for menu item images"
            )
        
        # Read file data
        file_data = await file.read()
        
        if len(file_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Upload to S3
        result = await s3_service.upload_menu_item_image(
            file_data=file_data,
            file_name=file.filename,
            restaurant_id=restaurant_id,
            content_type=file.content_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {result['error']}"
            )
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "file_id": result["file_id"],
            "original_name": result["original_name"],
            "s3_url": result["s3_url"],
            "s3_key": result["s3_key"],
            "size": result["size"],
            "content_type": result["content_type"],
            "restaurant_id": result["restaurant_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@inject
async def upload_file(
    file: UploadFile = File(...),
    restaurant_id: int = Form(...),
    file_type: str = Form("documents"),
    s3_service: S3Service = Depends(Provide[Container.s3_service])
) -> Dict[str, Any]:
    """
    Upload any file type
    
    Args:
        file: File to upload
        restaurant_id: Restaurant ID for organization
        file_type: Type of file (images, audio, documents, etc.)
        s3_service: Injected S3 service
        
    Returns:
        Upload result with S3 URL and metadata
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Read file data
        file_data = await file.read()
        
        if len(file_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Upload to S3
        result = await s3_service.upload_file(
            file_data=file_data,
            file_name=file.filename,
            restaurant_id=restaurant_id,
            file_type=file_type,
            content_type=file.content_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {result['error']}"
            )
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_id": result["file_id"],
            "original_name": result["original_name"],
            "s3_url": result["s3_url"],
            "s3_key": result["s3_key"],
            "size": result["size"],
            "content_type": result["content_type"],
            "restaurant_id": result["restaurant_id"],
            "file_type": result["file_type"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.delete("/delete")
@inject
async def delete_file(
    s3_key: str,
    s3_service: S3Service = Depends(Provide[Container.s3_service])
) -> Dict[str, Any]:
    """
    Delete a file from S3
    
    Args:
        s3_key: S3 key of the file to delete
        s3_service: Injected S3 service
        
    Returns:
        Deletion result
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        result = await s3_service.delete_file(s3_key)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Delete failed: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/list")
@inject
async def list_files(
    restaurant_id: int,
    file_type: str = "images",
    s3_service: S3Service = Depends(Provide[Container.s3_service])
) -> Dict[str, Any]:
    """
    List files for a restaurant and file type
    
    Args:
        restaurant_id: Restaurant ID
        file_type: Type of files to list (images, audio, documents, etc.)
        s3_service: Injected S3 service
        
    Returns:
        List of files
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        result = await s3_service.list_files(restaurant_id, file_type)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"List failed: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )
