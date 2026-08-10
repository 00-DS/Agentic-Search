import re
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

def store_doc(doc_id: str,
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

def list_docs() -> list[dict]:
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


def _get_doc(doc_id: str) -> str:
    """按 doc_id 取出整篇文档的完整文本。找不到抛 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc["text"]


def read_lines(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定文档从 start_line 到 end_line 的原始文本（行号从 1 开始，含两端）。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    return "\n".join(lines[start_line - 1 : end_line])


def search_doc(doc_id: str, pattern: str) -> list[dict]:
    """用正则表达式搜索指定文档内容，返回每个命中行 [{doc_id, line_number, line}]。"""
    if not doc_id:
        raise ValueError("doc_id 不能为空。")
    regex = re.compile(pattern)
    text = _get_doc(doc_id)
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if regex.search(line):
            hits.append({"doc_id": doc_id, "line_number": i, "line": line})
    return hits


def get_abstract(doc_id: str) -> str:
    """提取文档的 Abstract 段落。找不到独立 Abstract 段落时返回提示信息。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "abstract":
            for j in range(i + 1, len(lines)):
                para = lines[j].strip()
                if para:
                    end = j + 1
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    return "\n".join(lines[j:end])
            return "Abstract 标题下方无内容"
    return "未找到独立 Abstract 段落"