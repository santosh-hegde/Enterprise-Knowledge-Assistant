import os

# FAISS and PyTorch both ship libomp; on macOS that aborts the process.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
INDEX_DIR = ROOT / "indexes"
FAISS_DIR = INDEX_DIR / "faiss"
BM25_PATH = INDEX_DIR / "chunks.json"

CHAT_MODEL = "gemini-3.1-flash-lite"
EMBED_MODEL = "models/gemini-embedding-001"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TIKTOKEN_ENCODING = "cl100k_base"

RETRIEVE_K = 20
RERANK_K = 10
HYBRID_WEIGHTS = [0.5, 0.5]  # faiss, bm25
# MiniLM logits on these long chunks are often negative even for a real hit.
# "annual leave entitlement" scored about -6.5; "CEO salary" about -10.
RERANK_MIN_SCORE = -8.0
MEMORY_WINDOW = 6

SUPPORTED_EXTS = {".pdf", ".docx", ".txt"}


def gemini_api_key():
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if key and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = key
    return key
