# doc 02 新增「LangSmith 可视化 ReAct 循环」教学步骤 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 doc 02 新增独立教学步骤「用 LangSmith 可视化 ReAct 循环的执行」，填补「代码结构（第 5 步）→ 实际跑起来长什么样 → 自动化测试」中间的可视化空白。

**Architecture:** 3 个文件改动——`main.py` 加 `load_dotenv()` 桥接（让 .env 注入 os.environ，LangSmith SDK 能读到）、`.env.example` 加 3 个 `LANGSMITH_*` 变量（TRACING 默认 true，学生只需填 API Key）、doc 02 新增第 12 步（4 小节：什么是 LangSmith → 配置 → 跑查询看 trace → 读 trace 导读）+ pytest 重编号 12→13 + 两处交叉引用更新 + 完成检查补 LangSmith。零依赖新增（python-dotenv 已作为 pydantic-settings 依赖安装）。

**Tech Stack:** Python (main.py)、env (.env.example)、Markdown 教学文档。

**Spec:** `docs/superpowers/specs/2026-08-10-02-langsmith-trace-step-design.md`

## Global Constraints

- **`LANGSMITH_TRACING` 默认 `true`**（用户决定）：学生注册后只需填 API Key 即开启，无需改开关。未填 key 时 langsmith SDK 静默跳过（实测验证零 warning 零 error）。
- **不改 `graph.py`、`config.py`、`routes.py`、`tools.py`**——LangSmith 自动追踪 LangGraph，零代码侵入。
- **零依赖新增**——`python-dotenv` 已作为 pydantic-settings 依赖安装。
- **文档政策**：只写「为什么这样」，禁否定措辞「不使用 XXX」。
- 行号为近似值——以内容定位为准（grep 关键短语），不盲目按行号切割。
- **`LANGSMITH_*` 不进 `config.py` 的 Settings 类**——它们由 langsmith SDK 直接从 os.environ 读，不经 pydantic-settings。`load_dotenv()` 桥接把 .env 的值注入 os.environ，SDK 自己取。

## File Structure

- `backend/src/agentic_search/main.py` — 加 2 行 `load_dotenv()` 桥接（在所有 agentic_search import 之前）。
- `backend/.env.example` — 末尾加 3 个 `LANGSMITH_*` 变量。
- `任务文档/02-LangGraph-Agent.md` — 新增第 12 步 + pytest 重编号 12→13 + 两处交叉引用 + 完成检查。

---

## Task 1: main.py 加 load_dotenv() 桥接

**Files:**
- Modify: `backend/src/agentic_search/main.py`（L1 之前插入 2 行）

**Interfaces:** 无（纯 import 桥接，不改任何函数签名或行为）。

**Why before this file:** `load_dotenv()` 必须在 `from agentic_search.api.routes import router`（L4）之前执行——这条 import 链触发 `routes.py → graph.py → langchain import`，LangSmith 在 langchain import 时检查 `os.environ["LANGSMITH_TRACING"]`。

- [ ] **Step 1: 在 main.py 最顶部（L1 之前）插入 load_dotenv 桥接**

当前（L1-5）：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router
```

改为：

```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router
```

- [ ] **Step 2: 验证——不改 .env（LANGSMITH_API_KEY 空）启动不报错**

```bash
cd backend
uv run python -c "from agentic_search.main import app; print('import OK')"
```

应输出 `import OK`，无 warning 无 error。（已实测验证：TRACING=true + 空 key → SDK 静默跳过。）

---

## Task 2: .env.example 加 LANGSMITH_* 变量

**Files:**
- Modify: `backend/.env.example`（L9 后追加）

**Interfaces:** 无。

- [ ] **Step 1: 在 .env.example 末尾（L9 `MONGO_DB = agentic_search` 之后）追加 LangSmith 配置块**

追加：

```env

# LangSmith 追踪（填入 API Key 即开启——TRACING 已默认 true）
LANGSMITH_TRACING = true
LANGSMITH_API_KEY = 
LANGSMITH_PROJECT = agentic-search
```

注意：`LANGSMITH_API_KEY = ` 行尾有空格后无值（跟 L2 `LLM_API_KEY = ` 同格式）。

---

## Task 3: doc 02 新增第 12 步 + 重编号 + 交叉引用 + 完成检查

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`

**Interfaces:** 无（纯文档）。

- [ ] **Step 1: 更新 Swagger 步骤的两处交叉引用（L808 intro + L840 outro）**

L808 当前：
```
启动服务后，你已经用第 10 步的 `httpx` 命令验证了每个端点能跑。FastAPI 还提供更直观的方式——两个自动生成的 API 文档界面，零额外代码。这一步先用它们**手动感受一遍**，下一步（第 12 步）再把验证固化成 pytest 自动化测试。
```

改为（把末句「下一步（第 12 步）再把验证固化成 pytest 自动化测试」替换为引出 LangSmith）：
```
启动服务后，你已经用第 10 步的 `httpx` 命令验证了每个端点能跑。FastAPI 还提供更直观的方式——两个自动生成的 API 文档界面，零额外代码。这一步先用它们**手动感受 API 的外观**，下一步（第 12 步）再用 LangSmith 看 agent 内部实际怎么跑。
```

L840 当前：
```
现在你已经亲手试过每个端点、确认它们正常工作。下一步（第 12 步）把这些手动验证**固化成 pytest 自动化测试**——把「每次改代码手动点一遍」升级成「每次改代码自动跑一遍」。
```

改为（衔接 LangSmith 而非 pytest）：
```
现在你已经用 API 文档界面直观感受了 4 个端点的外部行为。但 agent 内部的 ReAct 循环——LLM 决策、工具调用、多轮探索——在终端只看到 `[retry]` 和 SSE 输出，不够直观。下一步（第 12 步）用 LangSmith 可视化 agent 的完整执行轨迹。
```

- [ ] **Step 2: 在 L842 `---` 之后、L844 `## 第 12 步：编写测试（pytest）` 之前，插入新第 12 步**

插入以下完整内容（含末尾 `---` 分隔）：

```markdown
## 第 12 步：用 LangSmith 可视化 ReAct 循环的执行

第 5 步教了 ReAct 循环的代码结构——`llm_call → should_continue → tool_node → llm_call → ...` 循环直到 LLM 给出纯文本回答。但「代码长什么样」和「实际跑起来长什么样」是两回事。终端日志的 `[retry]` 和 SSE 输出只能间接推断 agent 的多轮决策路径，不够直观。

LangSmith 是 LangChain 团队的追踪/可观测平台，与 LangGraph 天然集成——设好环境变量后，graph 每一步的执行自动上报，在 smith.langchain.com 上以嵌套瀑布图展示。这一步配置 LangSmith，把 ReAct 循环变成可见的执行轨迹。

### 12.1 什么是 LangSmith —— 为什么用它看 ReAct 循环

LangSmith 的价值：把第 5 步的 ReAct 循环代码变成可见的执行轨迹——每个 `llm_call` 节点里 LLM 决策了什么（调哪个工具、传什么参数）、每个 `tool_node` 里工具返回了什么、`should_continue` 何时走 `tool_node` 何时走 `END`，一目了然。每步的耗时、token 用量、输入输出全部完整可见。

### 12.2 配置 LangSmith

三步：

1. **注册**：到 [smith.langchain.com](https://smith.langchain.com) 注册账号 → Settings → 获取 API Key。
2. **`.env` 加配置**：在 `.env` 文件加三行（`.env.example` 已有模板）：

   ```env
   LANGSMITH_TRACING = true
   LANGSMITH_API_KEY = 你的key
   LANGSMITH_PROJECT = agentic-search
   ```

   `LANGSMITH_PROJECT` 是项目名（在 LangSmith 里分组用），随意取。

3. **`main.py` 加桥接**：`main.py` 顶部已加了两行：

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

   **为什么需要这个桥接**：项目的 `.env` 有两条消费路径。第一条是 pydantic-settings——`config.py` 的 `Settings` 类打开 `.env`，只提取匹配自己字段的变量（如 `LLM_API_KEY`），存入 `settings` 对象，全程不碰 `os.environ`。第二条是 LangSmith SDK——它直接读 `os.environ["LANGSMITH_TRACING"]` 等变量，没有「传参」的替代方式。`load_dotenv()` 读 `.env` 把所有变量注入 `os.environ`，补上这条断裂的桥。（`python-dotenv` 已作为 pydantic-settings 的依赖安装，无需额外添加。）

   > 💡 默认 `LANGSMITH_TRACING = true` 但 API Key 为空时，LangSmith SDK 会检测到缺失 key 静默跳过——不报错、不追踪，服务照常运行。填入有效 API Key 后重启服务即开启追踪。

### 12.3 跑一个查询，在 LangSmith 看 trace

重启服务 → 用第 10 步的 httpx 命令跑一个跨论文问题（触发多轮工具调用，trace 更丰富）：

```bash
uv run python -c '
import httpx
with httpx.stream("POST", "http://localhost:8000/api/query", json={"question": "对比语料库里两篇论文分别是什么研究方向？"}, timeout=60) as r:
    for line in r.iter_lines():
        if line: print(line)
'
```

打开 [smith.langchain.com](https://smith.langchain.com) → 左侧选 `agentic-search` 项目 → 点最新一条 trace，看到嵌套瀑布图。

### 12.4 读 trace：ReAct 循环的可视化

trace 的嵌套结构，每一层对应代码里的什么：

- **顶层**：整个 graph 的运行（`build_graph().astream()` 的一次调用）。
- **循环层**：`llm_call` 节点 → `should_continue`（有 `tool_calls` 继续循环）→ `tool_node` 节点 → 回 `llm_call` → ... 往复。
- **`llm_call` 节点**：展开看输入 messages（对话历史）+ 输出（AIMessage，含 `tool_calls` 字段——LLM 决定调哪个工具、传什么参数）。
- **`tool_node` 节点**：展开看工具执行结果（ToolMessage，工具返回的内容）。
- **最后一轮 `llm_call`**：LLM 不再生成 `tool_calls`，给出纯文本回答 → `should_continue` 路由到 `END` → 循环结束。

这就是第 5 步 `should_continue()` 条件边的可视化——有 `tool_calls` 走 `tool_node` 继续，没有走 `END` 结束。现在你已经亲眼看到 agent 内部实际怎么跑了。下一步（第 13 步）把验证固化成 pytest 自动化测试。

---
```

- [ ] **Step 3: 重编号当前 pytest 步骤 12 → 13**

- `## 第 12 步：编写测试（pytest）` → `## 第 13 步：编写测试（pytest）`
- `### 12.1 测试图逻辑` → `### 13.1 测试图逻辑`
- `### 12.2 测试 API 接口` → `### 13.2 测试 API 接口`

> 已 grep 确认全文无其它对「第 12 步」「12.1」「12.2」的交叉引用，重编号零散落。

- [ ] **Step 4: 完成检查补 LangSmith 条目**

在完成检查里，pytest 条目（`uv run pytest tests/ -v` 全部绿色）**之前**加一条：

```markdown
- [ ] 配置 `LANGSMITH_TRACING=true` 并填入 API Key 后，在 smith.langchain.com 看到本次查询的完整 trace（`llm_call` 与 `tool_node` 节点交替出现，对应 ReAct 循环）
```

- [ ] **Step 5: 通读复核**

手动复核：
1. **步骤号连续**：grep `^## 第 [0-9]+ 步` 确认 10 → 11（Swagger）→ **12（LangSmith）** → 13（pytest），无跳号。
2. **重编号无残留**：grep 全文「第 12 步」确认只出现在新 LangSmith 步骤 + Swagger 步骤的交叉引用（L808/L840 已改为指向 LangSmith）+ 完成检查（LangSmith 条目）；pytest 内容已全改 13.x。
3. **交叉引用对齐**：Swagger 步骤 L808/L840 引向 LangSmith（第 12 步），LangSmith 步骤 outro 引向 pytest（第 13 步）。
4. **禁否定措辞**：新增内容里无「不使用 XXX」。

---

## Self-Review

**1. Spec coverage：**
- spec §2.4 无害性（TRACING=true + 空 key 静默跳过）→ Task 1 Step 2 验证 + Task 3 Step 2 的 12.2 💡 提示。✅
- spec §3.2 main.py 改动 → Task 1 Step 1。✅
- spec §3.3 .env.example 改动 → Task 2 Step 1。✅（注：spec §3.3 写「改为 true 并填入 API Key 即开启」，plan 里已按用户最新决定改为「填入 API Key 即开启——TRACING 已默认 true」。）
- spec §3.4 新第 12 步 4 小节 → Task 3 Step 2。✅
- spec §3.5 重编号 → Task 3 Step 3。✅
- spec §3.6 完成检查 → Task 3 Step 4。✅
- spec §3.7 交叉引用更新 → Task 3 Step 1。✅
- spec §4 验证计划 → Task 1 Step 2（import 验证）+ Task 3 Step 5（文档通读）。✅

**2. Placeholder scan：** 无 TBD/TODO；每步含具体内容或命令；新第 12 步完整成文。

**3. Type consistency：** 子节号 12.1–12.4 内部一致；与重编号后第 13 步（13.1/13.2）不冲突；完成检查措辞与 12.2 配置描述一致。

**4. 跨文件顺序：** Task 1（main.py）→ Task 2（.env.example）→ Task 3（doc 02）。doc 02 Task 3 Step 2 的 12.2 小节会引用 main.py 的 load_dotenv() 和 .env.example 的 LANGSMITH_* 模板——前两个 Task 先完成，文档引用才成立。
