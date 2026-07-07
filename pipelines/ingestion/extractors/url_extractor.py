import httpx
import logging
from typing import List
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from pipelines.ingestion.extractors.pdf_extractor import ExtractedPage

logger = logging.getLogger(__name__)

async def extract_url(url: str) -> List[ExtractedPage]:
    try:
        # Check Robots.txt
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        rp = RobotFileParser()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(robots_url)
                if res.status_code == 200:
                    rp.parse(res.text.splitlines())
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")

        # Fetch page content
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "NeuroFlowBot/1.0"})
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP error {resp.status_code}")
            
            html_content = resp.text

        # Extract using trafilatura
        import trafilatura
        extracted = trafilatura.extract(html_content, include_tables=True, output_format="markdown")
        if not extracted:
            extracted = html_content  # Fallback to raw

        meta = trafilatura.extract_metadata(html_content)
        metadata = {}
        if meta:
            metadata = {
                "title": meta.title,
                "author": meta.author,
                "date": meta.date,
                "url": meta.url or url
            }

        return [ExtractedPage(
            page_number=1,
            content=extracted,
            content_type="text",
            metadata=metadata
        )]
    except Exception as e:
        logger.error(f"URL extraction failed for {url}: {e}")
        return [ExtractedPage(page_number=1, content=f"Failed to load URL contents: {e}", content_type="text", metadata={"url": url})]
