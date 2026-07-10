# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import hashlib
import json
import logging
import os
import uuid

import aiofiles
import redis.asyncio as redis
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl

from backend.config import settings
from backend.db.pool import db_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])

class URLIngestRequest(BaseModel):
    url: HttpUrl
    pipeline_id: str | None = None
    metadata: dict | None = None

async def enqueue_ingestion(payload: dict) -> None:
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password
    )
    await r.lpush("queue:ingest", json.dumps(payload))
    await r.aclose()

from fastapi import APIRouter, Depends

from backend.security.auth import ScopeRequired
from backend.security.validators import sanitize_text, validate_file_type, validate_url


@router.post("")
async def ingest_file_or_url(
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    pipeline_id: str | None = Form(None),
    metadata: str | None = Form(None),
    _user = Depends(ScopeRequired("ingest"))
):
    pool = db_pool.get_pool()
    if not pool:
        raise HTTPException(status_code=500, detail="Database connection pool unavailable.")

    # Parse metadata if present
    meta_dict = {}
    if metadata:
        try:
            # Strip HTML from metadata input
            sanitized_meta = sanitize_text(metadata)
            meta_dict = json.loads(sanitized_meta)
        except Exception:
            pass

    content_hash = ""
    source_type = ""
    file_path = None

    if file:
        file_bytes = await file.read()
        
        # File type validation with magic bytes
        validate_file_type(file_bytes, file.filename)
        
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # Deduplication check
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT id, status FROM documents WHERE content_hash = $1", content_hash)
            if existing:
                return {
                    "document_id": str(existing["id"]),
                    "status": existing["status"],
                    "duplicate": True
                }

        # Save temporary file
        file_ext = file.filename.split(".")[-1].lower()
        source_type = file_ext if file_ext in ["pdf", "docx", "image", "csv", "text"] else "text"
        if file_ext in ["jpg", "jpeg", "png", "webp"]:
            source_type = "image"

        temp_dir = "/Users/vaish/Downloads/projects/Complete Recommendation System/NeuroFlow-HiDevs/scratch"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{file_ext}")
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

    elif url:
        # Validate URL to prevent SSRF
        validate_url(url)
        
        content_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
        source_type = "url"
        
        # Deduplication check
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT id, status FROM documents WHERE content_hash = $1", content_hash)
            if existing:
                return {
                    "document_id": str(existing["id"]),
                    "status": existing["status"],
                    "duplicate": True
                }
    else:
        raise HTTPException(status_code=400, detail="Payload must contain either file upload or url.")

    # Create document row in database
    doc_id = uuid.uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO documents (id, filename, source_type, content_hash, metadata, pipeline_id, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'queued')
            """,
            doc_id,
            file.filename if file else url,
            source_type,
            content_hash,
            json.dumps(meta_dict),
            uuid.UUID(pipeline_id) if pipeline_id else None
        )

    # Queue background task
    await enqueue_ingestion({
        "document_id": str(doc_id),
        "file_path": file_path,
        "source_type": source_type,
        "url": url
    })

    return {
        "document_id": str(doc_id),
        "status": "queued",
        "duplicate": False
    }

@router.get("/documents/{document_id}")
async def get_document_status(document_id: str):
    pool = db_pool.get_pool()
    if not pool:
        raise HTTPException(status_code=500, detail="Database connection pool unavailable.")
        
    async with pool.acquire() as conn:
        doc = await conn.fetchrow(
            "SELECT id, filename, source_type, status, chunk_count, metadata, created_at FROM documents WHERE id = $1",
            uuid.UUID(document_id)
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
            
        return {
            "document_id": str(doc["id"]),
            "filename": doc["filename"],
            "source_type": doc["source_type"],
            "status": doc["status"],
            "chunk_count": doc["chunk_count"],
            "metadata": json.loads(doc["metadata"]),
            "created_at": doc["created_at"]
        }
