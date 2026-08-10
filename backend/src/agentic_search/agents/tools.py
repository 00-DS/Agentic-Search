from langchain.tools import tool

from agentic_search.services.documents import (
    get_abstract,
    list_docs,
    read_lines,
    search_doc,
)


@tool
def list_papers() -> list[dict]:
    """列出语料库中所有可用论文。返回 [{doc_id, filename}]，不含正文。
    先用本工具了解语料库里有哪些论文，再用 read_paper 或 search_papers 深入某一篇。
    """
    return list_docs()


@tool
def read_paper(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定论文从 start_line 到 end_line 的原始文本（行号从 1 开始，含两端）。
    默认返回前 50 行。搜索或摘要给出某个行号后，用本工具读取该位置附近的完整上下文。
    """
    return read_lines(doc_id, start_line, end_line)


@tool
def search_papers(pattern: str, doc_id: str) -> list[dict]:
    """用正则表达式搜索指定论文内容，返回每个命中行 [{doc_id, line_number, line}]。
    pattern 是 Python 正则（如 'transformer|attention'），不是自然语言问题。
    doc_id 必填——先用 list_papers 查看可用论文，拿到 doc_id 后再调本工具。
    拿到命中行号后，用 read_paper 读取该位置附近的上下文。
    """
    if not doc_id:
        raise ValueError("doc_id 不能为空。请先调用 list_papers 获取可用的 doc_id。")
    return search_doc(doc_id, pattern)


@tool
def extract_abstract(doc_id: str) -> str:
    """提取论文的 Abstract 段落，用于快速判断论文是否与问题相关。
    找不到独立 Abstract 段落时返回提示信息。
    """
    return get_abstract(doc_id)
