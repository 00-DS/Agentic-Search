# Task 5 Report — `任务文档/概念速查.md`

## Brief steps applied (8/8)

All 8 edit steps applied verbatim, no mismatches.

| Step | Brief target line | Applied at (post-edit) | Status |
|------|-------------------|------------------------|--------|
| 1 — pymupdf wording (LangGraph entry) | 13 | 13 | ✅ exact |
| 2 — rewrite whole `## marker-pdf` entry → `## pymupdf` | 154–164 | 154–166 | ✅ full replacement |
| 3 — db name + core→configs (MongoDB entry) | 174 | 176 | ✅ exact |
| 4 — db name (Compass entry) | 188 | 190 | ✅ exact |
| 5 — db name (PyMongo example) | 235 | 237 | ✅ exact |
| 6 — core→configs (包化布局 entry) | 365 | 367 | ✅ exact |
| 7 — db name + core→configs + pymupdf (数据存储 entry) | 379 | 381 | ✅ exact (3 sub-changes) |
| 8 — db name (数据存储 tree diagram) | 383 | 385 | ✅ exact |

(Line numbers shifted by +2 in the lower half of the file because the new pymupdf entry is 13 lines vs the old marker-pdf entry's 11 lines.)

## Post-fix grep sweeps

```
$ grep -n "marker" 任务文档/概念速查.md
160:> **关于"结构化"的取舍**：理论上，能保留标题层级（`#`）、表格、公式的结构化 Markdown（如 marker-pdf、MinerU）比纯文本更利于 LLM 理解。...

$ grep -n "agentic_search_db" 任务文档/概念速查.md
(no matches)

$ grep -nE "core/config|from agentic_search\.core|agentic_search/core|├── core" 任务文档/概念速查.md
(no matches)
```

- `marker` — exactly **1 hit**, the intentional contrast "如 marker-pdf、MinerU" inside the new pymupdf entry's `取舍` blockquote. Per the task brief, this is explicitly allowed. No stale tool references remain.
- `agentic_search_db` — **0 hits**. ✅
- core/config patterns — **0 hits**. ✅

## MongoDB doc URL integrity (the core→configs exception)

Both MongoDB URLs containing `core/databases-and-collections` are **intact** (not touched by core→configs):

```
$ grep -n "databases-and-collections" 任务文档/概念速查.md
180:**延伸阅读**：[MongoDB 官方文档（数据库与集合）](https://www.mongodb.com/zh-cn/docs/manual/core/databases-and-collections/)
393:**延伸阅读**：详见 [模块 1](./01-Python文档工具.md) 与 [模块 4](./04-TMT记忆系统.md)，以及 [MongoDB 官方文档](https://www.mongodb.com/zh-cn/docs/manual/core/databases-and-collections/)
```

Both still point to `…/manual/core/databases-and-collections/`. ✅

## Brief-missed references

None. Every `marker` / `agentic_search_db` / `core` occurrence in the file was covered by a brief step. The sweep found no additional same-category references to fix.

## Files changed

- `任务文档/概念速查.md` (committed for the first time to git — was previously untracked, hence the pure-insertion stat).

## Commit

`3a75c8a` — `docs(概念速查): pymupdf entry, core->configs, db name agentic_search`
