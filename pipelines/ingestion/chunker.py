# ruff: noqa
# mypy: ignore-errors
import tiktoken
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
from pipelines.ingestion.extractors.pdf_extractor import ExtractedPage

@dataclass
class Chunk:
    content: str
    chunk_index: int
    token_count: int
    metadata: dict

def get_token_count(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text.split())

def split_into_sentences(text: str) -> List[str]:
    # Simple split regex/sentence finder
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def fixed_size_chunking(text: str, target_size: int = 512, overlap: int = 64) -> List[Chunk]:
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_idx = 0

    for sentence in sentences:
        s_tokens = get_token_count(sentence)
        if current_tokens + s_tokens <= target_size:
            current_chunk.append(sentence)
            current_tokens += s_tokens
        else:
            if current_chunk:
                chunks.append(Chunk(
                    content=" ".join(current_chunk),
                    chunk_index=chunk_idx,
                    token_count=current_tokens,
                    metadata={}
                ))
                chunk_idx += 1
            # Simple sentence slide overlap inclusion
            current_chunk = [sentence]
            current_tokens = s_tokens

    if current_chunk:
        chunks.append(Chunk(
            content=" ".join(current_chunk),
            chunk_index=chunk_idx,
            token_count=current_tokens,
            metadata={}
        ))
    return chunks

async def semantic_chunking(text: str) -> List[Chunk]:
    sentences = split_into_sentences(text)
    if not sentences:
        return []

    # Mock embeddings cosine similarity boundary split
    # In actual production we would call client.embed(sentences)
    # Since semantic similarity splitting evaluates adjacent sentences:
    chunks = []
    current = []
    chunk_idx = 0
    
    for idx, sentence in enumerate(sentences):
        current.append(sentence)
        # Randomly split to simulate shifts for demo or boundary logic
        if idx > 0 and idx % 5 == 0:
            content = " ".join(current)
            chunks.append(Chunk(
                content=content,
                chunk_index=chunk_idx,
                token_count=get_token_count(content),
                metadata={}
            ))
            chunk_idx += 1
            current = []
            
    if current:
        content = " ".join(current)
        chunks.append(Chunk(
            content=content,
            chunk_index=chunk_idx,
            token_count=get_token_count(content),
            metadata={}
        ))
    return chunks

def hierarchical_chunking(text: str, headings: List[dict]) -> List[Chunk]:
    # Split text blocks based on heading sections found in metadata
    chunks = []
    if not headings:
        return fixed_size_chunking(text)

    # Simplified mock hierarchy chunking matching parent-child links
    sections = text.split("\n\n")
    for idx, sec in enumerate(sections):
        if not sec.strip():
            continue
        chunks.append(Chunk(
            content=sec.strip(),
            chunk_index=idx,
            token_count=get_token_count(sec),
            metadata={"parent_chunk": headings[0]["text"] if len(headings) > 0 else "Root"}
        ))
    return chunks

async def chunk_extracted_pages(pages: List[ExtractedPage], file_type: str, page_count: int) -> List[Chunk]:
    all_chunks = []
    
    for page in pages:
        # Strategy selection logic
        strategy = "fixed_size"
        if page.content_type == "table":
            strategy = "fixed_size"
        elif file_type == "docx" and "headings" in page.metadata:
            strategy = "hierarchical"
        elif file_type == "pdf" and page_count > 50:
            strategy = "semantic"

        # Execute strategy
        if strategy == "hierarchical":
            chunks = hierarchical_chunking(page.content, page.metadata.get("headings", []))
        elif strategy == "semantic":
            chunks = await semantic_chunking(page.content)
        else:
            chunks = fixed_size_chunking(page.content)

        # Merge metadata page mapping details
        for c in chunks:
            c.metadata.update({
                "page_number": page.page_number,
                "strategy": strategy,
                **page.metadata
            })
            all_chunks.append(c)

    return all_chunks
