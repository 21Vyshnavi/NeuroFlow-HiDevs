import io
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class ExtractedPage:
    page_number: int
    content: str
    content_type: str  # "text" | "table" | "image_description"
    metadata: dict

async def extract_pdf(file_bytes: bytes) -> List[ExtractedPage]:
    pages = []
    # Mocking pypdfium2/pdfplumber/pytesseract for environments where libraries might have trouble installing
    # Or native load:
    try:
        import pypdfium2 as pdfium
        import pdfplumber
        import pytesseract
        from PIL import Image

        pdf = pdfium.PdfDocument(file_bytes)
        for i, page in enumerate(pdf):
            text = page.get_textpage().get_text_range()
            # Check scanned condition (< 50 chars)
            if len(text.strip()) < 50:
                # OCR Scanned page
                pil_image = page.render(scale=2).to_pil()
                text = pytesseract.image_to_string(pil_image, config="--psm 6")
            
            pages.append(ExtractedPage(
                page_number=i + 1,
                content=text,
                content_type="text",
                metadata={"engine": "pypdfium2"}
            ))

        # Tables with pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf_plumb:
            for i, page in enumerate(pdf_plumb.pages):
                tables = page.extract_tables()
                for t in tables:
                    # convert to markdown table
                    md_rows = []
                    for row in t:
                        md_rows.append("| " + " | ".join([str(cell or "").replace("\n", " ") for cell in row]) + " |")
                    if md_rows:
                        pages.append(ExtractedPage(
                            page_number=i + 1,
                            content="\n".join(md_rows),
                            content_type="table",
                            metadata={"engine": "pdfplumber"}
                        ))
    except Exception as e:
        logger.warning(f"Using fallback parser for PDF: {e}")
        # fallback simple string decoding mock
        pages.append(ExtractedPage(
            page_number=1,
            content=file_bytes.decode('utf-8', errors='ignore'),
            content_type="text",
            metadata={"engine": "fallback"}
        ))
    return pages
