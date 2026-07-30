# 用 pymupdf 替换 marker-pdf + 三处结构修正（任务文档更新）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `任务文档/` 中所有 marker-pdf 内容改为 pymupdf（最简纯文本提取），并同步三处结构修正：① 初始化命令改为 `uv init --lib agentic-search`；② 数据库名 `agentic_search_db` → `agentic_search`；③ 配置目录 `core/` → `configs/`。

**Architecture:** 零代码架构改动——只更新教学文档。`parse_pdf` 签名不变、只换函数体；store/read/list 三函数不动；ingest-time 解析 + MongoDB 存储的流程不变。叙事上保留"结构助 LLM 理解"的通论，加一处"刻意选最简提取"的诚实标注。

**Tech Stack:** pymupdf（现代 `import pymupdf` API，非旧 `import fitz`）

## Global Constraints

- **范围：仅改 `任务文档/` 下的 `.md` 文件。`backend/` 实现代码一律不动。**
- pymupdf：导入写 **`import pymupdf`**（≥1.23.8 官方推荐别名），**不用** `import fitz`。`parse_pdf` 返回**纯文本**：`page.get_text()` 逐页提取、`"\n".join(...)` 空行拼接。`get_text()` 默认不输出图片/矢量图，"丢弃非文字"天然成立，**无需后处理**。`parse_pdf(pdf_path: str | Path) -> str` **签名与职责不变**，只换函数体。**移除**旧 marker-pdf 的 `_converter` / `_get_converter()` 整段。`store_document`/`read_document`/`list_documents` 三函数**不动**。
- 叙事策略：**保留通论 + 标注简化**——保留"为什么结构重要"通论，加一句"本项目刻意选最简提取"。
- **数据库名统一为 `agentic_search`**（**不要 `_db` 后缀**）。所有 `agentic_search_db` → `agentic_search`，含默认值字符串（如 03 的 `mongo_db: str = "agentic_search_db"`→`"agentic_search"`）。
- **配置目录 `core/` → `configs/`**：含文件名 `core/config.py`→`configs/config.py`、目录树中的 `core/`→`configs/`、import 路径 `from agentic_search.core.config`→`from agentic_search.configs.config`。**⚠️ 例外：MongoDB 官方文档 URL `https://www.mongodb.com/zh-cn/docs/manual/core/databases-and-collections/` 中的 `core/` 是 URL 路径，绝对不能改。**
- **初始化命令**：`uv init --lib agentic-search`（带包名，从源头解决命名问题），再手动把生成的 `agentic-search/` 调整到 `backend/` 位置。
- pymupdf 链接统一 `https://pymupdf.readthedocs.io/`。每个文件改完即 commit。

---

## Task 1: `01-Python文档工具.md` — pymupdf 技术叙事与依赖

**Files:**
- Modify: `任务文档/01-Python文档工具.md`（多处）

**Interfaces:**
- Consumes: 无（第一个 task）
- Produces: 01 的"工具身份"从 marker-pdf 切到 pymupdf。

- [ ] **Step 1: 改标题行技术栈（第 2 行）**

原文：`> 技术栈：Python 3.11+ / uv / marker-pdf / pydantic-settings / pymongo / MongoDB / pytest`
改为：`> 技术栈：Python 3.11+ / uv / pymupdf / pydantic-settings / pymongo / MongoDB / pytest`

- [ ] **Step 2: 改学习目标第 4 条（第 14 行）**

原文：`4. 使用 **marker-pdf + PyMongo** 在 `services/documents.py` 中实现 `parse_pdf`、`store_document`、`list_documents`、`read_document` 四个文档工具函数，把 Markdown 全文存入 MongoDB`
改为：`4. 使用 **pymupdf + PyMongo** 在 `services/documents.py` 中实现 `parse_pdf`、`store_document`、`list_documents`、`read_document` 四个文档工具函数，把 PDF 提取的纯文本全文存入 MongoDB`

- [ ] **Step 3: 重写 §技术概念「marker-pdf」段为「pymupdf」（第 50-54 行）**

把整个 `### marker-pdf` 小节替换为：

```markdown
### pymupdf

**pymupdf** 是基于 MuPDF 内核的轻量 PDF 处理库。它通过 `page.get_text()` 直接从 PDF 文本层提取文字——单一 wheel、无模型下载、无 GPU 依赖、即装即用。

**为什么需要把 PDF 转成文字而非用 RAG 切片？** 传统的 RAG（检索增强生成）方案需要把文档预先切片，再用 BM25 等关键词检索算法定位相关片段——这种方案诞生于 2022 年，当时 LLM 上下文窗口有限（4K–8K tokens），无法一次性读完一篇论文。现代 LLM 上下文窗口已达 128K tokens 以上，一篇 20 页论文全文（约 8K–12K tokens）可以完整放入上下文。因此本项目的做法是：**直接读文档全文，让 LLM 做语义理解**，不做关键词匹配。pymupdf 提取的纯文本全文，正是「全文」的可读形态。

> **关于"结构化"的取舍说明**：理论上，能保留标题层级（`#`）、表格、公式的**结构化 Markdown** 比纯文本更利于 LLM 理解——标题预示新章节、表格是数据浓缩、公式有语义。保留结构的工具（如 marker-pdf、MinerU）需要下载并加载深度学习模型，依赖链重、首次启动慢。本项目为降低安装与上手门槛，**刻意选择最简的纯文本提取**（pymupdf）：零模型、零下载、即装即用。对教学而言，这足以演示「全文进 LLM 上下文」的核心思想。生产环境若需保留结构，可换用更重的工具。
```

- [ ] **Step 4: 改 mermaid 图节点（第 102-103 行）**

原文：
```
    Services --> Marker["marker-pdf<br/>PDF 解析"]
    Marker --> Docs[("MongoDB documents<br/>Markdown 全文")]
```
改为：
```
    Services --> Pymupdf["pymupdf<br/>PDF 纯文本提取"]
    Pymupdf --> Docs[("MongoDB documents<br/>纯文本全文")]
```

- [ ] **Step 5: 改项目结构说明（第 138 行，含数据库名一并修正）**

此行同时含 marker-pdf 与 `agentic_search_db`，一次性改两处（数据库名 `agentic_search_db`→`agentic_search` 属全局约束，在此一并修正）。

原文：`> 本项目不使用任何本地文件目录存储数据。PDF 经 marker-pdf 转换后的完整 Markdown 全文，以及 L1/L2 记忆，全部存入 MongoDB（`agentic_search_db` 数据库，`localhost:27017`）。学生可用 **MongoDB Compass** 可视化查看数据库状态。安装 MongoDB Community Server 与 Compass 的步骤见[开始之前](./00-开始指南.md)。`
改为：`> 本项目不使用任何本地文件目录存储数据。PDF 经 pymupdf 提取的完整纯文本全文，以及 L1/L2 记忆，全部存入 MongoDB（`agentic_search` 数据库，`localhost:27017`）。学生可用 **MongoDB Compass** 可视化查看数据库状态。安装 MongoDB Community Server 与 Compass 的步骤见[开始之前](./00-开始指南.md)。`

- [ ] **Step 6: 改 pyproject.toml 依赖示例（第 180 行）**

原文：`    "marker-pdf",                   # PDF → 结构化 Markdown`
改为：`    "pymupdf",                      # PDF → 纯文本提取`

- [ ] **Step 7: 改依赖讲解段（第 199 行）**

原文：`本模块需 `marker-pdf`、`pydantic-settings`、`pymongo``
改为：`本模块需 `pymupdf`、`pydantic-settings`、`pymongo``

- [ ] **Step 8: 删除"模型权重下载"预警（第 214 行）**

原文：`marker-pdf 首次安装可能需要下载模型权重，请耐心等待。` → **整行删除**。

- [ ] **Step 9: 改依赖验证命令（第 238 行）**

原文：`uv run python -c "import marker; from pydantic_settings import BaseSettings; import pymongo; print('依赖安装成功')"`
改为：`uv run python -c "import pymupdf; from pydantic_settings import BaseSettings; import pymongo; print('依赖安装成功')"`

- [ ] **Step 10: 改 config 讲解里 marker-pdf 措辞（第 271 行）**

原文：`本模块文档服务把 marker-pdf 转出的 Markdown 全文存入该库`
改为：`本模块文档服务把 pymupdf 提取的纯文本全文存入该库`

- [ ] **Step 11: 改 §步骤3 函数表（第 327 行）**

原文：`| `parse_pdf(pdf_path)` | 用 marker-pdf 把 PDF 转为结构化 Markdown 文本 |`
改为：`| `parse_pdf(pdf_path)` | 用 pymupdf 把 PDF 提取为纯文本 |`

- [ ] **Step 12: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): rewrite marker-pdf tech narrative to pymupdf"
```

---

## Task 2: `01-Python文档工具.md` — parse_pdf spec 与测试

**Files:**
- Modify: `任务文档/01-Python文档工具.md`（§3.1、§3.2 注释、§4.1、§步骤5）

- [ ] **Step 1: 整段重写 §3.1 `parse_pdf(pdf_path)`（约第 340-425 行，到 `### 3.2` 前）**

替换为：

````markdown
### 3.1 `parse_pdf(pdf_path)`

**功能定义**：

```python
def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF 文件，使用 pymupdf 提取纯文本（图片等非文字内容丢弃）。"""
```

输入：PDF 文件路径（如 `"paper.pdf"`，可放在 `backend/` 下任意位置）。输出：提取后的纯文本，页与页之间用空行拼接。

**pymupdf 基础用法**（官方文档：https://pymupdf.readthedocs.io/）。核心是「打开文档 → 逐页取文字」：

```python
import pymupdf

doc = pymupdf.open("example.pdf")   # 打开文档
parts = []
for page in doc:                    # 逐页迭代
    parts.append(page.get_text())   # get_text() 默认只返回文字
text = "\n".join(parts)             # 页间空行拼接
```

关键概念：`pymupdf.open(path)` 打开 PDF（返回 Document 对象）；`for page in doc` 遍历每一页；`page.get_text()` 提取该页**文字**（默认不输出图片、矢量图等非文字内容，"丢弃"天然成立）；`"\n".join(...)` 把各页文字用空行拼成一段连续文本。

> 现代导入写 `import pymupdf`（pymupdf ≥1.23.8 的官方推荐别名）。旧代码里的 `import fitz` 仍可用，但官方文档统一用 `import pymupdf`，本项目也用这个。

**转换效果**。假设 PDF 中有：

```
1 Introduction
Transformers have revolutionized NLP...
```

pymupdf 提取后得到的是**纯文本**（无 `#` 标题标记、无 Markdown 表格重建）：

```
1 Introduction

Transformers have revolutionized NLP...
```

文字内容原样保留，但文档的**逻辑结构标记**（标题层级、表格格式、公式）不复存在。对本项目而言这足够——全文交给 LLM 做语义理解，模型能从文字本身读出章节含义。

**你需要实现的逻辑**：检查文件是否存在 → 打开 PDF → 逐页提取文字 → 关闭文档 → 返回拼接结果。以下是**教学示例，展示核心逻辑，非完整实现**：

```python
from pathlib import Path
import pymupdf


def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF 文件，使用 pymupdf 提取纯文本（图片等非文字内容丢弃）。"""
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    doc = pymupdf.open(p)
    parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(parts)
```

讲解要点：

- **无需缓存 converter**：marker-pdf 之类工具初始化要加载模型、开销大，需用模块级缓存；pymupdf 的 `open()` 是轻量操作，每次调用即可，无需缓存层。
- **错误处理**：路径不存在时抛出 `FileNotFoundError` 并附上具体路径，便于排查。调用方（[模块 3](./03-LangGraph-Agent.md) 的 API 层）可以捕获此异常并向用户返回友好提示。
- **图片等非文字内容**：`get_text()` 默认不输出，无需额外处理即满足"只留文字"的要求。

**测试你的函数**：准备任意一个 PDF 文件，放在 `backend/` 下：

```bash
uv run python -c "from agentic_search.services.documents import parse_pdf; print(parse_pdf('你的文件.pdf')[:200])"
```

**验证**：输出 PDF 提取后的纯文本前 200 个字符，而非报错。注意输出是连续纯文本，不含 `#` 标题标记。
````

- [ ] **Step 2: 改 store_document 示例注释（第 454 行附近）**

原文：`            "markdown": markdown,                   # marker-pdf 转出的完整 Markdown 全文`
改为：`            "markdown": markdown,                   # pymupdf 提取的完整纯文本全文`

- [ ] **Step 3: 重写 §4.1 测试（约第 551-579 行，`#### 4.1` 到 `#### 4.2` 前）**

替换为：

````markdown
#### 4.1 测试 `parse_pdf`

`parse_pdf` 是纯提取函数（输入文件路径、输出纯文本字符串），不依赖 MongoDB，测试最直接：

```python
from agentic_search.services.documents import parse_pdf
import pytest


def test_parse_pdf_returns_string():
    """parse_pdf 应返回字符串。"""
    result = parse_pdf("test_sample.pdf")
    assert isinstance(result, str)
    assert len(result) > 0  # 不应为空


def test_parse_pdf_file_not_found():
    """传入不存在的路径应抛出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        parse_pdf("nonexistent_file.pdf")
```

> 你需要准备一个测试用 PDF（放在 `backend/` 目录下，命名为 `test_sample.pdf`）。可创建一个简单文本文档导出为 PDF，或使用任何已有论文 PDF。`parse_pdf` 不依赖 MongoDB，故可独立测试。

注意：提取结果是纯文本，不再断言含 `#` 之类结构标记——pymupdf 输出不含这些。
````

- [ ] **Step 4: 改 §步骤5 集成验证示例（第 647-648 行）**

原文：
```
# 1. 将一个 PDF 转换为 Markdown
markdown = parse_pdf('你的文件.pdf')
print(f'转换完成，Markdown 长度: {len(markdown)} 字符')
```
改为：
```
# 1. 将一个 PDF 提取为纯文本
markdown = parse_pdf('你的文件.pdf')
print(f'提取完成，文本长度: {len(markdown)} 字符')
```

- [ ] **Step 5: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): rewrite parse_pdf spec and tests for pymupdf"
```

---

## Task 3: `01-Python文档工具.md` — uv init 命令 + core→configs + 数据库名

> 三处结构修正在本文件的集中改动。注意 core→configs 要避开 MongoDB URL（本文件 §延伸阅读第 763 行有 `core/databases-and-collections` URL，不改）。

**Files:**
- Modify: `任务文档/01-Python文档工具.md`（多处）

- [ ] **Step 1: 重写 §1.1 初始化命令（第 148-156 行）**

原文：
```
打开命令行，进入项目根目录，创建并进入 `backend/`：

​```bash
mkdir backend
cd backend
uv init --lib .
​```

`uv init --lib` 创建一个**库项目**：生成 `pyproject.toml`（含构建后端声明）和 `src/` 目录结构。这与 `uv init`（默认的应用项目）的区别在于，库项目会带上 `[build-system]` 字段，使其可被 `pip install`。
```
改为：
```
打开命令行，进入项目根目录，用 `uv init --lib <包名>` 初始化库项目（直接把包名传给 `uv init`，从源头让生成物命名正确）：

​```bash
uv init --lib agentic-search
​```

`uv init --lib agentic-search` 会创建一个名为 `agentic-search/` 的目录，其内部已经生成 `pyproject.toml`（含 `[build-system]` 字段）和 `src/agentic_search/`（连字符自动转下划线，命名已正确）。

随后**手动把目录调整到本项目的 `backend/` 位置**——把生成的 `agentic-search/` 改名为 `backend/`（或将其内容移入已有的 `backend/`）：

​```bash
mv agentic-search backend
cd backend
​```

`uv init --lib` 创建的是**库项目**：生成 `pyproject.toml`（含构建后端声明）和 `src/` 目录结构。这与 `uv init`（默认的应用项目）的区别在于，库项目会带上 `[build-system]` 字段，使其可被 `pip install`。
```

- [ ] **Step 2: 改 §1.3 讲解段（第 172 行）**

原文：`​`uv init --lib`​ 生成的 `pyproject.toml` 已有基本骨架。需要将其中的包名改为 `agentic-search`，并补充依赖。`
改为：`由于初始化时已传入包名 `agentic-search`，生成的 `pyproject.toml` 已有正确的 `name` 字段，无需再改包名，只补充依赖即可。`

- [ ] **Step 3: 改"默认包名"提示（第 202 行）**

原文：`> `uv init --lib` 默认生成的包名可能是 `backend`。请务必改为 `agentic-search`，并确保 `src/` 下的目录名是 `agentic_search`（下划线）。若目录名不符，需用 `mv` 重命名。`
改为：`> 因为初始化命令已指定包名 `agentic-search`，`src/` 下的目录名自动为 `agentic_search`（下划线），无需手动改名。`

- [ ] **Step 4: core→configs — 扁平结构对比图（第 36 行）**

原文：`                             ├── core/config.py`
改为：`                             ├── configs/config.py`

- [ ] **Step 5: core→configs — 学习目标第 3 条（第 13 行）**

原文：`3. 使用 **pydantic-settings** 编写配置层 `core/config.py`，从 `.env` 读取...`
改为：`3. 使用 **pydantic-settings** 编写配置层 `configs/config.py`，从 `.env` 读取...`

- [ ] **Step 6: core→configs — 产出说明（第 17 行）**

原文：`...包化骨架（`pyproject.toml` + `src/agentic_search/`）、配置层（`core/config.py`）与文档服务...`
改为：`...包化骨架（`pyproject.toml` + `src/agentic_search/`）、配置层（`configs/config.py`）与文档服务...`

- [ ] **Step 7: core→configs — §1.5 目录说明（第 233 行）**

原文：`每个 Python 子包（`core/`、`services/`）都需要一个 `__init__.py` 文件（可为空）来标记其为包。`
改为：`每个 Python 子包（`configs/`、`services/`）都需要一个 `__init__.py` 文件（可为空）来标记其为包。`

- [ ] **Step 8: core→configs — §步骤2 标题（第 245 行）**

原文：`## 步骤 2：`core/config.py` — 配置层`
改为：`## 步骤 2：`configs/config.py` — 配置层`

- [ ] **Step 9: core→configs — §2.2 小标题（第 275 行）**

原文：`### 2.2 编写 `core/config.py``
改为：`### 2.2 编写 `configs/config.py``

- [ ] **Step 10: core→configs — import 路径（第 309 行）**

原文：`整个项目通过 `from agentic_search.core.config import settings` 引用同一个配置对象`
改为：`整个项目通过 `from agentic_search.configs.config import settings` 引用同一个配置对象`

- [ ] **Step 11: core→configs — store_document 示例 import（第 439 行）**

原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

- [ ] **Step 12: 数据库名 — 技术概念段（第 58 行）**

原文：`本项目用 `agentic_search_db` 数据库下的 `documents` 集合存放论文 Markdown 全文`
改为：`本项目用 `agentic_search` 数据库下的 `documents` 集合存放论文 Markdown 全文`

- [ ] **Step 13: 数据库名 — §3.2 术语说明（第 431 行）**

原文：`在 MongoDB 术语中，一个 database（本项目为 `agentic_search_db`）下有若干 collection...`
改为：`在 MongoDB 术语中，一个 database（本项目为 `agentic_search`）下有若干 collection...`

- [ ] **Step 14: 数据库名 — §3.2 验证（第 467 行）**

原文：`...打开 **MongoDB Compass** 查看 `agentic_search_db` 的 `documents` 集合——应能看到一条新记录，其 `markdown` 字段含完整的 `#` 标题结构。`
改为：`...打开 **MongoDB Compass** 查看 `agentic_search` 的 `documents` 集合——应能看到一条新记录，其 `markdown` 字段含完整纯文本全文。`

- [ ] **Step 15: 数据库名 — 验证预期输出（第 317 行）**

原文：`预期输出：`mongodb://localhost:27017 agentic_search_db gpt-4o-mini``
改为：`预期输出：`mongodb://localhost:27017 agentic_search gpt-4o-mini``

- [ ] **Step 16: 数据库名 — 集成验证（第 671 行）**

原文：`...连接 `mongodb://localhost:27017`，在 `agentic_search_db` 数据库的 `documents` 集合中应能看到刚才存入的记录，其 `markdown` 字段含完整全文。`
改为：`...连接 `mongodb://localhost:27017`，在 `agentic_search` 数据库的 `documents` 集合中应能看到刚才存入的记录，其 `markdown` 字段含完整全文。`

- [ ] **Step 17: 数据库名 — 完成检查（第 682 行）**

原文：`- [ ] MongoDB 服务已启动（`localhost:27017`），MongoDB Compass 可连接查看 `agentic_search_db``
改为：`- [ ] MongoDB 服务已启动（`localhost:27017`），MongoDB Compass 可连接查看 `agentic_search``

- [ ] **Step 18: 数据库名 + core→configs — 完成检查（第 679、680、688 行）**

第 679 行原文：`- [ ] `backend/pyproject.toml` 存在，包名为 `agentic-search`，包含 `marker-pdf`、`pydantic-settings`、`pymongo`、`pytest`（dev）`
改为：`- [ ] `backend/pyproject.toml` 存在，包名为 `agentic-search`，包含 `pymupdf`、`pydantic-settings`、`pymongo`、`pytest`（dev）`

第 680 行原文：`- [ ] `backend/src/agentic_search/core/config.py` 存在，`settings` 含 `mongo_uri`、`mongo_db`...`
改为：`- [ ] `backend/src/agentic_search/configs/config.py` 存在，`settings` 含 `mongo_uri`、`mongo_db`...`

第 688 行原文：`uv run python -c "from agentic_search.services.documents import parse_pdf; from agentic_search.core.config import settings; print(settings.mongo_uri); print('包化 import 成功')"`
改为：`uv run python -c "from agentic_search.services.documents import parse_pdf; from agentic_search.configs.config import settings; print(settings.mongo_uri); print('包化 import 成功')"`

- [ ] **Step 19: core→configs — 模块总结（第 773 行）**

原文：`...同时 Agent 会用到 `core/config.py` 中的 LLM 配置...`
改为：`...同时 Agent 会用到 `configs/config.py` 中的 LLM 配置...`

- [ ] **Step 20: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): uv init with name, rename core->configs, db name agentic_search"
```

---

## Task 4: `03-LangGraph-Agent.md` — pymupdf + core→configs + 数据库名

**Files:**
- Modify: `任务文档/03-LangGraph-Agent.md`

- [ ] **Step 1: pymupdf — 引言段（第 88 行）**

原文：`...它直接读取论文全文（marker-pdf 转出的 Markdown），让 LLM 基于全文内容生成回答。`
改为：`...它直接读取论文全文（pymupdf 提取的纯文本），让 LLM 基于全文内容生成回答。`

- [ ] **Step 2: pymupdf — 对比表（第 94 行）**

原文：`| 预处理 | 需切片 + 建向量索引 | 只需 marker-pdf 转 Markdown |`
改为：`| 预处理 | 需切片 + 建向量索引 | 只需 pymupdf 提取纯文本 |`

- [ ] **Step 3: pymupdf — read_and_answer 注释（第 370 行）**

原文：`#    返回 marker-pdf 转换的结构化 Markdown 文本（保留标题层级、段落、表格结构）`
改为：`#    返回 pymupdf 提取的纯文本全文（图片等非文字内容已丢弃）`

- [ ] **Step 4: pymupdf — ingest 注释（第 609、615 行）**

原文：
```
    # ② marker-pdf 的 PdfConverter 需要文件路径：写入临时文件
    ...
    #    # ③ 纯转换：parse_pdf 只负责 marker-pdf 转 Markdown，返回字符串
```
改为：
```
    # ② pymupdf 的 open() 需要文件路径：写入临时文件
    ...
    #    # ③ 纯提取：parse_pdf 只负责 pymupdf 提取纯文本，返回字符串
```

- [ ] **Step 5: pymupdf — §9.2 设计说明（第 630-631 行）**

原文：
```
- **零文件系统依赖**：PDF 字节流写入 `tempfile` 临时文件，marker-pdf 转换后 `os.unlink` 立即删除。...即使转换抛异常，临时文件也会被清理。
- **职责分离**：`parse_pdf` 只做「PDF → Markdown」转换（纯函数...）；`store_document` 只做...
```
改为：
```
- **零文件系统依赖**：PDF 字节流写入 `tempfile` 临时文件，pymupdf 提取后 `os.unlink` 立即删除。...即使提取抛异常，临时文件也会被清理。
- **职责分离**：`parse_pdf` 只做「PDF → 纯文本」提取（纯函数...）；`store_document` 只做...
```

- [ ] **Step 6: core→configs — 读图说明（第 57 行）**

原文：`所有可配置项（LLM 模型名、超时、路径）集中在 `core/config.py`。`
改为：`所有可配置项（LLM 模型名、超时、路径）集中在 `configs/config.py`。`

- [ ] **Step 7: core→configs — 目录树（第 112-113 行）**

原文：
```
├── core/
│   └── config.py        # 本模块新建：配置层（读 .env）
```
改为：
```
├── configs/
│   └── config.py        # 本模块新建：配置层（读 .env）
```

- [ ] **Step 8: core→configs — 依赖表（第 144 行）**

原文：`| `pydantic-settings` | 从 `.env` 读取配置 | `core/config.py` |`
改为：`| `pydantic-settings` | 从 `.env` 读取配置 | `configs/config.py` |`

- [ ] **Step 9: core→configs — §第3步标题与说明（第 206、208 行）**

第 206 行原文：`## 第 3 步：配置层 —— `core/config.py``
改为：`## 第 3 步：配置层 —— `configs/config.py``

第 208 行原文：`...这些可变值集中放到 `core/config.py`，从 `.env` 文件读取。...`
改为：`...这些可变值集中放到 `configs/config.py`，从 `.env` 文件读取。...`

- [ ] **Step 10: core→configs — 代码注释（第 211 行）**

原文：`# core/config.py —— 教学示例：集中管理配置`
改为：`# configs/config.py —— 教学示例：集中管理配置`

- [ ] **Step 11: core→configs — import 注释（第 233 行）**

原文：`# 模块级单例：其他模块 `from agentic_search.core.config import settings` 直接使用`
改为：`# 模块级单例：其他模块 `from agentic_search.configs.config import settings` 直接使用`

- [ ] **Step 12: core→configs — 验证命令（第 255 行）**

原文：`uv run python -c "from agentic_search.core.config import settings; print(settings.llm_model)"`
改为：`uv run python -c "from agentic_search.configs.config import settings; print(settings.llm_model)"`

- [ ] **Step 13: core→configs — analyze_intent import（第 309 行）**

原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

- [ ] **Step 14: 数据库名 — config 默认值（第 226 行）**

原文：`    mongo_db: str = "agentic_search_db"           # 数据库名（记忆与文档均存于此）`
改为：`    mongo_db: str = "agentic_search"              # 数据库名（记忆与文档均存于此）`

- [ ] **Step 15: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/03-LangGraph-Agent.md
git commit -m "docs(03): pymupdf wording, core->configs, db name agentic_search"
```

---

## Task 5: `概念速查.md` — pymupdf + core→configs + 数据库名

> ⚠️ core→configs 在本文件要**避开 MongoDB URL**（第 178、391 行的 `core/databases-and-collections` 不改）。

**Files:**
- Modify: `任务文档/概念速查.md`

- [ ] **Step 1: pymupdf — LangGraph 条目（第 13 行）**

原文：`...后者读取由 marker-pdf 转换的 Markdown 全文并生成回答。...`
改为：`...后者读取由 pymupdf 提取的纯文本全文并生成回答。...`

- [ ] **Step 2: pymupdf — 整段重写「marker-pdf」概念条目为「pymupdf」（第 154-164 行）**

替换为：

```markdown
## pymupdf

**定义**：基于 MuPDF 内核的轻量 PDF 处理库，通过 `page.get_text()` 从 PDF 文本层直接提取纯文字。单一 wheel、无模型下载、无 GPU 依赖。

**为什么需要**：本项目要把整篇论文全文交给 LLM 做语义理解，需要先把 PDF 转成可读文字。pymupdf 用最简的方式做到：即装即用、零额外依赖。它在每一页上调用 `get_text()`，文字层内容原样返回，图片等非文字内容默认不输出。

> **关于"结构化"的取舍**：理论上，能保留标题层级（`#`）、表格、公式的结构化 Markdown（如 marker-pdf、MinerU）比纯文本更利于 LLM 理解。但这些工具需要加载深度学习模型，依赖链重。本项目为降低门槛，**刻意选择最简的纯文本提取**（pymupdf），足以演示「全文进 LLM 上下文」的核心思想。

**本项目用法**：在 `backend/src/agentic_search/services/documents.py` 的 `parse_pdf()` 函数中调用 pymupdf。上传的 PDF 在内存中经 pymupdf 提取为纯文本后，连同 `doc_id`、`filename`、上传时间直接存入 MongoDB 的 `documents` 集合（`markdown` 字段保存全文），原 PDF 不落盘、不保留任何文件。Agent 的 `read_and_answer` 节点经 `read_document(doc_id)` 从 MongoDB 读取全文。

**理解示例**（教学示例）：一份多页论文 PDF，pymupdf 逐页调用 `get_text()` 拿到文字，用空行拼接成一段连续文本——文字内容齐全，但不带 `## 3 Method` 之类的结构标记，也不含图表。

**延伸阅读**：[pymupdf 官方文档](https://pymupdf.readthedocs.io/)
```

- [ ] **Step 3: core→configs + 数据库名 — MongoDB 条目（第 174 行）**

原文：`**本项目用法**：本地运行一个 MongoDB 实例（默认地址 `localhost:27017`），所有数据集中存于名为 `agentic_search_db` 的数据库。...连接配置 `mongo_uri` 与 `mongo_db` 定义在 `core/config.py`，后端通过 PyMongo 读写这两个集合...`
改为：`**本项目用法**：本地运行一个 MongoDB 实例（默认地址 `localhost:27017`），所有数据集中存于名为 `agentic_search` 的数据库。...连接配置 `mongo_uri` 与 `mongo_db` 定义在 `configs/config.py`，后端通过 PyMongo 读写这两个集合...`

- [ ] **Step 4: 数据库名 — Compass 条目（第 188 行）**

原文：`...即可在左侧目录树中看到 `agentic_search_db` 数据库...`
改为：`...即可在左侧目录树中看到 `agentic_search` 数据库...`

- [ ] **Step 5: 数据库名 — PyMongo 条目示例（第 235 行）**

原文：`db = client["agentic_search_db"]`
改为：`db = client["agentic_search"]`

- [ ] **Step 6: core→configs — 包化布局条目（第 365 行）**

原文：`...其下含 `main.py`、`core/`、`api/`、`agents/`、`memory/`、`services/`）...`
改为：`...其下含 `main.py`、`configs/`、`api/`、`agents/`、`memory/`、`services/`）...`

- [ ] **Step 7: 数据库名 + core→configs — 数据存储条目（第 379 行）**

原文：`**本项目用法**：数据库名为 `agentic_search_db`（地址 `localhost:27017`，配置项 `mongo_uri` / `mongo_db` 在 `core/config.py`），...`documents` 集合存放 marker-pdf 转出的完整 Markdown 全文...上传流程把 PDF 经 marker-pdf 转成 Markdown 后直接写入...`
改为：`**本项目用法**：数据库名为 `agentic_search`（地址 `localhost:27017`，配置项 `mongo_uri` / `mongo_db` 在 `configs/config.py`），...`documents` 集合存放 pymupdf 提取的完整纯文本全文...上传流程把 PDF 经 pymupdf 提取为纯文本后直接写入...`

- [ ] **Step 8: 数据库名 — 数据存储理解示例图（第 383 行）**

原文：`MongoDB: agentic_search_db（localhost:27017，唯一数据存储）`
改为：`MongoDB: agentic_search（localhost:27017，唯一数据存储）`

- [ ] **Step 9: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/概念速查.md
git commit -m "docs(概念速查): pymupdf entry, core->configs, db name agentic_search"
```

---

## Task 6: `项目概览.md` — pymupdf + core→configs + 数据库名

**Files:**
- Modify: `任务文档/项目概览.md`

- [ ] **Step 1: pymupdf — M1 描述（第 116 行）**

原文：`2. **services/documents.py** — `parse_pdf()` 用 marker-pdf 转 Markdown 后存入 MongoDB...`
改为：`2. **services/documents.py** — `parse_pdf()` 用 pymupdf 提取纯文本后存入 MongoDB...`

- [ ] **Step 2: pymupdf — 数据流图（第 196 行）**

原文：`marker-pdf → Markdown（内存中处理，不落盘）`
改为：`pymupdf → 纯文本（内存中处理，不落盘）`

- [ ] **Step 3: pymupdf — 技术栈表（第 247 行）**

原文：`| marker-pdf | PDF → 结构化 Markdown | services/documents.py |`
改为：`| pymupdf | PDF → 纯文本提取 | services/documents.py |`

- [ ] **Step 4: pymupdf — 延伸阅读（第 283 行）**

原文：`- **marker-pdf**（PDF 转结构化 Markdown）：https://github.com/VikParuchuri/marker`
改为：`- **pymupdf**（PDF 纯文本提取）：https://pymupdf.readthedocs.io/`

- [ ] **Step 5: core→configs — 精简目录树（第 27 行）**

原文：`    │   core/config.py      # 配置（.env）`
改为：`    │   configs/config.py     # 配置（.env）`

- [ ] **Step 6: core→configs — 详细目录树（第 68-69 行）**

原文：
```
│   │   ├── core/
│   │   │   └── config.py           # 配置（从 .env 读：超时、MongoDB URI/库名、LLM 模型名）
```
改为：
```
│   │   ├── configs/
│   │   │   └── config.py           # 配置（从 .env 读：超时、MongoDB URI/库名、LLM 模型名）
```

- [ ] **Step 7: core→configs — 模块清单（第 97 行）**

原文：`- `core/config.py` — 配置层，从 `.env` 读 LLM 模型名、超时、MongoDB URI 与库名。`
改为：`- `configs/config.py` — 配置层，从 `.env` 读 LLM 模型名、超时、MongoDB URI 与库名。`

- [ ] **Step 8: 数据库名 — 目录树注释（第 80-81 行）**

原文：
```
│   │   #   · agentic_search_db.memories  → L1/L2 记忆
│   │   #   · agentic_search_db.documents → 完整 Markdown 全文
```
改为：
```
│   │   #   · agentic_search.memories  → L1/L2 记忆
│   │   #   · agentic_search.documents → 完整 Markdown 全文
```

- [ ] **Step 9: 数据库名 — 技术栈表（第 251 行）**

原文：`| MongoDB | 记忆数据 + 完整 Markdown 文档存储 | agentic_search_db（localhost:27017） |`
改为：`| MongoDB | 记忆数据 + 完整 Markdown 文档存储 | agentic_search（localhost:27017） |`

- [ ] **Step 10: 数据库名 — 验证标准 M3（第 265 行）**

原文：`...MongoDB Compass 中 `agentic_search_db.memories` 集合出现 L2 记录...`
改为：`...MongoDB Compass 中 `agentic_search.memories` 集合出现 L2 记录...`

- [ ] **Step 11: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/项目概览.md
git commit -m "docs(项目概览): pymupdf, core->configs, db name agentic_search"
```

---

## Task 7: `00-开始指南.md` — pymupdf + 数据库名

**Files:**
- Modify: `任务文档/00-开始指南.md`

- [ ] **Step 1: pymupdf — uv 依赖说明（第 58 行）**

原文：`...后端的全部依赖（FastAPI、LangGraph、marker-pdf、pytest 等）都由它安装。`
改为：`...后端的全部依赖（FastAPI、LangGraph、pymupdf、pytest 等）都由它安装。`

- [ ] **Step 2: pymupdf — 延伸阅读（第 121 行）**

原文：`- marker-pdf（PDF 转 Markdown）：https://github.com/VikParuchuri/marker`
改为：`- pymupdf（PDF 纯文本提取）：https://pymupdf.readthedocs.io/`

- [ ] **Step 3: 数据库名 — MongoDB 说明（第 74 行）**

原文：`> 后端通过 PyMongo（MongoDB 的 Python 驱动）连接 `mongodb://localhost:27017`，数据库名为 `agentic_search_db`。这些配置在模块 1 中讲解。`
改为：`> 后端通过 PyMongo（MongoDB 的 Python 驱动）连接 `mongodb://localhost:27017`，数据库名为 `agentic_search`。这些配置在模块 1 中讲解。`

- [ ] **Step 4: 数据库名 — Compass 说明（第 81 行）**

原文：`- 打开后默认连接 `mongodb://localhost:27017`，即可看到本项目的 `agentic_search_db` 数据库`
改为：`- 打开后默认连接 `mongodb://localhost:27017`，即可看到本项目的 `agentic_search` 数据库`

- [ ] **Step 5: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/00-开始指南.md
git commit -m "docs(00): pymupdf deps, db name agentic_search"
```

---

## Task 8: `02-HTML前端.md` — 数据库名

> 本文件只有一处 `agentic_search_db`，无 pymupdf/core 内容。

**Files:**
- Modify: `任务文档/02-HTML前端.md`

- [ ] **Step 1: 数据库名 — M3 验证（第 451 行）**

原文：`3. 在 MongoDB Compass 的 `agentic_search_db.memories` 集合中应出现一条 L2 记录`
改为：`3. 在 MongoDB Compass 的 `agentic_search.memories` 集合中应出现一条 L2 记录`

- [ ] **Step 2: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/02-HTML前端.md
git commit -m "docs(02): db name agentic_search"
```

---

## Task 9: `04-TMT记忆系统.md` — 数据库名 + core→configs

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`

- [ ] **Step 1: 数据库名 — 引言（第 55 行）**

原文：`存储采用 MongoDB（`agentic_search_db` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作，便于教学调试与用 MongoDB Compass 人工查看。`
改为：`存储采用 MongoDB（`agentic_search` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作，便于教学调试与用 MongoDB Compass 人工查看。`

- [ ] **Step 2: 数据库名 — §2.4 说明（第 196 行）**

原文：`记忆存储采用 MongoDB（`agentic_search_db` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作。...`
改为：`记忆存储采用 MongoDB（`agentic_search` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作。...`

- [ ] **Step 3: core→configs — 逐段讲解（第 155 行）**

原文：`- `call_llm(prompt)`：封装的 LLM 调用函数（模型名、超时等从 `core/config.py` 读取）。`
改为：`- `call_llm(prompt)`：封装的 LLM 调用函数（模型名、超时等从 `configs/config.py` 读取）。`

- [ ] **Step 4: core→configs + 数据库名 — 连接代码示例（第 207、210 行）**

第 207 行原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

第 210 行原文：`db = client[settings.mongo_db]                  # 选中 agentic_search_db`
改为：`db = client[settings.mongo_db]                  # 选中 agentic_search`

- [ ] **Step 5: 数据库名 — 验证（第 276 行）**

原文：`**验证：** 打开 MongoDB Compass 连接 `localhost:27017` → 选择 `agentic_search_db` → `memories` 集合...`
改为：`**验证：** 打开 MongoDB Compass 连接 `localhost:27017` → 选择 `agentic_search` → `memories` 集合...`

- [ ] **Step 6: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/04-TMT记忆系统.md
git commit -m "docs(04): db name agentic_search, core->configs"
```

---

## Task 10: 全局一致性校验

**Files:**
- 校验：`任务文档/` 全目录

- [ ] **Step 1: grep 确认无 marker-pdf 残留**

Run: `grep -rn "marker" 任务文档/`
Expected: **无任何输出**。命中则回对应 task 修复。

- [ ] **Step 2: grep 确认无 PdfConverter/_converter 残留**

Run: `grep -rn "PdfConverter\|create_model_dict\|_converter" 任务文档/`
Expected: **无输出**。

- [ ] **Step 3: grep 确认无 "import fitz"**

Run: `grep -rn "import fitz" 任务文档/`
Expected: **无输出**。

- [ ] **Step 4: grep 确认数据库名全部为 agentic_search**

Run: `grep -rn "agentic_search_db" 任务文档/`
Expected: **无输出**（全部应为 `agentic_search`）。

- [ ] **Step 5: grep 确认 core→configs 干净，且 URL 保留**

Run: `grep -rn "core/config\|from agentic_search\.core\|src/agentic_search/core\|├── core/\|├ core/\|│   ├── core/" 任务文档/`
Expected: **无输出**。
再确认 MongoDB 文档 URL **未被误改**：
Run: `grep -rn "core/databases-and-collections" 任务文档/`
Expected: 仍有命中（这些是 URL，**必须保留**）。

- [ ] **Step 6: 校验"刻意简化"叙事存在**

确认 `01-Python文档工具.md` pymupdf 技术概念段 + `概念速查.md` pymupdf 条目都含"刻意选择最简"取舍说明。

- [ ] **Step 7: 校验 uv init 命令**

Run: `grep -rn "uv init --lib agentic-search" 任务文档/`
Expected: 至少 1 处命中（01 §1.1）。确认 `uv init --lib .`（带点）已不存在。

- [ ] **Step 8: 修补 commit（若有残留）**

若 Step 1-5 发现残留并已修复：

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/
git commit -m "docs: fix residual references found in consistency check"
```

全部干净则跳过。
