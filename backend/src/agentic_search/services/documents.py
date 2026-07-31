from datetime import UTC, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import pymupdf
from pymongo import MongoClient
from agentic_search.configs.config import settings


def parse_pdf(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{path}")
    with pymupdf.open(p) as doc:
        parts = [page.get_text("text") for page in doc]
    return "\n".join(parts)

_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_documents_collection = _db["documents"]

def store_document(doc_id: str, 
                   filename: str,
                   markdown: str) ->None:
    _documents_collection.insert_one(
        {
            "doc_id": doc_id,
            "filename": filename,
            "markdown": markdown,
            "uploaded_at": datetime.now(ZoneInfo("Asia/Shanghai")),
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

def read_document(doc_id: str) -> str:
    doc = _documents_collection.find_one(
        {
            "doc_id": doc_id
        }
    )
    if doc is None:
        raise KeyError(f"文档不存在：{doc_id}")
    return doc["markdown"]