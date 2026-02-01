"""
Conversion endpoints
Handles PDF to EPUB conversion
"""
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import os
import shutil

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.converter import PDFConverter
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.conversion_job import ConversionJob, JobStatus

router = APIRouter()


class ConversionRequest(BaseModel):
    file_id: str = Field(..., description="File ID from upload")
    start_page: Optional[int] = Field(None, ge=1, description="Starting page number")
    max_pages: Optional[int] = Field(None, ge=1, le=500, description="Maximum pages to process")
    languages: Optional[str] = Field("English", description="Comma-separated list of languages")
    batch_multiplier: Optional[int] = Field(2, ge=1, le=4, description="GPU memory multiplier")
    extract_tables_as_images: Optional[bool] = Field(False, description="Extract tables as images instead of markdown (Marker v1.7.5+)")


class ConversionResponse(BaseModel):
    job_id: str
    file_id: str
    status: str
    message: str
    epub_url: Optional[str] = None


def get_file_path(file_id: str, user_id: Optional[str] = None) -> Path:
    """Get the path to uploaded file, checking user directory if authenticated"""
    upload_dir = Path(settings.STORAGE_PATH) / settings.UPLOAD_DIR
    
    if user_id:
        user_path = upload_dir / user_id / f"{file_id}.pdf"
        if user_path.exists():
            return user_path
    
    # Fall back to root upload dir (for trial users)
    return upload_dir / f"{file_id}.pdf"


def get_output_path(job_id: str, user_id: Optional[str] = None) -> Path:
    """Get the output path for EPUB, organized by user if authenticated"""
    output_dir = Path(settings.STORAGE_PATH) / settings.OUTPUT_DIR
    if user_id:
        output_dir = output_dir / user_id
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{job_id}.epub"


@router.post("", response_model=ConversionResponse, status_code=status.HTTP_202_ACCEPTED)
async def convert_pdf(
    request: ConversionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Convert uploaded PDF to EPUB format
    
    - **file_id**: UUID of the uploaded file
    - **start_page**: Optional starting page (default: 1)
    - **max_pages**: Optional max pages to process (default: all)
    - **languages**: Languages in document (default: English)
    - **batch_multiplier**: GPU memory multiplier (default: 2)
    
    Returns job_id to check conversion status
    """
    # Verify file exists
    user_id = str(current_user.id) if current_user else None
    pdf_path = get_file_path(request.file_id, user_id)
    
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found. Please upload the file first."
        )
    
    # Create database record for authenticated users
    job_id = None
    if current_user:
        conversion_job = ConversionJob(
            user_id=current_user.id,
            file_id=request.file_id,
            original_filename=pdf_path.name,
            file_size=pdf_path.stat().st_size,
            status=JobStatus.PROCESSING,
            start_page=request.start_page,
            max_pages=request.max_pages,
            languages=request.languages,
            batch_multiplier=request.batch_multiplier,
        )
        db.add(conversion_job)
        db.commit()
        db.refresh(conversion_job)
        job_id = str(conversion_job.id)
    
    # For MVP, we'll do synchronous conversion
    # In Phase 2, this will be a Celery task
    converter = PDFConverter()
    
    try:
        result = await converter.convert(
            file_id=request.file_id,
            pdf_path=pdf_path,
            start_page=request.start_page,
            max_pages=request.max_pages,
            languages=request.languages,
            batch_multiplier=request.batch_multiplier,
            extract_tables_as_images=request.extract_tables_as_images
        )
        
        # result contains {"job_id": job_id, "epub_path": epub_path}
        converter_job_id = result["job_id"]
        
        # For authenticated users, we already created a ConversionJob with database tracking
        # Update its status and move the EPUB to the user-organized location
        if current_user and job_id:
            # Move the generated EPUB to user-specific directory
            source_epub_path = Path(result["epub_path"])
            target_epub_path = get_output_path(job_id, user_id)
            
            if source_epub_path.exists():
                # Create target directory if needed
                target_epub_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_epub_path), str(target_epub_path))
            
            conversion_job.status = JobStatus.COMPLETED
            conversion_job.epub_filename = f"{job_id}.epub"
            conversion_job.processing_time = int((datetime.utcnow() - conversion_job.created_at).total_seconds())
            db.commit()
            
            final_job_id = job_id
        else:
            # For trial users, use the converter's job_id
            final_job_id = converter_job_id
        
        return ConversionResponse(
            job_id=final_job_id,
            file_id=request.file_id,
            status="completed",
            message="Conversion completed successfully",
            epub_url=f"/api/v1/convert/download/{final_job_id}"
        )
        
    except Exception as e:
        # Update job status for authenticated users
        if current_user and job_id:
            conversion_job.status = JobStatus.FAILED
            conversion_job.error_message = str(e)
            db.commit()
        
        import traceback
        error_trace = traceback.format_exc()
        print(f"CONVERSION ERROR: {str(e)}")
        print(f"FULL TRACEBACK:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_conversion_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get the status of a conversion job
    
    - **job_id**: UUID of the conversion job
    """
    # Try to get from database first (for authenticated users)
    if current_user:
        from uuid import UUID
        try:
            job = db.query(ConversionJob).filter(
                ConversionJob.id == UUID(job_id),
                ConversionJob.user_id == current_user.id
            ).first()
            
            if job:
                return {
                    "job_id": job_id,
                    "status": job.status.value,
                    "epub_url": f"/api/v1/convert/download/{job_id}" if job.status == JobStatus.COMPLETED else None
                }
        except:
            pass
    
    # Fall back to file system check (for trial users or if DB record not found)
    user_id = str(current_user.id) if current_user else None
    epub_path = get_output_path(job_id, user_id)
    
    if epub_path.exists():
        return {
            "job_id": job_id,
            "status": "completed",
            "epub_url": f"/api/v1/convert/download/{job_id}"
        }
    else:
        return {
            "job_id": job_id,
            "status": "processing",
            "epub_url": None
        }


@router.get("/download/{job_id}")
async def download_epub(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Download the converted EPUB file
    
    - **job_id**: UUID of the conversion job
    """
    user_id = str(current_user.id) if current_user else None
    epub_path = get_output_path(job_id, user_id)
    
    if not epub_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="EPUB file not found. Conversion may still be in progress."
        )
    
    return FileResponse(
        path=epub_path,
        media_type="application/epub+zip",
        filename=f"cleanread_{job_id}.epub"
    )


@router.get("/history")
async def get_conversion_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Get user's conversion history
    
    Requires authentication
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    jobs = db.query(ConversionJob).filter(
        ConversionJob.user_id == current_user.id
    ).order_by(
        ConversionJob.created_at.desc()
    ).limit(limit).all()
    
    return {
        "jobs": [
            {
                "id": str(job.id),
                "filename": job.original_filename,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "epub_url": f"/api/v1/convert/download/{job.id}" if job.status == JobStatus.COMPLETED else None,
                "file_size": job.file_size,
                "processing_time": job.processing_time,
            }
            for job in jobs
        ],
        "retention_notice": f"Files are automatically deleted after {settings.FILE_RETENTION_DAYS} days"
    }


@router.delete("/job/{job_id}")
async def delete_conversion(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversion job and associated files
    
    - **job_id**: UUID of the conversion job to delete
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Find the job
    job = db.query(ConversionJob).filter(
        ConversionJob.id == job_id,
        ConversionJob.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion job not found"
        )
    
    user_id = str(current_user.id)
    
    # Delete input file
    input_path = get_file_path(job.file_id, user_id)
    if input_path.exists():
        try:
            os.remove(input_path)
        except Exception:
            pass  # Continue even if input file deletion fails
    
    # Delete output file
    output_path = get_output_path(str(job.id), user_id)
    if output_path.exists():
        try:
            os.remove(output_path)
        except Exception:
            pass  # Continue even if output file deletion fails
    
    # Delete database record
    db.delete(job)
    db.commit()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Conversion deleted successfully"}
    )


def cleanup_old_files(db: Session):
    """
    Utility function to delete files older than retention period
    Can be called by a scheduled task or on startup
    """
    cutoff_date = datetime.utcnow() - timedelta(days=settings.FILE_RETENTION_DAYS)
    
    old_jobs = db.query(ConversionJob).filter(
        ConversionJob.created_at < cutoff_date
    ).all()
    
    deleted_count = 0
    for job in old_jobs:
        user_id = str(job.user_id)
        
        # Delete files
        input_path = get_file_path(job.file_id, user_id)
        if input_path.exists():
            try:
                os.remove(input_path)
            except Exception:
                pass
        
        output_path = get_output_path(str(job.id), user_id)
        if output_path.exists():
            try:
                os.remove(output_path)
            except Exception:
                pass
        
        # Delete database record
        db.delete(job)
        deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    return deleted_count
