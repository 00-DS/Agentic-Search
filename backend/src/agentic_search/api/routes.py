import json
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessageChunk

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

@router.post("/query")
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    async def event_stream():
        try:
            async for chunk, metadata in graph.astream(
                {"messages": [HumanMessage(content=req.question)]},
                stream_mode="messages"
            ):
                if not isinstance(chunk, AIMessageChunk):
                    continue
                if chunk.content:
                    yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
                elif chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            yield f"event: tool\ndata: {tc['name']}\n\n"
        except Exception as e:
            yield f"data: {json.dumps(f'[错误：{e}]', ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """上传 PDF，提取纯文本并存入 MongoDB（零文件系统依赖）。"""
    pdf_bytes = await file.read()
    text = parse_pdf(pdf_bytes)
    doc_id = Path(file.filename).stem
    store_document(doc_id, file.filename, text)

    return IngestResponse(doc_id=doc_id, filename=file.filename)
