from pydantic import BaseModel


class QueryRequest(BaseModel):
    """POST /api/query 的请求体。"""

    question: str
    session_id: str = (
        "default"  # 会话 ID（模块 3 前端传 currentSessionId；缺省 default）
    )


class IngestResponse(BaseModel):
    """POST /api/ingest 的响应。"""

    doc_id: str
    filename: str


class DocumentResponse(BaseModel):
    """GET /api/documents 返回的单个文档。"""

    doc_id: str
    filename: str


class ConsolidateRequest(BaseModel):
    """POST /api/consolidate 的请求体。"""

    session_id: str  # 会话 ID（level="L5" 时仅作占位，画像整合与具体会话无关）
    level: str = "L2"  # 整合级别："L2" 会话摘要 / "L5" 用户画像


class ConsolidateResponse(BaseModel):
    """POST /api/consolidate 的响应。"""

    status: str  # 状态
    l2_id: str = ""  # level="L2" 时为生成的 L2 记忆 ID，否则为空
    profile_id: str = ""  # level="L5" 时为画像记忆 ID，否则为空
