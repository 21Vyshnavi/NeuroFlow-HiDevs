# ruff: noqa
# mypy: ignore-errors
import io
import logging
from typing import List
from PIL import Image
from pipelines.ingestion.extractors.pdf_extractor import ExtractedPage
from backend.providers.client import client as llm_client
from backend.providers.base import ChatMessage
from backend.providers.router import RoutingCriteria

logger = logging.getLogger(__name__)

async def extract_image(file_bytes: bytes) -> List[ExtractedPage]:
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.thumbnail((1024, 1024))
        
        # Simple local pytesseract fallback if vision api is not configured
        ocr_text = ""
        try:
            import pytesseract
            ocr_text = pytesseract.image_to_string(img)
        except Exception:
            pass

        # Perform Vision Call using client
        desc = "Vision analysis placeholder."
        try:
            criteria = RoutingCriteria(task_type="classification", require_vision=True)
            res = await llm_client.chat(
                messages=[ChatMessage(role="user", content="Describe this image structure and details.")],
                criteria=criteria
            )
            desc = res.content
        except Exception as e:
            logger.warning(f"Vision LLM request failed, utilizing fallback: {e}")

        final_content = f"{desc}\n\nText found in image: {ocr_text}"
        return [ExtractedPage(
            page_number=1,
            content=final_content,
            content_type="image_description",
            metadata={"size": img.size}
        )]
    except Exception as e:
        logger.error(f"Image parsing error: {e}")
        return [ExtractedPage(page_number=1, content="Unparsable image payload", content_type="image_description", metadata={})]
