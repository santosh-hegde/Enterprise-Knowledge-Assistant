import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from src.logging_setup import setup_logging
from src.ingestion.pipeline import run_ingest


if __name__ == "__main__":
    setup_logging()
    n = run_ingest()
    print(f"done. {n} chunks written to indexes/")
