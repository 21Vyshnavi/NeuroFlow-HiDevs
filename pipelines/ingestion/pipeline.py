import json
import logging
import hashlib
import time
from opentelemetry import trace
from backend.db.pool import db_pool
from backend.providers.client import client as llm_client
from pipelines.ingestion.extractors.pdf_extractor import extract_pdf, ExtractedPage
from pipelines.ingestion.extractors.docx_extractor import extract_docx
from pipelines.ingestion.extractors.image_extractor import extract_image
from pipelines.ingestion.extractors.csv_extractor import extract_csv
from pipelines.ingestion.extractors.url_extractor import extract_url
from pipelines.ingestion.chunker import chunk_extracted_pages

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("neuroflow.ingestion")

async def process_document_job(document_id: str, file_path: str, source_type: str, url: str = None):
    pool = db_pool.get_pool()
    if not pool:
        logger.error("DB Pool not initialized in worker context")
        return

    start_time = time.time()
    
    with tracer.start_as_current_span("ingestion.process") as span:
        span.set_attribute("document_id", document_id)
        span.set_attribute("source_type", source_type)

        async with pool.acquire() as conn:
            # Update status to processing
            await conn.execute("UPDATE documents SET status = 'processing' WHERE id = $1", document_id)

            # Read File Contents
            file_bytes = b""
            if url:
                file_bytes = url.encode("utf-8")
            else:
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                except Exception as e:
                    logger.error(f"Failed to read file: {e}")
                    await conn.execute("UPDATE documents SET status = 'failed', metadata = $2 WHERE id = $1", document_id, json.dumps({"error": str(e)}))
                    return

            # Extract content based on modality
            with tracer.start_as_current_span(f"ingestion.extract.{source_type}"):
                pages = []
                if source_type == "pdf":
                    pages = await extract_pdf(file_bytes)
                elif source_type == "docx":
                    pages = await extract_docx(file_bytes)
                elif source_type == "image":
                    pages = await extract_image(file_bytes)
                elif source_type == "csv":
                    pages = await extract_csv(file_bytes)
                elif source_type == "url":
                    pages = await extract_url(url)
                else:
                    pages = [ExtractedPage(page_number=1, content=file_bytes.decode('utf-8', errors='ignore'), content_type="text", metadata={})]

            page_count = len(pages)
            span.set_attribute("page_count", page_count)

            # Segment pages into chunks
            with tracer.start_as_current_span("ingestion.chunk"):
                chunks = await chunk_extracted_pages(pages, source_type, page_count)
            span.set_attribute("chunk_count", len(chunks))

            # Scan and redact secrets & check for prompt injection patterns
            from backend.security.secret_detector import scan_and_redact_secrets
            from backend.security.prompt_injection import scan_pattern_injection

            for chunk in chunks:
                # 1. Redact secrets
                redacted, redactions = scan_and_redact_secrets(chunk.content, document_id=document_id)
                chunk.content = redacted
                
                # 2. Check prompt injection pattern
                injection_result = scan_pattern_injection(chunk.content)
                if injection_result:
                    chunk.metadata.update(injection_result)

            # Batch Generate Embeddings
            chunk_contents = [c.content for c in chunks]
            embeddings = []
            if chunk_contents:
                with tracer.start_as_current_span("ingestion.embed"):
                    try:
                        embeddings = await llm_client.embed(chunk_contents)
                        span.set_attribute("embedding_calls", len(chunk_contents))
                    except Exception as e:
                        logger.error(f"Failed to generate embeddings: {e}")
                        # Provide dummy fallback embeddings (1536 zero floats)
                        embeddings = [[0.0] * 1536 for _ in chunk_contents]

            # Save chunks to PostgreSQL
            with tracer.start_as_current_span("ingestion.write_db"):
                async with conn.transaction():
                    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                        await conn.execute(
                            """
                            INSERT INTO chunks (document_id, content, embedding, chunk_index, token_count, metadata)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            """,
                            document_id,
                            chunk.content,
                            emb,
                            chunk.chunk_index,
                            chunk.token_count,
                            json.dumps(chunk.metadata)
                        )

                    # Update Document Record
                    await conn.execute(
                        "UPDATE documents SET status = 'complete', chunk_count = $2 WHERE id = $1",
                        document_id,
                        len(chunks)
                    )

        # Update metrics
        try:
            from backend.monitoring.metrics import ingestion_docs_total
            ingestion_docs_total.labels(source_type=source_type).inc()
        except ImportError:
            pass

        duration = (time.time() - start_time) * 1000
        logger.info(json.dumps({
            "event": "ingestion_complete",
            "document_id": document_id,
            "duration_ms": duration,
            "chunks": len(chunks),
            "tokens": sum(c.token_count for c in chunks)
        }))
