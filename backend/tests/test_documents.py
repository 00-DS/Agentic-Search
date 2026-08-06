from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document
import pytest

def test_parse_pdf_return_string():
    from pathlib import Path
    pdf_path = r"D:\Python\Common\Agentic Search\任务文档\TiMem Temporal-Hierarchical Memory Consolidation for Long-Horizon Conversational Agents.pdf"
    result = parse_pdf(Path(pdf_path).read_bytes())
    assert isinstance(result, str)
    assert len(result) > 0

def test_parse_pdf_empty_bytes_raises():
    """空字节流应被 pymupdf 拒绝。"""
    import pymupdf
    with pytest.raises(pymupdf.EmptyFileError):
        parse_pdf(b"")

def test_store_and_read_document():
    """存入后应能按 doc_id 读回完整文本。"""
    doc_id = "test-doc-001"
    store_document(doc_id, "测试论文.pdf", "正文内容")
    doc = read_document(doc_id)
    assert isinstance(doc["text"], str)
    assert "正文内容" in doc["text"]


def test_list_documents_returns_list():
    """list_documents 应返回列表。"""
    result = list_documents()
    assert isinstance(result, list)


def test_list_documents_result_format():
    """每个结果应包含 doc_id 与 filename 字段。"""
    result = list_documents()
    if result:  # 有记录时才校验字段
        assert "doc_id" in result[0]
        assert "filename" in result[0]


def test_read_document_not_found():
    """读取不存在的 doc_id 应抛出 KeyError。"""
    with pytest.raises(KeyError):
        read_document("不存在的doc_id")