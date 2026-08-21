# 设计：ruff 全绿规范 + 文档-代码对齐 + 04 波及总览

日期：2026-08-21
状态：待用户审阅
前置：模块 4 后端/前端代码已落地并端到端跑通（L1/L2/L5 全链路验证过），但工作区未提交。

## 背景与问题

模块 4 代码落地后留下三类债：

1. **ruff 违规 10 条**（`uv run ruff check src tests`）：I001 import 排序 ×4、F401 未用导入 ×1、UP017 `timezone.utc` → `UTC` 别名 ×4、B006 可变默认参 ×1。
2. **文档-代码漂移**：文档钦定的 `datetime.now(timezone.utc)` 教学写法与 UP017 冲突；04:636 的教学省略号 `history = {"user": ..., "agent": ...}` 仍是文档形态（用户照抄进代码曾导致 L1 静默零提取——真 bug 已修，文档未同步真实实现）；`.env.example` 的 `MONGO_URI` 名字与 Settings 字段 `mongo_url` 不匹配；AGENTS.md 仍描述「模块 3/4 未落地、consolidate 占位、memory 空包」。
3. **04 缺波及总览**：模块 4 对 02/03 侧文件（llm.py 拆分、schemas/routes 增量、graph 扩展、前端会话与按钮、pyyaml 依赖）的改造点分散在第 2/3/4/5 步里，没有一处集中的「前面被波及的地方怎么更新」视图。

## 用户裁决

- **全修**：代码采纳 UP017/B006 修复，文档同步对齐（不引入 ruff ignore 配置，保持零配置全绿）。
- `main.py` 的 `load_dotenv()` 桥接**保留**（02 L876-880 钦定：LangSmith SDK 只读真正的 `os.environ`，pydantic-settings 不注入环境变量）——I001 修复只补空行分隔格式，调用时序不动。

## 改动一：代码 ruff 全绿

### 1a. 机械修复（7 条，`ruff check --fix`）

| 位置 | 规则 | 修法 |
|---|---|---|
| `main.py:1` | I001 | `load_dotenv()` 调用与 import 块之间补空行（isort 分隔约定），桥接语义不动 |
| `tests/test_api.py`、`tests/test_graph.py`、`tests/test_documents.py` | I001 ×3 | import 块排序 |
| `tests/test_documents.py:1` | F401 | 删除未用导入 `store_doc` |

### 1b. UP017 ×4（代码语义改动）

`from datetime import datetime, timezone` → `from datetime import UTC, datetime`；调用点 `datetime.now(timezone.utc)` → `datetime.now(UTC)`。

- `memory/memory.py` ×3：extract_l1 时间戳（L24）、consolidate_l2（L40）、consolidate_profile（L61）——均为 `.isoformat()` 字符串
- `services/documents.py` ×1：`uploaded_at`（L27）——BSON Date 对象

Python 3.11+ 提供 `datetime.UTC` 别名，项目钉 `>=3.12`，无兼容问题。

### 1c. B006 ×1（代码语义改动）

`memory/memory.py` 的 `extract_l1` 签名：

```python
# 修复前
def extract_l1(history: dict, session_id: str, recent_l1: list[Memory] = []) -> list[Memory]:
# 修复后
def extract_l1(history: dict, session_id: str, recent_l1: list[Memory] | None = None) -> list[Memory]:
    if recent_l1 is None:
        recent_l1 = []
```

可变默认参是 Python 陷阱：默认 `[]` 在函数定义时创建一次、所有调用共享。本例只读不写、无活性 bug，但修法统一为 None 哨兵模式。

### 1d. pyyaml 转正（对齐 04:273 已有契约）

`uv add pyyaml`——`configs/prompts.py` 直接 `import yaml`，此前靠 uvicorn 传递依赖侥幸能用。pyproject 声明与 04 契约对齐。

### 1e. 代码验证

1. `uv run ruff check src tests` 零输出（零配置零压制）
2. `uv run ruff format --check src tests`（如格式化有 diff 先跑 format）
3. 服务重启（用户 `--reload` 窗口）+ 一轮真实提问（走 `extract_l1` 的 None 哨兵路径）→ 无错误事件、L1 正常落库（新 session_id，事后 Compass 清理）

## 改动二：文档对齐

### 2a. `01-Python文档工具.md` ×2 处（UP017）

- L473 代码：`"uploaded_at": datetime.now(timezone.utc),` → `datetime.now(UTC),`
- L482 散文：「`datetime.now(timezone.utc)` 用带时区的 UTC 时间」→ 同步改写法

### 2b. `04-TMT记忆系统.md` ×7 处（UP017）+ 2 处（B006）

UP017：L154 散文、L157 区 import 块示例、L167 散文、L330（extract_l1）、L364（consolidate_l2）、L396（consolidate_profile）、L463（upsert_l2 的 `$set`）。
B006：§2.2 代码示例签名 L315 同步为 None 哨兵形态；**逐段讲解区新增一条**「为什么默认值是 `None` 而非 `[]`」——可变默认值陷阱（ruff B006），只写为什么，符合文档政策。

### 2c. `04:636` 教学省略号 → 真实实现（防再咬人）

`history = {"user": ..., "agent": ...}` 替换为 graph.py 当前真实代码（`reversed(state["messages"])` 按 `m.type` 取最后一对），并保留教学注释说明人设/记忆 SystemMessage 不参与提取。

### 2d. `backend/.env.example` ×1 处

`MONGO_URI` → `MONGO_URL`（pydantic-settings 按名匹配 Settings 字段 `mongo_url`）。

### 2e. `AGENTS.md` 全面刷新

过期描述改为已实现态：

- 头部：「代码当前实现到模块 2、模块 3/4 未落地」→ 四模块全部落地
- 架构 mermaid：补记忆层（memory/db.py + memory.py）与 `/api/consolidate` 端点、`services/llm.py`、prompts.yaml
- 关键目录：`memory/` 双文件已实现、`frontend/` 已存在、`tests/` 3 个文件（`test_memory.py` 属 04 第 6 步待写）
- 端点表：`/api/consolidate` 占位 → 已转正（level 分流）
- 陷阱区：删「memory/ 是空包」「consolidate 占位」两条失效陷阱，补当前真实陷阱（SSE 流内错误 + HTTP 200 的诊断口诀、`store_memory` 路由值、教学省略号照抄风险已随 2c 消除）
- 代码约定区：模块 4 契约从「文档定稿，代码待实现」改为「已实现」措辞
- 依赖表：补 `pyyaml`

### 2f. 不动的文档

- **02 冻结**：本轮零波及（dotenv 桥接 L876-880 本来就在且保留）
- **03**：模块 3 教学文档保持模块 3 状态；04 §5 已用「替换模块 3 的写死值」「在模块 3 的基础上新增」的增量表述指向改动，双源不复制

## 改动三：04 新增「对前面模块的波及总览」

位置：`## 核心思路` 之后、`## 第 1 步` 之前（学生动手前先看到爆炸半径）。形态为索引表，每行指回 04 已有步骤（不复制内容，单源不变）：

| 前面模块的文件 | 波及改动 | 详见 |
|---|---|---|
| `services/llm.py`（新增） | LLM 客户端从 `build_graph` 提出共享单例（`llm` + `call_llm`） | 第 2 步前置 |
| `configs/prompts.yaml` + `prompts.py`（新增） | prompt 集中管理；`pyyaml` 转直接依赖 | 第 2 步前置 |
| `api/schemas.py` | `QueryRequest` 加 `session_id`；新增 `ConsolidateRequest/Response` | 第 3 步 / 第 4 步 |
| `api/routes.py` | `/api/consolidate` 占位转正（level 分流）；`/api/query` 传 session_id | 第 3 步 / 第 4 步 |
| `agents/graph.py` | `MemoryState` + `retrieve_memory`/`store_memory` 节点 + persona 前置 | 第 4 步 |
| `frontend/app.js` + `index.html` | 真会话 ID（localStorage）、请求体带 session_id、新增两按钮及绑定 | 第 5 步 |

表后一句：模块 1（`services/documents.py`）零波及。

## 范围外（明确不做）

- `tests/test_memory.py` 编写（04 第 6 步，独立任务）
- 既有测试的隔离性改造（真 Mongo/真 LLM/硬编码路径是已知现状）
- 02/03 文档任何改动
- ruff ignore 配置（用户裁决全修，保持零配置）
- ruff 之外的 lint 工具引入（mypy/pyright 等）

## 验收清单

1. `uv run ruff check src tests` 退出码 0、零输出
2. `uv run ruff format --check src tests` 通过
3. 服务重启后一轮真实提问：无 SSE 错误事件、回答正常、新 L1 落库（None 哨兵路径被真实执行）
4. `grep -c "timezone.utc"` 在 01/04 文档中为 0（代码中同样为 0）
5. `grep -n "= \.\.\." 04` 中 store_memory 的 history 行已无省略号形态
6. `.env.example` 无 `MONGO_URI`
7. 04 波及总览表存在且各「详见」指向的步骤标题真实存在
8. AGENTS.md 无「空占位」「占位返回 pending」「未落地」字样（git grep 验证）
9. 全部文档 markdown 围栏配对（awk 计数为偶数）
10. 四文档（01/04/.env.example/AGENTS.md）改动后逐文件 diff 审读一遍

## 提交策略

- spec 单独提交（本文件）
- 实施分两个提交：①代码 ruff 全绿 + pyyaml（backend 全部 + .env.example）②文档对齐 + 04 波及总览（01/04/AGENTS.md）
- 用户工作区既有未提交内容（模块 4 全套代码 + 前端）由用户决定打包时机，本设计不代提交
