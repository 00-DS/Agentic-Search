## Task 6: `项目概览.md` — pymupdf + core→configs + 数据库名

**Files:**
- Modify: `任务文档/项目概览.md`

- [ ] **Step 1: pymupdf — M1 描述（第 116 行）**

原文：`2. **services/documents.py** — `parse_pdf()` 用 marker-pdf 转 Markdown 后存入 MongoDB...`
改为：`2. **services/documents.py** — `parse_pdf()` 用 pymupdf 提取纯文本后存入 MongoDB...`

- [ ] **Step 2: pymupdf — 数据流图（第 196 行）**

原文：`marker-pdf → Markdown（内存中处理，不落盘）`
改为：`pymupdf → 纯文本（内存中处理，不落盘）`

- [ ] **Step 3: pymupdf — 技术栈表（第 247 行）**

原文：`| marker-pdf | PDF → 结构化 Markdown | services/documents.py |`
改为：`| pymupdf | PDF → 纯文本提取 | services/documents.py |`

- [ ] **Step 4: pymupdf — 延伸阅读（第 283 行）**

原文：`- **marker-pdf**（PDF 转结构化 Markdown）：https://github.com/VikParuchuri/marker`
改为：`- **pymupdf**（PDF 纯文本提取）：https://pymupdf.readthedocs.io/`

- [ ] **Step 5: core→configs — 精简目录树（第 27 行）**

原文：`    │   core/config.py      # 配置（.env）`
改为：`    │   configs/config.py     # 配置（.env）`

- [ ] **Step 6: core→configs — 详细目录树（第 68-69 行）**

原文：
```
│   │   ├── core/
│   │   │   └── config.py           # 配置（从 .env 读：超时、MongoDB URI/库名、LLM 模型名）
```
改为：
```
│   │   ├── configs/
│   │   │   └── config.py           # 配置（从 .env 读：超时、MongoDB URI/库名、LLM 模型名）
```

- [ ] **Step 7: core→configs — 模块清单（第 97 行）**

原文：`- `core/config.py` — 配置层，从 `.env` 读 LLM 模型名、超时、MongoDB URI 与库名。`
改为：`- `configs/config.py` — 配置层，从 `.env` 读 LLM 模型名、超时、MongoDB URI 与库名。`

- [ ] **Step 8: 数据库名 — 目录树注释（第 80-81 行）**

原文：
```
│   │   #   · agentic_search_db.memories  → L1/L2 记忆
│   │   #   · agentic_search_db.documents → 完整 Markdown 全文
```
改为：
```
│   │   #   · agentic_search.memories  → L1/L2 记忆
│   │   #   · agentic_search.documents → 完整 Markdown 全文
```

- [ ] **Step 9: 数据库名 — 技术栈表（第 251 行）**

原文：`| MongoDB | 记忆数据 + 完整 Markdown 文档存储 | agentic_search_db（localhost:27017） |`
改为：`| MongoDB | 记忆数据 + 完整 Markdown 文档存储 | agentic_search（localhost:27017） |`

- [ ] **Step 10: 数据库名 — 验证标准 M3（第 265 行）**

原文：`...MongoDB Compass 中 `agentic_search_db.memories` 集合出现 L2 记录...`
改为：`...MongoDB Compass 中 `agentic_search.memories` 集合出现 L2 记录...`

- [ ] **Step 11: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/项目概览.md
git commit -m "docs(项目概览): pymupdf, core->configs, db name agentic_search"
```

---
