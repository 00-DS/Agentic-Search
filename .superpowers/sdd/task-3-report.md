# Task 3 Report — 全局同步（概念速查 / 项目概览 / 00-开始指南）

## Status
✅ Complete. All 15 brief steps applied + 3 brief-implicit fixes. Committed.

## Commit
`b2652bb55b1b81976160bd454a06fe7c9b873b10`
Message: `docs(全局同步): 工具名/schema 统一——list_papers/read_paper/search_papers/extract_abstract`
Diff: 3 files changed, +34 −34.

## Verification (grep gate — PASSED)
Searched all 3 files for `list_sections | read_section | search_sections | section_id | get_text(.*dict) | sections`:
**0 matches.** No old tool names, no `section_id`, no `get_text("dict")`, no `sections` array.

Positive check confirmed new tokens present everywhere: `read_paper` / `search_papers` / `extract_abstract` / `get_text("text")` / `text, uploaded_at`.

## Summary of changes

### 概念速查.md (Steps 1–7 + extras)
- L11 (Step 1): exploration tools → `search_papers` → `read_paper` → `extract_abstract`.
- L13 (Step 1): four-tool list → `list_papers`/`read_paper`/`search_papers`/`extract_abstract`.
- L198–206 (Step 2): full pymupdf entry replaced — `get_text("text")` flat text, no sectioning; agent uses `read_paper`/`search_papers`.
- L214/216/218 (Step 3 + siblings): MongoDB entry — schema `{_id, doc_id, filename, text, uploaded_at}`, `text` = 完整纯文本; cleaned `前端不再` → `前端不`.
- L228/230 (Step 4 + sibling): Compass entry — `{doc_id, filename, text, uploaded_at}`.
- L268 (Step 5): PyMongo entry — `read_document()` returns `text` 完整纯文本; dropped `read_section`.
- L316/318 (Step 6): ReAct entry — tool set + typical trajectory use new names.
- L164–192 (Step 7): LangGraph entry checked — no specific tool names, no change needed.
- L430/432/434/441/442 (**brief-implicit**): 数据存储 entry contained `section_id`/`read_section`/`sections`/`parse_pdf 切章节` NOT enumerated in the brief. Fixed to flat schema + `read_paper`/`search_papers`. *The verification gate (zero `section_id`/`read_section`/`sections`) required this; leaving it would have failed.*

### 项目概览.md (Steps 8–13 + extra)
- L78/81 (Step 8): file-tree + data comment → parse_pdf 转纯文本 / 论文完整文本.
- L99/100 (Step 9): layer responsibilities — new tool set + `get_text("text")`.
- L116/117 (Step 10): M1 design — flat schema, new tools.
- L196/199 (Step 11): upload dataflow → `get_text("text")` / `{doc_id, filename, text, uploaded_at}`.
- L215 (Step 12): query dataflow — new tool set.
- L246 (Step 13): tech-stack pymupdf row → 纯文本提取.
- L251 (**brief-implicit**): tech-stack MongoDB row `论文章节文档存储` → `论文文档存储` (flat-schema consistency within the table already being edited).

### 00-开始指南.md (Step 14 + contradictions)
- L15 (**brief-implicit**): project-intro exploration line `先翻目录、再读相关章节` → `定位关键段落、按需读取` — contradicted the synced tool set in L36 of the same file.
- L22 (**brief-implicit**): skills-table row `PDF → 章节文本` → `PDF → 纯文本` — contradicted synced L35.
- L35/36 (Step 14): learning-path — `把 PDF 转成完整纯文本` + new tool set.

## Deviations from the brief (all justified)
1. **概念速查 数据存储 entry (L430/432/434/441/442)** — not in any numbered step but contained `section_id`, `read_section`, `sections` (gate-forbidden). Fixed; mandatory.
2. **项目概览 L251** + **00-开始指南 L15/L22** — internal contradictions with synced lines in the same files; aligned to keep docs self-consistent ("工具名/schema 统一" goal).
3. **不再 cleanup (概念速查 L216)** — rewrote the line I was authoring to drop `不再` (Global Constraint forbids it); meaning preserved.
4. Commit message uses the brief's Step 15 wording (fuller than the job-section shorthand).

## Concerns
- None blocking. `backend/` untouched (docs-only scope honored).
- Residual `不再` instances exist in prose OUTSIDE this task's scope (frontend-behavior clauses: 概念速查 L27/L122, 项目概览 L131, and runtime-loop semantics like 概念速查 L13/L190, 00-开始指南 L54). These describe loop termination or frontend dropdown removal, not schema/tool migration, so they are legitimate runtime prose — left untouched per scope discipline. If a later pass wants a strictly zero-`不再` docs set, those are the remaining spots.
- A few reading-metaphor uses of 章节 (e.g. 概念速查 L10 「实验章节」, L15 「挑相关章节精读」, ReAct L314) remain — a paper does have chapters as a reading concept; these are not schema references and were intentionally preserved.
