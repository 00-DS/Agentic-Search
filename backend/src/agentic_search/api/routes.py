from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import AIMessageChunk, HumanMessage

from agentic_search.agents.graph import build_graph
from agentic_search.api.schemas import (
    ConsolidateRequest,
    ConsolidateResponse,
    DocumentResponse,
    IngestResponse,
    QueryRequest,
)
from agentic_search.services.documents import list_documents, parse_pdf, store_document

router = APIRouter(prefix="/api")
graph = build_graph()

@router.post("/query", response_class=EventSourceResponse)
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    try:
        async for chunk, metadata in graph.astream(
            {"messages": [HumanMessage(content=req.question)]},
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue                              # 跳过 ToolMessage 等非 LLM chunk
            if chunk.content:                         # 文字 token：JSON 编码传输
                yield ServerSentEvent(data=chunk.content)
            elif chunk.tool_call_chunks:              # LLM 决定调工具
                for tc in chunk.tool_call_chunks:
                    if tc.get("name"):
                        yield ServerSentEvent(event="tool", data={"name": tc["name"]})
    except Exception as e:
        yield ServerSentEvent(data=f"[错误：{e}]")

@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile):
    """上传 PDF，提取纯文本并存入 MongoDB（零文件系统依赖）。"""
    if not file.filename:
        raise HTTPException(422, "缺少文件名（filename）")
    pdf_bytes = await file.read()
    text = parse_pdf(pdf_bytes)
    doc_id = Path(file.filename).stem
    store_document(doc_id, file.filename, text)

    return IngestResponse(doc_id=doc_id, filename=file.filename)

@router.get("/documents", response_model=list[DocumentResponse])
async def documents():
    """列出已上传的文档。"""
    return list_documents()

@router.post("/consolidate", response_model=ConsolidateResponse)
async def consolidate(req: ConsolidateRequest):
    """手动触发 L2 会话记忆整合。

    注意：L2 整合逻辑在模块 4 的 memory/store.py 中实现。
    本路由负责把 HTTP 请求转发到记忆层；此处为占位，
    模块 4 将补全真正的整合调用。
    """
    # 模块 4 将在此处调用 memory.store 的整合函数
    # from agentic_search.memory.store import consolidate_session
    # return ConsolidateResponse(status="ok", l2_id=consolidate_session(req.session_id))
    return ConsolidateResponse(status="pending", l2_id="")
