import threading

from langchain_core.documents import Document

from src.config import RERANK_K, RERANKER_MODEL

_model = None
_lock = threading.Lock()


def _get_model():
    global _model
    with _lock:
        if _model is None:
            from sentence_transformers import CrossEncoder

            _model = CrossEncoder(RERANKER_MODEL)
        return _model


def rerank(query: str, docs: list[Document], top_k: int = RERANK_K) -> list[tuple[Document, float]]:
    if not docs:
        return []
    model = _get_model()
    pairs = [(query, d.page_content) for d in docs]
    scores = model.predict(pairs)
    ranked = sorted(zip(docs, scores), key=lambda x: float(x[1]), reverse=True)
    return [(doc, float(score)) for doc, score in ranked[:top_k]]
