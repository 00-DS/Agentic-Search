## Task 9: `04-TMT记忆系统.md` — 数据库名 + core→configs

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`

- [ ] **Step 1: 数据库名 — 引言（第 55 行）**

原文：`存储采用 MongoDB（`agentic_search_db` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作，便于教学调试与用 MongoDB Compass 人工查看。`
改为：`存储采用 MongoDB（`agentic_search` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作，便于教学调试与用 MongoDB Compass 人工查看。`

- [ ] **Step 2: 数据库名 — §2.4 说明（第 196 行）**

原文：`记忆存储采用 MongoDB（`agentic_search_db` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作。...`
改为：`记忆存储采用 MongoDB（`agentic_search` 数据库的 `memories` 集合），用 **PyMongo 同步驱动** 操作。...`

- [ ] **Step 3: core→configs — 逐段讲解（第 155 行）**

原文：`- `call_llm(prompt)`：封装的 LLM 调用函数（模型名、超时等从 `core/config.py` 读取）。`
改为：`- `call_llm(prompt)`：封装的 LLM 调用函数（模型名、超时等从 `configs/config.py` 读取）。`

- [ ] **Step 4: core→configs + 数据库名 — 连接代码示例（第 207、210 行）**

第 207 行原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

第 210 行原文：`db = client[settings.mongo_db]                  # 选中 agentic_search_db`
改为：`db = client[settings.mongo_db]                  # 选中 agentic_search`

- [ ] **Step 5: 数据库名 — 验证（第 276 行）**

原文：`**验证：** 打开 MongoDB Compass 连接 `localhost:27017` → 选择 `agentic_search_db` → `memories` 集合...`
改为：`**验证：** 打开 MongoDB Compass 连接 `localhost:27017` → 选择 `agentic_search` → `memories` 集合...`

- [ ] **Step 6: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/04-TMT记忆系统.md
git commit -m "docs(04): db name agentic_search, core->configs"
```

---
