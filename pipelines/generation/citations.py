import re
import uuid
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Citation:
    reference: str        # "Source 1"
    chunk_id: uuid.UUID
    document_name: str
    page_number: int | None
    content_preview: str  # first 100 chars
    invalid_citation: bool = False

def parse_citations(response_text: str, sources_metadata: List[Dict[str, Any]]) -> List[Citation]:
    # Find all patterns matching [Source N]
    matches = re.findall(r"\[Source (\d+)\]", response_text)
    citations = []

    for m in matches:
        idx = int(m) - 1
        ref_str = f"Source {m}"
        
        # Check for hallucinated citation
        if idx < 0 or idx >= len(sources_metadata):
            citations.append(Citation(
                reference=ref_str,
                chunk_id=uuid.UUID(int=0),
                document_name="Unknown",
                page_number=None,
                content_preview="",
                invalid_citation=True
            ))
            continue
            
        src = sources_metadata[idx]
        citations.append(Citation(
            reference=ref_str,
            chunk_id=uuid.UUID(str(src["chunk_id"])),
            document_name=src.get("document_name", "unknown_doc"),
            page_number=src.get("page_number"),
            content_preview="", # can map if full chunks are passed
            invalid_citation=False
        ))
        
    return citations
