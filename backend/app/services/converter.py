"""
PDF to EPUB conversion service using DataLab Marker API.

DataLab handles:
- PDF parsing and layout detection
- Text extraction (OCR)
- Image extraction with captions
- Table extraction (as images or markdown)
- Equation/formula recognition
- All visual content processing

Post-processing:
- Render equations (>6 chars) as matplotlib PNG images
- Keep short equations (<= 6 chars) as italic inline text
"""

import os
import shutil
import uuid
import re
from pathlib import Path
from typing import Dict
from datetime import datetime

import markdown
from ebooklib import epub
from bs4 import BeautifulSoup

from app.core.config import settings

# Import DataLab service for PDF to Markdown
try:
    from .datalab_service import get_datalab_converter
    DATALAB_AVAILABLE = True
except Exception as e:
    DATALAB_AVAILABLE = False
    print(f"Warning: DataLab service not available: {e}")

# Matplotlib for equation rendering
try:
    import matplotlib
    matplotlib.use('Agg')  # Headless mode
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PDFConverter:
    """
    Clean EPUB converter using DataLab Marker API for all PDF processing.
    
    DataLab Marker API handles:
    - Text extraction (OCR)
    - Table extraction (optionally as images via block_relabel_str)
    - Image extraction with captions
    - Equation recognition
    - Complex layout handling
    - Quality scoring
    """
    
    def __init__(self):
        self.output_dir = Path(settings.STORAGE_PATH) / settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize DataLab converter
        self.datalab = None
        if DATALAB_AVAILABLE:
            try:
                self.datalab = get_datalab_converter()
                print("[PDFConverter] DataLab API initialized")
            except Exception as e:
                print(f"[PDFConverter] DataLab not available: {e}")
                self.datalab = None

    async def convert(self, file_id: str, pdf_path: Path, **kwargs) -> Dict[str, str]:
        """
        Convert PDF to EPUB using DataLab Marker API.
        
        Options:
        - extract_tables_as_images: FUTURE - Not yet supported (REST API limitation)
        - mode: "fast", "balanced" (default), or "accurate"
        - max_pages: Limit pages to process
        
        NOTE: DataLab REST API limitation - tables/equations come as HTML/Markdown.
              Tables as images is only supported in local Marker SDK (v1.7.5+).
        """
        job_id = str(uuid.uuid4())
        work_dir = self.output_dir / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        epub_path = self.output_dir / f"{job_id}.epub"
        
        try:
            # Require DataLab API (cloud-based, no GPU needed)
            if not self.datalab:
                raise Exception("DataLab API is not available. Please try again later.")
            
            print(f"[{job_id}] Converting with DataLab Marker API...")
            print(f"[{job_id}] Options: extract_tables_as_images={kwargs.get('extract_tables_as_images', False)}, mode={kwargs.get('mode', 'balanced')}")
            
            # DataLab handles ALL processing:
            # - PDF parsing
            # - Text extraction (OCR)
            # - Image extraction with captions
            # - Tables (as images if requested via block_relabel_str)
            # - Equations
            # - Layout detection
            markdown_content, images, metadata = await self.datalab.convert_pdf_to_markdown(
                pdf_path,
                mode=kwargs.get("mode", "balanced"),
                max_pages=kwargs.get("max_pages"),
                extract_images=True,
                extract_tables_as_images=kwargs.get("extract_tables_as_images", False),
                image_captions=True
            )
            
            print(f"[{job_id}] DataLab conversion complete:")
            print(f"  - Quality: {metadata.get('parse_quality_score', 'N/A')}/5.0")
            print(f"  - Pages: {metadata.get('page_count', 'N/A')}")
            print(f"  - Images (including table images): {len(images)}")
            
            # Validate markdown content
            if not markdown_content or not markdown_content.strip():
                raise Exception("DataLab returned empty markdown content")
            
            # Add title if not present
            if not markdown_content.startswith('#'):
                markdown_content = f"# {pdf_path.stem}\n\n{markdown_content}"
            
            # Save images to work_dir
            images_dir = work_dir / "images"
            images_dir.mkdir(exist_ok=True)
            for img_name, img_data in images.items():
                img_path = images_dir / img_name
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                print(f"[{job_id}] Saved image: {img_name}")

            print(f"[{job_id}] Processing visuals (equations)...")
            final_md = self._process_equations(markdown_content, work_dir)

            # Path Normalization
            final_md = self._fix_image_paths(final_md)

            # Build EPUB
            print(f"[{job_id}] Building EPUB...")
            self._create_epub(final_md, epub_path, pdf_path.stem, images_dir)
            
            print(f"[{job_id}] ✅ EPUB created: {epub_path}")
            return {"job_id": job_id, "epub_path": str(epub_path)}

        except Exception as e:
            print(f"[{job_id}] ❌ Conversion failed: {e}")
            if work_dir.exists():
                shutil.rmtree(work_dir)
            raise e

    def _process_equations(self, text: str, work_dir: Path) -> str:
        """
        Process equations:
        - Equations > 6 characters: render as PNG images
        - Equations <= 6 characters: keep as italic inline text
        """
        if not MATPLOTLIB_AVAILABLE:
            return text
        
        images_dir = work_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        eq_count = {'block': 0, 'inline': 0, 'rendered': 0}
        
        # Process block equations ($$...$$) FIRST - use DOTALL for newlines
        def replace_block_equation(match):
            latex = match.group(1).strip()
            eq_count['block'] += 1
            
            if len(latex) <= 6:
                print(f"[Equations] Block eq (short): {latex}")
                return f'\n\n*{latex}*\n\n'
            
            print(f"[Equations] Block eq (long, rendering): {latex[:50]}...")
            img_name = self._render_equation(latex, images_dir, fontsize=12)
            if img_name:
                eq_count['rendered'] += 1
                return f'\n\n![BlockEquation](images/{img_name})\n\n'
            print(f"[Equations] Failed to render, using italic")
            return f'\n\n*{latex}*\n\n'
        
        text = re.sub(r'\$\$(.*?)\$\$', replace_block_equation, text, flags=re.DOTALL)
        
        # Process inline equations ($...$) - be careful not to match $$
        def replace_inline_equation(match):
            latex = match.group(1).strip()
            if not latex or '$$' in latex:  # Skip if it looks like block equation
                return match.group(0)
                
            eq_count['inline'] += 1
            
            if len(latex) <= 6:
                print(f"[Equations] Inline eq (short): {latex}")
                return f'*{latex}*'
            
            print(f"[Equations] Inline eq (long, rendering): {latex[:50]}...")
            img_name = self._render_equation(latex, images_dir, fontsize=10)
            if img_name:
                eq_count['rendered'] += 1
                return f'![InlineEq](images/{img_name})'
            print(f"[Equations] Failed to render, using italic")
            return f'*{latex}*'
        
        # Only match single $ (not $$)
        text = re.sub(r'(?<!\$)\$(?!\$)([^$]+?)\$(?!\$)', replace_inline_equation, text)
        
        print(f"[Equations] Found {eq_count['block']} block, {eq_count['inline']} inline, rendered {eq_count['rendered']}")
        return text

    def _render_equation(self, latex: str, images_dir: Path, fontsize: int = 12) -> str:
        """Render LaTeX equation as PNG using matplotlib"""
        try:
            # Create figure with white background
            fig, ax = plt.subplots(figsize=(10, 1.2), dpi=150)
            fig.patch.set_facecolor('white')
            
            # Render the equation
            ax.text(0.5, 0.5, f'${latex}$', 
                   ha='center', va='center',
                   fontsize=fontsize, 
                   transform=ax.transAxes,
                   color='black')
            
            ax.axis('off')
            ax.margins(0.05)
            
            # Create unique filename
            img_name = f'eq_{hash(latex) & 0x7FFFFFFF}.png'
            img_path = images_dir / img_name
            
            # Save with tight bbox
            fig.savefig(
                str(img_path),
                bbox_inches='tight',
                pad_inches=0.2,
                dpi=150,
                facecolor='white',
                edgecolor='none'
            )
            plt.close(fig)
            
            return img_name
            
        except Exception as e:
            print(f"[Equations] Error rendering '{latex[:30]}...': {e}")
            return None

    def _fix_image_paths(self, text: str) -> str:
        """Ensure image paths are properly formatted"""
        def replacer(match):
            filename = match.group(1)
            if filename.startswith("images/"):
                return f"]({filename})"
            return f"](images/{filename})"
        return re.sub(r'\]\(([^)]+\.(?:png|jpg|jpeg|gif))\)', replacer, text)

    def _create_epub(self, markdown_content: str, output_path: Path, title: str, images_dir: Path):
        """Build EPUB from Markdown content and images."""
        book = epub.EpubBook()
        
        # Set metadata
        book.set_identifier(f'cleanread_{uuid.uuid4()}')
        book.set_title(title)
        book.set_language('en')
        book.add_author('CleanRead')
        
        # Convert Markdown to HTML (equations already processed and replaced with ![...](images/...))
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code']
        )
        
        # Create main chapter
        chapter = epub.EpubHtml()
        chapter.file_name = 'chap_01.xhtml'
        chapter.title = title
        
        # Add images to EPUB
        if images_dir.exists():
            for img_path in images_dir.glob('*'):
                if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                    img_item = epub.EpubImage()
                    img_item.file_name = f'images/{img_path.name}'
                    with open(img_path, 'rb') as f:
                        img_item.content = f.read()
                    book.add_item(img_item)
        
        # Process HTML to make image references relative
        soup = BeautifulSoup(html_content, 'html.parser')
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src.startswith('images/'):
                img['src'] = f'images/{src.split("/")[-1]}'
        
        chapter.content = str(soup)
        book.add_item(chapter)
        
        # Add table of contents and spine
        book.toc = (chapter,)
        book.spine = ['nav', chapter]
        
        # Add default NCX and NAV files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Write EPUB
        epub.write_epub(output_path, book, {})


def get_converter() -> PDFConverter:
    """Get or create converter singleton"""
    return PDFConverter()
