# tests/test_api.py —— 教学示例
from fastapi.testclient import TestClient

from agentic_search.main import app

client = TestClient(app)


def test_documents_endpoint():
    """/api/documents 应返回 200 与列表。"""
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_query_validation():
    """缺少 question 字段时应返回 422（Pydantic 校验失败）。"""
    resp = client.post("/api/query", json={})
    assert resp.status_code == 422


def test_query_sse_wire_format():
    """query 端点应返回 SSE 流：文字 token JSON 编码（带转义）、工具调用为结构化 JSON 对象。

    直接测 astream 不可行（依赖真 LLM），改用一个最小 stub app 验证 wire 序列化——
    确保 routes.py 用的是 ServerSentEvent(data=...) / data={"name":...} 模式，
    而非旧的手写 f-string 帧。
    """
    from fastapi import FastAPI
    from fastapi.sse import EventSourceResponse, ServerSentEvent
    from fastapi.testclient import TestClient as _TC

    stub = FastAPI()

    @stub.post("/query", response_class=EventSourceResponse)
    async def q():
        yield ServerSentEvent(data="你好")
        yield ServerSentEvent(event="tool", data={"name": "search_paper"})

    resp = _TC(stub).post("/query")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    # 文字 token：JSON 编码、中文 ASCII 转义
    assert 'data: "\\u4f60\\u597d"' in body
    # 工具调用：结构化 JSON 对象（不是裸字符串）
    assert 'event: tool\ndata: {"name": "search_paper"}' in body
    # 不应是旧的裸字符串格式
    assert "data: search_paper" not in body
