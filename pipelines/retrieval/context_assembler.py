# ruff: noqa
# mypy: ignore-errors
import tiktoken
from typing import List, Dict, Any
from pipelines.retrieval import RetrievalResult

def get_token_count(text: str) -> int:
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text.split())

def assemble_context(candidates: List[RetrievalResult], token_budget: int = 4000) -> Dict[str, Any]:
    used_chunks = []
    sources = []
    total_tokens = 0
    formatted_parts = []

    for idx, c in enumerate(candidates):
        doc_name = c.metadata.get("filename", "unknown_doc")
        page_num = c.metadata.get("page_number", "?")
        
        header = f"[Source {idx + 1} — {doc_name}, page {page_num}]\n"
        content_part = f"{c.content}\n\n"
        full_part = header + content_part
        
        part_tokens = get_token_count(full_part)
        
        if total_tokens + part_tokens <= token_budget:
            total_tokens += part_tokens
            formatted_parts.append(full_part)
            used_chunks.append(c.chunk_id)
            sources.append({
                "source_index": idx + 1,
                "document_name": doc_name,
                "page_number": page_num,
                "chunk_id": c.chunk_id
            })
        else:
            # Over budget limit reached
            break

    assembled_text = "".join(formatted_parts).strip()
    return {
        "context": assembled_text,
        "chunks_used": used_chunks,
        "total_tokens": total_tokens,
        "sources": sources
    }
