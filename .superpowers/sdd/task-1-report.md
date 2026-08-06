# Task 1 Report: 01-Python文档工具.md — 零预处理改写

## Status: DONE

## File Changed
- `任务文档/01-Python文档工具.md` (only file touched; +91 / −196; 851 → 745 lines)

## Commit
- `c1dfb54` — `docs(01): 零预处理——删 section 切分，parse_pdf 改 get_text(text)，schema 扁平化`

## Changes Applied (16 content steps + 2 consistency fixes)

| Step | Location | Change |
|------|----------|--------|
| 1 | line 14 (学习目标) | `parse_pdf（结构化提取，切分章节）… read_section …` → `parse_pdf（PDF 转纯文本）、store_document、list_documents、read_document … 完整文本` |
| 2 | line 17 (产出段落) | `read_section/search_sections … 章节文本片段` → `read_paper/search_papers … 按行号按需读取完整文本片段` |
| 3 | lines 50–58 (pymupdf 概念) | 整段重写：删 `get_text("dict")`/blocks/lines/spans/标题启发式/兜底 section；改为 `get_text("text")` 纯文本 + 零预处理理由（对齐 omp grep+read） |
| 4 | line 62 (MongoDB 概念) | `每篇按章节切分为 sections 数组` → `每篇存为完整纯文本` |
| 5 | lines 106–107 (mermaid) | `结构化提取（dict + 标题启发式）` → `PDF 转纯文本`；`sections 章节数组` → `完整文本` |
| 6 | line 142 (Compass 引用) | `章节数组（sections）` → `完整文本` |
| 7 | lines 191–193 (pyproject 注释) | pymupdf/pymongo 注释去 sections/标题启发式 |
| 8 | lines 334–340 (函数表) | 重写为 4 函数：`parse_pdf`→str / `store_document(doc_id,filename,text)` / `list_documents` / `read_document`→dict |
| 9 | line 345 (import) | 删 `read_section` |
| 10 | lines 350–480 (3.1 parse_pdf) | 整段重写为纯文本提取；删 `_extract_sections`、字号中位数启发式、兜底 section、图片 block 处理；新签名 `-> str`，`page.get_text("text")` 拼接 |
| 11 | lines 482–523 (3.2 store_document) | 重写：schema `{doc_id, filename, text, uploaded_at}` 扁平；`text` 完整纯文本 |
| 12 | lines 525–582 (3.3 list/read) | 重写：删 `read_section`；`read_document(doc_id)->dict` 返回完整记录；验证块补 `bash` fence |
| 13 | lines 586–712 (测试) | `test_parse_pdf_returns_sections`→`test_parse_pdf_returns_text`(断言 str)；删 `test_read_section`；`test_store_and_read_document` 改存 text、断言 `doc["text"]`；4.2 标题/import/说明去 read_section；讲解要点 `sections`→`text`；预期输出 7→6 passed |
| 14 | lines 716–754 (集成验证) | 重写：`text=parse_pdf`→`store_document(...,text)`→`read_document(doc_id)['text']`；验证说明 `sections 字段`→`text 字段` |
| 15 | lines 758–798 (检查清单) | 函数表去 `read_section`；预期输出改名+6 passed；额外验证命令改 `text`/`['text']` |
| 16 | line 848 (下一步) | `list_papers/list_sections/read_section/search_sections … read_section … 章节片段` → `list_papers/read_paper/search_papers/extract_abstract … read_document … 按行号读取完整文本` |
| extra | line 348 | 删除被禁措辞「旧版…不再依赖」，改写为「包化布局让 import 路径只依赖包名，与文件在磁盘上的相对位置无关」 |
| extra | line 62 | 删 `level` 字段引用 → `filename` |
| extra | line 279 | `提取的章节` → `提取的完整文本` |

## Verification

Forbidden-term grep on `任务文档/01-Python文档工具.md` (pattern: `section|get_text\(.?dict|标题启发式|_extract_sections|read_section|章节|\blevel\b|兜底|statistics|span|block\[`) → **No matches found**.

Banned comparison-word grep (pattern: `旧版|原来|之前|不再|改用`):
- `旧版` / `原来` / `不再` / `改用` → none.
- `之前` → only inside `[开始之前](./00-开始指南.md)` (cross-link to module 00's title "开始之前"), not a comparison phrase. Acceptable.

New-signature presence confirmed:
- `def parse_pdf(pdf_path: str | Path) -> str:` ✓
- `def store_document(doc_id: str, filename: str, text: str) -> None:` ✓
- `def list_documents() -> list[dict]:` ✓
- `def read_document(doc_id: str) -> dict:` ✓
- `get_text("text")` and `doc["text"]` usage ✓

Structural integrity: 66 code-fence markers = 33 balanced blocks; net line delta −106 (851→745) consistent with removing `_extract_sections`/heading-heuristic code.

## Concerns
- **Surgical edits applied in original-line-number order, bottom-up**, re-grounding the edit-tool snapshot tag after each edit. No overlap or drift.
- Steps that fell outside the brief's explicit line ranges (line 62 `level`, line 279 `章节`, line 348 `旧版`) were fixed as required consistency changes — they referenced the deleted section schema or used banned wording and would have left the doc internally inconsistent. These are in-scope under the Global Constraints.
- Backend `services/documents.py` was **not** touched (doc-only scope honored).
