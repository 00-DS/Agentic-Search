# tools.py → documents.py 分层重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 tools.py 的文档操作逻辑下沉到 documents.py（service 层），tools.py 变成纯薄 @tool 委托层。消除三层违规：import 私有 `_documents_collection`、内联 MongoDB 查询、业务逻辑错层。

**Architecture:** documents.py 新增 `_get_doc`（私有）+ `read_lines`/`search_doc`/`get_abstract`（3 个公开函数）。tools.py 的 4 个工具改为纯委托。4 个 @tool 签名/docstring 不变。

**Spec:** `docs/superpowers/specs/2026-08-10-02-tools-documents-refactor-design.md`

## Global Constraints

- **4 个 @tool 工具的函数名、参数签名、docstring 全不变**——graph.py 零改动。
- **`_get_doc` 私有**（下划线开头），tools.py 不碰它和 `_documents_collection`。
- **`import re` 从 tools.py 移到 documents.py**。
- **文档政策**：只写「为什么这样」，禁否定措辞「不使用 XXX」。
- 行号为近似值——以内容定位为准（grep 关键短语）。
- Do NOT run pytest/ruff project-wide — only the verification commands per task.
- `.pyc` caches are tracked in this repo — unstage them before commit, don't commit cache files.

## File Structure

- `backend/src/agentic_search/services/documents.py` — 新增 `import re` + 4 个函数
- `backend/src/agentic_search/agents/tools.py` — 瘦身为纯委托
- `任务文档/01-Python文档工具.md` — step 3 新增 §3.4 + step 4 重写
- `任务文档/02-LangGraph-Agent.md` — 架构图 + 目录树同步
- `任务文档/概念速查.md` — 如有分层描述同步
- `任务文档/项目概览.md` — 目录树 + 层级列表同步
- `AGENTS.md` — 重要文件表 + 代码约定

---

## Task 1: 代码层 — documents.py + tools.py

**Files:**
- Modify: `backend/src/agentic_search/services/documents.py`
- Modify: `backend/src/agentic_search/agents/tools.py`

- [ ] **Step 1: documents.py — 新增 `import re` + 4 个函数**

在 `list_documents` 函数之后（文件末尾），追加：

```python
import re  # 顶部加（或跟现有 import 一起）


def _get_doc(doc_id: str) -> str:
    """按 doc_id 取出整篇文档的完整文本。找不到抛 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc["text"]


def read_lines(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定文档从 start_line 到 end_line 的原始文本（行号从 1 开始，含两端）。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    return "\n".join(lines[start_line - 1 : end_line])


def search_doc(doc_id: str, pattern: str) -> list[dict]:
    """用正则表达式搜索指定文档内容，返回每个命中行 [{doc_id, line_number, line}]。"""
    if not doc_id:
        raise ValueError("doc_id 不能为空。")
    regex = re.compile(pattern)
    text = _get_doc(doc_id)
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if regex.search(line):
            hits.append({"doc_id": doc_id, "line_number": i, "line": line})
    return hits


def get_abstract(doc_id: str) -> str:
    """提取文档的 Abstract 段落。找不到独立 Abstract 段落时返回提示信息。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "abstract":
            for j in range(i + 1, len(lines)):
                para = lines[j].strip()
                if para:
                    end = j + 1
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    return "\n".join(lines[j:end])
            return "Abstract 标题下方无内容"
    return "未找到独立 Abstract 段落"
```

注意：`import re` 加在文件顶部（跟 `import pymupdf` 等同级），不是在函数内部。

- [ ] **Step 2: tools.py — 瘦身为纯委托**

整个文件改为：

```python
from langchain.tools import tool

from agentic_search.services.documents import (
    get_abstract,
    list_documents,
    read_lines,
    search_doc,
)


@tool
def list_papers() -> list[dict]:
    """列出语料库中所有可用论文。返回 [{doc_id, filename}]，不含正文。
    先用本工具了解语料库里有哪些论文，再用 read_paper 或 search_papers 深入某一篇。
    """
    return list_documents()


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
```

注意：docstring 全部保持原样（LLM 工具 schema 不变）。`import re` 和 `_documents_collection` 彻底删除。

- [ ] **Step 3: 验证**

```bash
cd backend
# import smoke test
uv run python -c "from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract; print([t.name for t in [list_papers, read_paper, search_papers, extract_abstract]])"
# 零 _documents_collection in tools.py
grep "_documents_collection" src/agentic_search/agents/tools.py || echo "clean"
# 零 _get_doc in tools.py
grep "_get_doc" src/agentic_search/agents/tools.py || echo "clean"
```

- [ ] **Step 4: 提交**

```bash
cd "D:/Python/Common/Agentic Search"
git add backend/src/agentic_search/services/documents.py backend/src/agentic_search/agents/tools.py
# 注意：unstage .pyc caches
git commit -m "refactor: tools.py → documents.py 分层重构

documents.py 新增 _get_doc(私有) + read_lines/search_doc/get_abstract。
tools.py 4 个 @tool 改为纯委托，删除 _documents_collection import
和内联 MongoDB 查询。@tool 签名/docstring 不变，graph.py 零改动。"
```

---

## Task 2: doc 01 — step 3 新增 §3.4 + step 4 重写

**Files:**
- Modify: `任务文档/01-Python文档工具.md`

- [ ] **Step 1: 更新 §3.3 的「Agent 怎么读单篇论文？」提示框（L509）**

当前 L509 引向模块 2。改为引向同模块的 §3.4：

```markdown
> **Agent 怎么读单篇论文？** 下面 §3.4 实现的 `read_lines`（读取行片段）、`search_doc`（正则搜索）、`get_abstract`（提取摘要）覆盖了 agent 读取论文的全部需求。模块 2 的 `agents/tools.py` 只是用 `@tool` 把它们包装成 LLM 可调用的工具——薄委托，零直接数据访问。
```

- [ ] **Step 2: 在 §3.3 验证块之后（L519 ` ``` ` 闭合后）、L521 `---` 之前，插入 §3.4**

插入：

```markdown
### 3.4 文档读取操作：`read_lines` / `search_doc` / `get_abstract`

除了「存入」和「列出」，agent 还需要三种读取操作：按行号读片段、正则搜索关键词、提取摘要。这三个函数共享一个私有 helper `_get_doc`——按 `doc_id` 从 MongoDB 取出完整文本。

#### `_get_doc`（私有 helper）

```python
def _get_doc(doc_id: str) -> str:
    """按 doc_id 取出整篇文档的完整文本。找不到抛 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc["text"]
```

`_get_doc` 以下划线开头——这是 Python 的惯例，表示「模块内部使用，外部不应直接调用」。三个公开函数内部调它，tools.py 不碰它。

#### `read_lines(doc_id, start_line, end_line)`

按行号读取指定范围的文本。行号从 1 开始（对齐 `read_paper` 工具的 `start_line`/`end_line` 参数）：

```python
def read_lines(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定文档从 start_line 到 end_line 的原始文本（行号从 1 开始，含两端）。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    return "\n".join(lines[start_line - 1 : end_line])
```

行号是 1-indexed（人读论文的习惯），列表是 0-indexed（Python 的习惯），所以 `lines[start_line - 1 : end_line]` 减 1 对齐。

#### `search_doc(doc_id, pattern)`

用正则表达式搜索文档内容，返回每个命中行及其行号：

```python
import re

def search_doc(doc_id: str, pattern: str) -> list[dict]:
    """用正则表达式搜索指定文档内容，返回每个命中行 [{doc_id, line_number, line}]。"""
    if not doc_id:
        raise ValueError("doc_id 不能为空。")
    regex = re.compile(pattern)
    text = _get_doc(doc_id)
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if regex.search(line):
            hits.append({"doc_id": doc_id, "line_number": i, "line": line})
    return hits
```

`pattern` 是 Python 正则（如 `'transformer|attention'`）。`enumerate(..., 1)` 让行号从 1 开始——agent 拿到行号后可以直接传给 `read_lines` 读上下文。

#### `get_abstract(doc_id)`

提取论文的 Abstract 段落——找到独立成行的 `"abstract"` 标题，收集其下方第一个非空自然段：

```python
def get_abstract(doc_id: str) -> str:
    """提取文档的 Abstract 段落。找不到独立 Abstract 段落时返回提示信息。"""
    text = _get_doc(doc_id)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "abstract":
            for j in range(i + 1, len(lines)):
                para = lines[j].strip()
                if para:
                    end = j + 1
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    return "\n".join(lines[j:end])
            return "Abstract 标题下方无内容"
    return "未找到独立 Abstract 段落"
```

`line.strip().lower() == "abstract"` 只匹配独立成行的标题（不是正文里出现的 "abstract" 单词），对齐论文 PDF 的常见排版。
```

- [ ] **Step 3: 重写 step 4（L523-626）—— tools.py 改为薄委托教学**

整个 step 4 的代码块（L529-604）替换为瘦版。说明文字也更新——强调「委托」模式。

当前 L529-604 的代码块替换为：

```python
# agents/tools.py —— 教学示例：四个论文导航工具（薄委托）
from langchain.tools import tool

from agentic_search.services.documents import (
    get_abstract,
    list_documents,
    read_lines,
    search_doc,
)


@tool
def list_papers() -> list[dict]:
    """列出语料库中所有可用论文。返回 [{doc_id, filename}]，不含正文。
    先用本工具了解语料库里有哪些论文，再用 read_paper 或 search_papers 深入某一篇。
    """
    return list_documents()


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
```

step 4 的 L525 说明段（「Agent 的手和眼...函数体一行没改，就变成了 LLM 可调用的工具」）之后追加一段分层说明：

```markdown
注意每个工具的函数体——它们只做委托：`list_papers` 调 `list_documents()`，`read_paper` 调 `read_lines()`，`search_papers` 调 `search_doc()`（外加输入校验），`extract_abstract` 调 `get_abstract()`。这是有意的分层设计：`services/documents.py` 拥有所有 MongoDB 访问和文档操作逻辑，`agents/tools.py` 只是用 `@tool` 装饰器把这些函数包装成 LLM 可调用的工具。`@tool` 从函数的类型注解和 docstring 自动生成工具 schema——函数体的逻辑在 service 层，装饰器只管「让 LLM 看到这个工具」。
```

- [ ] **Step 4: 提交**

```bash
git add "任务文档/01-Python文档工具.md"
git commit -m "docs(01): step 3 新增 §3.4 文档读取操作 + step 4 重写为薄委托教学"
```

---

## Task 3: doc 02 + 概念速查 + 项目概览 + AGENTS.md 同步

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`
- Modify: `任务文档/概念速查.md`
- Modify: `任务文档/项目概览.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: doc 02 同步**

- L93 架构图：`services/documents.py<br/>list_documents / find_one` → `services/documents.py<br/>list_documents / read_lines / search_doc / get_abstract`
- L144 目录树：`tools.py # 模块 1 已实现：list_papers / read_paper / search_papers / extract_abstract` → `tools.py # 模块 1 已实现：list_papers / read_paper / search_papers / extract_abstract（薄委托，逻辑在 documents.py）`

- [ ] **Step 2: 概念速查.md 同步**

检查是否有 tools.py / documents.py 分层描述需更新。如果 §PyMongo 或 §pytest 里有提到 `_documents_collection` 或 tools.py 直接查 MongoDB，改为薄委托描述。

- [ ] **Step 3: 项目概览.md 同步**

- L79 目录树：`documents.py # 文档工具（parse_pdf 转纯文本 / list_documents）` → `documents.py # 文档工具（parse_pdf / store / list / read_lines / search_doc / get_abstract）`
- L102 层级列表：`services/documents.py — 文档工具（parse_pdf / list_documents）` → `services/documents.py — 文档工具（parse_pdf / store / list / read_lines / search_doc / get_abstract）`
- 如有 tools.py 描述，加「薄委托」说明

- [ ] **Step 4: AGENTS.md 同步**

- L92 重要文件表：`documents.py | parse_pdf·store_document·list_documents` → `documents.py | parse_pdf·store_document·list_documents·_get_doc(私有)·read_lines·search_doc·get_abstract`
- 代码约定新增一条分层原则：`tools.py（agent 层）= 薄 @tool 委托，零 MongoDB 访问；documents.py（service 层）= 所有文档操作 + MongoDB 访问`

- [ ] **Step 5: 全文验证 + 提交**

```bash
# tools.py 不再访问 _documents_collection / _get_doc
grep "_documents_collection\|_get_doc" backend/src/agentic_search/agents/tools.py || echo "clean"
# 否定措辞检查
grep -c "不使用" "任务文档/01-Python文档工具.md" "任务文档/02-LangGraph-Agent.md"
git add -A
# unstage .pyc
git commit -m "docs: 同步 tools→documents 分层重构（doc 02 + 概念速查 + 项目概览 + AGENTS.md）"
```

---

## Self-Review

**1. Spec coverage：** §2.2 4 个函数 → Task 1 Step 1 ✅。§2.3 tools.py → Task 1 Step 2 ✅。§2.4 切片理由 → doc 01 §3.4 read_lines 教学体现 ✅。§2.5 输入校验 → Task 1 Step 2 search_papers 保留校验 ✅。§4 文档影响 → Task 2-3 ✅。§5 验证 → Task 1 Step 3 + Task 3 Step 5 ✅。

**2. Placeholder scan：** 无 TBD/TODO；代码块完整。

**3. 跨文件顺序：** Task 1（代码）先完成，Task 2-3（文档引用代码）后跟进。
