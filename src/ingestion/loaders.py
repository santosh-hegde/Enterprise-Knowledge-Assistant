import logging
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader
from docx import Document as DocxFile

from src.config import SUPPORTED_EXTS

log = logging.getLogger(__name__)


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _read_docx(path: Path) -> str:
    doc = DocxFile(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


READERS = {
    ".pdf": _read_pdf,
    ".docx": _read_docx,
    ".txt": _read_txt,
}


def load_documents(data_dir: Path) -> list[Document]:
    docs = []
    if not data_dir.exists():
        log.error("data folder missing: %s", data_dir)
        return docs

    files = sorted(p for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS)
    for path in files:
        try:
            text = READERS[path.suffix.lower()](path).strip()
            if not text:
                log.warning("skipped empty file %s", path.name)
                continue
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": path.name, "path": str(path)},
                )
            )
            log.info("loaded %s (%s chars)", path.name, len(text))
        except Exception:
            log.exception("failed to read %s, skipping", path.name)
    return docs
