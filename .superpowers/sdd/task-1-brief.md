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
