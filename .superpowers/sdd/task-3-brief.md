## Task 3: `01-Python文档工具.md` — uv init 命令 + core→configs + 数据库名

> 三处结构修正在本文件的集中改动。注意 core→configs 要避开 MongoDB URL（本文件 §延伸阅读第 763 行有 `core/databases-and-collections` URL，不改）。

**Files:**
- Modify: `任务文档/01-Python文档工具.md`（多处）

- [ ] **Step 1: 重写 §1.1 初始化命令（第 148-156 行）**

原文：
```
打开命令行，进入项目根目录，创建并进入 `backend/`：

​```bash
mkdir backend
cd backend
uv init --lib .
​```

`uv init --lib` 创建一个**库项目**：生成 `pyproject.toml`（含构建后端声明）和 `src/` 目录结构。这与 `uv init`（默认的应用项目）的区别在于，库项目会带上 `[build-system]` 字段，使其可被 `pip install`。
```
改为：
```
打开命令行，进入项目根目录，用 `uv init --lib <包名>` 初始化库项目（直接把包名传给 `uv init`，从源头让生成物命名正确）：

​```bash
uv init --lib agentic-search
​```

`uv init --lib agentic-search` 会创建一个名为 `agentic-search/` 的目录，其内部已经生成 `pyproject.toml`（含 `[build-system]` 字段）和 `src/agentic_search/`（连字符自动转下划线，命名已正确）。

随后**手动把目录调整到本项目的 `backend/` 位置**——把生成的 `agentic-search/` 改名为 `backend/`（或将其内容移入已有的 `backend/`）：

​```bash
mv agentic-search backend
cd backend
​```

`uv init --lib` 创建的是**库项目**：生成 `pyproject.toml`（含构建后端声明）和 `src/` 目录结构。这与 `uv init`（默认的应用项目）的区别在于，库项目会带上 `[build-system]` 字段，使其可被 `pip install`。
```

- [ ] **Step 2: 改 §1.3 讲解段（第 172 行）**

原文：`​`uv init --lib`​ 生成的 `pyproject.toml` 已有基本骨架。需要将其中的包名改为 `agentic-search`，并补充依赖。`
改为：`由于初始化时已传入包名 `agentic-search`，生成的 `pyproject.toml` 已有正确的 `name` 字段，无需再改包名，只补充依赖即可。`

- [ ] **Step 3: 改"默认包名"提示（第 202 行）**

原文：`> `uv init --lib` 默认生成的包名可能是 `backend`。请务必改为 `agentic-search`，并确保 `src/` 下的目录名是 `agentic_search`（下划线）。若目录名不符，需用 `mv` 重命名。`
改为：`> 因为初始化命令已指定包名 `agentic-search`，`src/` 下的目录名自动为 `agentic_search`（下划线），无需手动改名。`

- [ ] **Step 4: core→configs — 扁平结构对比图（第 36 行）**

原文：`                             ├── core/config.py`
改为：`                             ├── configs/config.py`

- [ ] **Step 5: core→configs — 学习目标第 3 条（第 13 行）**

原文：`3. 使用 **pydantic-settings** 编写配置层 `core/config.py`，从 `.env` 读取...`
改为：`3. 使用 **pydantic-settings** 编写配置层 `configs/config.py`，从 `.env` 读取...`

- [ ] **Step 6: core→configs — 产出说明（第 17 行）**

原文：`...包化骨架（`pyproject.toml` + `src/agentic_search/`）、配置层（`core/config.py`）与文档服务...`
改为：`...包化骨架（`pyproject.toml` + `src/agentic_search/`）、配置层（`configs/config.py`）与文档服务...`

- [ ] **Step 7: core→configs — §1.5 目录说明（第 233 行）**

原文：`每个 Python 子包（`core/`、`services/`）都需要一个 `__init__.py` 文件（可为空）来标记其为包。`
改为：`每个 Python 子包（`configs/`、`services/`）都需要一个 `__init__.py` 文件（可为空）来标记其为包。`

- [ ] **Step 8: core→configs — §步骤2 标题（第 245 行）**

原文：`## 步骤 2：`core/config.py` — 配置层`
改为：`## 步骤 2：`configs/config.py` — 配置层`

- [ ] **Step 9: core→configs — §2.2 小标题（第 275 行）**

原文：`### 2.2 编写 `core/config.py``
改为：`### 2.2 编写 `configs/config.py``

- [ ] **Step 10: core→configs — import 路径（第 309 行）**

原文：`整个项目通过 `from agentic_search.core.config import settings` 引用同一个配置对象`
改为：`整个项目通过 `from agentic_search.configs.config import settings` 引用同一个配置对象`

- [ ] **Step 11: core→configs — store_document 示例 import（第 439 行）**

原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

- [ ] **Step 12: 数据库名 — 技术概念段（第 58 行）**

原文：`本项目用 `agentic_search_db` 数据库下的 `documents` 集合存放论文 Markdown 全文`
改为：`本项目用 `agentic_search` 数据库下的 `documents` 集合存放论文 Markdown 全文`

- [ ] **Step 13: 数据库名 — §3.2 术语说明（第 431 行）**

原文：`在 MongoDB 术语中，一个 database（本项目为 `agentic_search_db`）下有若干 collection...`
改为：`在 MongoDB 术语中，一个 database（本项目为 `agentic_search`）下有若干 collection...`

- [ ] **Step 14: 数据库名 — §3.2 验证（第 467 行）**

原文：`...打开 **MongoDB Compass** 查看 `agentic_search_db` 的 `documents` 集合——应能看到一条新记录，其 `markdown` 字段含完整的 `#` 标题结构。`
改为：`...打开 **MongoDB Compass** 查看 `agentic_search` 的 `documents` 集合——应能看到一条新记录，其 `markdown` 字段含完整纯文本全文。`

- [ ] **Step 15: 数据库名 — 验证预期输出（第 317 行）**

原文：`预期输出：`mongodb://localhost:27017 agentic_search_db gpt-4o-mini``
改为：`预期输出：`mongodb://localhost:27017 agentic_search gpt-4o-mini``

- [ ] **Step 16: 数据库名 — 集成验证（第 671 行）**

原文：`...连接 `mongodb://localhost:27017`，在 `agentic_search_db` 数据库的 `documents` 集合中应能看到刚才存入的记录，其 `markdown` 字段含完整全文。`
改为：`...连接 `mongodb://localhost:27017`，在 `agentic_search` 数据库的 `documents` 集合中应能看到刚才存入的记录，其 `markdown` 字段含完整全文。`

- [ ] **Step 17: 数据库名 — 完成检查（第 682 行）**

原文：`- [ ] MongoDB 服务已启动（`localhost:27017`），MongoDB Compass 可连接查看 `agentic_search_db``
改为：`- [ ] MongoDB 服务已启动（`localhost:27017`），MongoDB Compass 可连接查看 `agentic_search``

- [ ] **Step 18: 数据库名 + core→configs — 完成检查（第 679、680、688 行）**

第 679 行原文：`- [ ] `backend/pyproject.toml` 存在，包名为 `agentic-search`，包含 `marker-pdf`、`pydantic-settings`、`pymongo`、`pytest`（dev）`
改为：`- [ ] `backend/pyproject.toml` 存在，包名为 `agentic-search`，包含 `pymupdf`、`pydantic-settings`、`pymongo`、`pytest`（dev）`

第 680 行原文：`- [ ] `backend/src/agentic_search/core/config.py` 存在，`settings` 含 `mongo_uri`、`mongo_db`...`
改为：`- [ ] `backend/src/agentic_search/configs/config.py` 存在，`settings` 含 `mongo_uri`、`mongo_db`...`

第 688 行原文：`uv run python -c "from agentic_search.services.documents import parse_pdf; from agentic_search.core.config import settings; print(settings.mongo_uri); print('包化 import 成功')"`
改为：`uv run python -c "from agentic_search.services.documents import parse_pdf; from agentic_search.configs.config import settings; print(settings.mongo_uri); print('包化 import 成功')"`

- [ ] **Step 19: core→configs — 模块总结（第 773 行）**

原文：`...同时 Agent 会用到 `core/config.py` 中的 LLM 配置...`
改为：`...同时 Agent 会用到 `configs/config.py` 中的 LLM 配置...`

- [ ] **Step 20: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): uv init with name, rename core->configs, db name agentic_search"
```

---
