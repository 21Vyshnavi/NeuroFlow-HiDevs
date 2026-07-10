# ruff: noqa
# mypy: ignore-errors
import io
import logging
from typing import List
from pipelines.ingestion.extractors.pdf_extractor import ExtractedPage

logger = logging.getLogger(__name__)

async def extract_csv(file_bytes: bytes) -> List[ExtractedPage]:
    pages = []
    try:
        import pandas as pd
        df = pd.read_csv(io.BytesIO(file_bytes))
        num_rows = len(df)
        
        if num_rows < 1000:
            # Convert to markdown
            md = df.to_markdown(index=False)
            pages.append(ExtractedPage(
                page_number=1,
                content=md,
                content_type="table",
                metadata={"rows": num_rows}
            ))
        else:
            # Statistical summary
            summary = []
            summary.append(f"CSV Row Count: {num_rows}")
            summary.append(f"Columns: {list(df.columns)}")
            summary.append("\nData Types:")
            summary.append(df.dtypes.to_string())
            summary.append("\nStatistical Summary:")
            summary.append(df.describe(include='all').to_string())
            summary.append("\nFirst 5 Sample Rows:")
            summary.append(df.head(5).to_markdown(index=False))
            
            # Batch into 100-row blocks
            block_size = 100
            for idx, i in enumerate(range(0, num_rows, block_size)):
                block = df.iloc[i : i + block_size]
                pages.append(ExtractedPage(
                    page_number=idx + 1,
                    content="\n".join(summary) + f"\n\n--- Block {idx+1} (Rows {i} to {i+len(block)}) ---\n" + block.to_markdown(index=False),
                    content_type="text",
                    metadata={"block_index": idx}
                ))
    except Exception as e:
        logger.warning(f"Pandas CSV parsing failed: {e}")
        pages.append(ExtractedPage(
            page_number=1,
            content=file_bytes.decode('utf-8', errors='ignore'),
            content_type="text",
            metadata={"engine": "fallback"}
        ))
    return pages
