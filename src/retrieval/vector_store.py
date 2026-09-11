import json

from src.config import BM25_PATH, FAISS_DIR
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from src.models import embeddings as make_embeddings


def indexes_exist() -> bool:
    return (FAISS_DIR / "index.faiss").exists() and BM25_PATH.exists()


def load_vectorstore() -> FAISS:
    embeddings = make_embeddings()
    return FAISS.load_local(
        str(FAISS_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def load_chunks() -> list[Document]:
    raw = json.loads(BM25_PATH.read_text(encoding="utf-8"))
    return [Document(page_content=item["page_content"], metadata=item.get("metadata") or {}) for item in raw]
