# 设计：LLM 客户端提升为共享模块（services/llm.py）

> 日期：2026-08-20
> 背景：`任务文档/04-TMT记忆系统.md` 的 `store.py` 教学示例使用 `call_llm(prompt)`，但该函数在 04 中无出处；模块 2 的 LLM 客户端是 `build_graph()` 内部闭包，外部拿不到。
> 状态：设计已获用户批准（方案 A 提升共享模块 + 位置 services/llm.py）。

## 问题

1. `call_llm` 无引入：04 的 `extract_l1` / `consolidate_l2` / `consolidate_profile` 三个函数裸调 `call_llm(prompt)`，读者无法得知其来源与实现。
2. 闭包锁死：02 的 `llm = init_chat_model(...)` 是 `build_graph()` 局部变量，`llm_call` 节点闭包捕获；`store.py` 需要裸 LLM（无工具绑定），拿不到。
3. 循环导入陷阱：模块 4 中 `graph.py` 会 import `memory/store.py`（图节点调记忆函数）；若 `store.py` 反向从 `graph.py` 取 LLM 则成环。LLM 客户端必须放双方都能 import 的第三方模块。
4. 工具绑定差异：图用 `bind_tools()` 过的 LLM，记忆函数用裸 LLM——共享对象应是 `init_chat_model` 原始实例，`bind_tools` 留在图内。

## 方案（已批准）

### 1. 新模块 `services/llm.py`

```python
from langchain.chat_models import init_chat_model
from agentic_search.configs.config import settings

llm = init_chat_model(
    model=settings.llm_model,
    model_provider=settings.llm_model_provider,
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    timeout=settings.llm_timeout,
)

def call_llm(prompt: str) -> str:
    """裸 LLM 调用（无工具绑定），记忆提取/整合用。"""
    return str(llm.invoke(prompt).content)   # str() 是 Pylance 绕过：content 静态类型为 str | list[str | dict] 联合（多模态遗留），运行时恒为 str——与 parse_pdf 的 str() 同一惯例（2026-08-20 补）
```

- 与 `services/documents.py` 同构：模块级持有一个外部服务客户端（documents 持 Mongo，llm 持 LLM），参数全部从 `settings` 读。
- `llm` 公开（`build_graph` 要 `bind_tools`）；私有化规范（`_` 前缀）只约束集合句柄这类实现细节，共享客户端与 `settings` 同级公开。
- `call_llm` 不带 `@retry`：`@retry` 是 02 的手写装饰器教学点，留在 `graph.py`；记忆调用失败由用户重点按钮/下一轮对话兜底，04 FAQ 补一条说明。

### 2. `build_graph()` 改动（04 教这个重构）

```python
from agentic_search.services.llm import llm
# 删除闭包内的 init_chat_model(...) 块（约 7 行）
llm_with_tools = llm.bind_tools(tools)   # bind 留在图内——工具绑定是图特有的
```

### 3. 04 文档改动

- **第 2 步开头**（"## 第 2 步：实现 `memory/store.py`" 标题后、`### 2.1` 之前）插入一段无编号前置小节：说明 + `services/llm.py` 代码 + `build_graph()` 两行改动。教学点：「闭包在第二个消费者出现时提升为模块级」——`store.py` 既有端点调用方又有图节点调用方，且图 import store，LLM 放 graph 会循环导入。不改任何既有小节编号与交叉引用（"见 2.4"、"见 2.6"、"见 2.7" 等原样保留）。
- 前置小节末尾注明：`store.py` 文件头部需 `from agentic_search.services.llm import call_llm`（第 2 步开头面向调用方的包化 import 清单 `from agentic_search.memory.store import ...` 保持原样，那是消费方视角）。
- FAQ 增补一条：「为什么 `call_llm` 不做重试？」——`@retry` 是模块 2 手写装饰器的教学点，包在图的 `llm_call` 上；记忆调用是后台/手动操作，失败由重按按钮或下一轮对话兜底，教学从简。

### 4. 02 文档：一行前向注记

在 02 §6 逐段讲解的「**为什么 `@retry` 包在 `llm_call` 而非 `init_chat_model` 上？**」段（02:441）之后，新增一条独立 blockquote，对齐 02:100 前向引用模块 4 的既有先例：

> 模块 4 的记忆层也需要 LLM，届时会把这里的客户端提升为 `services/llm.py` 共享模块；本模块先保持闭包，聚焦图组装。

### 5. AGENTS.md 同步

代码约定区新增一行：LLM 客户端 = `services/llm.py` 模块级单例（`llm` 供 `bind_tools`，`call_llm` 供记忆层裸调用），`graph.py` 与 `memory/store.py` 共用，`bind_tools` 留在 `build_graph()` 内。

## 依赖方向（无环）

```
configs/config.py ← services/llm.py ← agents/graph.py（bind_tools）
                      ↑                ↑
                      memory/store.py ─┘（graph import store；store 只 import llm，无环）
api/routes.py → memory/store.py
```

## 交付物清单

| 文件 | 改动 |
|---|---|
| `任务文档/04-TMT记忆系统.md` | 第 2 步开头前置小节 + store.py import 行 + FAQ 一条 |
| `任务文档/02-LangGraph-Agent.md` | 一行前向注记 |
| `AGENTS.md` | 代码约定一行 |

## 验收

1. `grep -n "call_llm" 任务文档/04-TMT记忆系统.md` 每处要么在 `services/llm.py` 定义处，要么上下文已说明来源。
2. 04 既有小节编号（2.1–2.7）与交叉引用零变动（`git diff` 确认无重编号）。
3. 02 仅新增一行 blockquote（`git diff --stat` 显示 +1）。
4. AGENTS.md 代码约定区含 services/llm.py 条目。
