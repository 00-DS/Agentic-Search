## Task 10: 全局一致性校验

**Files:**
- 校验：`任务文档/` 全目录

- [ ] **Step 1: grep 确认无 marker-pdf 残留**

Run: `grep -rn "marker" 任务文档/`
Expected: **无任何输出**。命中则回对应 task 修复。

- [ ] **Step 2: grep 确认无 PdfConverter/_converter 残留**

Run: `grep -rn "PdfConverter\|create_model_dict\|_converter" 任务文档/`
Expected: **无输出**。

- [ ] **Step 3: grep 确认无 "import fitz"**

Run: `grep -rn "import fitz" 任务文档/`
Expected: **无输出**。

- [ ] **Step 4: grep 确认数据库名全部为 agentic_search**

Run: `grep -rn "agentic_search_db" 任务文档/`
Expected: **无输出**（全部应为 `agentic_search`）。

- [ ] **Step 5: grep 确认 core→configs 干净，且 URL 保留**

Run: `grep -rn "core/config\|from agentic_search\.core\|src/agentic_search/core\|├── core/\|├ core/\|│   ├── core/" 任务文档/`
Expected: **无输出**。
再确认 MongoDB 文档 URL **未被误改**：
Run: `grep -rn "core/databases-and-collections" 任务文档/`
Expected: 仍有命中（这些是 URL，**必须保留**）。

- [ ] **Step 6: 校验"刻意简化"叙事存在**

确认 `01-Python文档工具.md` pymupdf 技术概念段 + `概念速查.md` pymupdf 条目都含"刻意选择最简"取舍说明。

- [ ] **Step 7: 校验 uv init 命令**

Run: `grep -rn "uv init --lib agentic-search" 任务文档/`
Expected: 至少 1 处命中（01 §1.1）。确认 `uv init --lib .`（带点）已不存在。

- [ ] **Step 8: 修补 commit（若有残留）**

若 Step 1-5 发现残留并已修复：

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/
git commit -m "docs: fix residual references found in consistency check"
```

全部干净则跳过。