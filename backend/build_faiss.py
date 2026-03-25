"""
Build FAISS index LOCALLY with embeddings.

This script MUST be run locally to create a compatible FAISS index.
DO NOT run this on Render - it requires heavy ML dependencies.

Usage:
    pip install sentence-transformers torch transformers pypdf
    python build_faiss.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration
PDF_PATH = Path(__file__).parent / "data" / "knowledge_base.pdf"
FAISS_INDEX_PATH = Path(__file__).parent / "data" / "faiss_index"
HF_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def build_faiss_index():
    """Build FAISS index from PDF."""
    
    print("=" * 60)
    print("FAISS INDEX BUILDER")
    print("=" * 60)
    
    # Check if PDF exists
    if not PDF_PATH.exists():
        print(f"❌ PDF not found: {PDF_PATH}")
        return False
    
    print(f"📄 PDF: {PDF_PATH}")
    print(f"📁 Output: {FAISS_INDEX_PATH}")
    print(f"🧠 Model: {HF_EMBEDDING_MODEL}")
    print()
    
    # 1. Load PDF
    print("1️⃣ Loading PDF...")
    loader = PyPDFLoader(str(PDF_PATH))
    documents = loader.load()
    print(f"   ✅ Loaded {len(documents)} page(s)")
    
    # 2. Split into chunks
    print("2️⃣ Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"   ✅ Created {len(chunks)} chunk(s)")
    
    # 3. Initialize embeddings
    print("3️⃣ Initializing embeddings (this may take a minute)...")
    embeddings = HuggingFaceEmbeddings(
        model_name=HF_EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
    )
    print(f"   ✅ Embeddings ready")
    
    # 4. Build FAISS index
    print("4️⃣ Building FAISS index...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    print(f"   ✅ Index built with {vector_store.index.ntotal} vectors")
    
    # 5. Save to disk
    print("5️⃣ Saving to disk...")
    FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(FAISS_INDEX_PATH))
    print(f"   ✅ Saved to {FAISS_INDEX_PATH}")
    
    print()
    print("=" * 60)
    print("✅ FAISS INDEX BUILT SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Commit the index: git add backend/data/faiss_index/")
    print("  2. Push to GitHub: git commit -m 'add: rebuilt FAISS index'")
    print("  3. Deploy to Render")
    print()
    
    return True


if __name__ == "__main__":
    build_faiss_index()
