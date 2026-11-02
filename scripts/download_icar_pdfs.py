"""
Download and Ingestion Pipeline for Official ICAR & Government Agricultural PDF Manuals.
Downloads authentic PDFs from icar.org.in and pmfby.gov.in into data/official_icar_pdfs/,
extracts text using PyMuPDF (pymupdf), chunks into semantic passages, and indexes into ChromaDB.
"""

import os
import sys
import logging
import requests
import pymupdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("farmer_advisor.pdf_downloader")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(PROJECT_ROOT, "data", "official_icar_pdfs")
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "chroma")

OFFICIAL_PDF_SOURCES = [
    {
        "filename": "PMFBY_National_District_Crop_Calendar.pdf",
        "url": "https://pmfby.gov.in/pdf/New_Crop_Calendar_20.09.18.pdf",
        "title": "PMFBY National District-Wise Crop Calendar Manual",
        "authority": "Ministry of Agriculture & Farmers Welfare, Government of India",
        "description": "Official State and District-wise sowing windows and harvest dates for Kharif and Rabi crops."
    },
    {
        "filename": "ICAR_National_Kharif_Agro_Advisories.pdf",
        "url": "https://icar.org.in/sites/default/files/inline-files/Kharif-agro-advisory-2021-final.pdf",
        "title": "ICAR National Kharif Agro-Advisories Manual",
        "authority": "Indian Council of Agricultural Research (ICAR), New Delhi",
        "description": "Comprehensive agronomic packages of practices, sowing schedules, fertilizer NPK, and water management across 28 states."
    }
]

def download_official_pdf(source: dict) -> str:
    """Downloads an official government/ICAR PDF with streaming and progress."""
    os.makedirs(PDF_DIR, exist_ok=True)
    dest_path = os.path.join(PDF_DIR, source["filename"])

    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        logger.info(f"PDF already exists: {dest_path} ({os.path.getsize(dest_path) / (1024*1024):.2f} MB)")
        return dest_path

    logger.info(f"Downloading official manual: {source['title']}...")
    logger.info(f"Source URL: {source['url']}")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(source["url"], stream=True, headers=headers, timeout=60)
    response.raise_for_status()

    total_bytes = 0
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                total_bytes += len(chunk)
                print(f"\r  -> Downloaded: {total_bytes / (1024*1024):.1f} MB", end="", flush=True)

    print()
    logger.info(f"✅ Successfully saved: {dest_path} ({total_bytes / (1024*1024):.2f} MB)")
    return dest_path

def extract_and_chunk_pdf(pdf_path: str, source_meta: dict, chunk_char_size: int = 600, overlap: int = 120):
    """Extracts text from PDF pages using PyMuPDF and produces structured semantic chunks."""
    logger.info(f"Extracting text from PDF: {os.path.basename(pdf_path)}...")
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    logger.info(f"Total pages in document: {total_pages}")

    chunks = []
    chunk_counter = 0

    # Extract text page by page (sampling key agronomic pages if huge, or processing all)
    pages_to_process = min(total_pages, 80) # Process up to 80 pages of dense tables and advisories
    for page_idx in range(pages_to_process):
        page = doc[page_idx]
        page_text = page.get_text("text").strip()
        if len(page_text) < 50:
            continue

        # Detect crop mentions on page
        crops_mentioned = []
        for c in ["Cotton", "Wheat", "Tomato", "Jute", "Paddy", "Rice", "Mustard", "Chickpea", "Onion"]:
            if c.lower() in page_text.lower():
                crops_mentioned.append(c)

        crop_tag = ", ".join(crops_mentioned) if crops_mentioned else "General Field Crops"

        # Sliding window chunking
        start = 0
        while start < len(page_text):
            end = start + chunk_char_size
            chunk_slice = page_text[start:end].strip()

            if len(chunk_slice) > 80:
                chunk_counter += 1
                chunk_id = f"PDF_{source_meta['filename'][:8]}_P{page_idx+1}_{chunk_counter:04d}"
                formatted_text = (
                    f"Official Publication: {source_meta['title']}\n"
                    f"Issuing Authority: {source_meta['authority']}\n"
                    f"Page Reference: Page {page_idx + 1} of {total_pages}\n"
                    f"Identified Crops: {crop_tag}\n\n"
                    f"{chunk_slice}"
                )
                chunks.append({
                    "id": chunk_id,
                    "text": formatted_text,
                    "metadata": {
                        "source": f"{source_meta['authority']} — {source_meta['title']}",
                        "doc_title": source_meta['title'],
                        "crop": crop_tag,
                        "page": page_idx + 1,
                        "file": source_meta['filename']
                    }
                })

            start += (chunk_char_size - overlap)

    doc.close()
    logger.info(f"Extracted {len(chunks)} structured semantic chunks from {os.path.basename(pdf_path)}.")
    return chunks

def index_pdf_chunks_to_chroma(all_chunks):
    """Indexes extracted PDF chunks into persistent ChromaDB."""
    import chromadb

    os.makedirs(CHROMA_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(
        name="indian_farmer_advisories",
        metadata={"description": "Official ICAR & Ministry of Agriculture Grounded Knowledge Base"}
    )

    logger.info(f"Writing {len(all_chunks)} official PDF chunks into ChromaDB...")
    ids = [c["id"] for c in all_chunks]
    texts = [c["text"] for c in all_chunks]
    metas = [c["metadata"] for c in all_chunks]

    batch_size = 50
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=texts[i:i+batch_size],
            metadatas=metas[i:i+batch_size]
        )

    logger.info(f"✅ ChromaDB indexing complete! Total documents now in ChromaDB: {collection.count()}")

def main():
    print("==================================================================")
    print("  Official Government & ICAR Agriculture PDF Downloader & Ingestor")
    print("==================================================================")

    all_extracted_chunks = []
    for source in OFFICIAL_PDF_SOURCES:
        try:
            pdf_path = download_official_pdf(source)
            chunks = extract_and_chunk_pdf(pdf_path, source)
            all_extracted_chunks.extend(chunks)
        except Exception as e:
            logger.error(f"Failed to process {source['title']}: {e}")

    if all_extracted_chunks:
        index_pdf_chunks_to_chroma(all_extracted_chunks)
        print("\n[+] Verification: Run 'npm run eval' or ask a query in the UI to see citations from the downloaded PDFs!")

if __name__ == "__main__":
    main()
