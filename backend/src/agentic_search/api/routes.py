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
from agentic_search.memory.db import load_memories, upsert_l2, upsert_profile
from agentic_search.memory.memory import consolidate_l2, consolidate_profile
from agentic_search.services.documents import list_docs, parse_pdf, store_doc

router = APIRouter(prefix="/api")
graph = build_graph()


@router.post("/query", response_class=EventSourceResponse)
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    try:
        async for chunk, metadata in graph.astream(
            {
                "messages": [HumanMessage(content=req.question)],
                "session_id": req.session_id,
            },
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue  # 跳过 ToolMessage 等非 LLM chunk
            if chunk.content:  # 文字 token：JSON 编码传输
                yield ServerSentEvent(data=chunk.content)
            elif chunk.tool_call_chunks:  # LLM 决定调工具
                for tc in chunk.tool_call_chunks:
                    if tc.get("name"):
                        yield ServerSentEvent(event="tool", data={"name": tc["name"]})
    except Exception as e:  # noqa: BLE001 流错误边界：异常转成 SSE 错误事件，防连接静默死
        yield ServerSentEvent(data=f"[错误：{e}]")


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile):
    """上传 PDF，提取纯文本并存入 MongoDB（零文件系统依赖）。"""
    if not file.filename:
        raise HTTPException(422, "缺少文件名（filename）")
    pdf_bytes = await file.read()
    text = parse_pdf(pdf_bytes)
    doc_id = Path(file.filename).stem
    store_doc(doc_id, file.filename, text)

    return IngestResponse(doc_id=doc_id, filename=file.filename)


@router.get("/documents", response_model=list[DocumentResponse])
async def documents():
    """列出已上传的文档。"""
    return list_docs()


@router.post("/consolidate", response_model=ConsolidateResponse)
async def consolidate(req: ConsolidateRequest):
    """手动触发记忆整合：level="L2" 整合该会话，level="L5" 整合全局画像。"""
    if req.level == "L5":
        l2_memories = load_memories(level="L2")
        if not l2_memories:
            raise HTTPException(422, "还没有会话摘要，先整合至少一个会话")
        previous = load_memories(level="L5")
        profile = consolidate_profile(l2_memories, previous[0] if previous else None)
        profile_id = upsert_profile(profile)
        return ConsolidateResponse(status="ok", profile_id=profile_id)

    l1_memories = load_memories(session_id=req.session_id, level="L1")
    if not l1_memories:
        raise HTTPException(422, "该会话没有 L1 记忆，先对话几轮再整合")
    l2 = consolidate_l2(l1_memories)
    l2_id = upsert_l2(l2)
    return ConsolidateResponse(status="ok", l2_id=l2_id)
