# Task 3 Report — `01-Python文档工具.md`

**Status:** DONE_WITH_CONCERNS

## Summary

Applied all 19 brief edits (Steps 1–19) to `任务文档/01-Python文档工具.md` covering three structural fixes: (1) uv-init command now passes the package name, (2) `core/` → `configs/` rename, (3) database name `agentic_search_db` → `agentic_search`. The brief's **hard** verification requirements all PASS. However, several stale references the brief did **not** list remain in the file (flagged below as concerns — they were out of scope for this task and "Make NO other edits" was explicit).

## Edits Applied (all 19 successful, verbatim)

- **Steps 1–3 (uv init, §1.1):** Rewrote §1.1 to `uv init --lib agentic-search` + `mv agentic-search backend`. Reworded the §1.3 lead-in (removed the "change package name" instruction). Reworded the default-name note. *(Note: on the first pass Step 2 left a redundant opening sentence; corrected immediately — line 181 now matches the brief's 改为 exactly.)*
- **Step 4:** flat-vs-src tree `├── core/config.py` → `├── configs/config.py` (line 36).
- **Step 5:** learning objective #3 `core/config.py` → `configs/config.py` (line 13).
- **Step 6:** 产出说明 `core/config.py` → `configs/config.py` (line 17).
- **Step 7:** §1.5 subdir description `core/` → `configs/` (line 241).
- **Step 8:** §步骤2 heading `core/config.py` → `configs/config.py` (line 253).
- **Step 9:** §2.2 heading `core/config.py` → `configs/config.py` (line 283).
- **Step 10:** import-path mention `from agentic_search.core.config` → `from agentic_search.configs.config` (line 317).
- **Step 11:** store_document sample import (line 436).
- **Step 12:** tech-concept db name → `agentic_search` (line 60).
- **Step 13:** §3.2 术语 db name (line 428).
- **Step 14:** §3.2 验证 db name **and** `# 标题结构` → `纯文本全文` (line 464).
- **Step 15:** 预期输出 db name (line 325).
- **Step 16:** 集成验证 db name only (line 664) — *intentionally keeps `# 标题结构` per the brief, which listed only the db-name change for this line.*
- **Step 17:** 完成检查 db name (line 675).
- **Step 18a:** checklist `marker-pdf` → `pymupdf` (line 672).
- **Step 18b:** checklist path `core/config.py` → `configs/config.py` (line 673).
- **Step 18c:** import-verify command `from agentic_search.core.config` → `from agentic_search.configs.config` (line 681).
- **Step 19:** 下一步 summary `core/config.py` → `configs/config.py` (line 765).

No mismatches against brief text. (Brief line numbers were stale vs. the post-Tasks-1/2 file, so each target was matched by surrounding content per the task instructions.)

## Verification Greps (brief's hard requirements)

```
$ grep -n "agentic_search_db" 任务文档/01-Python文档工具.md
  (no matches)        → PASS (0 hits)

$ grep -n "core/config\|from agentic_search.core" 任务文档/01-Python文档工具.md
  (no matches)        → PASS (0 hits)

$ grep -n "manual/core/databases-and-collections" 任务文档/01-Python文档工具.md
  755:- MongoDB 官方文档（数据库与集合概念）：https://www.mongodb.com/zh-cn/docs/manual/core/databases-and-collections/
  → MongoDB URL INTACT and unchanged. (It uses `manual/core/databases` as a URL path segment, not the project config dir, so correctly left alone.)
```

## `marker` grep — 7 remaining hits

```
 56  ...保留结构的工具（如 marker-pdf、MinerU）需要下载并加载深度学习模型...   ← INTENTIONAL contrast (keep)
412  - **无需缓存 converter**：marker-pdf 之类工具初始化要加载模型...pymupdf 的 open() 是轻量操作   ← INTENTIONAL technical contrast (keep)
462  - **零文件系统依赖**：上传的 PDF 经 marker-pdf 转换后即丢弃...          ← STALE (should be pymupdf) — NOT in brief ⚠️
718  ### Q：marker-pdf 首次运行时下载很慢或失败                              ← STALE FAQ — NOT in brief ⚠️
720  **A**：marker-pdf 首次使用需下载模型权重（约数百 MB）...                 ← STALE FAQ — NOT in brief ⚠️
724  **A**：复杂的合并单元格表格转 Markdown 时可能出现格式偏差，这是 marker-pdf 的已知限制...   ← STALE FAQ — NOT in brief ⚠️
754  - marker-pdf GitHub：https://github.com/VikParuchuri/marker             ← resources link — task anticipated this ("report it if found")
```

The brief's self-review expected only the §56 contrast (+ optionally the §754 GitHub link). Lines 412, 462, 718, 720, 724 are extras the brief did not include.

## Concerns (out-of-brief stale references — recommend a small follow-up)

These were NOT in the Task 3 brief, so they were left untouched per "Make NO other edits." They contradict the pymupdf narrative Tasks 1/2 established. None are blockers for the three structural fixes, but they make the doc internally inconsistent:

1. **Line 237** — `mkdir -p src/agentic_search/core src/agentic_search/services` — still creates `core/` (should be `configs/`). This is a core→configs item the brief's Steps 4–11 omitted. **Highest priority** — the §1.5 description (line 241) now says `configs/` but the command creates `core/`. Fix: `src/agentic_search/configs`.
2. **Line 462** — "上传的 PDF 经 marker-pdf 转换后即丢弃" — should read `pymupdf`.
3. **Lines 718, 720, 724 (FAQ)** — Q&A about marker-pdf model download slowness and table-format issues. Under pymupdf these are obsolete/incorrect (pymupdf has no model download; plain-text extraction has no table-format concern). Suggest rewriting or removing these FAQ entries.
4. **Line 754** — `marker-pdf GitHub` resources link (task-anticipated; consider whether to keep as a "see also" or drop).
5. **Line 664** — "Markdown 中包含 `#` 标题结构" — stale under pymupdf plain text. The brief's Step 16 deliberately touched only the db name on this line, so it was left as-is.

## Files Changed

- `任务文档/01-Python文档工具.md` (committed — see Step 20)

## Recommendation

The brief's contract is fully satisfied. The concerns above are a genuine gap in the *plan* (not the execution): file 01 still contains 5 stale marker-pdf/core references after "the last task." Suggest the main agent spin a quick follow-up (or expand scope) to fix lines 237, 462, 664, 718–724, and decide on 754 — otherwise the doc remains self-contradictory.

---

## Follow-up: 5 residual marker-pdf/core references fixed (commit 7be5133)

The "out-of-brief concerns" flagged above (lines 237, 462, 664, 718–724, 754) were resolved in a dedicated follow-up. All 5 stale marker-pdf/core references in `任务文档/01-Python文档工具.md` are now removed. No other edits were made; the legitimate contrast mentions at lines 56 and 412 (marker-pdf as the *rejected* heavier alternative) were intentionally left intact.

1. **Line 237** — `mkdir -p src/agentic_search/core` → `src/agentic_search/configs`. The §1.5 command now creates the `configs/` directory it describes (was creating the obsolete `core/`).
2. **Line 462** — store_document prose `经 marker-pdf 转换后` → `经 pymupdf 提取后`.
3. **Line 664** — §步骤5 集成验证: `Markdown 中包含 \`#\` 标题结构` → `文本中包含 PDF 原文内容` (pymupdf is plain-text, no `#` heading structure).
4. **Lines 718–724** — DELETED both obsolete FAQ Q&A entries (marker-pdf model-download slowness; parse_pdf table-format chaos). pymupdf has no model download and does not reconstruct tables, so both were incorrect. FAQ entries before (ModuleNotFoundError) and after (pytest 找不到测试文件) preserved.
5. **Line 754** — 延伸阅读 resources link `marker-pdf GitHub: https://github.com/VikParuchuri/marker` → `pymupdf 官方文档：https://pymupdf.readthedocs.io/`.

- Commit: `7be5133` — `docs(01): fix 5 residual marker-pdf/core references missed by brief` (+4 −12)
- Net diff: 3 single-line replacements + 1 deletion (8 FAQ lines) + 1 link replacement.
- Verification: `grep "marker-pdf|agentic_search/core"` now returns only the two intentional contrast mentions (lines 56, 412); no `agentic_search/core` directory references remain anywhere in file 01.
