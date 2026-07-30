## Task 7: `00-开始指南.md` — pymupdf + 数据库名

**Files:**
- Modify: `任务文档/00-开始指南.md`

- [ ] **Step 1: pymupdf — uv 依赖说明（第 58 行）**

原文：`...后端的全部依赖（FastAPI、LangGraph、marker-pdf、pytest 等）都由它安装。`
改为：`...后端的全部依赖（FastAPI、LangGraph、pymupdf、pytest 等）都由它安装。`

- [ ] **Step 2: pymupdf — 延伸阅读（第 121 行）**

原文：`- marker-pdf（PDF 转 Markdown）：https://github.com/VikParuchuri/marker`
改为：`- pymupdf（PDF 纯文本提取）：https://pymupdf.readthedocs.io/`

- [ ] **Step 3: 数据库名 — MongoDB 说明（第 74 行）**

原文：`> 后端通过 PyMongo（MongoDB 的 Python 驱动）连接 `mongodb://localhost:27017`，数据库名为 `agentic_search_db`。这些配置在模块 1 中讲解。`
改为：`> 后端通过 PyMongo（MongoDB 的 Python 驱动）连接 `mongodb://localhost:27017`，数据库名为 `agentic_search`。这些配置在模块 1 中讲解。`

- [ ] **Step 4: 数据库名 — Compass 说明（第 81 行）**

原文：`- 打开后默认连接 `mongodb://localhost:27017`，即可看到本项目的 `agentic_search_db` 数据库`
改为：`- 打开后默认连接 `mongodb://localhost:27017`，即可看到本项目的 `agentic_search` 数据库`

- [ ] **Step 5: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/00-开始指南.md
git commit -m "docs(00): pymupdf deps, db name agentic_search"
```

---
