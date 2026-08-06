from pydantic import BaseModel


class QueryRequest(BaseModel):
    """POST /api/query 的请求体。"""
    question: str


class ConsolidateRequest(BaseModel):
    """POST /api/consolidate 的请求体"""
    session_id: str


class IngestResponse(BaseModel):
    """POST /api/ingest 的响应。"""
    doc_id: str
    filename: str


class DocumentResponse(BaseModel):
    """GET /api/documents 返回的单个文档。"""
    doc_id: str
    filename: str


class ConsolidateResponse(BaseModel):
    """POST /api/consolidate 的响应"""
    status: str
    l2_id: str