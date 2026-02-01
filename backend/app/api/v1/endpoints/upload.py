"""
File upload endpoints
Handles PDF and document uploads
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.conversion_job import ConversionJob

router = APIRouter()


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    message: str


def get_upload_dir(user_id: Optional[str] = None) -> Path:
    """
    Create and return the upload directory path
    If user_id is provided, organize files by user
    """
    upload_path = Path(settings.STORAGE_PATH) / settings.UPLOAD_DIR
    if user_id:
        upload_path = upload_path / user_id
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for conversion
    
    - **file**: PDF file (max 50MB for authenticated users, 5MB for trial)
    
    Returns file_id to use for conversion
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Validate file size (different limits for authenticated vs trial)
    content = await file.read()
    file_size = len(content)
    
    max_size = settings.MAX_UPLOAD_SIZE if current_user else settings.TRIAL_MAX_UPLOAD_SIZE
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {max_size / 1024 / 1024:.0f}MB"
        )
    
    # Check storage quota for authenticated users
    if current_user:
        total_size = db.query(func.sum(ConversionJob.file_size)).filter(
            ConversionJob.user_id == current_user.id
        ).scalar() or 0
        
        if total_size + file_size > settings.USER_STORAGE_QUOTA:
            quota_mb = settings.USER_STORAGE_QUOTA / 1024 / 1024
            used_mb = total_size / 1024 / 1024
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Storage quota exceeded. You have used {used_mb:.1f}MB of {quota_mb:.0f}MB. Please delete some old conversions."
            )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Save file (organized by user if authenticated)
    user_id = str(current_user.id) if current_user else None
    upload_dir = get_upload_dir(user_id)
    file_path = upload_dir / f"{file_id}.pdf"
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        message="File uploaded successfully"
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete an uploaded file
    
    - **file_id**: UUID of the uploaded file
    """
    upload_dir = get_upload_dir()
    file_path = upload_dir / f"{file_id}.pdf"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "File deleted successfully"}
    )
