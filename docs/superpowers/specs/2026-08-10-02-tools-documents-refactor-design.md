# tools.py → documents.py 分层重构 Design Spec

> **日期**: 2026-08-10
> **模块**: doc 01 + doc 02 + 全量文档同步
> **状态**: 待评审

## 1. 问题

当前 `agents/tools.py`（agent 层）存在三层违规：

1. **import 私有成员**：`from agentic_search.services.documents import _documents_collection` —— `_documents_collection` 是 documents.py 的模块级私有变量，不应被其他模块访问。
2. **内联数据访问**：`_get_doc_text` 和 `search_papers` 各自直接调 `_documents_collection.find_one()` 查询 MongoDB —— 数据访问逻辑分散在 agent 层。
3. **业务逻辑错层**：`search_papers` 的正则搜索和 `extract_abstract` 的摘要提取是文档处理逻辑，属于 service 层，却嵌在 agent 工具里。

唯一干净的工具是 `list_papers`——它已经是 `return list_documents()` 的薄委托。

## 2. 设计

### 2.1 分层原则

```
documents.py（service 层）= 所有 MongoDB 访问 + 所有文档操作
tools.py（agent 层）= 薄 @tool 封装，零 MongoDB 访问
```

### 2.2 documents.py 新增 3 个函数

| 新函数 | 来源 | 逻辑 |
|---|---|---|
| `get_doc(doc_id: str) -> str` | `tools._get_doc_text` | `_documents_collection.find_one({"doc_id": ...})` → 返回 `doc["text"]`，找不到抛 `KeyError` |
| `search_doc(doc_id: str, pattern: str) -> list[dict]` | `tools.search_papers` 主体 | 内部调 `get_doc(doc_id)` → `re.compile(pattern)` 逐行匹配 → 返回 `[{doc_id, line_number, line}]` |
| `get_abstract(doc_id: str) -> str` | `tools.extract_abstract` 主体 | 内部调 `get_doc(doc_id)` → 找 `"abstract"` 标题行 → 提取下方段落 |

`search_doc` 和 `get_abstract` 内部调 `get_doc` 拿文本——`get_doc` 是 service 层的公共基础函数，read_paper 工具也调它。

documents.py 需新增 `import re`（正则搜索需要）。

### 2.3 tools.py 瘦身后

```python
import re  # ← 删除（正则移到 documents.py）

from langchain.tools import tool

from agentic_search.services.documents import (
    list_documents,
    get_doc,        # ← 新（替代 _documents_collection + _get_doc_text）
    search_doc,     # ← 新（替代 search_papers 的主体）
    get_abstract,   # ← 新（替代 extract_abstract 的主体）
)
# _documents_collection ← 彻底删除


@tool
def list_papers() -> list[dict]:
    """...（docstring 不变）"""
    return list_documents()


@tool
def read_paper(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """...（docstring 不变）"""
    text = get_doc(doc_id)                              # ← 改调 get_doc
    lines = text.split("\n")
    return "\n".join(lines[start_line - 1 : end_line])  # 切片留工具层


@tool
def search_papers(pattern: str, doc_id: str) -> list[dict]:
    """...（docstring 不变）"""
    if not doc_id:                                      # 输入校验留工具层
        raise ValueError("doc_id 不能为空。请先调用 list_papers 获取可用的 doc_id。")
    return search_doc(doc_id, pattern)                  # ← 委托 service


@tool
def extract_abstract(doc_id: str) -> str:
    """...（docstring 不变）"""
    return get_abstract(doc_id)                         # ← 纯委托
```

### 2.4 行号切片为什么留 tools.py

`read_paper` 的 `lines[start_line - 1 : end_line]` 是「给 LLM 看多少行」的工具层展示逻辑——同一个 `get_doc` 返回完整文本，不同的工具可以用不同的切片方式。这不是文档数据的操作，是 agent 的阅读策略。

### 2.5 输入校验为什么留 tools.py

`search_papers` 的 `if not doc_id: raise ValueError("...请先调用 list_papers...")` 是 agent 面向的输入校验——错误消息引导 LLM 的行为（「先调 list_papers」），不是数据层校验。

## 3. 不变的东西

- **4 个 `@tool` 工具的函数名、参数签名、docstring 全不变**——graph.py 的 `bind_tools` 和 SSE 工具事件不受影响。
- **graph.py、routes.py、config.py**：零改动。
- **依赖**：零新增（`re` 是标准库）。
- **现有测试**：`test_documents.py`（parse_pdf/store_document/list_documents）不受影响；`test_graph.py` 打真 LLM 也不受影响（工具行为不变）。

## 4. 文档影响

### 4.1 doc 01（主要影响——step 3 和 step 4）

**step 3（services/documents.py）**：新增 3.4 节教 `get_doc`/`search_doc`/`get_abstract`（三个文档操作函数），与 3.1-3.3 的 CRUD 函数一起构成完整的 service 层。3.3 的「Agent 怎么读单篇论文？」提示框需要更新（不再说「模块 2 实现」，而是指向同模块 3.4）。

**step 4（agents/tools.py）**：重写为「薄封装」教学——每个 `@tool` 展示委托模式（调 service 层函数），不再内联 MongoDB 查询。这是教学重点：`@tool` 装饰器把 service 函数包装成 LLM 可调用的工具，函数体只是委托。

### 4.2 doc 02

- L93 架构图 `services/documents.py<br/>list_documents / find_one` → `services/documents.py<br/>list_documents / get_doc / search_doc / get_abstract`
- L144 目录树 `tools.py # 模块 1 已实现：list_papers / read_paper / search_papers / extract_abstract` → 加注释说明 tools.py 是薄封装层

### 4.3 其他文档

- **概念速查.md**：如有 tools.py / documents.py 分层描述，同步更新。
- **项目概览.md**：L79 目录树注释 + L102 层级列表同步。
- **AGENTS.md**：重要文件表（documents.py 函数列表）+ 代码约定（分层原则）。

## 5. 验证计划

1. **import smoke test**：`from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract` 无报错。
2. **零 `_documents_collection` 访问**：`grep "_documents_collection" tools.py` 返回空。
3. **零 `_get_doc_text` 残留**：`grep "_get_doc_text" tools.py` 返回空。
4. **现有测试通过**：`uv run pytest tests/test_documents.py -v` 仍全绿（4 个测试不变）。
5. **行号连续 + 无否定措辞**（doc 01/02 文档检查）。

## 6. 教学脉络（doc 01 改后）

```
step 3：services/documents.py —— service 层（所有文档操作 + MongoDB 访问）
  3.1 parse_pdf（PDF → 纯文本）
  3.2 store_document（写入 MongoDB）
  3.3 list_documents（列出文档）
  3.4 get_doc / search_doc / get_abstract（读取、搜索、摘要）  ← 新增

step 4：agents/tools.py —— agent 层（薄 @tool 封装）
  每个 @tool = docstring（LLM 看的）+ 委托 service 函数（实际逻辑）
```

两层职责清晰：service 层拥有数据，agent 层拥有 LLM 接口。
