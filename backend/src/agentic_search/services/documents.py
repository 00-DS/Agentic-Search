from datetime import datetime, timezone

import pymupdf
from pymongo import MongoClient

from agentic_search.configs.config import settings


def parse_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流提取纯文本（不读文件、不落盘）。"""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(str(page.get_text("text")) for page in doc)

_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_documents_collection = _db["documents"]

def store_document(doc_id: str,
                   filename: str,
                   text: str) -> None:
    _documents_collection.insert_one(
        {
            "doc_id": doc_id,
            "filename": filename,
            "text": text,
            "uploaded_at": datetime.now(timezone.utc),
        }
    )

def list_documents() -> list[dict]:
    cursor = _documents_collection.find(
        {},
        {
            "doc_id": 1,
            "filename": 1,
            "_id": 0,
        }
    )
    return [
        {
            "doc_id": doc["doc_id"],
            "filename": doc["filename"]
        }
        for doc in cursor
    ]