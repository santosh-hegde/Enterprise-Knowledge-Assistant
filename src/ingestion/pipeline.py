import json
import logging
import shutil

from src.config import (
    BM25_PATH,
    DATA_DIR,
    FAISS_DIR,
    INDEX_DIR,
    gemini_api_key,
)
from langchain_community.vectorstores import FAISS
from src.ingestion.chunking import split_documents
from src.ingestion.loaders import load_documents
from src.models import embeddings as make_embeddings

log = logging.getLogger(__name__)


def run_ingest() -> int:
    if not gemini_api_key():
        raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")

    docs = load_documents(DATA_DIR)
    if not docs:
        raise RuntimeError(f"No readable pdf/docx/txt files in {DATA_DIR}")

    chunks = split_documents(docs)
    if not chunks:
        raise RuntimeError("Documents loaded but chunking produced nothing.")

    embeddings = make_embeddings()
    store = FAISS.from_documents(chunks, embeddings)

    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    INDEX_DIR.mkdir(parents=True)
    store.save_local(str(FAISS_DIR))

    payload = [
        {"page_content": c.page_content, "metadata": dict(c.metadata)}
        for c in chunks
    ]
    BM25_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    sources = {d.metadata.get("source") for d in docs}
    log.info("indexed %s chunks from %s files", len(chunks), len(sources))
    return len(chunks)
