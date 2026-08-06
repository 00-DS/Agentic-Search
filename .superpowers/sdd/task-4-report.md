# Task 4 Report — `03-HTML前端.md` 去掉文档选择，配合新 query 契约

**Status:** ✅ Complete
**Commit:** `520b962` — `docs(03): 去掉文档选择下拉框，query 契约去掉 doc_id（配合 agent 自主探索）`
**File changed:** `任务文档/03-HTML前端.md` (untracked new file under redesign; 501 insertions, single file)
**Scope respected:** only `任务文档/03-HTML前端.md` staged/committed; backend untouched; no edits to sibling-task files (00/02/04/概念速查/项目概览).

## Steps implemented (all 8)

1. **学习目标 (line 16)** — reframed "调用 4 个 API 端点" → "调用后端 API（上传、流式提问、整合记忆）". The 5 learning objectives (HTML/DOM/fetch/ReadableStream/FormData) don't mention document selection — untouched, still hold.
2. **删除下拉框 HTML (1.2 控件区)** — removed `<h2>文档列表</h2>`, `<div id="doc-list">`, its `<hr>`, and the leading blank; reframed "三块功能" → "两块功能（PDF 上传、整合会话记忆按钮）". Upload button (`/api/ingest`) kept. 1.1 骨架 comment updated to "上传 + 整合记忆按钮".
3. **`askQuestion()` fetch body (step 5, line 317)** — `{ question: question, doc_id: currentDocId }` → `{ question: question }`. This is the core contract change.
4. **`loadDocuments()` (step 3)** — frontend no longer renders a dropdown. `GET /api/documents` is reframed as "现供 agent 的 `list_papers` 工具调用，前端不再渲染它，仅作 GET + JSON 解析语法演示". `renderDocList` (3.2) deleted entirely (was pure dropdown DOM logic; the createElement/appendChild fundamentals are still taught in step 2.3). `loadDocuments()` no longer called by `uploadFile()` or at init.
5. **模块结构 mermaid + 数据流描述 (line 51)** — mermaid `BE` block correctly still shows 4 backend endpoints (backend has 4). Data-flow prose reframed: frontend calls `ingest`/`query`/`consolidate` (3), `documents` serves the agent's `list_papers` tool; added "用户只管提问，读哪篇论文由 agent 自主探索决定".
6. **「为什么前端排在模块 2 之后」(line 60)** — "需要后端能响应 4 个 API 端点" → "需要后端的 agent 已经能自主探索论文并流式作答".
7. **grep 一致性扫描** — see below.
8. **Commit** — done (`520b962`).

## grep summary (`doc_id|doc-list|loadDocuments|docListEl|currentDocId|renderDocList|下拉`)

Dropdown logic **fully removed**:
- `doc-list` / `loadDocuments` / `docListEl` / `currentDocId` / `renderDocList` → **0 hits**.
- `下拉框` → 2 hits, both **explanatory notes** stating the dropdown was removed (line 51 data-flow, line 230 step-3 intro). Intentional.

`doc_id` survives only in **2 legitimate backend response-contract** spots (not the query body, not the dropdown), both aligned with module 02's actual contract:
- step 3.1 GET example: `[{doc_id: "abc", filename: "paper.pdf"}]` — matches module 02 `DocumentItem` (`doc_id` + `filename`). Also fixes a stale `id/name` from the old example.
- step 4 upload comment: `// 后端返回 {doc_id, filename}` — matches module 02 `IngestResponse`.

## Cross-reference integrity

- **Decorator network (02 @retry ↔ 04 @dataclass ↔ 02 @router):** module 03 is not a carrier — unaffected.
- **Module 04 ↔ 03:** 04 references 03 only for the `consolidateMemory()` L2 button (step 6) — **unchanged**, still present in 03. No dropdown dependency in 04.
- **Module 03 ↔ 02:** 03's endpoint/contract descriptions now match 02's rewritten contract (`/api/query` takes only `question`; `documents` endpoint serves `list_papers` tool; 4 backend endpoints total). Prereq (line 55) and step-0 (line ~89) still say backend exposes 4 endpoints — accurate.

## What stayed (per brief)

HTML structure teaching, fetch/AJAX teaching, FormData upload teaching, ReadableStream streaming, module-4 memory display, `/api/ingest` upload — all preserved. The frontend now makes 3 POSTs (ingest/query/consolidate) and zero GETs; the GET concept is still taught in step 3.1 as a syntax demo against the agent-served `/api/documents`.

## Concerns

- **Minor pedagogical shift:** removing `renderDocList` (3.2) drops the "iterate an array → render multiple nodes" example. The createElement/appendChild fundamentals remain in step 2.3 (`appendMessage`). Bulk-list rendering is a minor extension; acceptable given the dropdown it served no longer exists. Flagging for awareness, not a blocker.
- **File was untracked under redesign:** old `任务文档/02-HTML前端.md` is deleted (module renumbered 02→03); `03-HTML前端.md` committed as a new file. This is consistent with the broader redesign, not an artifact of my work.

## Verification

- grep scan confirms dropdown logic gone (above).
- Re-read all 7 changed sections (1.2 controls, step 3, upload, query body, step-5 verify, app.js skeleton, checklist) — coherent, no dangling references.
- Single-file commit isolated from sibling tasks' working-tree changes.
