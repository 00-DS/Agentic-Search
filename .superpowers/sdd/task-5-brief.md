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
