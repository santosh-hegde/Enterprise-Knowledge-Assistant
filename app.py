import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import html
import logging

import streamlit as st

from src.config import DATA_DIR, ROOT, gemini_api_key
from src.logging_setup import setup_logging
from src.rag.chain import answer_question
from src.rag.memory import new_memory
from src.retrieval.vector_store import indexes_exist, load_chunks, load_vectorstore

setup_logging()
log = logging.getLogger("app")

st.set_page_config(
    page_title="Pinnacle Infotech · Knowledge Assistant",
    page_icon="▣",
    layout="centered",
)

SAMPLES = [
    "What's the leave policy here?",
    "How many days of annual leave?",
    "What do I need before international travel?",
]


def _css():
    css = (ROOT / "assets" / "app.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _index_ok() -> bool:
    return indexes_exist()


@st.cache_resource
def _load_index():
    return load_vectorstore(), load_chunks()


def _source_chips(names: list[str]) -> str:
    chips = "".join(f'<span class="source-chip">{html.escape(n)}</span>' for n in names)
    return f'<div class="source-row">{chips}</div>'


def _show_assistant(msg: dict):
    st.markdown(msg["content"])
    if msg.get("sources"):
        st.markdown(_source_chips(msg["sources"]), unsafe_allow_html=True)
    rewritten = msg.get("rewritten_query")
    asked = msg.get("asked")
    if rewritten and asked and rewritten.strip() != asked.strip():
        st.markdown(
            f'<div class="rewrite">Searched as: {html.escape(rewritten)}</div>',
            unsafe_allow_html=True,
        )
    if msg.get("snippets"):
        with st.expander("Retrieved chunks"):
            for sn in msg["snippets"]:
                st.markdown(f"**{sn['source']}** · score {sn['score']}")
                st.write(sn["preview"])


def _ask(question: str, vectorstore, chunks):
    st.session_state.messages.append({"role": "user", "content": question})
    try:
        result = answer_question(question, st.session_state.memory, vectorstore, chunks)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
                "snippets": result["snippets"],
                "rewritten_query": result.get("rewritten_query"),
                "asked": question,
            }
        )
    except Exception as e:
        log.exception("answer failed")
        st.session_state.messages.append(
            {"role": "assistant", "content": f"Something went wrong: {e}"}
        )


_css()

if "memory" not in st.session_state:
    st.session_state.memory = new_memory()
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    """
    <div class="hero">
      <div class="hero-mark">PI</div>
      <div>
        <h1>Employee Knowledge Assistant</h1>
        <p>Pinnacle Infotech · leave, travel, IT, benefits, remote work</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="sidebar-kicker">Library</div>', unsafe_allow_html=True)
    st.subheader("Indexed policies")
    if _index_ok():
        try:
            chunks = load_chunks()
            files = sorted({c.metadata.get("source") for c in chunks if c.metadata.get("source")})
            st.caption(f"{len(chunks)} chunks · {len(files)} files")
            for name in files:
                st.markdown(
                    f'<div class="doc-chip">{html.escape(name)}</div>',
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.error(str(e))
    else:
        st.warning("No index yet. Run `python ingest.py` from the project folder.")

    data_files = []
    if DATA_DIR.exists():
        data_files = sorted(
            p.name for p in DATA_DIR.iterdir() if p.suffix.lower() in {".pdf", ".docx", ".txt"}
        )
    if data_files and not _index_ok():
        st.caption("Waiting to index: " + ", ".join(data_files))

    st.divider()
    if st.button("Clear chat", use_container_width=True):
        st.session_state.memory = new_memory()
        st.session_state.messages = []
        st.rerun()

if not gemini_api_key():
    st.error("GEMINI_API_KEY is missing. Copy `.env.example` to `.env` and paste your key.")
    st.stop()

if not _index_ok():
    st.info("Index is missing, so I cannot answer yet. Run `python ingest.py` and refresh.")
    st.stop()

try:
    vectorstore, chunks = _load_index()
except Exception as e:
    log.exception("index load failed")
    st.error(f"Could not load the index: {e}")
    st.stop()

if not st.session_state.messages:
    st.markdown('<p class="suggest-label">Try one of these</p>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(SAMPLES):
        if cols[i % 2].button(q, use_container_width=True):
            _ask(q, vectorstore, chunks)
            st.rerun()

for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        if role == "assistant":
            _show_assistant(msg)
        else:
            st.markdown(msg["content"])

prompt = st.chat_input("Ask a policy question…")
if prompt:
    _ask(prompt, vectorstore, chunks)
    st.rerun()
