"""
Full RAG Document Ingestion & Chunking Pipeline.
Reads authentic ICAR textbooks and manuals, splits into semantic chunks,
computes embeddings, and stores them in persistent ChromaDB.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("farmer_advisor.rag_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CHROMA_PERSIST_DIR = "data/chroma"
MANUALS_DIR = "data/textbooks_and_manuals"
ADVISORIES_DIR = "data/advisories"

def chunk_markdown_manual(file_path: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Parses a markdown reference manual into semantic chunks based on headers and paragraphs.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = os.path.basename(file_path)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else filename.replace(".md", "").replace("_", " ")

    # Detect crop entity from filename and content
    crop = "General Agriculture"
    if "Cotton" in filename or "CICR" in filename:
        crop = "Cotton"
    elif "Jute" in filename or "CRIJAF" in filename:
        crop = "Jute"
    elif "Tomato" in filename or "IIHR" in filename:
        crop = "Tomato"
    elif "Wheat" in filename or "IIWBR" in filename:
        crop = "Wheat"
    elif "Rice" in filename or "Paddy" in filename or "NRRI" in filename:
        crop = "Paddy / Rice"

    # Identify publishing authority
    source_match = re.search(r"\*\*(?:Publishing Body|Publication Authority):\*\*\s*(.+)$", content, re.MULTILINE)
    source = source_match.group(1).strip() if source_match else "ICAR Reference Manual"

    # Split by major markdown sections (## or ###)
    sections = re.split(r"(?=\n#{2,3}\s+)", content)
    chunks = []
    chunk_counter = 0

    for section in sections:
        section = section.strip()
        if not section or len(section) < 40:
            continue

        # Extract section heading
        sec_header_match = re.search(r"^#{2,3}\s+(.+)$", section, re.MULTILINE)
        section_name = sec_header_match.group(1).strip() if sec_header_match else "General Advisory"

        # Determine topic
        sec_lower = section.lower()
        topic = "General"
        if any(w in sec_lower for w in ["sow", "calendar", "season", "window", "date"]):
            topic = "Sowing & Calendar"
        elif any(w in sec_lower for w in ["fertiliz", "npk", "urea", "dap", "nutrient", "zinc"]):
            topic = "Fertilizer & Nutrition"
        elif any(w in sec_lower for w in ["irrigat", "water", "moisture", "drip", "cri"]):
            topic = "Irrigation & Water"
        elif any(w in sec_lower for w in ["pest", "disease", "bollworm", "curl", "rust", "rot", "ipm"]):
            topic = "Pest & Disease IPM"

        # If section is longer than chunk_size, split by paragraphs or sliding window
        paragraphs = section.split("\n\n")
        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_len + len(para) <= chunk_size or not current_chunk:
                current_chunk.append(para)
                current_len += len(para)
            else:
                chunk_text = "\n\n".join(current_chunk)
                chunk_counter += 1
                chunks.append({
                    "id": f"{crop[:3].upper()}_MANUAL_{chunk_counter:03d}",
                    "text": f"Document: {doc_title}\nSection: {section_name}\nCrop: {crop}\nAuthority: {source}\n\n{chunk_text}",
                    "metadata": {
                        "doc_title": doc_title,
                        "section": section_name,
                        "crop": crop,
                        "topic": topic,
                        "source": source,
                        "file": filename
                    }
                })
                # Maintain overlap
                current_chunk = [para]
                current_len = len(para)

        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunk_counter += 1
            chunks.append({
                "id": f"{crop[:3].upper()}_MANUAL_{chunk_counter:03d}",
                "text": f"Document: {doc_title}\nSection: {section_name}\nCrop: {crop}\nAuthority: {source}\n\n{chunk_text}",
                "metadata": {
                    "doc_title": doc_title,
                    "section": section_name,
                    "crop": crop,
                    "topic": topic,
                    "source": source,
                    "file": filename
                }
            })

    return chunks

def ingest_all_manuals_and_advisories():
    """Ingests all authentic markdown manuals into ChromaDB."""
    logger.info("Starting ingestion of authentic ICAR reference manuals & advisories...")
    all_chunks = []

    # 1. Ingest markdown textbooks and manuals
    if os.path.exists(MANUALS_DIR):
        for fname in os.listdir(MANUALS_DIR):
            if fname.endswith(".md"):
                fpath = os.path.join(MANUALS_DIR, fname)
                logger.info(f"Chunking reference manual: {fname}...")
                chunks = chunk_markdown_manual(fpath)
                logger.info(f"  -> Generated {len(chunks)} semantic chunks from {fname}")
                all_chunks.extend(chunks)

    logger.info(f"Total reference chunks prepared for indexing: {len(all_chunks)}")

    # 2. Index into ChromaDB
    import chromadb
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Use collection
    collection = chroma_client.get_or_create_collection(
        name="indian_farmer_advisories",
        metadata={"description": "ICAR Textbooks, Extension Manuals and State Packages of Practices"}
    )

    logger.info(f"Writing {len(all_chunks)} chunks to ChromaDB at '{CHROMA_PERSIST_DIR}'...")
    ids = [c["id"] for c in all_chunks]
    texts = [c["text"] for c in all_chunks]
    metas = [c["metadata"] for c in all_chunks]

    # Batch upsert into ChromaDB
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=texts[i:i+batch_size],
            metadatas=metas[i:i+batch_size]
        )

    logger.info(f"✅ ChromaDB indexing complete! Collection now holds {collection.count()} chunks.")

    # 3. Verification test: Sample query retrieval
    logger.info("\n--- RAG Retrieval Verification Test ---")
    test_queries = [
        "What month to sow Cotton in Maharashtra?",
        "When is the critical first irrigation (CRI stage) for Wheat?",
        "How to prevent Blossom End Rot in Tomato?",
        "Jute retting duration with CRIJAF Sona"
    ]
    for q in test_queries:
        res = collection.query(query_texts=[q], n_results=1)
        doc = res["documents"][0][0]
        meta = res["metadatas"][0][0]
        dist = res["distances"][0][0] if "distances" in res else 0.0
        logger.info(f"Query: '{q}'")
        logger.info(f"  Retrieved Chunk ID: {meta.get('doc_title')} -> {meta.get('section')} (Distance: {dist:.3f})")
        logger.info(f"  Excerpt: {doc[:160]}...\n")

if __name__ == "__main__":
    ingest_all_manuals_and_advisories()
