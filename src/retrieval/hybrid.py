from src.config import HYBRID_WEIGHTS, RETRIEVE_K
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def hybrid_search(query: str, vectorstore: FAISS, chunks: list[Document]) -> list[Document]:
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVE_K})
    bm25 = BM25Retriever.from_documents(chunks)
    bm25.k = RETRIEVE_K
    mixed = EnsembleRetriever(
        retrievers=[faiss_retriever, bm25],
        weights=HYBRID_WEIGHTS,
    )
    docs = mixed.invoke(query)
    return _dedupe(docs)


def _dedupe(docs: list[Document]) -> list[Document]:
    seen = set()
    out = []
    for d in docs:
        key = (d.metadata.get("source"), d.metadata.get("chunk_index"), d.page_content[:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out
