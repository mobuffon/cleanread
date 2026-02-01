# """
# PDF to EPUB conversion service
# Uses pdf2epub (which uses marker-pdf) to convert PDFs to EPUB format
# """
# import os
# import shutil
# import subprocess
# import uuid
# from pathlib import Path
# from typing import Optional, Dict, List
# from datetime import datetime

# import markdown
# import re
# import uuid
# import io
# try:
#     import latex2mathml.converter
#     LATEX2MATHML_AVAILABLE = True
# except ImportError:
#     LATEX2MATHML_AVAILABLE = False

# try:
#     import matplotlib.pyplot as plt
#     plt.switch_backend('Agg') # Headless backend
#     MATPLOTLIB_AVAILABLE = True
# except ImportError:
#     MATPLOTLIB_AVAILABLE = False

# from app.core.config import settings

# try:
#     # Try importing marker-pdf functions
#     from marker.convert import convert_single_pdf
#     from marker.models import load_all_models
    
#     # Fix surya-ocr config bug with transformers logging
#     # These config classes fail when transformers tries to create
#     # a default instance for diff comparison during logging
#     try:
#         from surya.model.ordering.config import SuryaOrderConfig
#         SuryaOrderConfig.has_no_defaults_at_init = True
#     except Exception:
#         pass
    
#     try:
#         from surya.model.recognition.config import SuryaOCRConfig
#         SuryaOCRConfig.has_no_defaults_at_init = True
#     except Exception:
#         pass
    
#     try:
#         from surya.model.detection.config import SuryaDetectionConfig
#         SuryaDetectionConfig.has_no_defaults_at_init = True
#     except Exception:
#         pass
    
#     try:
#         from surya.model.table_rec.config import SuryaTableRecConfig
#         SuryaTableRecConfig.has_no_defaults_at_init = True
#     except Exception:
#         pass
    
#     MARKER_AVAILABLE = True
# except Exception as e:
#     print(f"Warning: marker-pdf not available: {e}")
#     MARKER_AVAILABLE = False

# # Note: mark2epub is not available as a PyPI package
# # Using ebooklib for EPUB generation (same approach as our custom implementation)
# MARK2EPUB_AVAILABLE = False
import os
import shutil
import uuid
import asyncio
import re
import io
import math
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import markdown
from openai import AsyncOpenAI
from ebooklib import epub

# Import OCR service
from .ocr_service import get_ocr_service

# Import DataLab service for PDF to Markdown
try:
    from .datalab_service import get_datalab_converter
    DATALAB_AVAILABLE = True
except Exception as e:
    DATALAB_AVAILABLE = False
    print(f"Warning: DataLab service not available: {e}")

# PyMuPDF import (optional, for fallback)
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available, some fallback features disabled")

# pypdfium2 import (optional, alternative fallback)
try:
    import pypdfium2
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False

# Marker is no longer used - replaced by DataLab API
MARKER_AVAILABLE = False

# Import Matplotlib (Only for Math now)
try:
    import matplotlib.pyplot as plt
    plt.switch_backend('Agg') # Headless mode
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from app.core.config import settings

class PDFConverter:
    """
    Hybrid Converter V9 (Micro Tables):
    - Tables: HTML/Markdown with 0.6em font (Micro sized) to fit complex data.
    - Math: Hybrid (Images for complex equations, LaTeX text for simple ones).
    """
    
    def __init__(self):
        self.output_dir = Path(settings.STORAGE_PATH) / settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM client only if API key is available
        self.llm_client = None
        if os.getenv("DEEPSEEK_API_KEY"):
            try:
                self.llm_client = AsyncOpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"), 
                    base_url="https://api.deepseek.com"
                )
            except Exception as e:
                print(f"[PDFConverter] Failed to initialize DeepSeek client: {e}")
                self.llm_client = None
        
        # Initialize OCR service (fallback)
        self.ocr_service = get_ocr_service()
        
        # Initialize DataLab converter for PDF to Markdown
        self.datalab = None
        if DATALAB_AVAILABLE:
            try:
                self.datalab = get_datalab_converter()
                print("[PDFConverter] DataLab API initialized")
            except Exception as e:
                print(f"[PDFConverter] DataLab not available: {e}")
                self.datalab = None
        
        # Cache for rendered equations to avoid duplicate rendering
        self.equation_cache = {}

    async def convert(self, file_id: str, pdf_path: Path, **kwargs) -> Dict[str, str]:
        job_id = str(uuid.uuid4())
        work_dir = self.output_dir / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        epub_path = self.output_dir / f"{job_id}.epub"
        
        try:
            # Require DataLab API (cloud-based, no GPU needed)
            if not self.datalab:
                raise Exception("DataLab API is not available. Please try again later.")
            
            print(f"[{job_id}] Using DataLab Marker API (cloud-based)")
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
            print(f"  - Images: {len(images)}")
            
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
            
            # Clean up with DeepSeek if available (disabled for now)
            # if os.getenv("DEEPSEEK_API_KEY") and len(markdown_content) > 100:
            #     print(f"[{job_id}] Cleaning text with DeepSeek...")
            #     try:
            #         markdown_content = await self._reconcile_text(markdown_content, markdown_content)
            #     except Exception as e:
            #         print(f"[{job_id}] DeepSeek cleaning failed: {e}")
            
            # Visual Processing (Math rendering)
            print(f"[{job_id}] Processing visuals...")
            final_md = self._process_visuals(markdown_content, work_dir)

            # Path Normalization
            final_md = self._fix_image_paths(final_md)

            # EPUB Assembly
            print(f"[{job_id}] Building EPUB...")
            self._create_epub(final_md, epub_path, pdf_path.stem, images, work_dir)
            
            print(f"[{job_id}] ✅ EPUB created: {epub_path}")
            return {"job_id": job_id, "epub_path": str(epub_path)}

        except Exception as e:
            print(f"[{job_id}] ❌ Conversion failed: {e}")
            if work_dir.exists():
                shutil.rmtree(work_dir)
            raise e

    # --- Step 1: Marker (Structure Only) ---
    async def _run_marker(self, pdf_path: Path, work_dir: Path, **kwargs) -> Tuple[str, Dict]:
        """
        Use marker-pdf for structure detection ONLY
        Disable its OCR since we use OCR.space for text
        """
        loop = asyncio.get_event_loop()
        
        def _run():
            # convert_single_pdf with ocr_all_pages=False to skip marker's OCR
            # This saves significant GPU time since marker won't do text recognition
            return convert_single_pdf(
                fname=str(pdf_path), 
                model_lst=self.model_lst, 
                max_pages=kwargs.get('max_pages', None), 
                batch_multiplier=2,
                ocr_all_pages=False  # CRITICAL: Skip marker's OCR
            )
        
        result = await loop.run_in_executor(None, _run)
        
        # Extract structure info (marker will return minimal text)
        if isinstance(result, tuple):
            structure_md, images, _ = result
        else:
            structure_md = result.markdown
            images = result.images
        
        print(f"[Marker] Structure extraction complete. Text placeholder: {len(structure_md)} chars")
        print(f"[Marker] Images found: {len(images)}")
        
        # Save images
        images_dir = work_dir / "images"
        images_dir.mkdir(exist_ok=True)
        for name, img in images.items():
            img.save(images_dir / name)
        
        # Return minimal structure (marker won't have much text due to ocr_all_pages=False)
        return structure_md, images

    # --- Step 2: Text Layer ---
    async def _extract_text_layer(self, pdf_path: Path) -> str:
        """Extract text using OCR.space API"""
        print(f"[Text Extraction] Using OCR.space API")
        
        try:
            # Use OCR.space for text extraction
            text = await self.ocr_service.extract_text_from_pdf(pdf_path, language="eng")
            
            if not text or len(text.strip()) < 100:
                print(f"[Text Extraction] OCR.space returned minimal text")
                # Try fallback if available
                text = self._fallback_text_extraction(pdf_path)
            
            print(f"[Text Extraction] Extracted {len(text)} characters")
            return text
            
        except Exception as e:
            print(f"[Text Extraction] OCR.space failed: {e}, using fallback")
            # Fallback extraction
            return self._fallback_text_extraction(pdf_path)
    
    def _fallback_text_extraction(self, pdf_path: Path) -> str:
        """Fallback text extraction when OCR.space fails"""
        print(f"[Text Extraction] Using fallback extraction")
        
        # Try PyMuPDF first if available
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                text = "\n\n".join([page.get_text("text", sort=True) for page in doc])
                doc.close()
                print(f"[Text Extraction] PyMuPDF fallback extracted {len(text)} characters")
                return text
            except Exception as e:
                print(f"[Text Extraction] PyMuPDF error: {e}")
        
        # Try pypdfium2 if available
        if PYPDFIUM2_AVAILABLE:
            try:
                pdf = pypdfium2.PdfDocument(str(pdf_path))
                text_parts = []
                for page_num in range(len(pdf)):
                    page = pdf.get_page(page_num)
                    textpage = page.get_textpage()
                    text_parts.append(textpage.get_text_range())
                    textpage.close()
                    page.close()
                pdf.close()
                text = "\n\n".join(text_parts)
                print(f"[Text Extraction] pypdfium2 fallback extracted {len(text)} characters")
                return text
            except Exception as e:
                print(f"[Text Extraction] pypdfium2 error: {e}")
        
        # Last resort: return placeholder
        print(f"[Text Extraction] No fallback available, using placeholder")
        return f"[Text extraction failed for {pdf_path.name}. Please ensure OCR.space API key is set.]"

    # --- Step 3: DeepSeek ---
    async def _reconcile_text(self, visual_md: str, raw_text: str) -> str:
        chunks = visual_md.split("\n\n")
        grouped_chunks = []
        current_chunk = []
        current_len = 0
        
        for p in chunks:
            if current_len + len(p) > 6000:
                grouped_chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(p)
            current_len += len(p)
        if current_chunk:
            grouped_chunks.append("\n\n".join(current_chunk))

        tasks = [self._process_single_chunk(chunk) for chunk in grouped_chunks]
        cleaned_chunks = await asyncio.gather(*tasks)
        return "\n\n".join(cleaned_chunks)

    async def _process_single_chunk(self, text_chunk: str) -> str:
        if not text_chunk.strip(): return ""
        
        system_prompt = """You are a Text Reconstruction Expert. 
        1. Fix OCR errors.
        2. PRESERVE LATEX ($...$).
        3. PRESERVE TABLES: Ensure standard Markdown table syntax (|---|).
        4. PRESERVE IMAGES (![]).
        5. Do not summarize."""

        try:
            response = await self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_chunk}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception:
            return text_chunk

    # --- Step 4: Visuals (Math Only) ---
    def _process_visuals(self, text: str, work_dir: Path) -> str:
        if not MATPLOTLIB_AVAILABLE: return text

        images_dir = work_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Counters for debugging/optimization tracking
        block_equations_total = 0
        block_equations_rendered = 0
        inline_equations_total = 0
        inline_equations_rendered = 0

        # A. Block Math ($$ ... $$) -> Only render complex equations
        def replace_block_math(match):
            nonlocal block_equations_total, block_equations_rendered
            block_equations_total += 1
            
            latex = match.group(1).strip()
            
            # Skip simple numeric references like (1), 1.2, etc.
            if re.match(r'^\(?\d+(\.\d+)*\)?$', latex):
                return f'\n**Equation {latex}**\n'
            
            # Only render complex block equations
            if self._is_complex_math(latex):
                img_name = self._render_equation(latex, images_dir, fontsize=12)
                if img_name:
                    block_equations_rendered += 1
                    return f'\n![BlockEquation](images/{img_name})\n'
            
            # Keep simple block equations as LaTeX text (centered)
            return f'\n<div align="center">${latex}$</div>\n'

        text = re.sub(r'\$\$(.*?)\$\$', replace_block_math, text, flags=re.DOTALL)

        # B. Inline Math ($ ... $) -> Only render complex equations
        def replace_inline_math(match):
            nonlocal inline_equations_total, inline_equations_rendered
            inline_equations_total += 1
            
            latex = match.group(1).strip()
            
            # Skip simple numeric references
            if re.match(r'^\(?\d+(\.\d+)*\)?$', latex):
                return latex
            
            # Simple variables and equations -> Keep as LaTeX text (italics)
            if not self._is_complex_math(latex):
                # Preserve LaTeX formatting for simple equations
                return f"*${latex}$*"
            
            # Complex equations -> Render as small image
            img_name = self._render_equation(latex, images_dir, fontsize=10)
            if img_name:
                inline_equations_rendered += 1
                return f'![InlineEquation](images/{img_name})'
            
            # Fallback: keep as LaTeX if rendering fails
            return f"*${latex}$*"

        text = re.sub(r'\$(.*?)\$', replace_inline_math, text)
        
        # Log optimization results
        if block_equations_total > 0 or inline_equations_total > 0:
            print(f"[Math Optimization] Block equations: {block_equations_rendered}/{block_equations_total} rendered")
            print(f"[Math Optimization] Inline equations: {inline_equations_rendered}/{inline_equations_total} rendered")
            print(f"[Math Optimization] Cache hits: {len([k for k in self.equation_cache.keys() if 'eq_' in k])} equations cached")
        
        return text

    def _fix_image_paths(self, text: str) -> str:
        def replacer(match):
            filename = match.group(1)
            if filename.startswith("images/"):
                return f"]({filename})"
            return f"](images/{filename})"
        return re.sub(r'\]\(([^)]+\.(?:png|jpg|jpeg|gif))\)', replacer, text)

    def _is_complex_math(self, latex: str) -> bool:
        """Determine if a LaTeX equation is complex enough to warrant image rendering."""
        
        # Simple single variables/letters (x, y, z, α, β, etc.)
        if re.match(r'^[a-zA-Zα-ωΑ-Ω]$', latex.strip()):
            return False
        
        # Simple numeric expressions (1, 1.2, (3), etc.)
        if re.match(r'^\(?\d+(\.\d+)*\)?$', latex.strip()):
            return False
        
        # Simple subscripts/superscripts (x_i, y^2)
        if re.match(r'^[a-zA-Zα-ωΑ-Ω](_[a-zA-Z0-9]|\^[0-9])?$', latex.strip()):
            return False
        
        # Complex LaTeX commands that need rendering
        complex_triggers = [
            '\\sum', '\\int', '\\frac', '\\sqrt', '\\begin', '\\prod', '\\lim', 
            '\\infty', '\\partial', '\\mathbf', '\\hat', '\\bar', '\\vec', '\\mathcal',
            '\\binom', '\\oint', '\\nabla', '\\cdot', '\\times', '\\div', '\\pm',
            '\\mp', '\\leq', '\\geq', '\\neq', '\\approx', '\\equiv', '\\propto',
            '\\subset', '\\supset', '\\in', '\\notin', '\\cup', '\\cap', '\\wedge',
            '\\vee', '\\oplus', '\\otimes', '\\bigcup', '\\bigcap', '\\bigoplus'
        ]
        
        if any(trigger in latex for trigger in complex_triggers):
            return True
        
        # Equations with operators (=, <, >, etc.)
        if any(op in latex for op in ['=', '<', '>', '≤', '≥', '≠', '≈', '≡', '∝', '→', '←']):
            return True
        
        # Fractions (simple a/b pattern)
        if '/' in latex and '\\frac' not in latex:
            # Check if it's a simple fraction like a/b
            parts = latex.split('/')
            if len(parts) == 2 and all(re.match(r'^[a-zA-Z0-9]+$', p.strip()) for p in parts):
                return False
        
        # Long equations (likely complex)
        if len(latex) > 30:
            return True
        
        # Multiple terms with operators
        operator_count = sum(1 for op in ['+', '-', '*', '/', '='] if op in latex)
        if operator_count > 1:
            return True
        
        # Contains brackets with complex content
        if '{' in latex and '}' in latex:
            # Check if it's just simple formatting like \alpha_{i}
            if re.search(r'\\[a-zA-Z]+\{[a-zA-Z0-9]+\}', latex):
                # Simple command with single argument
                return False
        
        return False

    def _render_equation(self, latex: str, images_dir: Path, fontsize: int = 12) -> Optional[str]:
        """Render LaTeX equation to PNG image with caching."""
        
        # Create cache key (latex + fontsize)
        cache_key = f"{latex}_{fontsize}"
        
        # Check cache first
        if cache_key in self.equation_cache:
            cached_img_name = self.equation_cache[cache_key]
            # Check if the cached image still exists
            cached_path = images_dir / cached_img_name
            if cached_path.exists():
                return cached_img_name
            else:
                # Remove stale cache entry
                del self.equation_cache[cache_key]
        
        try:
            img_name = f"eq_{uuid.uuid4().hex[:8]}.png"
            img_path = images_dir / img_name
            
            # Create figure with minimal size
            fig = plt.figure(figsize=(0.1, 0.1))
            fig.text(0.5, 0.5, f"${latex}$", fontsize=fontsize, ha='center', va='center')
            
            # Render to buffer
            buf = io.BytesIO()
            plt.axis('off')
            plt.savefig(
                buf, 
                format='png', 
                bbox_inches='tight', 
                pad_inches=0.02, 
                transparent=True, 
                dpi=300
            )
            plt.close(fig)
            
            # Save to file
            with open(img_path, 'wb') as f:
                f.write(buf.getvalue())
            
            # Cache the result
            self.equation_cache[cache_key] = img_name
            
            return img_name
            
        except Exception as e:
            print(f"Warning: Failed to render equation '{latex}': {e}")
            return None

    # --- Step 5: EPUB Assembly ---
    def _create_epub(self, markdown_content: str, output_path: Path, title: str, images: Dict, work_dir: Path):
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(title)
        book.set_language("en")

        chapters = self._split_chapters(markdown_content)
        epub_chapters = []
        
        for i, (chap_title, content) in enumerate(chapters):
            html = markdown.markdown(content, extensions=['extra', 'codehilite', 'tables'])
            c = epub.EpubHtml(title=chap_title, file_name=f"chapter_{i}.xhtml", lang="en")
            c.content = f"<h1>{chap_title}</h1>{html}"
            book.add_item(c)
            epub_chapters.append(c)

        images_dir = work_dir / "images"
        if images_dir.exists():
            for img_path in images_dir.glob("*"):
                if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                    img_item = epub.EpubImage(
                        uid=img_path.name,
                        file_name=f"images/{img_path.name}",
                        media_type=f"image/{img_path.suffix[1:]}",
                        content=img_path.read_bytes()
                    )
                    book.add_item(img_item)

        # CSS - THE CRITICAL PART FOR MICRO TABLES
        style = """
            body { font-family: Georgia, serif; line-height: 1.6; padding: 5%; }
            img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
            
            /* INLINE MATH */
            img[alt="InlineEquation"] { 
                display: inline-block; 
                vertical-align: -0.2em;
                height: 1.0em; 
                width: auto;
                margin: 0 1px;
                box-shadow: none;
            }
            
            /* BLOCK MATH */
            img[alt="BlockEquation"] {
                display: block;
                margin: 1.5em auto;
                max-width: 90%;
            }
            
            /* MICRO TABLE CSS */
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
                /* Reduced from 0.7em to 0.6em (Very Small) */
                font-size: 0.6em; 
                line-height: 1.1;
                /* Allow words to break to save width */
                word-wrap: break-word; 
                hyphens: auto;
            }
            th, td {
                border: 1px solid #444; 
                /* Extremely tight padding */
                padding: 1px 2px;
                text-align: left;
                vertical-align: top;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
        """
        nav_css = epub.EpubItem(uid="style_nav", file_name="style.css", media_type="text/css", content=style)
        book.add_item(nav_css)

        book.toc = epub_chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav'] + epub_chapters
        epub.write_epub(str(output_path), book, {})

    def _split_chapters(self, text: str) -> List[Tuple[str, str]]:
        lines = text.split('\n')
        chapters = []
        curr_title = "Start"
        curr_lines = []
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                if curr_lines: chapters.append((curr_title, "\n".join(curr_lines)))
                curr_title = line.replace("#", "").strip()
                curr_lines = []
            else: curr_lines.append(line)
        if curr_lines: chapters.append((curr_title, "\n".join(curr_lines)))
        return chapters if chapters else [("Document", text)]

# class PDFConverter:
#     """
#     PDF to EPUB converter using pdf2epub (which uses marker-pdf)
#     Falls back to custom implementation if pdf2epub unavailable
#     """
    
#     def __init__(self):
#         self.output_dir = Path(settings.STORAGE_PATH) / settings.OUTPUT_DIR
#         self.output_dir.mkdir(parents=True, exist_ok=True)
#         self.model_lst = None
#         self.pdf2epub_path = Path("/opt/pdf2epub/main.py")
#         self.pdf2epub_available = self.pdf2epub_path.exists()
#         self.marker_available = MARKER_AVAILABLE
        
#         # Initialize marker models if available (for fallback)
#         if self.marker_available:
#             try:
#                 print("Loading marker-pdf models (this may take a minute)...")
#                 import traceback
#                 import torch
                
#                 # Detect best available device
#                 if torch.cuda.is_available():
#                     device = torch.device("cuda")
#                     dtype = torch.float16
#                     print("Using CUDA GPU for inference")
#                 elif torch.backends.mps.is_available():
#                     device = torch.device("mps")
#                     dtype = torch.float16
#                     print("Using Apple M3 GPU (MPS) for inference")
#                 else:
#                     device = torch.device("cpu")
#                     dtype = torch.float32
#                     print("Using CPU for inference")
                
#                 self.model_lst = load_all_models(device=device, dtype=dtype)
#                 print(f"Marker models loaded successfully ({len(self.model_lst)} models)")
#             except Exception as e:
#                 print(f"Warning: Could not initialize marker models: {e}")
#                 traceback.print_exc()
#                 self.marker_available = False
    
#     async def convert(
#         self,
#         file_id: str,
#         pdf_path: Path,
#         start_page: Optional[int] = None,
#         max_pages: Optional[int] = None,
#         languages: Optional[str] = "English",
#         batch_multiplier: int = 2,
#     ) -> Dict[str, str]:
#         """
#         Convert PDF to EPUB
        
#         Args:
#             file_id: Unique identifier for the uploaded file
#             pdf_path: Path to the PDF file
#             start_page: Starting page number (optional)
#             max_pages: Maximum pages to process (optional)
#             languages: Comma-separated languages (default: English)
#             batch_multiplier: GPU batch size multiplier (default: 2)
            
#         Returns:
#             Dictionary with job_id and output paths
#         """
#         job_id = str(uuid.uuid4())
        
#         # Create temporary working directory
#         work_dir = self.output_dir / job_id
#         work_dir.mkdir(parents=True, exist_ok=True)
        
#         try:
#             epub_path = self.output_dir / f"{job_id}.epub"
            
#             # Try pdf2epub first (best quality EPUB generation)
#             if self.pdf2epub_available:
#                 try:
#                     await self._convert_with_pdf2epub(
#                         pdf_path=pdf_path,
#                         output_path=epub_path,
#                         work_dir=work_dir,
#                         start_page=start_page,
#                         max_pages=max_pages,
#                         languages=languages,
#                         batch_multiplier=batch_multiplier,
#                     )
#                 except Exception as e:
#                     print(f"Warning: pdf2epub conversion failed: {e}, falling back to custom implementation")
#                     # Fall through to fallback
#                     await self._convert_with_marker_fallback(
#                         pdf_path=pdf_path,
#                         output_path=epub_path,
#                         work_dir=work_dir,
#                         start_page=start_page,
#                         max_pages=max_pages,
#                         languages=languages,
#                         batch_multiplier=batch_multiplier,
#                     )
#             elif self.marker_available and self.model_lst:
#                 # Use marker-pdf directly with custom EPUB generation
#                 await self._convert_with_marker_fallback(
#                     pdf_path=pdf_path,
#                     output_path=epub_path,
#                     work_dir=work_dir,
#                     start_page=start_page,
#                     max_pages=max_pages,
#                     languages=languages,
#                     batch_multiplier=batch_multiplier,
#                 )
#             else:
#                 # Fallback to placeholder if nothing available
#                 print("Warning: No conversion tools available, using placeholder EPUB")
#                 self._create_placeholder_epub(epub_path, pdf_path.name)
            
#             return {
#                 "job_id": job_id,
#                 "epub_path": str(epub_path),
#             }
            
#         except Exception as e:
#             # Clean up on error
#             if work_dir.exists():
#                 shutil.rmtree(work_dir)
#             if epub_path.exists():
#                 epub_path.unlink()
#             raise Exception(f"Conversion failed: {str(e)}")
    
#     async def _convert_with_pdf2epub(
#         self,
#         pdf_path: Path,
#         output_path: Path,
#         work_dir: Path,
#         start_page: Optional[int],
#         max_pages: Optional[int],
#         languages: str,
#         batch_multiplier: int,
#     ):
#         """
#         Convert PDF to EPUB using pdf2epub subprocess
#         This provides the best EPUB quality with chapter splitting and proper formatting
#         """
#         import asyncio
        
#         # Build pdf2epub command
#         # pdf2epub expects: python main.py [input_path] [output_path] [options]
#         cmd = [
#             "python3",
#             str(self.pdf2epub_path),
#             str(pdf_path),
#             str(work_dir),  # Output directory
#         ]
        
#         # Add optional parameters (matching pdf2epub CLI interface)
#         if start_page:
#             cmd.extend(["--start-page", str(start_page)])
        
#         if max_pages:
#             cmd.extend(["--max-pages", str(max_pages)])
        
#         if languages:
#             cmd.extend(["--langs", languages])
        
#         cmd.extend(["--batch-multiplier", str(batch_multiplier)])
        
#         # Run pdf2epub in executor (it's synchronous)
#         def run_pdf2epub():
#             result = subprocess.run(
#                 cmd,
#                 capture_output=True,
#                 text=True,
#                 cwd=str(self.pdf2epub_path.parent),
#                 timeout=600,  # 10 minute timeout
#             )
#             if result.returncode != 0:
#                 raise Exception(f"pdf2epub failed: {result.stderr}")
#             return result
        
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, run_pdf2epub)
        
#         # pdf2epub creates EPUB in work_dir
#         # It may create a subdirectory named after the PDF (without extension)
#         # or put the EPUB directly in work_dir
#         epub_files = []
        
#         # Check root of work_dir first
#         epub_files.extend(work_dir.glob("*.epub"))
        
#         # Check subdirectories (pdf2epub creates document_name/ directory)
#         for subdir in work_dir.iterdir():
#             if subdir.is_dir():
#                 epub_files.extend(subdir.glob("*.epub"))
#                 # Also check nested directories
#                 for nested_dir in subdir.iterdir():
#                     if nested_dir.is_dir():
#                         epub_files.extend(nested_dir.glob("*.epub"))
        
#         if epub_files:
#             # Use the largest EPUB file (most likely the complete one)
#             generated_epub = max(epub_files, key=lambda f: f.stat().st_size)
#             # Copy to our output location (don't move, in case we need the original)
#             shutil.copy2(str(generated_epub), str(output_path))
#         else:
#             # Debug: list what was actually created
#             created_files = list(work_dir.rglob("*"))
#             raise Exception(
#                 f"pdf2epub did not generate EPUB file. "
#                 f"Created files: {[str(f) for f in created_files[:10]]}"
#             )
    
#     async def _convert_with_marker_fallback(
#         self,
#         pdf_path: Path,
#         output_path: Path,
#         work_dir: Path,
#         start_page: Optional[int],
#         max_pages: Optional[int],
#         languages: str,
#         batch_multiplier: int,
#     ):
#         """
#         Convert PDF to EPUB using marker-pdf
        
#         This uses marker-pdf to extract text and structure from PDF,
#         then converts the markdown output to EPUB format.
#         """
#         # Parse languages
#         lang_list = [lang.strip() for lang in languages.split(",")] if languages else ["English"]
        
#         # Convert PDF to markdown using marker-pdf
#         # Note: convert_single_pdf is synchronous, so we run it in executor
#         import asyncio
        
#         def run_marker_conversion():
#             # convert_single_pdf signature:
#             # (fname, model_lst, max_pages, start_page, metadata, langs, batch_multiplier, ocr_all_pages)
#             # Returns: (markdown_text, images_dict, metadata_dict)
#             return convert_single_pdf(
#                 fname=str(pdf_path),
#                 model_lst=self.model_lst,
#                 max_pages=max_pages or settings.PDF_MAX_PAGES,
#                 start_page=start_page,
#                 langs=lang_list,
#                 batch_multiplier=batch_multiplier,
#             )
        
#         # Run marker conversion in thread pool (it's CPU/GPU intensive)
#         print(f"Starting marker-pdf conversion for {pdf_path.name}...")
#         print(f"This may take 1-5 minutes depending on PDF size and complexity...")
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, run_marker_conversion)
#         print(f"Marker-pdf conversion complete for {pdf_path.name}")
        
#         # Handle different return types from convert_single_pdf
#         # Depending on version, it may return a tuple or a result object
#         if isinstance(result, tuple):
#             markdown_text, images_dict, metadata = result
#         else:
#             # Result might be an object with attributes
#             markdown_text = getattr(result, 'markdown', '') or getattr(result, 'text', '') or str(result)
#             images_dict = getattr(result, 'images', {}) or {}
#             metadata = getattr(result, 'metadata', {}) or {}
        
#         print(f"Markdown content length: {len(markdown_text) if markdown_text else 0} characters")
#         print(f"Images extracted: {len(images_dict) if images_dict else 0}")
#         if images_dict:
#              print(f"DEBUG: Image filenames from marker: {list(images_dict.keys())}")
#         if markdown_text:
#              print(f"DEBUG: Markdown sample (first 1000 chars):\n{markdown_text[:1000]}")
#              # Search for image references
#              img_refs = re.findall(r'!\[.*?\]\((.*?)\)', markdown_text)
#              print(f"DEBUG: Image refs found in markdown: {img_refs[:10]}")
#              # Search for 'different' variations
#              lit_refs = re.findall(r'di.erent', markdown_text)
#              print(f"DEBUG: 'different' patterns found: {lit_refs[:10]}")
        
#         # Save images to work_dir if any
#         images_dir = None
#         if images_dict:
#             images_dir = work_dir / "images"
#             images_dir.mkdir(exist_ok=True)
#             for img_name, img in images_dict.items():
#                 img.save(images_dir / img_name)
        
#         markdown_content = markdown_text if markdown_text else ""
        
#         # If markdown is empty, raise an error
#         if not markdown_content.strip():
#             print(f"WARNING: Marker-pdf returned empty markdown content")
#             print(f"Result type: {type(result)}")
#             print(f"Result: {result[:500] if isinstance(result, str) else result}")
#             raise Exception("PDF conversion produced no text content. The PDF may be image-only or encrypted.")
        
#         # Convert markdown to EPUB using ebooklib
#         print(f"Converting markdown to EPUB...")
#         self._markdown_to_epub(
#             markdown_content=markdown_content,
#             markdown_file=work_dir / "output.md",  # Not actually used, just for reference
#             output_path=output_path,
#             title=pdf_path.stem,
#             images_dir=images_dir,
#         )
    
#     def _render_equation(self, latex: str, images_dir: Optional[Path]) -> Optional[str]:
#         """
#         Render LaTeX equation to PNG image using matplotlib
#         Returns relative path to image if successful, None otherwise
#         """
#         if not MATPLOTLIB_AVAILABLE or not images_dir:
#             return None
            
#         try:
#             # Create a unique filename
#             img_name = f"eq_{uuid.uuid4().hex[:8]}.png"
#             img_path = images_dir / img_name
            
#             # Setup figure
#             fig = plt.figure(figsize=(0.1, 0.1))
#             fig.text(0.5, 0.5, f"${latex}$", fontsize=20, ha='center', va='center')
            
#             # Save to buffer first to crop
#             buf = io.BytesIO()
#             plt.axis('off')
            
#             # Render
#             plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, transparent=True, dpi=300)
#             plt.close(fig)
            
#             # Write to file
#             buf.seek(0)
#             with open(img_path, 'wb') as f:
#                 f.write(buf.read())
                
#             return f"images/{img_name}"
            
#         except Exception as e:
#             print(f"Warning: Failed to render equation '{latex}': {e}")
#             return None

#     def _render_markdown_table(self, table_markdown: str, images_dir: Optional[Path]) -> Optional[str]:
#         """
#         Render markdown table to PNG image using matplotlib
#         Returns relative path to image if successful, None otherwise
#         """
#         if not MATPLOTLIB_AVAILABLE or not images_dir:
#             return None
            
#         try:
#             # Parse markdown table
#             lines = [line.strip() for line in table_markdown.strip().split('\n') if line.strip()]
#             if not lines:
#                 return None
            
#             # Extract cell data
#             rows = []
#             for line in lines:
#                 # Skip separator lines (e.g., |---|---|)
#                 if set(line.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
#                     continue
#                 # Split by | and clean
#                 cells = [cell.strip() for cell in line.split('|')]
#                 # Remove empty first/last cells from leading/trailing |
#                 cells = [c for c in cells if c]
#                 if cells:
#                     rows.append(cells)
            
#             if not rows:
#                 return None
            
#             # Create unique filename
#             img_name = f"table_{uuid.uuid4().hex[:8]}.png"
#             img_path = images_dir / img_name
            
#             # Determine figure size based on content
#             num_rows = len(rows)
#             num_cols = max(len(row) for row in rows)
#             fig_width = min(12, num_cols * 2)
#             fig_height = min(10, num_rows * 0.6 + 1)
            
#             # Create figure with table
#             fig, ax = plt.subplots(figsize=(fig_width, fig_height))
#             ax.axis('tight')
#             ax.axis('off')
            
#             # Pad rows to have same number of columns
#             max_cols = max(len(row) for row in rows)
#             padded_rows = [row + [''] * (max_cols - len(row)) for row in rows]
            
#             # Create table
#             table = ax.table(cellText=padded_rows, cellLoc='left', loc='center')
#             table.auto_set_font_size(False)
#             table.set_fontsize(9)
#             table.scale(1, 2)
            
#             # Style header row (first row)
#             if len(padded_rows) > 0:
#                 for i in range(len(padded_rows[0])):
#                     cell = table[(0, i)]
#                     cell.set_facecolor('#f2f2f2')
#                     cell.set_text_props(weight='bold')
            
#             # Save to file
#             plt.savefig(img_path, bbox_inches='tight', pad_inches=0.1, dpi=150, 
#                        transparent=False, facecolor='white')
#             plt.close(fig)
            
#             return f"images/{img_name}"
            
#         except Exception as e:
#             print(f"Warning: Failed to render table: {e}")
#             return None

#     def _clean_text(self, text: str, images_dir: Optional[Path] = None) -> str:
#         """
#         Clean text of common OCR artifacts and process equations
#         """
#         # Fix common ligature issues where 'ff', 'fi', 'fl' become '!'
#         # We use specific replacements for common words to be safe
#         corrections = {
#             "di!erent": "different",
#             "di!erence": "difference",
#             "e!ect": "effect",
#             "a!ect": "affect",
#             "o!er": "offer",
#             "su!er": "suffer",
#             "e!ort": "effort",
#             "tra!ic": "traffic",
#             "signi!icant": "significant", # ! -> f
#             "speci!ic": "specific",       # ! -> f
#             "de!ine": "define",           # ! -> f
#             "di! erent": "different",
#             "di|erent": "different",
#             "e! ect": "effect",
#             "o!ice": "office",
#             "o!icial": "official",
#             "o!icer": "officer",
#             "e!ective": "effective",
#             "stu!": "stuff",
#             "sta!": "staff",
#             "a!ord": "afford",
#             "cli!": "cliff",
#             "sherri!": "sheriff",
#             "tari!": "tariff",
#             "sni!": "sniff",
#             "sti!": "stiff",
#             "gru!": "gruff",
#             "shu!le": "shuffle",
#             "wa!le": "waffle",
#             "o!shoot": "offshoot",
#             "o!set": "offset",
#         }
        
#         for error, fix in corrections.items():
#             text = text.replace(error, fix)
#             text = text.replace(error.capitalize(), fix.capitalize())
        
#         # Process equations - Render to images as requested
        
#         # Helper to check if latex is just a valid figure number reference e.g. (1), 1, (1.2)
#         def is_simple_ref(latex_str):
#             clean = latex_str.strip()
#             # Matches "1", "(1)", "1.2", "(1.2)"
#             return re.match(r'^\(?\d+(\.\d+)*\)?$', clean) is not None
        
#         # Convert $$...$$ block equations
#         def replace_block_math(match):
#             latex = match.group(1)
            
#             # Skip rendering if it's just a number
#             if is_simple_ref(latex):
#                 return f'<span class="math-ref">{latex}</span>'
            
#             # Try rendering to image first
#             img_rel_path = self._render_equation(latex, images_dir)
#             if img_rel_path:
#                 return f'![BlockEquation]({img_rel_path})'
            
#             # Fallback to MathML
#             if LATEX2MATHML_AVAILABLE:
#                 try:
#                     mathml = latex2mathml.converter.convert(latex)
#                     return f'<div class="math-block">{mathml}</div>'
#                 except Exception:
#                     pass
#             return f'<pre class="math-block">{latex}</pre>'
            
#         text = re.sub(r'\$\$(.*?)\$\$', replace_block_math, text, flags=re.DOTALL)
        
#         # Convert $...$ inline equations
#         def replace_inline_math(match):
#             latex = match.group(1)
            
#             # Skip rendering if it's just a number
#             if is_simple_ref(latex):
#                 return f'<span class="math-ref">{latex}</span>'
            
#             # Try rendering to image first
#             img_rel_path = self._render_equation(latex, images_dir)
#             if img_rel_path:
#                 return f'![InlineEquation]({img_rel_path})'
            
#             if LATEX2MATHML_AVAILABLE:
#                 try:
#                     mathml = latex2mathml.converter.convert(latex)
#                     return f'<span class="math-inline">{mathml}</span>'
#                 except Exception:
#                     pass
#             return f'<code class="math-inline">{latex}</code>'
            
#         text = re.sub(r'\$(.*?)\$', replace_inline_math, text)
        
#         return text

#     def _markdown_to_epub(
#         self,
#         markdown_content: str,
#         markdown_file: Path,
#         output_path: Path,
#         title: str,
#         images_dir: Optional[Path] = None,
#     ):
#         """
#         Convert markdown content to EPUB format using mark2epub
        
#         Args:
#             markdown_content: Markdown text content
#             markdown_file: Path to the markdown file (for mark2epub)
#             output_path: Path where EPUB file should be saved
#             title: Title of the book
#             images_dir: Optional directory containing images to include
#         """
#         # Use ebooklib for EPUB generation (mark2epub not available as PyPI package)
#         # This implementation provides the same functionality
#         self._markdown_to_epub_fallback(markdown_content, output_path, title, images_dir)
    
#     def _markdown_to_epub_fallback(
#         self,
#         markdown_content: str,
#         output_path: Path,
#         title: str,
#         images_dir: Optional[Path] = None,
#     ):
#         """
#         Fallback EPUB generation using ebooklib (used if mark2epub unavailable)
#         """
#         from ebooklib import epub
        
#         # Create EPUB book
#         book = epub.EpubBook()
        
#         # Set metadata
#         book.set_identifier(str(uuid.uuid4()))
#         book.set_title(title)
#         book.set_language("en")
#         book.add_author("CleanRead")
        
#         # Convert markdown to HTML
#         try:
#             html_content = markdown.markdown(
#                 markdown_content,
#                 extensions=["extra", "codehilite", "tables"],
#             )
#         except Exception:
#             # Fallback to basic markdown if extensions not available
#             html_content = markdown.markdown(markdown_content)
#         # Ensure we have some content
#         if not html_content or not html_content.strip():
#             html_content = "<p>No content could be extracted from this document.</p>"
        
#         # Clean text and render equations
#         markdown_content = self._clean_text(markdown_content, images_dir)
        
#         # Replace markdown tables with image references BEFORE HTML conversion
#         if images_dir and MATPLOTLIB_AVAILABLE:
#             # Regex to match markdown tables
#             # A markdown table is multiple consecutive lines starting with |
#             table_pattern = r'(?:^\|.+\|[ \t]*$\n?)+'
            
#             tables_in_md = list(re.finditer(table_pattern, markdown_content, re.MULTILINE))
            
#             print(f"DEBUG: Found {len(tables_in_md)} markdown tables to render")
            
#             # Replace each markdown table with rendered image (in reverse to preserve positions)
#             for idx, table_match in enumerate(reversed(tables_in_md)):
#                 table_markdown = table_match.group(0)
                
#                 # Render table to image
#                 img_rel_path = self._render_markdown_table(table_markdown, images_dir)
                
#                 if img_rel_path:
#                     print(f"DEBUG: Rendered table {len(tables_in_md) - idx - 1} as {img_rel_path}")
#                     # Replace with markdown image syntax
#                     img_ref = f'\n![Table]({img_rel_path})\n'
#                     markdown_content = (markdown_content[:table_match.start()] + 
#                                       img_ref + 
#                                       markdown_content[table_match.end():])
#                 else:
#                     print(f"DEBUG: Failed to render table {len(tables_in_md) - idx - 1}")

        
#         # Process images: Sanitize filenames and update references in content
#         if images_dir and images_dir.exists():
#             for img_path in list(images_dir.glob("*")): # list() to safely iterate while modifying
#                  if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
#                      # Skip equation images we just generated (start with eq_)
#                      if img_path.name.startswith("eq_"):
#                          continue
                         
#                      # Sanitize filename
#                      safe_name = "".join(c for c in img_path.stem if c.isalnum() or c in ('_', '-'))
#                      if not safe_name: safe_name = "image"
#                      safe_filename = f"images/{safe_name}{img_path.suffix}"
                     
#                      # Robust regex replacement for image references
#                      # We want to replace ANY reference to the filename (with optional path prefix) with the safe relative path.
#                      # Pattern matches: ]( ... filename ) where '...' is non-greedy optional content not containing close paren
#                      escaped_name = re.escape(img_path.name)
#                      # Match: ]( optional_path/name )
#                      pattern = r'\]\(\s*(?:[^)]*?/)?' + escaped_name + r'\s*\)'
                     
#                      if re.search(pattern, markdown_content):
#                         markdown_content = re.sub(pattern, f']({safe_filename})', markdown_content)
                        
#                         # Rename file on disk to match the new safe name
#                         new_path = images_dir / f"{safe_name}{img_path.suffix}"
#                         if new_path != img_path:
#                             shutil.move(str(img_path), str(new_path))
        
#         # Create chapter
#         chapter = epub.EpubHtml(
#             title="Content",
#             file_name="chapter.xhtml",
#             lang="en",
#         )
        
#         # Convert markdown to HTML after cleaning and image processing
#         try:
#             html_content = markdown.markdown(
#                 markdown_content,
#                 extensions=["extra", "codehilite", "tables"],
#             )
#         except Exception:
#             # Fallback to basic markdown if extensions not available
#             html_content = markdown.markdown(markdown_content)


#         chapter.content = f"""<?xml version="1.0" encoding="UTF-8"?>
# <!DOCTYPE html>
# <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
# <head>
#     <title>{title}</title>
#     <style>
#         body {{ font-family: Georgia, serif; line-height: 1.6; margin: 2em; }}
#         h1, h2, h3 {{ color: #333; }}
#         p {{ margin: 1em 0; }}
#         img {{ max-width: 100%; height: auto; }}
#         code {{ background: #f4f4f4; padding: 0.2em 0.4em; border-radius: 3px; }}
#         pre {{ background: #f4f4f4; padding: 1em; overflow-x: auto; }}
#         table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
#         th, td {{ border: 1px solid #ddd; padding: 0.5em; text-align: left; }}
#         th {{ background-color: #f2f2f2; }}
#         /* Math styles */
#         img[alt="InlineEquation"] {{ max-height: 1.5em; width: auto; vertical-align: middle; display: inline; }}
#         img[alt="BlockEquation"] {{ display: block; margin: 1em auto; max-width: 100%; height: auto; }}
#         img[alt="Table"] {{ display: block; margin: 1em auto; max-width: 100%; height: auto; }}
#         .math-ref {{ font-family: Georgia, serif; }}
#     </style>
# </head>
# <body>
# {html_content}
# </body>
# </html>""".encode('utf-8')
        
#         # Add chapter to book
#         book.add_item(chapter)
        
#         # Add images to book
#         if images_dir and images_dir.exists():
#             for img_path in images_dir.glob("*"):
#                 if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                   
#                    # For EPUB struct, we just need unique file_names
#                    # We already renamed files on disk to safe names if needed
                   
#                     img_item = epub.EpubImage(
#                         uid=f"img_{img_path.stem}",
#                         file_name=f"images/{img_path.name}",
#                         media_type=f"image/{img_path.suffix[1:].lower()}",
#                         content=img_path.read_bytes(),
#                     )
#                     book.add_item(img_item)
        
#         # Create table of contents
#         book.toc = [chapter]
        
#         # Add navigation files
#         book.add_item(epub.EpubNcx())
#         nav = epub.EpubNav()
#         nav.content = '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Navigation</title></head><body><nav epub:type="toc"><ol></ol></nav></body></html>'
#         book.add_item(nav)
        
#         # Set spine (order of content)
#         book.spine = ["nav", chapter]
        
#         # Write EPUB file
#         epub.write_epub(str(output_path), book, {})
    
#     def _create_placeholder_epub(self, output_path: Path, original_filename: str):
#         """
#         Create a placeholder EPUB for MVP
#         In Phase 2, this will be replaced with actual pdf2epub integration
#         """
#         # This is a minimal EPUB structure for testing
#         # We'll replace this with actual conversion logic
        
#         import zipfile
#         from datetime import datetime
        
#         with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
#             # mimetype (must be first and uncompressed)
#             epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
#             # META-INF/container.xml
#             epub.writestr('META-INF/container.xml', '''<?xml version="1.0"?>
# <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
#   <rootfiles>
#     <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
#   </rootfiles>
# </container>''')
            
#             # content.opf
#             epub.writestr('content.opf', f'''<?xml version="1.0"?>
# <package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
#   <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
#     <dc:title>{original_filename}</dc:title>
#     <dc:creator>CleanRead</dc:creator>
#     <dc:language>en</dc:language>
#     <dc:date>{datetime.now().isoformat()}</dc:date>
#     <meta property="dcterms:modified">{datetime.now().isoformat()}</meta>
#   </metadata>
#   <manifest>
#     <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
#     <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
#   </manifest>
#   <spine>
#     <itemref idref="content"/>
#   </spine>
# </package>''')
            
#             # nav.xhtml
#             epub.writestr('nav.xhtml', '''<?xml version="1.0"?>
# <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
#   <head><title>Navigation</title></head>
#   <body>
#     <nav epub:type="toc">
#       <ol>
#         <li><a href="content.xhtml">Content</a></li>
#       </ol>
#     </nav>
#   </body>
# </html>''')
            
#             # content.xhtml
#             epub.writestr('content.xhtml', f'''<?xml version="1.0"?>
# <html xmlns="http://www.w3.org/1999/xhtml">
#   <head>
#     <title>{original_filename}</title>
#   </head>
#   <body>
#     <h1>Converted from {original_filename}</h1>
#     <p>This is a placeholder EPUB created by CleanRead MVP.</p>
#     <p>Full PDF to EPUB conversion will be implemented in Phase 2.</p>
#   </body>
# </html>''')
