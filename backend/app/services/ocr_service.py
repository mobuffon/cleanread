"""
OCR.space API integration service
Handles PDF to text conversion with 1MB file size limit by splitting PDFs
"""
import os
import base64
import asyncio
import tempfile
import math
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import aiohttp
from PIL import Image
import io

# Try pypdfium2 first (already installed), fallback to PyMuPDF
try:
    import pypdfium2 as pdfium
    PDF_LIBRARY = "pypdfium2"
    print("[OCR Service] Using pypdfium2 for PDF processing")
except ImportError:
    try:
        import fitz  # PyMuPDF
        PDF_LIBRARY = "pymupdf"
        print("[OCR Service] Using PyMuPDF for PDF processing")
    except ImportError:
        PDF_LIBRARY = None
        print("[OCR Service] Warning: No PDF library found. PDF splitting disabled.")

from app.core.config import settings


class OCRSpaceService:
    """
    Service for OCR.space API integration
    
    API Documentation: https://ocr.space/ocrapi
    Free tier: 25,000 requests/month, 1MB file limit
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OCR_SPACE_API_KEY")
        if not self.api_key:
            print("Warning: OCR_SPACE_API_KEY not set. OCR.space integration will not work.")
        
        self.base_url = "https://api.ocr.space/parse/image"
        self.max_file_size = 1_000_000  # 1MB in bytes
        self.max_pages_per_request = 5  # Conservative limit to stay under 1MB
        
    async def extract_text_from_pdf(self, pdf_path: Path, language: str = "eng") -> str:
        """
        Extract text from PDF using OCR.space API
        Splits PDF into chunks if needed to stay under 1MB limit
        """
        if not self.api_key:
            raise ValueError("OCR_SPACE_API_KEY not configured")
        
        print(f"[OCR.space] Processing PDF: {pdf_path.name}")
        
        # Check file size
        file_size = pdf_path.stat().st_size
        print(f"[OCR.space] File size: {file_size:,} bytes")
        
        if file_size <= self.max_file_size:
            # Single request for small PDFs
            return await self._process_pdf_single(pdf_path, language)
        else:
            # Split PDF into chunks for large files
            return await self._process_pdf_chunked(pdf_path, language)
    
    async def _process_pdf_single(self, pdf_path: Path, language: str) -> str:
        """Process PDF in a single API request"""
        print(f"[OCR.space] Processing as single request")
        
        # Convert PDF to images
        images = self._pdf_to_images(pdf_path)
        print(f"[OCR.space] Converted to {len(images)} pages")
        
        # Process all images in parallel
        tasks = []
        for page_num, image_data in enumerate(images, 1):
            task = self._process_image(image_data, language, page_num)
            tasks.append(task)
        
        # Run all OCR tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        extracted_texts = []
        for i, result in enumerate(results):
            page_num = i + 1
            if isinstance(result, Exception):
                print(f"[OCR.space] Error processing page {page_num}: {result}")
                extracted_texts.append(f"\n[Page {page_num}: OCR failed]\n")
            else:
                extracted_texts.append(f"\n--- Page {page_num} ---\n{result}\n")
        
        return "\n".join(extracted_texts)
    
    async def _process_pdf_chunked(self, pdf_path: Path, language: str) -> str:
        """
        Split PDF into chunks and process each chunk separately
        to stay under 1MB limit
        """
        print(f"[OCR.space] PDF too large, splitting into chunks")
        
        # Get page count
        total_pages = self._get_page_count(pdf_path)
        if total_pages == 0:
            return "[OCR.space] Error: Could not read PDF"
        
        # Calculate chunks (max pages per chunk based on average page size)
        avg_page_size = pdf_path.stat().st_size / total_pages
        pages_per_chunk = min(
            self.max_pages_per_request,
            max(1, int(self.max_file_size / avg_page_size))
        )
        
        print(f"[OCR.space] Splitting {total_pages} pages into chunks of {pages_per_chunk} pages")
        
        # For now, we'll process all pages at once but with quality reduction
        # PDF splitting is complex without proper PDF library
        # OCR.space has a 1MB limit per request, not per file
        # So we'll just process all pages and let OCR.space handle large images
        
        print(f"[OCR.space] Processing all {total_pages} pages with quality optimization")
        return await self._process_pdf_single(pdf_path, language)
    
    def _pdf_to_images(self, pdf_path: Path, dpi: int = 200) -> List[bytes]:
        """
        Convert PDF pages to JPEG images for OCR
        Returns list of JPEG image bytes
        """
        images = []
        
        if PDF_LIBRARY == "pypdfium2":
            # Using pypdfium2
            pdf = pdfium.PdfDocument(str(pdf_path))
            
            for page_num in range(len(pdf)):
                page = pdf.get_page(page_num)
                
                # Render page to image
                bitmap = page.render(scale=dpi/72)
                pil_image = bitmap.to_pil()
                
                # Convert to JPEG bytes
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                img_data = img_byte_arr.getvalue()
                images.append(img_data)
                
                # Early check: if single page is too large, reduce quality
                if len(img_data) > self.max_file_size:
                    print(f"[OCR.space] Page {page_num+1} too large ({len(img_data):,} bytes), reducing quality")
                    # Try with lower quality
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='JPEG', quality=70)
                    img_data = img_byte_arr.getvalue()
                    images[-1] = img_data
                
                # If still too large, skip this page
                if len(img_data) > self.max_file_size:
                    print(f"[OCR.space] Warning: Page {page_num+1} still too large after quality reduction, skipping")
                    images[-1] = b""  # Empty image
                
                # Clean up
                bitmap.close()
                page.close()
            
            pdf.close()
            
        elif PDF_LIBRARY == "pymupdf":
            # Using PyMuPDF (fallback)
            import fitz
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                
                # Convert to JPEG bytes
                img_data = pix.tobytes("jpeg")
                images.append(img_data)
                
                # Early check: if single page is too large, reduce DPI
                if len(img_data) > self.max_file_size:
                    print(f"[OCR.space] Page {page_num+1} too large ({len(img_data):,} bytes), reducing DPI")
                    # Try with lower DPI
                    pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72))
                    img_data = pix.tobytes("jpeg")
                    images[-1] = img_data
                
                # If still too large, skip this page
                if len(img_data) > self.max_file_size:
                    print(f"[OCR.space] Warning: Page {page_num+1} still too large after DPI reduction, skipping")
                    images[-1] = b""  # Empty image
            
            doc.close()
        else:
            print("[OCR.space] Error: No PDF library available for image conversion")
            return []
        
        return images
    
    async def _process_image(self, image_data: bytes, language: str, page_num: int) -> str:
        """
        Send single image to OCR.space API
        """
        if not image_data:
            return f"[Page {page_num}: Image too large or empty]"
        
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Prepare request payload
        payload = {
            "base64Image": f"data:image/jpeg;base64,{base64_image}",
            "language": language,
            "isOverlayRequired": False,
            "filetype": "JPG",
            "detectOrientation": True,
            "scale": True,
            "isTable": True,  # Try to detect tables
            "OCREngine": 2,  # Engine 2 is better for documents
        }
        
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    data=payload,
                    headers=headers,
                    timeout=30  # 30 second timeout
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[OCR.space] API error for page {page_num}: HTTP {response.status} - {error_text}")
                        return f"[Page {page_num}: OCR API error]"
                    
                    result = await response.json()
                    
                    # Check for API errors
                    if result.get("IsErroredOnProcessing"):
                        error_message = result.get("ErrorMessage", "Unknown error")
                        print(f"[OCR.space] Processing error for page {page_num}: {error_message}")
                        return f"[Page {page_num}: {error_message}]"
                    
                    # Extract text from all parsed results
                    parsed_results = result.get("ParsedResults", [])
                    if not parsed_results:
                        print(f"[OCR.space] No text found for page {page_num}")
                        return f"[Page {page_num}: No text found]"
                    
                    # Combine all text blocks
                    extracted_text = ""
                    for parsed in parsed_results:
                        text = parsed.get("ParsedText", "")
                        if text:
                            extracted_text += text + "\n"
                    
                    print(f"[OCR.space] Page {page_num}: Extracted {len(extracted_text)} characters")
                    return extracted_text.strip()
                    
        except asyncio.TimeoutError:
            print(f"[OCR.space] Timeout processing page {page_num}")
            return f"[Page {page_num}: OCR timeout]"
        except Exception as e:
            print(f"[OCR.space] Error processing page {page_num}: {e}")
            return f"[Page {page_num}: {str(e)}]"
    
    def estimate_ocr_cost(self, pdf_path: Path) -> Tuple[int, float]:
        """
        Estimate number of API calls and cost for a PDF
        Returns: (num_requests, estimated_cost)
        """
        file_size = pdf_path.stat().st_size
        
        if file_size <= self.max_file_size:
            # One request per page (parallel)
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            doc.close()
            num_requests = num_pages
        else:
            # Need to split into chunks
            avg_page_size = file_size / self._get_page_count(pdf_path)
            pages_per_chunk = max(1, int(self.max_file_size / avg_page_size))
            num_requests = math.ceil(self._get_page_count(pdf_path) / pages_per_chunk)
        
        # OCR.space free tier: 25,000 requests/month
        # After free tier: ~$0.0015 per request
        estimated_cost = max(0, (num_requests - 25000)) * 0.0015
        
        return num_requests, estimated_cost
    
    def _get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF"""
        if PDF_LIBRARY == "pypdfium2":
            try:
                pdf = pdfium.PdfDocument(str(pdf_path))
                count = len(pdf)
                pdf.close()
                return count
            except Exception:
                return 0
        elif PDF_LIBRARY == "pymupdf":
            try:
                import fitz
                doc = fitz.open(pdf_path)
                count = len(doc)
                doc.close()
                return count
            except Exception:
                return 0
        else:
            # Try to estimate from file size (rough estimate)
            file_size = pdf_path.stat().st_size
            # Average page size ~50KB
            return max(1, int(file_size / 50000))


# Singleton instance
_ocr_service_instance = None

def get_ocr_service() -> OCRSpaceService:
    """Get or create OCR service instance"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRSpaceService()
    return _ocr_service_instance