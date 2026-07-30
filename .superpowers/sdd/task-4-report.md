# Task 4 Report — `03-LangGraph-Agent.md`

## Brief steps applied

All 14 brief steps applied verbatim with **no mismatches**. Every step's 原文 matched the file content exactly (matched by text, not line number).

| Step | Category | Location | Status |
|------|----------|----------|--------|
| 1 | pymupdf | §核心设计 引言段 | ✅ applied |
| 2 | pymupdf | §核心设计 对比表 | ✅ applied |
| 3 | pymupdf | `read_and_answer` 注释 | ✅ applied |
| 4 | pymupdf | `ingest` 注释 (×2 lines) | ✅ applied |
| 5 | pymupdf | §9.2 设计说明 (×2 lines) | ✅ applied |
| 6 | core→configs | §分层架构 读图说明 | ✅ applied |
| 7 | core→configs | 目录树 (×2 lines) | ✅ applied |
| 8 | core→configs | 依赖表 | ✅ applied |
| 9 | core→configs | §第3步 标题 + 说明 (×2 lines) | ✅ applied |
| 10 | core→configs | 代码注释 | ✅ applied |
| 11 | core→configs | import 注释 | ✅ applied |
| 12 | core→configs | 验证命令 | ✅ applied |
| 13 | core→configs | `analyze_intent` import | ✅ applied |
| 14 | db name | config 默认值 | ✅ applied |

## Post-fix grep sweeps (3/3 clean — no brief-missed references)

### 1. `marker`
```
$ grep -n "marker" 任务文档/03-LangGraph-Agent.md
(no matches)
```
→ **0 hits.** All marker-pdf prose converted to pymupdf. No stale tool references.

### 2. `agentic_search_db`
```
$ grep -n "agentic_search_db" 任务文档/03-LangGraph-Agent.md
(no matches)
```
→ **0 hits.** DB name is now `agentic_search` everywhere.

### 3. core/ references (`core/config|from agentic_search\.core|agentic_search/core|├── core`)
```
$ grep -nE "core/config|from agentic_search\.core|agentic_search/core|├── core" 任务文档/03-LangGraph-Agent.md
(no matches)
```
→ **0 hits.** All `core/` → `configs/` renames complete (directory tree, code comments, import paths, import-path docstrings, verification command).

## Brief-missed references fixed

**None.** Unlike Task 3 (file 01), the brief's line-number mapping for file 03 was fully accurate. The grep sweep found zero stale same-category references beyond the 14 steps. The brief covered file 03 completely.

## MongoDB doc URLs

The task noted that any MongoDB doc URL containing `databases-and-collections` should stay intact. Grep sweep #3 returned **0** `core/` hits — there are no MongoDB doc URLs containing `core/` in this file, and no URLs were touched. All links preserved.

## Files changed

- `任务文档/03-LangGraph-Agent.md` — 16 line-level edits (across the 14 brief steps; 3 steps spanned 2 adjacent lines each).

## Conclusion

File 03 now has: **no** `marker`, **no** `agentic_search_db`, **no** `core/config` / `from agentic_search.core` / `agentic_search/core` / `├── core`. Clean.

## Task 4 — Markdown → 纯文本 terminology fixes (任务文档/03-LangGraph-Agent.md)

All 7 lines matched exactly by surrounding text; no mismatches.

1. L90: `一篇论文的 Markdown 全文` → `一篇论文的纯文本全文`
2. L281: `读取的论文全文 Markdown` → `读取的论文全文纯文本`
3. L364: `读取论文全文 Markdown` → `读取论文全文纯文本`
4. L368: `读取论文全文 Markdown` → `读取论文全文纯文本`
5. L377: `论文全文（Markdown 格式）` → `论文全文（纯文本）`
6. L398: `读取第一篇论文的 Markdown 全文` → `读取第一篇论文的纯文本全文`
7. L605: `转 Markdown 并存入` → `提取纯文本并存入`

Verification: `grep Markdown` on the file → 0 matches after edit. Diff = 7 insertions, 7 deletions, no other lines touched.

Commit: 8ae4255 — `docs(03): align Markdown terminology to 纯文本 for pymupdf output`
