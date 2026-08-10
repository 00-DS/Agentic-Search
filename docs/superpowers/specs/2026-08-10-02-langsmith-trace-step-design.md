# doc 02 新增「LangSmith 可视化 ReAct 循环」教学步骤 Design Spec

> **日期**: 2026-08-10
> **模块**: doc 02 (`任务文档/02-LangGraph-Agent.md`)
> **状态**: 待评审

## 1. 背景

doc 02 当前教学脉络（第 9–12 步 + 完成检查）：

```
第 9 步：瘦入口 main.py + CORS
第 10 步：启动服务 + httpx 验证
第 11 步：Swagger UI / redoc（API 外观，手动直观感受）
第 12 步：pytest（自动化测试）
完成检查
```

**Gap**：第 5 步教了 ReAct 循环的**代码结构**（`llm_call → should_continue → tool_node → llm_call → ...`），第 12 步（将成为第 13 步）教了**自动化测试**，但中间缺一个「**亲眼看到 agent 实际跑起来时每步发生了什么**」的环节。学生只能从终端日志的 `[retry]` 和 SSE 输出间接推断 agent 的多轮决策路径。

**LangSmith**（LangChain 团队的追踪/可观测平台）通过 3 个环境变量自动捕获 LangGraph 的每次节点调用、LLM 调用、工具调用，在 smith.langchain.com 上以嵌套瀑布图展示。它把抽象的 ReAct 循环变成可视化的执行轨迹——学生能看到「LLM 第 1 轮决定调 list_papers → 第 2 轮决定调 search_papers → 第 3 轮决定调 read_paper → 第 4 轮给出最终回答」的完整决策链。

## 2. 技术验证（已实测）

### 2.1 LangSmith 集成机制

LangSmith SDK 在 langchain import 时检查 `os.environ["LANGSMITH_TRACING"]`：值为 `"true"` 则开启自动追踪，不是则关闭。追踪一旦开启，LangGraph 的 `.invoke()` / `.astream()` 自动把每个节点、工具、LLM 调用上报到 `LANGSMITH_PROJECT` 指定的项目。**零代码侵入**——不需要在 graph.py 加任何 callback 或 wrapper。

### 2.2 .env 两条消费路径

项目当前 `.env` 只走 **pydantic-settings 路径**：

```python
# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", ...)
    llm_api_key: str = ""     # .env 里 LLM_API_KEY 匹配 → 读进 settings 对象
```

pydantic-settings 打开 .env，**只提取匹配 Settings 字段的变量**，存入 `settings` 对象。`LLM_API_KEY` 的旅程是 `.env → Settings 读取 → settings.llm_api_key → graph.py 显式传参`——全程不碰 `os.environ`。

LangSmith SDK 走的是 **os.environ 路径**——直接读 `os.environ["LANGSMITH_*"]`，没有「传参」替代方式。

**实测验证**（2026-08-10）：

```
uv run python -c "import os; os.environ.get('_TEST_DUMMY_VAR')"
→ NOT FOUND    （uv run 不自动加载 .env 进 os.environ）

from dotenv import load_dotenv; load_dotenv()
→ works        （手动 load_dotenv 把 .env 注入 os.environ）
```

### 2.3 桥接方案

`load_dotenv()` 读 .env 文件，把**所有**变量注入 `os.environ`。`python-dotenv` 已安装（pydantic-settings 的依赖，无需新增依赖）。

**放置位置**：`main.py` 顶部，在 `from agentic_search.api.routes import router`（L4）之前。这条 import 链触发 `routes.py → graph.py → langchain import`，LangSmith 在 langchain import 时检查 os.environ——`load_dotenv()` 必须在此之前执行。

### 2.4 无害性

`TRACING=true`（默认）但 API Key 为空时，langsmith SDK 检测到缺失 key 静默跳过（不报错、不追踪）。**实测验证**（2026-08-10）：`LANGSMITH_TRACING=true` + 空 `LANGSMITH_API_KEY` 下，完整 import 链 `from agentic_search.agents.graph import build_graph`（含 langgraph → langsmith client 初始化）stdout + stderr 全部干净，零 warning 零 error。`load_dotenv()` 本身只注入已存在的 .env 变量到 os.environ（不覆盖已有的系统环境变量，默认 `override=False`）。**未填 API Key 的学生，服务行为完全不变。**

## 3. 设计

### 3.1 涉及的改动

| 类型 | 文件 | 改动 |
|---|---|---|
| **代码** | `main.py` | 顶部加 2 行 `load_dotenv()` 桥接（在所有 agentic_search import 之前） |
| **代码** | `.env.example` | 加 3 个 `LANGSMITH_*` 变量（TRACING 默认 false） |
| **文档** | `任务文档/02-LangGraph-Agent.md` | 新增第 12 步（4 小节）+ 当前 pytest 步骤重编号 12→13 + 完成检查补 LangSmith 条目 |

### 3.2 main.py 改动

当前（L1-5）：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router
```

改后：

```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_search.api.routes import router
```

`load_dotenv()` 必须在 L4 `from agentic_search.api.routes import router` 之前——这条 import 链触发 langchain 加载，LangSmith 在此时检查 `os.environ["LANGSMITH_TRACING"]`。

### 3.3 .env.example 改动

在文件末尾加：

```env

# LangSmith 追踪（填入 API Key 即开启——TRACING 已默认 true）
LANGSMITH_TRACING = true
LANGSMITH_API_KEY = 
LANGSMITH_PROJECT = agentic-search
```

默认 `true`——学生注册后只需填入自己的 API Key 即开启追踪，无需再改 TRACING 开关。未填 API Key 时 langsmith SDK 检测到缺失 key 会静默跳过（不报错、不追踪），零影响。

> 注：`LANGSMITH_*` 不进 `config.py` 的 Settings 类——它们由 langsmith SDK 直接从 os.environ 读，不经 pydantic-settings。`load_dotenv()` 桥接把 .env 的值注入 os.environ，SDK 自己取。

### 3.4 新第 12 步内容结构

插入位置：当前第 11 步（Swagger UI）的 `---` 分隔之后、当前第 12 步（pytest）之前。

**标题**：`## 第 12 步：用 LangSmith 可视化 ReAct 循环的执行`

**开篇**：承接 Swagger（11）「看到 API 外观」，引出「现在看 agent 内部」——第 5 步教了 ReAct 循环的代码结构，但代码长什么样和实际跑起来长什么样是两回事。

**12.1 什么是 LangSmith —— 为什么用它看 ReAct 循环**

LangSmith 是 LangChain 团队的追踪/可观测平台。LangGraph 与 LangSmith 天然集成——设好环境变量后，graph 每一步的执行（LLM 调用、工具调用、消息流转）自动上报到 smith.langchain.com，以嵌套瀑布图展示。价值：把第 5 步的 ReAct 循环代码变成可见的执行轨迹——每个 `llm_call` 节点里 LLM 决策了什么、每个 `tool_node` 里工具返回了什么、`should_continue` 何时走 `tool_node` 何时走 `END`，一目了然。

**12.2 配置 LangSmith（.env + main.py 桥接）**

三步：
1. **注册**：到 [smith.langchain.com](https://smith.langchain.com) 注册账号 → Settings → 获取 API Key。
2. **`.env` 加 3 行**：`LANGSMITH_TRACING=true`（开启追踪）、`LANGSMITH_API_KEY=你的key`、`LANGSMITH_PROJECT=agentic-search`（项目名，随意取）。
3. **`main.py` 加 2 行桥接**：解释 `.env` 的两条消费路径（pydantic-settings 只读匹配字段，不注入 os.environ；LangSmith SDK 从 os.environ 读）→ `load_dotenv()` 把 .env 注入 os.environ，补上断裂的桥。`python-dotenv` 已作为 pydantic-settings 依赖安装，无需新增。

**12.3 跑一个查询，在 LangSmith 看 trace**

重启服务 → 用第 10 步的 httpx 命令跑一个跨论文问题（如「对比语料库里两篇论文分别是什么研究方向？」——触发多轮工具调用，trace 更丰富）→ 打开 smith.langchain.com → 左侧选 `agentic-search` 项目 → 点最新一条 trace。

**12.4 读 trace：ReAct 循环的可视化**

导读 trace 的嵌套结构，每一层对应代码里的什么：
- 顶层：整个 graph 的运行（`build_graph().astream()` 的一次调用）。
- 循环层：`llm_call` 节点 → `should_continue`（有 tool_calls 继循环）→ `tool_node` 节点 → 回 `llm_call` → ... 往复。
- `llm_call` 节点：展开看输入 messages（对话历史）+ 输出（AIMessage，含 `tool_calls` 字段——LLM 决定调哪个工具、传什么参数）。
- `tool_node` 节点：展开看工具执行结果（ToolMessage，工具返回的内容）。
- 最后一轮 `llm_call`：LLM 不再生成 tool_calls，给出纯文本回答 → `should_continue` 路由到 `END` → 循环结束。
- 每步耗时、token 用量、输入输出完整可见。

收尾：这就是第 5 步 `should_continue()` 条件边的可视化——有 `tool_calls` 走 `tool_node` 继续，没有走 `END` 结束。下一步（第 13 步）把验证固化成 pytest 自动化测试。

### 3.5 重编号

当前第 12 步（pytest）→ 第 13 步：
- `## 第 12 步：编写测试（pytest）` → `## 第 13 步：编写测试（pytest）`
- `### 12.1 测试图逻辑` → `### 13.1 测试图逻辑`
- `### 12.2 测试 API 接口` → `### 13.2 测试 API 接口`

### 3.6 完成检查更新

在 pytest 条目（`uv run pytest tests/ -v` 全部绿色）之前加一条：

```markdown
- [ ] 配置 `LANGSMITH_TRACING=true` 后，在 smith.langchain.com 看到本次查询的完整 trace（`llm_call` 与 `tool_node` 节点交替出现，对应 ReAct 循环）
```

### 3.7 交叉引用更新（Swagger 步骤 → LangSmith → pytest）

插入 LangSmith 步骤后，教学脉络从「Swagger(11) → pytest(12)」变成「Swagger(11) → LangSmith(12) → pytest(13)」。需更新两处已有交叉引用：

- **L808（Swagger 步骤 intro）**：当前「下一步（第 12 步）再把验证固化成 pytest 自动化测试」→ 改为「下一步（第 12 步）用 LangSmith 可视化 agent 内部执行」。引出 LangSmith 而非 pytest。
- **L840（Swagger 步骤 outro）**：当前「下一步（第 12 步）把这些手动验证固化成 pytest 自动化测试」→ 改为「下一步（第 12 步）用 LangSmith 看 agent 内部实际怎么跑」。衔接 LangSmith。

新第 12 步（LangSmith）的 outro 自然衔接 pytest：「下一步（第 13 步）把验证固化成 pytest 自动化测试」。

> 步骤号 12 在两个版本里都是 12，但语义从 pytest 变成 LangSmith。L808 和 L840 里的「第 12 步」原本指向 pytest，改后指向 LangSmith。

## 4. 验证计划

### 4.1 代码验证

- **未填 API Key（TRACING=true 但 key 空）**：langsmith SDK 静默跳过追踪，`uv run uvicorn agentic_search.main:app --reload` 启动正常，所有端点行为不变，`load_dotenv()` 无害运行。
- **填入有效 key（TRACING=true）**：跑一次 query → smith.langchain.com → `agentic-search` 项目 → 出现 trace，展开能看到 `llm_call` 与 `tool_node` 的嵌套。
- **现有测试**：`uv run pytest tests/ -v` 仍全部通过（`load_dotenv()` 不影响测试）。

### 4.2 文档验证

- 步骤号连续：10 → 11（Swagger）→ **12（LangSmith）** → 13（pytest），无跳号。
- 重编号无残留：grep 全文「第 12 步」「12.1」「12.2」，确认新第 12 步用的是 12.x（LangSmith），旧 pytest 内容已全改 13.x。
- 无否定措辞（「不使用 XXX」）。
- 交叉引用同步：L808 的「下一步」指向正确。

## 5. 不改的东西

- **`graph.py`**：零改动。LangSmith 自动追踪 LangGraph，不需要加 callback 或 wrapper。
- **`config.py`**：零改动。`LANGSMITH_*` 由 SDK 从 os.environ 读，不经 pydantic-settings。
- **`routes.py`**：零改动。
- **`tools.py`**：零改动。
- **依赖**：零新增。`python-dotenv` 已作为 pydantic-settings 依赖安装。

## 6. 教学脉络（改后）

```
第 9 步：瘦入口 main.py + CORS
第 10 步：启动服务 + httpx 验证       ← 命令行验证
第 11 步：Swagger UI / redoc           ← API 外观（手动直观感受）
第 12 步：LangSmith 可视化（新增）      ← agent 内部执行（手动直观感受）
第 13 步：pytest                        ← 自动化测试
完成检查
```

从「代码结构」（第 5 步）到「实际跑起来长什么样」（第 12 步 LangSmith）到「固化成测试」（第 13 步 pytest），三层递进。
