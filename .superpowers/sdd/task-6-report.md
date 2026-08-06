# Task 6 Report — 跨文档同步（概念速查 + 项目概览 + 00-开始指南）

## Status

✅ **Complete.** All three overview/reference docs synced from the linear-graph narrative to the
agent paradigm (ReAct loop + tool calling + conditional edges), existing decorator cross-reference
network preserved and strengthened, all committed together in one commit.

## Commit

- **`ffa5b12`** — `docs(sync): 概念速查/项目概览/00 同步 agent 范式（ReAct + 工具 + 条件边）`
- 3 files, +136 / -85
- `任务文档/概念速查.md` | 143 lines changed
- `任务文档/项目概览.md` | 50 lines changed
- `任务文档/00-开始指南.md` | 28 lines changed
- Working tree clean for all three after commit. Pre-existing uncommitted decorator-network
  changes (earlier-session work) were preserved and committed alongside the new agent-paradigm
  sync — nothing discarded.

## What changed

### 概念速查.md
- **Agentic Search 条目**: removed the obsolete "128K 上下文窗口 / 整篇论文直接放入" rationale;
  rewrote 为什么需要/本项目用法/理解示例 around on-demand agent exploration
  (`list_sections` → `read_section` → `search_sections`), omp/Claude-Code analogy.
- **LangGraph 条目**: rewrote from linear `analyze_intent → read_and_answer` to the ReAct loop
  (`llm_call ⇄ tool_node` + 条件边 `should_continue`); added `bind_tools` / `ToolNode` /
  `add_conditional_edges` and a ReAct-loop code example.
- **新增 ReAct 条目** (inserted alphabetically before ReadableStream): defines ReAct + tool
  calling, names all four tools, the omp/Claude-Code analogy, and the "search_sections 用正则、不用
  embedding" stance. Carries the grep-required terms into this file.
- **pymupdf 条目**: `get_text()` plain text → `get_text("dict")` structured → `{section_id,
  title, level, text}` sections.
- **MongoDB / Compass / 数据存储 条目**: documents schema `{markdown}` → `{sections}`; agent reads
  via `read_section`/`read_document`.
- **Pydantic 条目 + example**: `/api/query` body from `{question, doc_id}` → `{question}` only
  (read-which-paper is now the agent's call).
- **PyMongo / SSE 条目**: `read_and_answer` node → agent ReAct loop; added `read_section`.
- **AJAX / DOM 操作 / HTML / fetch 条目**: removed stale frontend `loadDocuments()` / `#doc-list`
  references (03 frontend no longer has a doc dropdown); fetch example body `{question, doc_id}`
  → `{question}`.
- **装饰器条目**: PRESERVED (定义/为什么需要/示例/延伸阅读 untouched). Only "本项目用法" updated
  from 三处 → 四处 to add LangChain `@tool` (keeping it consistent with 02's four-decorator
  teaching: `@retry`/`@tool`/`@router`/`@dataclass`). Pointer to 模块 2 第 5 步 retained.
- **FastAPI 条目**: `@router` decorator teaching confirmed still valid — untouched.

### 项目概览.md
- **系统架构 mermaid**: `LangGraph Agent（读文档 + 回答）` → `ReAct Agent（llm_call ⇄ tool_node + 条件边）`.
- **文件结构 tree + 各层职责**: `graph.py` described as ReAct agent + 4 tools + 条件边;
  `documents.py` adds `read_section`; data comment "完整纯文本全文" → "论文章节正文（sections 数组）".
- **M1 学习目标**: added "ReAct agent（工具调用 + 条件边）" alongside the preserved "装饰器（decorator）".
- **M1 内容**: `parse_pdf` → `get_text("dict")` 切章节; module-2 graph described as ReAct agent.
- **M2 app.js**: removed `loadDocuments()` from core functions (frontend no doc dropdown).
- **API 设计表 + 前端示例**: `/api/query` body `{question, doc_id}` → `{question}`.
- **数据流-提问流程**: `analyze_intent/read_and_answer` → ReAct loop
  (`[ llm_call ⇄ tool_node ]` with the four tools).
- **上传流程**: pymupdf → 章节数组; schema `{sections}`.
- **技术栈表**: added LangChain row (`init_chat_model`/`bind_tools`); LangGraph row now "ReAct
  agent 图（ToolNode + 条件边）"; pymupdf → 章节结构化提取; MongoDB → 论文章节. No chroma/embedding.
- **验证 curl**: `/api/query` body dropped `doc_id`.

### 00-开始指南.md
- **学习路径 模块 2**: "LangGraph 编排「分析意图 → 读文档 → 回答」" → "搭一个 ReAct agent，LLM
  自主调 list_papers/list_sections/read_section/search_sections 探索论文".
- **项目简介 第 15 行**: "AI 阅读论文全文" → "AI 自主探索论文（先翻目录、再读相关章节）".
- **「你将学到什么」表**: LangGraph row → "ReAct agent（工具调用 + 条件边）"; Python row "PDF → Markdown"
  → "PDF → 章节文本"; module-1 path "可读的 Markdown" → "可读的章节文本".
- **项目概述 / DeepSeek 配置**: confirmed still accurate, unchanged.

## Grep verification (Step 4-5) — all pass

| Check | Pattern | Result |
|------|---------|--------|
| 1 | `analyze_intent\|read_and_answer\|_read_first_document` | **0 matches** ✓ |
| 2 | `chroma\|embedding\|向量库\|向量检索` | only **negation** ("不用 embedding"/"不用向量库") in 02 + 概念速查 ReAct entry ✓ |
| 3 | `doc_id.*=.*""` | only the **`search_sections(pattern, doc_id="")` tool signature** — exactly the brief's expected "only tool signature" ✓ |
| 4 | `读全文\|128K\|全文进.*窗口\|整篇.*窗口` | **no `128K` anywhere**; remaining `读全文` are negation/contrast ("不写死先读全文") or the `read_document` convenience helper ✓ |
| 5 | `bind_tools\|ToolNode\|add_conditional_edges\|list_papers\|search_sections` | present in **02 + 概念速查 + 项目概览** ✓ |

## Decorator cross-reference network (Step 5) — 5/5 intact

1. 概念速查「装饰器」条目 → **02 第 5 步** (`@retry`) — line 67 延伸阅读 pointer retained ✓
2. 02 技术概念段落 → 第 5 步 / 第 9 步 / 模块 4 — lines 48 + 374 ✓
3. 02 第 5 步「插曲——什么是装饰器？」+ `@retry` — line 321 ✓
4. 02 第 9 步 `@router` 呼应 — line 618 ✓
5. 04 `@dataclass` 呼应 → 02 `@retry` — line 123 ✓

Bonus: concept entry upgraded 三处→四处 to add LangChain `@tool`, matching 02's now-four-decorator
learning objective. Strengthens rather than breaks the network.

## Concerns / Notes

- **`GET /api/documents` response row** in 项目概览 still shows `[{"id", "name"}]` (legacy field
  names, not the project's doc_id/filename contract). Left unchanged — it pre-existed, is out of
  the brief's explicit scope (brief targets only `/api/query`), the frontend no longer renders it,
  and the agent's `list_papers` tool now consumes the endpoint. Flagging for a future consistency
  pass.
- **概念速查 pytest 条目** still has a `test_read_document_returns_markdown` illustration. It's a
  generic pytest-syntax example, not a data-model claim; left as-is.
- LF→CRLF git warnings on commit are harmless Windows line-ending normalization.
- No backend code touched; scope held strictly to `任务文档/`.

## Report path

`D:/Python/Common/Agentic Search/.superpowers/sdd/task-6-report.md`
