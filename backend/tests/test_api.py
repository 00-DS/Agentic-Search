# tests/test_api.py —— 教学示例
from agentic_search.main import app
from fastapi.testclient import TestClient

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
