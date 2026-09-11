import logging

from src.config import RERANK_MIN_SCORE, gemini_api_key
from langchain_community.vectorstores import FAISS
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document

from src.models import chat_llm, response_text
from src.rag.memory import history_text
from src.rag.prompts import ANSWER_PROMPT, NOT_FOUND, REWRITE_PROMPT
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import rerank

log = logging.getLogger(__name__)


def _llm():
    return chat_llm()


def rewrite_query(question: str, memory: BaseChatMessageHistory) -> str:
    text = history_text(memory)
    if not text.strip():
        return question
    prompt = REWRITE_PROMPT.format(history=text, question=question)
    out = response_text(_llm().invoke(prompt))
    log.info("rewrite: %s -> %s", question, out)
    return out or question


def _format_context(ranked: list[tuple[Document, float]]) -> str:
    blocks = []
    for doc, score in ranked:
        src = doc.metadata.get("source", "unknown")
        blocks.append(f"[{src}]\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)


def source_names(ranked: list[tuple[Document, float]]) -> list[str]:
    names = []
    for doc, _ in ranked:
        src = doc.metadata.get("source")
        if src and src not in names:
            names.append(src)
    return names


def answer_question(
    question: str,
    memory: BaseChatMessageHistory,
    vectorstore: FAISS,
    chunks: list[Document],
) -> dict:
    if not gemini_api_key():
        raise RuntimeError("GEMINI_API_KEY is not set.")

    standalone = rewrite_query(question, memory)
    retrieved = hybrid_search(standalone, vectorstore, chunks)
    ranked = rerank(standalone, retrieved)
    log.info("retrieved %s, kept %s after rerank", len(retrieved), len(ranked))

    if not ranked or ranked[0][1] < RERANK_MIN_SCORE:
        log.info("low/no relevance (top score=%s)", ranked[0][1] if ranked else None)
        answer = NOT_FOUND
        sources = []
        snippets = []
    else:
        context = _format_context(ranked)
        prompt = ANSWER_PROMPT.format(context=context, question=standalone)
        answer = response_text(_llm().invoke(prompt))
        sources = source_names(ranked)
        snippets = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "score": round(score, 3),
                "preview": doc.page_content[:240].replace("\n", " "),
            }
            for doc, score in ranked
        ]

    memory.add_user_message(question)
    memory.add_ai_message(answer)
    return {
        "answer": answer,
        "sources": sources,
        "snippets": snippets,
        "rewritten_query": standalone,
    }
