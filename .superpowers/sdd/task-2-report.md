# Task 2 Report — `01-Python文档工具.md` parse_pdf spec & tests (pymupdf)

**File modified:** `任务文档/01-Python文档工具.md`
**Commit:** `15d17f4` — `docs(01): rewrite parse_pdf spec and tests for pymupdf`
**Diff size:** +35 / -50

## Edits applied

### Step 1 — Rewrite §3.1 `parse_pdf(pdf_path)` ✅
- Replaced the entire §3.1 section (old lines 341–426, up to but not including `### 3.2`)
  with the pymupdf version from the brief.
- Old `PdfConverter` / `create_model_dict` / module-level `_converter` cache code is gone;
  replaced with `import pymupdf` → `pymupdf.open()` → `page.get_text()` → `"\n".join(parts)`.
- The "转换效果" block now shows plain-text output (no `#` heading markers).
- `doc.close()` present in the teaching example.
- Matched by section boundaries (start heading + `### 3.2` anchor), not raw line numbers
  — matched cleanly on the first read.

### Step 2 — store_document code comment ✅
- Changed (line 444):
  - `# marker-pdf 转出的完整 Markdown 全文` → `# pymupdf 提取的完整纯文本全文`
- Exact `原文` text from the brief matched verbatim.

### Step 3 — Rewrite §4.1 test `parse_pdf` ✅
- Replaced entire §4.1 section (old lines 541–569, up to but not including `#### 4.2`).
- Removed `test_parse_pdf_contains_markdown_structure` and its `assert "#" in result`.
- Kept `test_parse_pdf_returns_string` and `test_parse_pdf_file_not_found`.
- Added closing note: "提取结果是纯文本，不再断言含 `#` 之类结构标记——pymupdf 输出不含这些。"
- Intro line changed from "纯转换函数...输出 Markdown 字符串" to "纯提取函数...输出纯文本字符串".
- Inner triple-backtick code fences written as literal doc content (four-backtick fence
  in the brief was only the replacement delimiter).

### Step 4 — §步骤5 integration example ✅
- Line 632: `# 1. 将一个 PDF 转换为 Markdown` → `# 1. 将一个 PDF 提取为纯文本`
- Line 634: `print(f'转换完成，Markdown 长度: {len(markdown)} 字符')` → `print(f'提取完成，文本长度: {len(markdown)} 字符')`
- Middle line (`markdown = parse_pdf('你的文件.pdf')`) preserved.

## Verification — marker-pdf references in §3.1 / §4.1 area

`grep -n "marker-pdf"` in lines 320–570 (§3.1 → §4.1):

```
405:- **无需缓存 converter**：marker-pdf 之类工具初始化要加载模型、开销大，需用模块级缓存；pymupdf 的 `open()` 是轻量操作，每次调用即可，无需缓存层。
455:- **零文件系统依赖**：上传的 PDF 经 marker-pdf 转换后即丢弃，不在磁盘上留存任何 `.md` 文件。所有数据集中在 MongoDB 一处，便于备份、迁移与可视化查看。
```

Interpretation:
- **Line 405** is INSIDE §3.1 but is the **intended** contrast sentence written verbatim
  by the brief's Step 1 replacement (it explains why pymupdf needs no converter cache by
  comparing to marker-pdf). Not a leftover — it is the new content.
- **Line 455** is in **§3.2 store_document** prose (讲解要点), NOT in §3.1/§4.1 and NOT
  one of my 4 assigned edits. Per the task brief, out-of-scope marker-pdf refs belong to
  Task 3. Left untouched.
- **§4.1 (lines 541–565)** contains **zero** marker-pdf references. ✅
- No `PdfConverter`, `contains_markdown_structure`, `assert "#" in result`,
  `Markdown 长度`, or `转换为 Markdown` strings remain anywhere in the file.

## Scope check
- Only the 4 brief edits applied. No edits to `core/`→`configs/`, `uv init`, DB name, FAQ,
  or checklist — those are Task 3.
- No `backend/` code touched.
- Only `任务文档/01-Python文档工具.md` changed.

## Files changed
- `任务文档/01-Python文档工具.md` (+35 / −50)

## Follow-up fix — stale sample pytest output (Task 2 review)

**Commit:** `be169b1` — `docs(01): fix stale sample pytest output (6 tests, drop removed test)`
**Diff size:** +1 / -2

### Issue
Step 3 removed `test_parse_pdf_contains_markdown_structure` from §4.1 (pymupdf output has
no `#` structure to assert), but the `§完成检查` sample pytest output block still listed
the deleted test and showed `7 passed` — now stale: only 6 tests remain.

### Edits applied (2 lines)
- Deleted the line `tests/test_documents.py::test_parse_pdf_contains_markdown_structure PASSED`
  from the sample output block.
- Changed `======================== 7 passed in 1.2s ========================`
  → `======================== 6 passed in 1.2s ========================`.

### Scope check
- Touched only the sample pytest output block (~lines 686–695). No checklist items,
  no other sections, no `backend/` code.
