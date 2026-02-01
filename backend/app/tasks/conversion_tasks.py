"""
Celery tasks for PDF conversion
Will be implemented in Phase 2 for async processing
"""
from app.tasks.celery_app import celery_app


@celery_app.task(name="convert_pdf_to_epub")
def convert_pdf_task(file_id: str, **kwargs):
    """
    Async task for PDF to EPUB conversion
    
    This will be implemented in Phase 2.
    For MVP, conversion is synchronous in the API endpoint.
    """
    # Placeholder for Phase 2 implementation
    pass
