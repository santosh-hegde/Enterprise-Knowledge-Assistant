# Employee Knowledge Assistant

Final project (Project 2) for the GenAI Development Program.

I built a RAG chatbot over a fake company handbook for **Pinnacle Infotech**. It is not a plain chat-with-PDF. Search is hybrid (FAISS + BM25), then a local cross-encoder reranks the hits. Follow-up questions get rewritten using chat history so that "what about carry-forward?" still hits the leave policy.

## Problem

Employees ask policy questions and should get answers from internal docs, with sources. If the docs do not have the answer, the app should say so instead of guessing.

## How it works

```text
data/  -> load pdf/docx/txt -> chunk (800 tokens, 150 overlap) -> embed
                                                    |
                                              FAISS + chunk JSON
                                                    |
query -> rewrite (if there is history) -> FAISS + BM25 (RRF)
                                                    |
                                              cross-encoder rerank
                                                    |
                                         Gemini + memory
                                                    |
                                         answer + source filenames
```

Streamlit is the UI.

## Stack

- Python, LangChain, Gemini (chat/embed model names are in `src/config.py`)
- FAISS, BM25 (`rank-bm25` via LangChain), `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Streamlit, pypdf, python-docx

## Layout

```text
app.py                 streamlit
ingest.py              build the index
src/config.py          chunk size, models, k values
src/ingestion/         loaders + chunking
src/retrieval/         faiss, hybrid, rerank
src/rag/               prompts, memory, answer loop
data/                  sample policies
indexes/               created locally, not in git
sample_outputs/        example Q&A
```

## Setup

Python 3.11+ (I used 3.12).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your Gemini key in `.env` as `GEMINI_API_KEY` (Google AI Studio). Nothing else belongs there. Chunk size, overlap, retrieve k, rerank k are in `src/config.py`.

First ingest (needs the key; also downloads the reranker on the first question):

```bash
python ingest.py
streamlit run app.py
```

If you change files under `data/` or `CHUNK_SIZE` / `CHUNK_OVERLAP`, run ingest again.

To rebuild the PDF/DOCX samples (optional): `pip install fpdf2` then `python scripts/build_sample_docs.py`.

## Sample questions

See [sample_outputs/sample_qa.md](sample_outputs/sample_qa.md).

- What is the annual leave entitlement?
- What about carry-forward?  (after the first question)
- What do I need before international travel?
- What is the CEO's salary?  (should refuse)

## Design notes

**800 / 150 chunks.** Token splitter via tiktoken, not character size. 800 is roughly one policy section. 150 overlap is so a sentence on a split still lands in a chunk. Values are in `src/config.py`.

**Hybrid.** FAISS misses exact phrases like "GlobalProtect" sometimes; BM25 is the opposite. LangChain `EnsembleRetriever` fuses with RRF.

**Rerank.** Local MiniLM so I am not paying Cohere. Weak top score (`RERANK_MIN_SCORE` in config) skips the LLM and returns the not-found line.

**Rewrite.** Without it, "what about carry-forward?" retrieves random HR text. Chat history is LangChain `InMemoryChatMessageHistory`, windowed with `trim_messages` (last 6 turns). Swap the store for Redis/SQL later; the rest of the code types against `BaseChatMessageHistory`.

**Chunks on disk.** FAISS for vectors. The same chunks are saved as `indexes/chunks.json` so BM25 can be rebuilt on startup (no pickle).

## Limitations

- Needs a Gemini API key. No local LLM path.
- English only, small toy corpus.
- MiniLM reranker will miss some long or paraphrased clauses.
- FAISS `load_local` has to allow deserialization; that is fine on a laptop, not something I would expose on a public server.
- First run is slow while the cross-encoder downloads.
- The sample files are short, so you will usually get one chunk per file. The 800/150 splitter still applies if you drop in a longer handbook.
