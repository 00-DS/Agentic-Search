# Task 1: 01-Python文档工具.md — parse_pdf 简化 + schema 扁平化

## Files
- Modify: `任务文档/01-Python文档工具.md`

## Interfaces
- Produces: `parse_pdf(path) -> str`（纯文本），`store_document(doc_id, filename, text)`，`list_documents() -> list[dict]`，`read_document(doc_id) -> dict`（返回完整文档记录含 text 字段）

## 改动点（按文档结构从上到下）

### Step 1: 学习目标第 4 条（line 14）

把 `parse_pdf（结构化提取，切分章节）、list_documents、read_document、read_section 四个文档工具函数，把按章节切分的文本存入 MongoDB` 改为：

`parse_pdf（PDF 转纯文本）、store_document、list_documents、read_document 四个文档工具函数，把完整文本存入 MongoDB`

### Step 2: 本模块产出段落（line 17）

把 `Agent 的论文导航工具（read_section/search_sections 等）调用——Agent 按需读取本模块产出的章节文本片段` 改为：

`Agent 的论文导航工具（read_paper/search_papers 等）调用——Agent 按行号按需读取本模块产出的完整文本片段`

### Step 3: pymupdf 技术概念段落（lines 50-58）

整段替换为：

```
### pymupdf

**pymupdf** 是基于 MuPDF 内核的轻量 PDF 处理库。它通过 `page.get_text("text")` 从 PDF 文本层提取纯文本——单一 wheel、无模型下载、无 GPU 依赖、即装即用。

**`get_text("text")` 返回什么？** 每一页的纯文本字符串，按 PDF 的排版顺序拼接。项目只需把所有页的文本拼成一个完整字符串，存入 MongoDB。不做任何切分——切分是 agent 的职责，它用正则搜索定位行号、按行号读取片段，完全自主。

**为什么不做结构化切分？** 这对齐 omp 的文件读取模型：文件以原始形态存在，agent 用 `grep`（正则搜索行号）+ `read :50-100`（按行号取片段）自主探索，不在入库时做任何预处理。预切分会破坏跨段上下文、切分位置可能出错，反而降低 agent 的探索效果。
```

### Step 4: MongoDB 技术概念段落（line 62）

把 `存放论文（每篇按章节切分为 sections 数组）` 改为 `存放论文（每篇存为完整纯文本）`

### Step 5: 模块结构 mermaid 图（lines 97-113）

把 `Pymupdf["pymupdf<br/>结构化提取（dict + 标题启发式）"]` 改为 `Pymupdf["pymupdf<br/>PDF 转纯文本"]`

把 `Docs[("MongoDB documents<br/>sections 章节数组")]` 改为 `Docs[("MongoDB documents<br/>完整文本")]`

### Step 6: Compass 段落引用（line 142）

把 `PDF 经 pymupdf 提取的章节数组（sections），以及 L1/L2 记忆` 改为 `PDF 经 pymupdf 提取的完整文本，以及 L1/L2 记忆`

### Step 7: pyproject.toml 依赖注释（lines 191-193）

把 `"pymupdf", # PDF → 结构化提取（get_text("dict") + 标题启发式）` 改为 `"pymupdf", # PDF → 纯文本提取（get_text("text")）`

把 `"pymongo", # MongoDB Python 驱动（同步）：存取 sections 章节与记忆` 改为 `"pymongo", # MongoDB Python 驱动（同步）：存取文档文本与记忆`

### Step 8: 步骤 3 函数表（lines 334-340）

整段替换为：

```
| 函数 | 职责 |
|------|------|
| `parse_pdf(pdf_path)` | 用 pymupdf 把 PDF 转为完整纯文本 |
| `store_document(doc_id, filename, text)` | 把完整文本写入 MongoDB `documents` 集合 |
| `list_documents()` | 从 MongoDB 查询所有文档，返回 doc_id 与文件名 |
| `read_document(doc_id)` | 从 MongoDB 读取指定文档的完整记录（含 text 字段） |
```

### Step 9: 步骤 3 import 行（line 345）

把 `from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document, read_section` 改为 `from agentic_search.services.documents import parse_pdf, store_document, list_documents, read_document`

### Step 10: 步骤 3.1 parse_pdf 整段重写（lines 350-480）

整段替换为：

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

### Step 11: 步骤 3.2 store_document 重写（lines 482-523）

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

### Step 12: 步骤 3.3 list_documents / read_document 重写（lines 525-582）

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

### Step 13: 步骤 4 测试重写（lines 586-712）

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

### Step 14: 步骤 5 集成验证重写（lines 716-754）

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

### Step 15: 完成检查清单更新（lines 758-798）

`parse_pdf`、`store_document`、`list_documents`、`read_document`、`read_section` 改为 `parse_pdf`、`store_document`、`list_documents`、`read_document`。

额外验证命令更新为 `text = parse_pdf('你的文件.pdf'); store_document('verify', '你的文件.pdf', text); print(len(read_document('verify')['text']))`

### Step 16: 下一步段落（line 848）

把 `Agent 的论文导航工具（list_papers/list_sections/read_section/search_sections）将调用本模块的 read_section、list_documents 等函数，按需读取本模块切好的章节片段` 改为 `Agent 的论文导航工具（list_papers/read_paper/search_papers/extract_abstract）将调用本模块的 read_document、list_documents 等函数，按行号按需读取本模块产出的完整文本`

### Step 17: Commit

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): 零预处理——删 section 切分，parse_pdf 改 get_text(text)，schema 扁平化"
```

## Global Constraints

- **仅文档范围**：只编辑 `任务文档/` 下的 `.md` 文件，绝不碰 `backend/` 代码。
- **纯新版本，零历史包袱**：不出现"旧版"/"原来"/"之前"/"不再"/"改用"等对比性措辞。
- **无 embedding/向量库**。
- **MongoDB schema**：`{doc_id, filename, text, uploaded_at}`——扁平文档。无 `sections` 数组。
