import pytest

from agentic_search.services.documents import list_docs, parse_pdf


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


def test_list_docs_returns_list():
    """list_docs 应返回列表。"""
    result = list_docs()
    assert isinstance(result, list)


def test_list_docs_result_format():
    """每个结果应包含 doc_id 与 filename 字段。"""
    result = list_docs()
    if result:  # 有记录时才校验字段
        assert "doc_id" in result[0]
        assert "filename" in result[0]
