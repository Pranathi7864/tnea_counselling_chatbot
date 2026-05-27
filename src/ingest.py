"""
ingest.py
---------
Loads all TNEA documents (PDFs + Excel) and converts them into
clean text chunks ready for embedding.
"""

import os
import pdfplumber
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")

PDF_FILES  = [
    os.path.join(DATA_DIR, "Information_about_colleges.pdf"),
    os.path.join(DATA_DIR, "2_Information_Brochure_2026.pdf"),
]
EXCEL_FILE = os.path.join(DATA_DIR, "tnea 2025.xlsx")


# ── 1. PDF Loader ──────────────────────────────────────────────────────────
def load_pdfs() -> str:
    """Extract raw text from all PDF files."""
    all_text = ""
    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"[WARNING] PDF not found: {pdf_path}")
            continue
        print(f"[INFO] Loading PDF: {os.path.basename(pdf_path)}")
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
    return all_text


# ── 2. Text Splitter ───────────────────────────────────────────────────────
def split_text(raw_text: str) -> list[str]:
    """
    Split PDF raw text into overlapping chunks for embedding.
    chunk_size=500   → each chunk ~500 characters
    chunk_overlap=50 → 50 char overlap so context isn't lost
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "|", " ", ""]
    )
    chunks = splitter.split_text(raw_text)
    return chunks


# ── 3. Excel Loader ────────────────────────────────────────────────────────
def load_excel() -> list[str]:
    """
    Each college+branch combo becomes ONE dedicated chunk.
    Returns a list directly — no further splitting needed.
    """
    if not os.path.exists(EXCEL_FILE):
        print(f"[WARNING] Excel not found: {EXCEL_FILE}")
        return []

    print(f"[INFO] Loading Excel: tnea 2025.xlsx")
    df = pd.read_excel(EXCEL_FILE)
    df.columns = df.columns.str.strip()

    for col in ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]:
        df[col] = df[col].astype(str).str.replace("—", "N/A").str.strip()

    chunks = []
    for _, row in df.iterrows():
        college = str(row.get("College Name", "")).strip()
        code    = str(row.get("Code", "")).strip()
        branch  = str(row.get("Branch", "")).strip()

        if not college or not branch or branch == "nan":
            continue

        # Descriptive chunk format — helps embedding match accurately
        chunk = (
            f"TNEA Cutoff Data 2025\n"
            f"College Name: {college}\n"
            f"TNEA Code: {code}\n"
            f"Branch: {branch}\n"
            f"OC Cutoff Marks: {row.get('OC','N/A')}\n"
            f"BC Cutoff Marks: {row.get('BC','N/A')}\n"
            f"BCM Cutoff Marks: {row.get('BCM','N/A')}\n"
            f"MBC Cutoff Marks: {row.get('MBC','N/A')}\n"
            f"SC Cutoff Marks: {row.get('SC','N/A')}\n"
            f"SCA Cutoff Marks: {row.get('SCA','N/A')}\n"
            f"ST Cutoff Marks: {row.get('ST','N/A')}\n"
        )
        chunks.append(chunk)

    print(f"[INFO] Excel chunks created: {len(chunks)}")
    return chunks


# ── 4. Master Function ─────────────────────────────────────────────────────
def load_all_documents() -> list[str]:
    """
    Returns combined list of chunks from PDFs + Excel.
    Excel rows are kept as individual chunks (no splitting).
    PDF text is split normally.
    """
    print("\n===== DOCUMENT INGESTION STARTED =====")

    # PDFs — split into chunks normally
    pdf_text     = load_pdfs()
    pdf_chunks   = split_text(pdf_text) if pdf_text else []

    # Excel — each row is already one chunk, no splitting
    excel_chunks = load_excel()

    # Combine both
    all_chunks = pdf_chunks + excel_chunks

    print(f"[INFO] PDF chunks   : {len(pdf_chunks)}")
    print(f"[INFO] Excel chunks : {len(excel_chunks)}")
    print(f"[INFO] Total chunks : {len(all_chunks)}")
    print("===== DOCUMENT INGESTION DONE =====\n")
    return all_chunks


# ── Quick test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chunks = load_all_documents()
    print(f"\nSample PDF chunk:\n{chunks[0]}")
    print(f"\nSample Excel chunk:\n{chunks[-1]}")