# Task 2 Report — 02-LangGraph-Agent.md 四工具新签名

## Status: DONE

## Commit
- `fe9b901` — `docs(02): 四工具新签名——list_papers/read_paper/search_papers/extract_abstract` (+68 −58, 1 file)

## What Changed (per brief step)

| Step | Location (orig → final line) | Change |
|------|------------------------------|--------|
| 1 | 学习目标第 3 条 (line 9) | `list_papers/list_sections/read_section/search_sections` → `list_papers/read_paper/search_papers/extract_abstract` |
| 2 | ReAct 概念段 (line 20) | same tool-name swap in the "自主探索论文语料库" sentence |
| 3 | tool_calls JSON 示例 (line 31) | `"name": "search_sections"` → `"name": "search_papers"` |
| 4 | mermaid 流程图 (lines 84, 87) | `执行工具（read_section 等）` → `（read_paper 等）`; `list_documents / read_section` → `list_documents / read_document` |
| 5 | 前置要求 (line 100) | `parse_pdf（返回 sections 数组）…read_section 已实现` → `parse_pdf（返回完整纯文本）…read_document 已实现` (dropped read_section) |
| 6 | ReAct 设计说明段 (lines 108-113, 6 lines → 7) | full rewrite per brief: `两个逼出…约束` → `三个逼出…约束`; added `extract_abstract`/`read_paper`/`search_papers` omp analogies + 3rd constraint about extract_abstract being a read-time tool |
| 7 | 目录结构注释 (line 143) | `parse_pdf 切章节 / list / read / read_section` → `parse_pdf 转纯文本 / list / read_document` |
| 8 | 第 6 步 tools.py 整段 (lines 369-461 after +1 shift) | **largest change**: full tools.py rewrite. `list_papers/read_paper/search_papers/extract_abstract` operating on line numbers of full text (`_get_doc_text` helper, 1-indexed line slicing, regex line-scan returning `line_number`+`line`, abstract paragraph extraction). New omp-correspondence table + 2 design-rationale paragraphs (search_papers regex, extract_abstract read-time) + verification command |
| 9 | build_graph (lines 484, 490) | import + `tools = [...]` list swapped to new four names |
| — (beyond brief, required by Step 10) | narrative remnants (lines 789, 799, 824, 830) | swapped `search_sections`→`search_papers`, `read_section`→`read_paper`, `list_sections`→`extract_abstract` in curl example, verification text, test comment, test-observation paragraph |

## Verification — grep results (post-edit, file 920 lines)

- `list_sections|read_section|search_sections|section_id` → **No matches** ✓
- bare `sections` → **No matches** ✓
- New tool names present: `list_papers`/`read_paper`/`search_papers`/`extract_abstract` all match (definitions + table + import + tools list + narrative).

## Decorator network check (must stay intact)

- **`@retry` (Step 5)**: heading line 312; definition `def retry(...)` + `@retry(max_attempts=3)` demo at 358; applied in build_graph at lines 498-500 (`@retry(max_attempts=3)` wrapping `llm_call`); cross-ref rationale at 528. ✓
- **`@tool` (Step 6)**: four `@tool` decorators on `list_papers`(392), `read_paper`(400), `search_papers`(411), `extract_abstract`(429); cross-refs at 163, 365, 371, 523. ✓
- **`@router.post` (Step 9)**: at 625 (`/query`), 656 (`/ingest`), 699 (`/consolidate`) + `@router.get` at documents; cross-refs at 48, 365, 618. ✓
- **`@dataclass`** (module-4 forward refs): lines 10, 365. ✓

The `@retry → @tool → @router` teaching arc is fully intact and the cross-references (lines 48, 365, 523, 528, 618) all still resolve.

## Constraints honored
- Only `任务文档/02-LangGraph-Agent.md` edited; no `backend/` code touched. ✓
- No comparative phrasing ("旧版/原来/之前/不再/改用") introduced in the rewritten sections (pre-existing historical-comparison lines outside the task scope were left untouched per "仅文档范围 + 只做指定改动"). ✓
- `MessagesState` standard base class unchanged (Step 4 region not in scope). ✓
- Four tool signatures match project-wide contract. ✓
- No embedding/向量库 introduced. ✓

## Files changed
- `任务文档/02-LangGraph-Agent.md` (+68 −58)

## Concerns
1. **Brief-internal docstring/code mismatch (carried over verbatim from brief, NOT introduced by me)**: `search_papers`'s docstring says it returns `[{doc_id, line_number, line, snippet}]` but the appended dict only has `{doc_id, line_number, line}` (no `snippet` field). This inconsistency exists in the brief itself (brief line 101 vs brief lines 105-114). I transcribed the brief exactly as specified rather than "fixing" it, since the brief is the authoritative spec. Flagging for awareness — a downstream reviewer may want the docstring trimmed to `[{doc_id, line_number, line}]`.
2. **Unused import (per brief)**: the new tools.py imports `read_document` from module 1 but never calls it (the `_get_doc_text` helper queries `_documents_collection` directly). This matches the brief verbatim (brief lines 67-69) — likely a deliberate teaching choice to surface the module-1 API surface. Kept as-is per spec; would be a lint warning (`F401`) in real code.
3. Minor: line-endings warning (LF→CRLF) on commit is benign on Windows.
