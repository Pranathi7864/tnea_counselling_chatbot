"""
embeddings.py
-------------
Converts text chunks into vector embeddings using
sentence-transformers and stores them in a FAISS index.
Run this ONCE to build the vector store. No need to run again
unless your documents change.
"""

import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from ingest import load_all_documents

# path
BASE_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store")
INDEX_PATH       = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")
CHUNKS_PATH      = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")

# model 
# all-mpnet-base-v2 → 384-dim, better semantic understanding than MiniLM
MODEL_NAME = "all-mpnet-base-v2"


# generate embeddings
def generate_embeddings(chunks: list[str]) -> np.ndarray:
    """
    Convert list of text chunks into a numpy array of embeddings.
    Shape: (num_chunks, 384)
    """
    print(f"[INFO] Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"[INFO] Generating embeddings for {len(chunks)} chunks...")
    # show_progress_bar gives a nice progress display in terminal
    embeddings = model.encode(
        chunks,
        show_progress_bar=True,
        convert_to_numpy=True,
        batch_size=64
    )
    print(f"[INFO] Embeddings shape: {embeddings.shape}")
    return embeddings


# Build & save FAISS index
def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """
    Build a FAISS flat L2 index from embeddings.
    IndexFlatL2 = exact nearest neighbour search (best for small-medium datasets)
    """
    dimension = embeddings.shape[1]  # 384 for MiniLM
    index = faiss.IndexFlatL2(dimension)

    # FAISS needs float32
    index.add(embeddings.astype(np.float32))
    print(f"[INFO] FAISS index built. Total vectors: {index.ntotal}")
    return index


#save to disk
def save_vector_store(index: faiss.IndexFlatL2, chunks: list[str]):
    """
    Save FAISS index and chunks list to vector_store/ folder.
    chunks.pkl  → original text (needed to return readable results)
    faiss_index.bin → the vector index
    """
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

    # Save FAISS index
    faiss.write_index(index, INDEX_PATH)
    print(f"[INFO] FAISS index saved to: {INDEX_PATH}")

    # Save chunks as pickle (to map index back to text)
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print(f"[INFO] Chunks saved to: {CHUNKS_PATH}")


#load from disk
def load_vector_store():
    """
    Load existing FAISS index and chunks from disk.
    Called by retriever.py — no need to rebuild every time.
    Returns: (index, chunks)
    """
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(
            "[ERROR] Vector store not found. Run embeddings.py first!"
        )

    print("[INFO] Loading FAISS index from disk...")
    index = faiss.read_index(INDEX_PATH)

    print("[INFO] Loading chunks from disk...")
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    print(f"[INFO] Vector store loaded. {index.ntotal} vectors, {len(chunks)} chunks.")
    return index, chunks


# ── 5. Master Function ─────────────────────────────────────────────────────
def build_vector_store():
    """
    Full pipeline:
    load documents → generate embeddings → build FAISS → save to disk
    Run this once from terminal: python src/embeddings.py
    """
    print("\n===== VECTOR STORE BUILDING STARTED =====")

    # Step 1: Load & chunk documents
    chunks = load_all_documents()

    # Step 2: Generate embeddings
    embeddings = generate_embeddings(chunks)

    # Step 3: Build FAISS index
    index = build_faiss_index(embeddings)

    # Step 4: Save everything
    save_vector_store(index, chunks)

    print("===== VECTOR STORE BUILDING DONE =====\n")
    print(f"[SUCCESS] {len(chunks)} chunks embedded and saved!")
    print("[NEXT] Now run: python src/retriever.py")


# ── Quick run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    build_vector_store()