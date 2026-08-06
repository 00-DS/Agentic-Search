# Task 3: 概念速查.md + 项目概览.md + 00-开始指南.md — 全局同步

## Files
- Modify: `任务文档/概念速查.md`
- Modify: `任务文档/项目概览.md`
- Modify: `任务文档/00-开始指南.md`

## Interfaces
- Consumes: Task 1+2 的最终工具名与 schema

## 概念速查.md 改动点

### Step 1: Agentic Search 条目（lines 11, 13）

line 11: 把 `先看目录（list_sections），再按需取某一章（read_section），或在全部章节里正则定位关键词（search_sections）` 改为 `先用正则定位关键词行号（search_papers），再按行号取片段（read_paper），或提取摘要判断相关性（extract_abstract）`

line 13: 把 `四个论文导航工具——list_papers（看有哪些论文）、list_sections（看某篇的目录）、read_section（取某一章正文）、search_sections（正则跨章节定位）` 改为 `四个论文导航工具——list_papers（看有哪些论文）、read_paper（按行号取片段）、search_papers（正则定位行号）、extract_abstract（提取摘要）`

### Step 2: pymupdf 条目（lines 196-206）

整段替换为：

```markdown
**定义**：基于 MuPDF 内核的轻量 PDF 处理库。`page.get_text("text")` 返回该页的纯文本字符串——单一 wheel、无模型下载、无 GPU 依赖、即装即用。

**为什么需要**：Agent 要按行号自主探索论文（正则定位、按行号取片段），需要先把 PDF 转成纯文本。pymupdf 用最简的方式做到：即装即用、零额外依赖。不做任何切分——切分是 agent 的职责，它用正则搜索定位行号、按行号读取片段。

**本项目用法**：在 `backend/src/agentic_search/services/documents.py` 的 `parse_pdf()` 函数中调用 pymupdf 的 `get_text("text")`，把 PDF 转为完整纯文本后连同 `doc_id`、`filename`、`uploaded_at` 存入 MongoDB 的 `documents` 集合。Agent 经 `read_paper(doc_id, start_line, end_line)` 按行号取片段，或经 `search_papers(pattern)` 正则定位。

**理解示例**（教学示例）：一份多页论文 PDF，pymupdf 逐页调用 `get_text("text")` 提取纯文本，所有页拼接成一个完整字符串存入 MongoDB——agent 想看实验就用 `search_papers("experiment|evaluation")` 定位行号，再用 `read_paper` 取那段文本。

**延伸阅读**：[pymupdf 官方文档](https://pymupdf.readthedocs.io/)
```

### Step 3: MongoDB 条目（line 216）

把 `{ _id, doc_id, filename, sections, uploaded_at }`，`sections` 是 `parse_pdf` 切好的 `{section_id, title, level, text}` 章节数组` 改为 `{ _id, doc_id, filename, text, uploaded_at }`，`text` 是 `parse_pdf` 提取的完整纯文本`

### Step 4: MongoDB Compass 条目（line 230）

把 `{ doc_id, filename, sections, uploaded_at }` 文档（`sections` 是章节数组，每项含 `section_id`/`title`/`level`/`text`）` 改为 `{ doc_id, filename, text, uploaded_at }` 文档（`text` 是完整纯文本）`

### Step 5: PyMongo 条目（line 268）

把 `read_document()` 用 `find_one()` 按 `doc_id` 取回一篇论文（`sections` 章节数组），`read_section()` 则从该数组取指定 `section_id` 的一章` 改为 `read_document()` 用 `find_one()` 按 `doc_id` 取回一篇论文（`text` 完整纯文本）`

### Step 6: ReAct 条目（lines 316, 318）

line 316: 把 `bind_tools` 把四个论文导航工具（`list_papers`/`list_sections`/`read_section`/`search_sections`）的 schema 绑给 LLM` 改为 `bind_tools` 把四个论文导航工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）的 schema 绑给 LLM`

把 `注意 search_sections 用正则` 改为 `注意 search_papers 用正则`

line 318: 把 `agent 的典型轨迹是 list_papers → list_sections → search_sections("dataset|corpus|benchmark") → 在命中章节用 read_section 取正文 → 给出答案` 改为 `agent 的典型轨迹是 list_papers → extract_abstract（判断相关性）→ search_papers("dataset|corpus|benchmark") → 在命中行号用 read_paper 取正文 → 给出答案`

### Step 7: LangGraph 条目（check lines 164-192 for tool references）

检查 line 164-192 段落，如有 `list_sections`/`read_section`/`search_sections` 引用则全部替换为新工具名。

## 项目概览.md 改动点

### Step 8: 文件结构树（lines 78, 80-81）

line 78: 把 `documents.py        # 文档工具（parse_pdf 切章节 / list / read / read_section）` 改为 `documents.py        # 文档工具（parse_pdf 转纯文本 / list / read_document）`

line 81: 把 `· agentic_search.documents → 论文章节正文（sections 数组）` 改为 `· agentic_search.documents → 论文完整文本`

### Step 9: 各层职责（lines 99-100）

line 99: 把 `bind_tools` 绑定 4 个论文导航工具（`list_papers`/`list_sections`/`read_section`/`search_sections`）` 改为 `bind_tools` 绑定 4 个论文导航工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）`

line 100: 把 `parse_pdf` 用 `get_text("dict")` 切章节 / `list_documents` / `read_document` / `read_section`）` 改为 `parse_pdf` 用 `get_text("text")` 转纯文本 / `list_documents` / `read_document`）`

### Step 10: M1 设计（lines 116-117, 122）

line 116: 把 `parse_pdf()` 用 pymupdf 的 `get_text("dict")` 把 PDF 切成 `{section_id, title, level, text}` 章节后存入 MongoDB、`list_documents()` 查询集合、`read_document(doc_id)` 拼全文、`read_section(doc_id, section_id)` 读某一章。` 改为 `parse_pdf()` 用 pymupdf 的 `get_text("text")` 把 PDF 转为完整纯文本后存入 MongoDB、`list_documents()` 查询集合、`read_document(doc_id)` 读完整文档。`

line 117: 把 `list_papers`/`list_sections`/`read_section`/`search_sections`` 改为 `list_papers`/`read_paper`/`search_papers`/`extract_abstract``

### Step 11: 数据流——上传 PDF 流程（lines 196-199）

line 196: 把 `pymupdf get_text("dict") → 章节数组（内存中处理，不落盘）` 改为 `pymupdf get_text("text") → 完整纯文本（内存中处理，不落盘）`

line 199: 把 `存入 MongoDB documents 集合 {doc_id, filename, sections: 章节数组, uploaded_at}` 改为 `存入 MongoDB documents 集合 {doc_id, filename, text: 完整纯文本, uploaded_at}`

### Step 12: 数据流——提问流程（line 215）

把 `LLM 自主调 list_papers / list_sections / read_section / search_sections 探索论文` 改为 `LLM 自主调 list_papers / read_paper / search_papers / extract_abstract 探索论文`

### Step 13: 技术栈表（line 246）

把 `PDF → 章节结构化提取（get_text("dict")）` 改为 `PDF → 纯文本提取（get_text("text")）`

## 00-开始指南.md 改动点

### Step 14: 学习路径（lines 35-36）

line 35: 把 `把 PDF 切成可读的章节文本` 改为 `把 PDF 转成完整纯文本`

line 36: 把 `LLM 自主调 list_papers/list_sections/read_section/search_sections 等工具探索论文` 改为 `LLM 自主调 list_papers/read_paper/search_papers/extract_abstract 等工具探索论文`

### Step 15: Commit

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/概念速查.md 任务文档/项目概览.md 任务文档/00-开始指南.md
git commit -m "docs(全局同步): 工具名/schema 统一——list_papers/read_paper/search_papers/extract_abstract"
```

## Global Constraints

- **仅文档范围**：只编辑 `任务文档/` 下的 `.md` 文件，绝不碰 `backend/` 代码。
- **纯新版本，零历史包袱**：不出现"旧版"/"原来"/"之前"/"不再"/"改用"等对比性措辞。
- **MongoDB schema**：`{doc_id, filename, text, uploaded_at}`——扁平文档。无 `sections` 数组。
- **四工具签名**：`list_papers()` / `read_paper(doc_id, start_line, end_line)` / `search_papers(pattern, doc_id)` / `extract_abstract(doc_id)`
