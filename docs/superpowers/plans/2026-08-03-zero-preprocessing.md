# 零预处理架构改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 01 的 section 切分预处理全部删除，改为 PDF → 纯文本完整存储；02 的工具集从 `list_sections`/`read_section`/`search_sections` 改为 `list_papers`/`read_paper`/`search_papers`/`extract_abstract`；同步更新所有交叉引用文档。

**Architecture:** 上传时零预处理——`get_text("text")` 提取完整纯文本存入 MongoDB（扁平 `{doc_id, filename, text, uploaded_at}`）。agent 用四个工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）按行号自主读取，完全对齐 omp 的 `glob`/`read`/`grep` 范式。`extract_abstract` 是读取时的便利工具（agent 按需调用），不是上传预处理。

**Tech Stack:** Python 3.11+ / pymupdf `get_text("text")` / pymongo / MongoDB / LangChain `@tool` / LangGraph / FastAPI

## Global Constraints

- **仅文档范围**：只编辑 `任务文档/` 下的 `.md` 文件，绝不碰 `backend/` 代码。
- **纯新版本，零历史包袱**：不出现"旧版"/"原来"/"之前"/"不再"/"改用"等对比性措辞。每个概念只按当前设计讲解一次。
- **无 embedding/向量库**：搜索用 Python `re` 正则。
- **DeepSeek 统一**：`base_url=https://api.deepseek.com`，`model=deepseek-v4-flash`。
- **四工具签名（全项目统一）**：`list_papers() -> list[dict]` / `read_paper(doc_id, start_line=1, end_line=50) -> str` / `search_papers(pattern, doc_id="") -> list[dict]` / `extract_abstract(doc_id) -> str`
- **MongoDB schema**：`{doc_id, filename, text, uploaded_at}`——扁平文档，`text` 是完整纯文本。无 `sections` 数组。
- **装饰器 cross-reference 网保持完整**：02 @retry（第5步）→ 02 @tool（第6步）→ 02 @router（第9步）→ 04 @dataclass（~line 123）→ 概念速查 decorator 条目。
- **MessagesState**：02 用标准 `MessagesState`（不自定义 AgentState）。

---

## 文件清单

| 文件 | 职责 | 改动规模 |
|---|---|---|
| `任务文档/01-Python文档工具.md` | parse_pdf 简化 + schema 扁平化 + 删 section 概念 | 大改 |
| `任务文档/02-LangGraph-Agent.md` | 四工具新签名 + ReAct 图 + 所有引用更新 | 大改 |
| `任务文档/概念速查.md` | pymupdf/MongoDB/Compass/PyMongo/ReAct/Agent 条目 | 中改 |
| `任务文档/项目概览.md` | 架构图/数据流/工具列表/技术栈/M1 | 中改 |
| `任务文档/00-开始指南.md` | 学习路径工具名 | 小改 |

---

### Task 1: 01-Python文档工具.md — parse_pdf 简化 + schema 扁平化

**Files:**
- Modify: `任务文档/01-Python文档工具.md`

**Interfaces:**
- Produces: `parse_pdf(path) -> str`（纯文本），`store_document(doc_id, filename, text)`，`list_documents() -> list[dict]`，`read_document(doc_id) -> dict`（返回完整文档记录含 text 字段）

**改动点（按文档结构从上到下）：**

- [ ] **Step 1: 学习目标第 4 条（line 14）**

把 `parse_pdf（结构化提取，切分章节）、list_documents、read_document、read_section 四个文档工具函数，把按章节切分的文本存入 MongoDB` 改为：

`parse_pdf（PDF 转纯文本）、store_document、list_documents、read_document 四个文档工具函数，把完整文本存入 MongoDB`

- [ ] **Step 2: 本模块产出段落（line 17）**

把 `Agent 的论文导航工具（read_section/search_sections 等）调用——Agent 按需读取本模块产出的章节文本片段` 改为：

`Agent 的论文导航工具（read_paper/search_papers 等）调用——Agent 按行号按需读取本模块产出的完整文本片段`

- [ ] **Step 3: pymupdf 技术概念段落（lines 50-58）**

整段替换为：

```
### pymupdf

**pymupdf** 是基于 MuPDF 内核的轻量 PDF 处理库。它通过 `page.get_text("text")` 从 PDF 文本层提取纯文本——单一 wheel、无模型下载、无 GPU 依赖、即装即用。

**`get_text("text")` 返回什么？** 每一页的纯文本字符串，按 PDF 的排版顺序拼接。项目只需把所有页的文本拼成一个完整字符串，存入 MongoDB。不做任何切分——切分是 agent 的职责，它用正则搜索定位行号、按行号读取片段，完全自主。

**为什么不做结构化切分？** 这对齐 omp 的文件读取模型：文件以原始形态存在，agent 用 `grep`（正则搜索行号）+ `read :50-100`（按行号取片段）自主探索，不在入库时做任何预处理。预切分会破坏跨段上下文、切分位置可能出错，反而降低 agent 的探索效果。
```

- [ ] **Step 4: MongoDB 技术概念段落（line 62）**

把 `存放论文（每篇按章节切分为 sections 数组）` 改为 `存放论文（每篇存为完整纯文本）`

- [ ] **Step 5: 模块结构 mermaid 图（lines 97-113）**

把 `Pymupdf["pymupdf<br/>结构化提取（dict + 标题启发式）"]` 改为 `Pymupdf["pymupdf<br/>PDF 转纯文本"]`

把 `Docs[("MongoDB documents<br/>sections 章节数组")]` 改为 `Docs[("MongoDB documents<br/>完整文本")]`

- [ ] **Step 6: Compass 段落引用（line 142）**

把 `PDF 经 pymupdf 提取的章节数组（sections），以及 L1/L2 记忆` 改为 `PDF 经 pymupdf 提取的完整文本，以及 L1/L2 记忆`

- [ ] **Step 7: pyproject.toml 依赖注释（lines 191-193）**

把 `"pymupdf", # PDF → 结构化提取（get_text("dict") + 标题启发式）` 改为 `"pymupdf", # PDF → 纯文本提取（get_text("text")）`

把 `"pymongo", # MongoDB Python 驱动（同步）：存取 sections 章节与记忆` 改为 `"pymongo", # MongoDB Python 驱动（同步）：存取文档文本与记忆`

- [ ] **Step 8: 步骤 3 函数表（lines 334-340）**

整段替换为：

```
| 函数 | 职责 |
|------|------|
| `parse_pdf(pdf_path)` | 用 pymupdf 把 PDF 转为完整纯文本 |
| `store_document(doc_id, filename, text)` | 把完整文本写入 MongoDB `documents` 集合 |
| `list_documents()` | 从 MongoDB 查询所有文档，返回 doc_id 与文件名 |
| `read_document(doc_id)` | 从 MongoDB 读取指定文档的完整记录（含 text 字段） |
```

- [ ] **Step 9: 步骤 3 import 行（line 345）**

把 `from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document, read_section` 改为 `from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document`

- [ ] **Step 10: 步骤 3.1 parse_pdf 整段重写（lines 350-480）**

这是最大的改动。整段替换（350-480）为：

```markdown
### 3.1 `parse_pdf(pdf_path)`

**功能定义**：

```python
def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF，用 pymupdf 提取完整纯文本。不做任何切分。"""
```

输入：PDF 文件路径（如 `"paper.pdf"`，可放在 `backend/` 下任意位置）。输出：完整纯文本字符串——所有页面的文字按排版顺序拼接。

**pymupdf 基础用法**（官方文档：https://pymupdf.readthedocs.io/）。核心是「打开文档 → 逐页取纯文本 → 拼接 → 关闭」：

```python
import pymupdf

doc = pymupdf.open("example.pdf")          # 打开文档
for page in doc:                            # 逐页迭代
    text = page.get_text("text")            # 该页的纯文本
    print(text)
doc.close()
```

关键概念：`pymupdf.open(path)` 打开 PDF（返回 Document 对象）；`for page in doc` 遍历每一页；`page.get_text("text")` 返回该页的纯文本字符串，按 PDF 排版顺序排列；`doc.close()` 释放资源。

> 现代导入写 `import pymupdf`（pymupdf ≥1.23.8 的官方推荐别名）。

**为什么只提取纯文本、不做切分？** 切分是 agent 的职责。agent 用 `search_papers(pattern)` 正则搜索行号定位关键词，再用 `read_paper(doc_id, start_line, end_line)` 按行号取上下文——完全自主地决定读哪段。上传时预切分会把全文打散成固定片段，agent 被迫在预切的边界里搜索，失去了自主定位的灵活性。这与 omp 用 `grep` + `read` 探索代码库完全一致：文件以原始形态存在，agent 按需读取。

**你需要实现的逻辑**：检查文件是否存在 → 打开 PDF → 逐页取 `get_text("text")` 拼接 → 关闭文档 → 返回完整字符串。以下是**教学示例，展示核心逻辑，非完整实现**：

```python
from pathlib import Path
import pymupdf


def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF，用 pymupdf 提取完整纯文本。不做任何切分。"""
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    doc = pymupdf.open(p)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(pages)
```

讲解要点：

- **无需缓存**：pymupdf 的 `open()` 是轻量操作，每次调用即可，无需缓存层。
- **错误处理**：路径不存在时抛出 `FileNotFoundError` 并附上具体路径，便于排查。
- **完整文本**：所有页的纯文本用 `"\n"` 拼接成一个字符串。这是 agent 工具（`read_paper`/`search_papers`/`extract_abstract`）按行号操作的基础。

**测试你的函数**：准备任意一个 PDF 文件，放在 `backend/` 下：

```bash
uv run python -c "
from agentic_search.services.documents import parse_pdf
text = parse_pdf('你的文件.pdf')
print(f'文本长度: {len(text)}')
print(f'前 200 字符: {text[:200]}')
"
```

**验证**：输出文本长度（非零）和前 200 字符（含 PDF 原文内容），而非报错。
```

- [ ] **Step 11: 步骤 3.2 store_document 重写（lines 482-523）**

整段替换为：

```markdown
### 3.2 `store_document(doc_id, filename, text)`

`parse_pdf` 只负责把 PDF 转为纯文本；持久化由 `store_document` 完成。它把完整文本连同文档标识、文件名、上传时间写入 MongoDB 的 `documents` 集合。集合中每条记录的固定结构为 `{_id, doc_id, filename, text, uploaded_at}`，其中 `text` 是完整纯文本。

> 在 MongoDB 术语中，一个 database（本项目为 `agentic_search`）下有若干 collection（集合，本项目为 `documents` 与 `memories`），每个集合里存放若干 document（文档，即一条记录）。注意区分「集合 collection」与「文档 document」：前者是表，后者是行。

MongoDB 的连接通过 PyMongo 的 `MongoClient` 建立。以下是**教学示例，展示核心逻辑，非完整实现**：

```python
from datetime import datetime, timezone
from pymongo import MongoClient

from agentic_search.configs.config import settings


# 模块级连接：MongoDB 连接建立后可复用，不必每次操作都新建客户端
_client = MongoClient(settings.mongo_uri)
_db = _client[settings.mongo_db]
_documents_collection = _db["documents"]


def store_document(doc_id: str, filename: str, text: str) -> None:
    """把一篇论文的完整纯文本存入 documents 集合。"""
    _documents_collection.insert_one(
        {
            "doc_id": doc_id,                       # 文档唯一标识（上传时生成）
            "filename": filename,                   # 原始 PDF 文件名
            "text": text,                           # 完整纯文本
            "uploaded_at": datetime.now(timezone.utc),  # 上传时间
        }
    )
```

讲解要点：

- **模块级连接**：`MongoClient(settings.mongo_uri)` 在模块被 import 时建立一次连接。PyMongo 的客户端内置连接池，多个 `insert_one` / `find_one` 复用同一连接，无需手动管理。
- **`insert_one`**：向集合插入一条记录。若 `documents` 集合尚不存在，MongoDB 会在首次写入时自动创建——无需提前建表。
- **`uploaded_at`**：记录上传时间。`datetime.now(timezone.utc)` 用带时区的 UTC 时间，避免不同服务器时区不一致导致的排序错误。
- **schema：`{doc_id, filename, text, uploaded_at}`**：扁平文档，`text` 是完整纯文本。agent 经 `read_paper(doc_id, start_line, end_line)` 按行号取片段，或经 `search_papers(pattern)` 正则定位。

**验证**：先用 `parse_pdf` 提取一个 PDF 的文本，再调用 `store_document` 存入，然后打开 **MongoDB Compass** 查看 `agentic_search` 的 `documents` 集合——应能看到一条新记录，其 `text` 字段是完整纯文本。
```

- [ ] **Step 12: 步骤 3.3 list_documents / read_document 重写（lines 525-582）**

整段替换为：

```markdown
### 3.3 `list_documents()` 与 `read_document(doc_id)`

这两个函数负责从 MongoDB 读取文档，供 Agent 自主决定「列出有哪些论文、读取某篇全文」。

- `list_documents() -> list[dict]`：查询 `documents` 集合中的全部记录，只取 `doc_id` 与 `filename` 两个字段（不取 `text` 正文），返回 `[{doc_id, filename}, ...]`。
- `read_document(doc_id) -> dict`：按 `doc_id` 精确查找一条记录，返回完整文档 `{doc_id, filename, text, uploaded_at}`。找不到则抛出 `KeyError`。

以下是**教学示例，展示核心逻辑，非完整实现**：

```python
def list_documents() -> list[dict]:
    """列出所有文档的 doc_id 与文件名。"""
    cursor = _documents_collection.find({}, {"doc_id": 1, "filename": 1, "_id": 0})
    return [
        {"doc_id": doc["doc_id"], "filename": doc["filename"]}
        for doc in cursor
    ]


def read_document(doc_id: str) -> dict:
    """按 doc_id 读取一篇文档的完整记录。找不到则抛出 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc
```

讲解要点：

- **`find({}, {投影})`**：第一个参数 `{}` 是查询条件（空字典表示「全部」）；第二个参数是**投影**——`{"doc_id": 1, "filename": 1}` 表示只返回这两个字段，`"_id": 0` 表示排除默认会返回的 `_id`。投影让列表接口只传输文件名而非整篇论文全文，大幅减少数据量。
- **`find_one({"doc_id": ...})`**：按条件查找**单条**记录，返回一个字典（找不到则返回 `None`）。

**验证**（假设已通过 `store_document` 存入至少一篇文档）：

```bash
uv run python -c "
from agentic_search.services.documents import list_documents, read_document
docs = list_documents()
print('文档列表:', docs)
if docs:
    did = docs[0]['doc_id']
    doc = read_document(did)
    print('读取成功，前 200 字符:', doc['text'][:200])
"
```
```

- [ ] **Step 13: 步骤 4 测试重写（lines 586-712）**

把测试文件内容改为新的函数签名。关键改动：

`test_parse_pdf_returns_sections` → `test_parse_pdf_returns_text`：
```python
def test_parse_pdf_returns_text():
    """parse_pdf 应返回非空字符串。"""
    result = parse_pdf("test_sample.pdf")
    assert isinstance(result, str)
    assert len(result) > 0
```

`test_read_section` 删除（函数不再存在）。

`test_store_and_read_document` 改为：
```python
def test_store_and_read_document():
    """存入后应能按 doc_id 读回完整文本。"""
    doc_id = "test-doc-001"
    store_document(doc_id, "测试论文.pdf", "正文内容")
    doc = read_document(doc_id)
    assert isinstance(doc["text"], str)
    assert "正文内容" in doc["text"]
```

`test_read_document_not_found` 保留但断言改为：
```python
def test_read_document_not_found():
    """读取不存在的 doc_id 应抛出 KeyError。"""
    with pytest.raises(KeyError):
        read_document("不存在的doc_id")
```

import 行删掉 `read_section`，test section_id 相关的测试全部删除。预期输出示例也更新（7 passed → 6 passed，因为删了 test_read_section）。

- [ ] **Step 14: 步骤 5 集成验证重写（lines 716-754）**

整段替换为：

```bash
uv run python -c "
from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document

# 1. 将一个 PDF 转为纯文本
text = parse_pdf('你的文件.pdf')
print(f'提取完成，文本长度: {len(text)}')

# 2. 存入 MongoDB documents 集合
doc_id = 'demo-paper'
store_document(doc_id, '你的文件.pdf', text)
print('已存入 MongoDB documents 集合')

# 3. 列出所有文档
print()
print('=== 文档列表 ===')
docs = list_documents()
for d in docs:
    print(f'  {d}')

# 4. 按 doc_id 读取文档
print()
print('=== 读取文档 ===')
doc = read_document(doc_id)
print(f'读取成功，前 200 个字符:')
print(doc['text'][:200])
"
```

验证说明：把 `sections 字段含完整章节数组` 改为 `text 字段是完整纯文本`。

- [ ] **Step 15: 完成检查清单更新（lines 758-798）**

`parse_pdf`、`store_document`、`list_documents`、`read_document`、`read_section` 改为 `parse_pdf`、`store_document`、`list_documents`、`read_document`。

额外验证命令更新为 `text = parse_pdf('你的文件.pdf'); store_document('verify', '你的文件.pdf', text); print(len(read_document('verify')['text']))`

- [ ] **Step 16: 下一步段落（line 848）**

把 `Agent 的论文导航工具（list_papers/list_sections/read_section/search_sections）将调用本模块的 read_section、list_documents 等函数，按需读取本模块切好的章节片段` 改为 `Agent 的论文导航工具（list_papers/read_paper/search_papers/extract_abstract）将调用本模块的 read_document、list_documents 等函数，按行号按需读取本模块产出的完整文本`

- [ ] **Step 17: Commit**

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): 零预处理——删 section 切分，parse_pdf 改 get_text(text)，schema 扁平化"
```

---

### Task 2: 02-LangGraph-Agent.md — 四工具新签名 + 所有引用更新

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`

**Interfaces:**
- Consumes: Task 1 的 `parse_pdf(path) -> str`、`store_document(doc_id, filename, text)`、`list_documents() -> list[dict]`、`read_document(doc_id) -> dict`
- Produces: `list_papers()`、`read_paper(doc_id, start_line, end_line)`、`search_papers(pattern, doc_id)`、`extract_abstract(doc_id)` 四个 `@tool` 工具

**改动点（按文档结构从上到下）：**

- [ ] **Step 1: 学习目标第 3 条（line 9）**

把 `实现四个论文导航工具（list_papers/list_sections/read_section/search_sections）` 改为 `实现四个论文导航工具（list_papers/read_paper/search_papers/extract_abstract）`

- [ ] **Step 2: ReAct 概念段落（line 20）**

把 `用 list_papers/list_sections/read_section/search_sections 自主探索论文语料库` 改为 `用 list_papers/read_paper/search_papers/extract_abstract 自主探索论文语料库`

- [ ] **Step 3: tool_calls JSON 示例（line 31）**

把 `"function": {"name": "search_sections"` 改为 `"function": {"name": "search_papers"`

- [ ] **Step 4: mermaid 流程图（lines 84-87）**

把 `执行工具（read_section 等）` 改为 `执行工具（read_paper 等）`

把 `调用` `services/documents.py<br/>list_documents / read_section` 改为 `services/documents.py<br/>list_documents / read_document`

- [ ] **Step 5: 前置要求（line 100）**

把 `parse_pdf（返回 sections 数组）、store_document、list_documents、read_document、read_section 已实现且测试通过` 改为 `parse_pdf（返回完整纯文本）、store_document、list_documents、read_document 已实现且测试通过`

- [ ] **Step 6: ReAct 设计说明段落（lines 108-113）**

整段替换为：

```markdown
本模块的 Agent 不写死「先读全文再回答」，而是一个 **ReAct 循环**：LLM 拿到问题后，自主决定调用哪个论文导航工具、调用几次、何时认为证据足够、直接作答。它对标 omp/hermes 探索本地代码库的能力——`list_papers` 相当于 `glob`（看有哪些论文），`read_paper` 相当于 `read :50-100`（按行号取片段），`search_papers` 相当于 `grep`（正则定位行号），`extract_abstract` 相当于 `summarizeCode()`（读取时的概览便利），对象从代码换成了论文。

三个逼出 agentic 行为的设计约束：

1. **没有「读整篇论文」的工具**。agent 必须先 `search_papers` 定位行号、再 `read_paper` 按行号取片段——这是「按需取片段」的强约束，既逼出真正的多轮探索，也是多论文场景下不撑爆上下文窗口的根本保障。
2. **`search_papers` 用正则、不用 embedding**。对齐 omp `grep`：参数是正则 `pattern`（不是语义 query），返回命中行+行号+上下文。智能来自 LLM 自主迭代构造正则。**不用向量库、不做 embedding。**
3. **`extract_abstract` 是读取时工具，不是上传预处理**。对齐 omp 的 `summarizeCode()`：agent 按需调用，从完整文本里正则提取 abstract 段落。不在上传时预计算。
```

- [ ] **Step 7: 目录结构注释（line 143）**

把 `parse_pdf 切章节 / list / read / read_section` 改为 `parse_pdf 转纯文本 / list / read_document`

- [ ] **Step 8: 第 6 步 tools.py 整段重写（lines 368-460）**

这是最大改动。整段替换为：

```markdown
## 第 6 步：论文导航工具集

这是 agent 的「手和眼」——四个工具，对标 omp 探索代码库的 `glob`/`read`/`grep`/`summarize`。用 LangChain 的 `@tool` 装饰器声明：装饰器会从函数的**类型注解 + docstring** 自动生成工具 schema，告诉 LLM「这个工具叫什么、接收什么参数、干什么」——这正是第 5 步装饰器概念的又一次「点亮」。

新建 `agents/tools.py`：

```python
# agents/tools.py —— 教学示例：四个论文导航工具
import re
from langchain.tools import tool
from agentic_search.services.documents import (
    list_documents, read_document, _documents_collection,
)


def _get_doc_text(doc_id: str) -> str:
    """按 doc_id 取出整篇文档的完整文本。找不到抛 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc["text"]


@tool
def list_papers() -> list[dict]:
    """列出语料库中所有论文。返回 [{doc_id, filename}]，不带正文。
    对标 omp 的 glob：只列有哪些文件，不返回内容——判断相关性靠后续自主探索。
    """
    return list_documents()


@tool
def read_paper(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定论文的指定行号范围。返回原始文本行。
    对标 omp 的 read :50-100：按行号取片段，而不是返回全文。
    """
    text = _get_doc_text(doc_id)
    lines = text.split("\n")
    # 行号是 1-indexed，列表是 0-indexed
    return "\n".join(lines[start_line - 1 : end_line])


@tool
def search_papers(pattern: str, doc_id: str = "") -> list[dict]:
    """跨语料库（或指定论文）用正则搜索内容。返回 [{doc_id, line_number, line, snippet}]。
    对标 omp 的 grep：参数是正则 pattern（不是语义 query），命中后 agent 通常再调
    read_paper 按行号深入——搜索只给位置和片段，不给全文。
    """
    regex = re.compile(pattern)
    hits = []
    docs = (_documents_collection.find_one({"doc_id": doc_id}) for _ in [None]) if doc_id else _documents_collection.find({})
    for d in docs:
        if d is None:
            continue
        for i, line in enumerate(d["text"].split("\n"), 1):
            if regex.search(line):
                hits.append({"doc_id": d["doc_id"], "line_number": i, "line": line})
    return hits


@tool
def extract_abstract(doc_id: str) -> str:
    """提取论文的 Abstract 段落。agent 按需调用，快速判断论文是否相关。
    对标 omp 的 summarizeCode()：读取时的概览便利，不是上传预处理。
    """
    text = _get_doc_text(doc_id)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "abstract":          # "abstract" 独立成段才算数
            # 收集其下方第一个非空自然段
            for j in range(i + 1, len(lines)):
                para = lines[j].strip()
                if para:                                  # 找到非空行，收集到空行为止
                    end = j + 1
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    return "\n".join(lines[j:end])
            return "Abstract 标题下方无内容"
    return "未找到独立 Abstract 段落"
```

四工具与 omp 的对应关系：

| 工具 | 签名 | 返回 | 对应 omp |
|------|------|------|----------|
| `list_papers` | `() -> list[dict]` | 语料库所有论文：`doc_id` + `filename`（**不带正文**） | `glob` |
| `read_paper` | `(doc_id, start_line?, end_line?) -> str` | 指定行号范围的原始文本 | `read :50-100` |
| `search_papers` | `(pattern, doc_id?) -> list[dict]` | 正则命中的 `doc_id`+`line_number`+`line` | `grep` |
| `extract_abstract` | `(doc_id) -> str` | Abstract 段落（或未找到提示） | `summarizeCode()` |

**为什么 `search_papers` 用正则、不用 embedding？** 这是对齐 omp `grep` 的核心决策，也是 agentic search 与旧时代 RAG 的根本区别。embedding/向量库会：① 引入额外的 embedding 模型依赖与首次下载；② 上传时对每段文本做向量入库的额外流程；③ 让搜索结果受模型质量制约、不可解释。正则命中是人能读懂的精确匹配，智能来自 LLM 自主迭代构造正则（先搜 `dataset|corpus|benchmark`，看结果再逼近），不是预计算的语义相似度。本项目严格对齐 omp 范式——**正则匹配、零额外依赖、结果可解释**。

**为什么 `extract_abstract` 是工具、不是上传预处理？** 对齐 omp 的 `summarizeCode()`：它是**读取时的可选便利**，agent 按需调用，不是入库步骤。上传时只做格式转换（PDF → 纯文本），不做任何内容分析。提取逻辑也极简：从头找第一个独立成段的 "abstract" 行，取其下方第一个非空自然段。鲁棒性靠一个检查保证——只有 "abstract" 单独占一行才算数（排除 "In this abstract, we..." 这类误命中）。

**验证**：

```bash
cd backend
uv run python -c "from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract; print([t.name for t in [list_papers, read_paper, search_papers, extract_abstract]])"
```

看到四个工具名即正确。
```

- [ ] **Step 9: 第 7 步 build_graph 工具列表更新（lines 474, 480）**

把 `from agentic_search.agents.tools import list_papers, list_sections, read_section, search_sections` 改为 `from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract`

把 `tools = [list_papers, list_sections, read_section, search_sections]` 改为 `tools = [list_papers, read_paper, search_papers, extract_abstract]`

- [ ] **Step 10: 下一步段落（line 896）**

无工具名引用，但确认无 section 残留。

- [ ] **Step 11: Commit**

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 四工具新签名——list_papers/read_paper/search_papers/extract_abstract"
```

---

### Task 3: 概念速查.md + 项目概览.md + 00-开始指南.md — 全局同步

**Files:**
- Modify: `任务文档/概念速查.md`
- Modify: `任务文档/项目概览.md`
- Modify: `任务文档/00-开始指南.md`

**Interfaces:**
- Consumes: Task 1+2 的最终工具名与 schema

**概念速查.md 改动点：**

- [ ] **Step 1: Agentic Search 条目（lines 11, 13）**

把 `先看目录（list_sections），再按需取某一章（read_section），或在全部章节里正则定位关键词（search_sections）` 改为 `先用正则定位关键词行号（search_papers），再按行号取片段（read_paper），或提取摘要判断相关性（extract_abstract）`

把 `四个论文导航工具——list_papers（看有哪些论文）、list_sections（看某篇的目录）、read_section（取某一章正文）、search_sections（正则跨章节定位）` 改为 `四个论文导航工具——list_papers（看有哪些论文）、read_paper（按行号取片段）、search_papers（正则定位行号）、extract_abstract（提取摘要）`

- [ ] **Step 2: pymupdf 条目（lines 196-206）**

整段替换为：

```markdown
**定义**：基于 MuPDF 内核的轻量 PDF 处理库。`page.get_text("text")` 返回该页的纯文本字符串——单一 wheel、无模型下载、无 GPU 依赖、即装即用。

**为什么需要**：Agent 要按行号自主探索论文（正则定位、按行号取片段），需要先把 PDF 转成纯文本。pymupdf 用最简的方式做到：即装即用、零额外依赖。不做任何切分——切分是 agent 的职责，它用正则搜索定位行号、按行号读取片段。

**本项目用法**：在 `backend/src/agentic_search/services/documents.py` 的 `parse_pdf()` 函数中调用 pymupdf 的 `get_text("text")`，把 PDF 转为完整纯文本后连同 `doc_id`、`filename`、`uploaded_at` 存入 MongoDB 的 `documents` 集合。Agent 经 `read_paper(doc_id, start_line, end_line)` 按行号取片段，或经 `search_papers(pattern)` 正则定位。

**理解示例**（教学示例）：一份多页论文 PDF，pymupdf 逐页调用 `get_text("text")` 提取纯文本，所有页拼接成一个完整字符串存入 MongoDB——agent 想看实验就用 `search_papers("experiment|evaluation")` 定位行号，再用 `read_paper` 取那段文本。

**延伸阅读**：[pymupdf 官方文档](https://pymupdf.readthedocs.io/)
```

- [ ] **Step 3: MongoDB 条目（line 216）**

把 `{ _id, doc_id, filename, sections, uploaded_at }`，`sections` 是 `parse_pdf` 切好的 `{section_id, title, level, text}` 章节数组` 改为 `{ _id, doc_id, filename, text, uploaded_at }`，`text` 是 `parse_pdf` 提取的完整纯文本`

- [ ] **Step 4: MongoDB Compass 条目（line 230）**

把 `{ doc_id, filename, sections, uploaded_at }` 文档（`sections` 是章节数组，每项含 `section_id`/`title`/`level`/`text`）` 改为 `{ doc_id, filename, text, uploaded_at }` 文档（`text` 是完整纯文本）`

- [ ] **Step 5: PyMongo 条目（line 268）**

把 `read_document()` 用 `find_one()` 按 `doc_id` 取回一篇论文（`sections` 章节数组），`read_section()` 则从该数组取指定 `section_id` 的一章` 改为 `read_document()` 用 `find_one()` 按 `doc_id` 取回一篇论文（`text` 完整纯文本）`

- [ ] **Step 6: ReAct 条目（lines 316, 318）**

把 `bind_tools` 把四个论文导航工具（`list_papers`/`list_sections`/`read_section`/`search_sections`）的 schema 绑给 LLM` 改为 `bind_tools` 把四个论文导航工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）的 schema 绑给 LLM`

把 `注意 search_sections 用正则` 改为 `注意 search_papers 用正则`

把 `agent 的典型轨迹是 list_papers → list_sections → search_sections("dataset|corpus|benchmark") → 在命中章节用 read_section 取正文 → 给出答案` 改为 `agent 的典型轨迹是 list_papers → extract_abstract（判断相关性）→ search_papers("dataset|corpus|benchmark") → 在命中行号用 read_paper 取正文 → 给出答案`

- [ ] **Step 7: LangGraph 条目（line 190 前，tool_calls 示例如有引用 search_sections 也改）**

检查 line 164-192 段落，如有 `list_sections`/`read_section`/`search_sections` 引用则全部替换为 `read_paper`/`search_papers`/`extract_abstract`。

**项目概览.md 改动点：**

- [ ] **Step 8: 文件结构树（lines 78, 80-81）**

把 `documents.py # 文档工具（parse_pdf 切章节 / list / read / read_section）` 改为 `documents.py # 文档工具（parse_pdf 转纯文本 / list / read_document）`

把 `· agentic_search.documents → 论文章节正文（sections 数组）` 改为 `· agentic_search.documents → 论文完整文本`

- [ ] **Step 9: 各层职责（lines 99-100）**

把 `bind_tools` 绑定 4 个论文导航工具（`list_papers`/`list_sections`/`read_section`/`search_sections`）` 改为 `bind_tools` 绑定 4 个论文导航工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）`

把 `parse_pdf` 用 `get_text("dict")` 切章节 / `list_documents` / `read_document` / `read_section`）` 改为 `parse_pdf` 用 `get_text("text")` 转纯文本 / `list_documents` / `read_document`）`

- [ ] **Step 10: M1 设计（lines 116-117, 122）**

把 `parse_pdf()` 用 pymupdf 的 `get_text("dict")` 把 PDF 切成 `{section_id, title, level, text}` 章节后存入 MongoDB` 改为 `parse_pdf()` 用 pymupdf 的 `get_text("text")` 把 PDF 转为完整纯文本后存入 MongoDB`

把 `read_section(doc_id, section_id)` 读某一章` 删除（函数不再存在）

把 `list_papers`/`list_sections`/`read_section`/`search_sections`` 改为 `list_papers`/`read_paper`/`search_papers`/`extract_abstract``

- [ ] **Step 11: 数据流——上传 PDF 流程（lines 196-199）**

把 `pymupdf get_text("dict") → 章节数组（内存中处理，不落盘）` 改为 `pymupdf get_text("text") → 完整纯文本（内存中处理，不落盘）`

把 `存入 MongoDB documents 集合 {doc_id, filename, sections: 章节数组, uploaded_at}` 改为 `存入 MongoDB documents 集合 {doc_id, filename, text: 完整纯文本, uploaded_at}`

- [ ] **Step 12: 数据流——提问流程（line 215）**

把 `LLM 自主调 list_papers / list_sections / read_section / search_sections 探索论文` 改为 `LLM 自主调 list_papers / read_paper / search_papers / extract_abstract 探索论文`

- [ ] **Step 13: 技术栈表（line 246）**

把 `PDF → 章节结构化提取（get_text("dict")）` 改为 `PDF → 纯文本提取（get_text("text")）`

**00-开始指南.md 改动点：**

- [ ] **Step 14: 学习路径（lines 35-36）**

把 `把 PDF 切成可读的章节文本` 改为 `把 PDF 转成完整纯文本`

把 `LLM 自主调 list_papers/list_sections/read_section/search_sections 等工具探索论文` 改为 `LLM 自主调 list_papers/read_paper/search_papers/extract_abstract 等工具探索论文`

- [ ] **Step 15: Commit**

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/概念速查.md 任务文档/项目概览.md 任务文档/00-开始指南.md
git commit -m "docs(全局同步): 工具名/schema 统一——list_papers/read_paper/search_papers/extract_abstract"
```

---

## 验收标准（全部完成后执行）

```bash
cd "D:\Python\Common\Agentic Search"
# 1. section 残留检查 → 应为 0
grep -rn "section\|sections\|section_id" 任务文档/
# 2. dict/版式教学残留 → 应为 0
grep -rn "get_text.*dict\|标题启发式\|heading\|span\|block.*type\|字号" 任务文档/
# 3. 旧工具名残留 → 应为 0
grep -rn "list_sections\|read_section\|search_sections" 任务文档/
# 4. 新工具名存在 → 四工具都应有命中
grep -rn "list_papers\|read_paper\|search_papers\|extract_abstract" 任务文档/
# 5. extract_abstract 有定义 → 02 至少 1 处
grep -rn "extract_abstract" 任务文档/02-LangGraph-Agent.md
# 6. 对比性措辞检查 → 应为 0
grep -rn "旧版\|原来\|之前\|不再\|改用" 任务文档/
```
