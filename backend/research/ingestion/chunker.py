import re
import hashlib
from typing import List
from datetime import datetime
from backend.models.schemas import Source, DocumentChunk

class DocumentChunker:
    """
    Boundary-preserving document chunker that operates STRICTLY on genuine acquired source text.
    Extracts chunks with SHA-256 integrity hash, character offsets, and section labels.
    """
    def chunk_sources(self, sources: List[Source]) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        for src in sources:
            if not src.raw_content or len(src.raw_content.strip()) == 0:
                continue

            raw_text = src.raw_content.strip()
            # Split by paragraph or double newline
            raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", raw_text) if len(p.strip()) > 0]
            if not raw_paragraphs:
                raw_paragraphs = [raw_text]

            # Segment large paragraphs into sentence-bounded segments
            segmented_paragraphs = []
            for p in raw_paragraphs:
                if len(p) <= 900:
                    segmented_paragraphs.append(p)
                else:
                    sentences = re.split(r"(?<=[.!?])\s+", p)
                    buf = []
                    curr_len = 0
                    for s in sentences:
                        buf.append(s)
                        curr_len += len(s) + 1
                        if curr_len >= 750:
                            segmented_paragraphs.append(" ".join(buf).strip())
                            buf = []
                            curr_len = 0
                    if buf:
                        segmented_paragraphs.append(" ".join(buf).strip())

            current_offset = 0
            for idx, paragraph in enumerate(segmented_paragraphs):
                content_hash = hashlib.sha256(paragraph.encode("utf-8")).hexdigest()[:16]
                end_offset = current_offset + len(paragraph)

                section_name = "Overview & Summary" if idx == 0 else f"Section {idx + 1}"
                if src.source_type.value == "ACADEMIC_PAPER":
                    section_name = "Abstract & Findings"

                chunk_id = f"chk-{src.id}-{idx + 1}"
                chunks.append(DocumentChunk(
                    id=chunk_id,
                    source_id=src.id,
                    text=paragraph,
                    section=section_name,
                    page_number=1,
                    start_offset=current_offset,
                    end_offset=end_offset,
                    content_hash=content_hash,
                    retrieved_at=src.retrieval_timestamp
                ))
                current_offset = end_offset + 2

        return chunks
