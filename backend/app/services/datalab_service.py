"""
DataLab Marker API integration for PDF to Markdown conversion.
Uses https://documentation.datalab.to/docs/recipes/marker/conversion-api-overview
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Tuple
import base64
import json

import requests


class DatalabConverter:
    """
    PDF to Markdown converter using DataLab's Marker API.
    
    Advantages over local marker-pdf:
    - No GPU required
    - Better handling of complex layouts
    - Cloud-based processing (scalable)
    - Support for multiple output formats (markdown, html, json)
    - Built-in image extraction and captioning
    - Better table recognition
    """
    
    def __init__(self):
        """Initialize DataLab client"""
        self.api_key = os.getenv("DATALAB_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DATALAB_API_KEY environment variable not set. "
                "Get an API key at https://www.datalab.to/auth/sign_up"
            )
        
        self.api_base = "https://www.datalab.to/api/v1/marker"

    async def convert_pdf_to_markdown(
        self,
        pdf_path: Path,
        mode: str = "balanced",
        max_pages: Optional[int] = None,
        page_range: Optional[str] = None,
        extract_images: bool = True,
        image_captions: bool = True,
        extract_tables_as_images: bool = False,
    ) -> Tuple[str, Dict[str, bytes], Dict]:
        """
        Convert PDF to Markdown using DataLab Marker API.
        
        Args:
            pdf_path: Path to the PDF file
            mode: Processing mode - "fast", "balanced" (default), or "accurate"
            max_pages: Maximum pages to process (None = all)
            page_range: Specific pages to process (e.g., "0-5,10", 0-indexed)
            extract_images: Whether to extract images
            image_captions: Whether to generate image captions
            extract_tables_as_images: FUTURE - Not yet supported by REST API (local Marker only)
        
        Returns:
            Tuple of:
            - markdown: Converted markdown text (tables as HTML by default)
            - images: Dict of {filename: binary_data}
              - Regular images (with captions in markdown)
              - Table as HTML (not images - REST API limitation)
            - metadata: Conversion metadata (quality score, page count, etc.)
            
        NOTE: DataLab REST API doesn't support block_relabel_str parameter yet.
              Tables/equations come as HTML/Markdown by default.
              Local Marker SDK supports this via block_relabel_str config.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"[DataLab] Converting {pdf_path.name} ({mode} mode)")
        
        return await self._convert_with_rest_api(
            pdf_path,
            mode=mode,
            max_pages=max_pages,
            page_range=page_range,
            extract_images=extract_images,
            image_captions=image_captions,
            extract_tables_as_images=extract_tables_as_images,
        )

    async def _convert_with_rest_api(
        self,
        pdf_path: Path,
        mode: str = "balanced",
        max_pages: Optional[int] = None,
        page_range: Optional[str] = None,
        extract_images: bool = True,
        image_captions: bool = True,
        extract_tables_as_images: bool = False,
    ) -> Tuple[str, Dict[str, bytes], Dict]:
        """Convert using REST API"""
        loop = asyncio.get_event_loop()
        
        def _submit_request():
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {
                    "output_format": "markdown",
                    "mode": mode,
                    "disable_image_extraction": not extract_images,
                    "disable_image_captions": not image_captions,
                }
                
                if max_pages:
                    data["max_pages"] = max_pages
                if page_range:
                    data["page_range"] = page_range
                
                # NOTE: DataLab REST API does not support block_relabel_str parameter
                # This is only available in the local Marker SDK (v1.7.5+)
                # Tables/equations will be returned as HTML/Markdown, not images
                # The extract_tables_as_images flag is kept for future compatibility
                # if DataLab adds support to their REST API
                
                headers = {"X-API-Key": self.api_key}
                
                print(f"[DataLab] Submitting conversion request...")
                if extract_tables_as_images:
                    print(f"[DataLab] Note: extract_tables_as_images not supported by REST API yet (local Marker only)")
                
                response = requests.post(
                    self.api_base,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30,
                )
                
                if response.status_code != 200:
                    raise Exception(f"Request submission failed: {response.text}")
                
                result = response.json()
                return result["request_check_url"]
        
        # Submit request
        check_url = await loop.run_in_executor(None, _submit_request)
        
        # Poll for completion
        headers = {"X-API-Key": self.api_key}
        max_wait = 300  # 5 minutes
        poll_interval = 2
        elapsed = 0
        
        print(f"[DataLab] Polling for results... (timeout: {max_wait}s)")
        
        def _poll():
            return requests.get(check_url, headers=headers, timeout=30).json()
        
        while elapsed < max_wait:
            result = await loop.run_in_executor(None, _poll)
            
            if result["status"] == "complete":
                print(f"[DataLab] Conversion complete!")
                
                # Decode images from base64
                images = {}
                if result.get("images"):
                    print(f"[DataLab] Found {len(result['images'])} images")
                    for filename, base64_data in result["images"].items():
                        images[filename] = base64.b64decode(base64_data)
                        print(f"[DataLab] - Decoded image: {filename}")
                else:
                    print(f"[DataLab] No images found in response")
                
                metadata = {
                    "page_count": result.get("page_count"),
                    "parse_quality_score": result.get("parse_quality_score"),
                    "cost_cents": result.get("cost_breakdown", {}).get("total_cents"),
                }
                
                print(f"[DataLab] Quality: {metadata['parse_quality_score']}/5.0, Pages: {metadata['page_count']}")
                
                return result.get("markdown", ""), images, metadata
            
            elif result["status"] == "failed":
                error_msg = result.get("error", "Unknown error")
                raise Exception(f"DataLab conversion failed: {error_msg}")
            
            # Still processing
            if elapsed % 10 == 0:  # Only log every 10 seconds
                print(f"[DataLab] Processing... ({elapsed}s)")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"DataLab conversion timed out after {max_wait} seconds")

    async def convert_with_options(
        self,
        pdf_path: Path,
        options: Dict,
    ) -> Tuple[str, Dict[str, bytes], Dict]:
        """
        Convert PDF with advanced options.
        
        Supported options:
        - mode: "fast", "balanced", "accurate"
        - max_pages: int
        - page_range: "0-5,10,15-20"
        - extract_images: bool
        - image_captions: bool
        - extract_tables_as_images: bool (requires Marker v1.7.5+)
        - keep_spreadsheet_formatting: bool
        - keep_pageheader_in_output: bool
        - keep_pagefooter_in_output: bool
        """
        return await self.convert_pdf_to_markdown(
            pdf_path,
            mode=options.get("mode", "balanced"),
            max_pages=options.get("max_pages"),
            page_range=options.get("page_range"),
            extract_images=options.get("extract_images", True),
            image_captions=options.get("image_captions", True),
            extract_tables_as_images=options.get("extract_tables_as_images", False),
        )


# Singleton instance
_datalab_converter = None


def get_datalab_converter() -> DatalabConverter:
    """Get or create DataLab converter singleton"""
    global _datalab_converter
    if _datalab_converter is None:
        _datalab_converter = DatalabConverter()
    return _datalab_converter
