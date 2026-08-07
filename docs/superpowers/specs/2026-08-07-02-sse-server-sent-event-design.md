# 设计：模块 02 §8.1 SSE 改用 `fastapi.sse.ServerSentEvent`

- 日期：2026-08-07
- 锚点：**`任务文档/02-LangGraph-Agent.md` 是后端契约的权威来源**。前端（doc 03）依后端契约实现，不反向。本设计按「doc 02 最优」决策，doc 03 的适配由负责它的 omp peer 协调完成。
- 直接范围：`任务文档/02-LangGraph-Agent.md`（文档）+ `backend/src/agentic_search/api/routes.py`（参考实现）
- 协调范围（不改文件，只通信）：`任务文档/03-HTML前端.md`（另一个 omp agent 负责）

---

## 1. 背景与问题

`02-LangGraph-Agent.md` §8.1 的 `POST /api/query` 端点用「`StreamingResponse` + 手写 SSE f-string」推送流式回答：

```python
return StreamingResponse(event_stream(), media_type="text/event-stream")
```

```python
yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"      # 文字 token
yield f"event: tool\ndata: {tc['name']}\n\n"                            # 工具调用
```

FastAPI 0.141.1 提供了更现代的 SSE 原语：`fastapi.sse` 模块下的 `ServerSentEvent`（结构化事件对象）与 `EventSourceResponse`（`StreamingResponse` 的 SSE 专用子类，自带 `text/event-stream`）。本项目 `pyproject.toml` 已锁定 `fastapi>=0.141.1`，两个原语均可用（已验证可导入）。继续手写 SSE 帧是过时写法，应改用官方原语。

## 2. 关键技术事实（均已运行时验证）

`EventSourceResponse` 用法（源码：`fastapi/sse.py`）：

- `EventSourceResponse` 是 `StreamingResponse` 的薄子类，`media_type = "text/event-stream"`，主要作为「标记 + 设对 Content-Type」。
- **正确用法是「路径操作函数本身声明为异步生成器 + `response_class=EventSourceResponse`」**，直接 `yield ServerSentEvent(...)`——不是在函数体里 `return EventSourceResponse(...)`（那样路由返回的是协程而非可迭代对象，触发 `TypeError: 'coroutine' object is not iterable`）。
- `EventSourceResponse` 不需要显式传 `media_type`（子类已设）。

**`EventSourceResponse` 开箱即用的 SSE 最佳实践**（官方文档「技术细节」节，非手写 `StreamingResponse` 能享受）：15 秒无消息时自动发保活 `:` 注释 ping（防代理超时断连）、自动设 `Cache-Control: no-cache`（防缓存流）、自动设 `X-Accel-Buffering: no`（防 Nginx 等代理缓冲，否则流式感会被破坏）。对本项目的 LLM 流式端点是真实增益，不是纯风格。

`ServerSentEvent` 字段（源码：`fastapi/sse.py`，Pydantic 模型）：

| 字段 | 语义 | 线材格式（端到端 TestClient 实测） |
|---|---|---|
| `data=` | **总**做 JSON 序列化（`json.dumps(jsonable_encoder(x))`，源码 `fastapi/routing.py`，**无** `ensure_ascii=False`）。字符串会被加引号，非 ASCII 转义为 `\uXXXX`。 | `ServerSentEvent(data="你好")` → `data: "\u4f60\u597d"`；`ServerSentEvent(event="tool", data="search_papers")` → `event: tool\ndata: "search_papers"` |
| `raw_data=` | 把字符串**原样**放进 `data:` 字段，不加引号、不转义。官方文档原话：「用于发送不进行 JSON 编码的数据……预格式化文本、日志行、特殊『哨兵』值（如 `[DONE]`）」。与 `data=` 互斥。**本设计不使用**（理由见 §3.2）。 | `ServerSentEvent(event="tool", raw_data="read_paper")` → `event: tool\ndata: read_paper` |
| `event=` | 事件类型名 → `event:` 行。 | `event: tool` |
| `id=` / `retry=` / `comment=` | 本端点不使用。 | — |

实测线材格式（TestClient `POST`，`response_class=EventSourceResponse`，方案 A）：

```
data: "\u4f60\u597d"          ← ServerSentEvent(data="你好")：转义、加引号

event: tool
data: "search_papers"         ← ServerSentEvent(event="tool", data="search_papers")：加引号
```

`Content-Type: text/event-stream; charset=utf-8`，`status: 200`。

**官方文档对方案 A 的背书**：FastAPI 官方 SSE 教程（`https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/`）的示例对「自然是字符串的值」一律用 `data=`（含 POST chat 示例里的每个 token）；`raw_data=` 仅用于 `[DONE]`、日志行等真正非 JSON 的哨兵负载。工具名是字符串标识符，属「自然是字符串的值」→ 用 `data=`。

## 3. 决策：方案 A（`data=` 一统，所有事件统一 JSON 编码）

### 3.1 方案对比

- **方案 A（`data=` 一统，选定）**：文字 token 与工具名都用 `data=`。每个事件的 `data:` 字段都是 JSON；前端对**任意** `data:` 行一律 `JSON.parse`。单一规则。
- **方案 B（`data=` + `raw_data=` 混用）**：文字用 `data=`、工具名用 `raw_data=`。工具名不带引号，与旧手写格式逐字节一致。代价：契约分裂成两条规则（默认事件 JSON、`event: tool` 事件原始），前端必须按事件类型决定是否 `JSON.parse`。
- **方案 C（维持现状）**：不改。与现代 FastAPI 惯用法脱节，且享受不到 `EventSourceResponse` 的保活/防缓冲增益。

### 3.2 选 A 的四条理由

1. **契约最简、最干净**：所有 `data:` 都是 JSON，前端一条规则 `JSON.parse(dataLine)` 吃下所有事件——文字、工具名、错误信息均如此。方案 B 把契约分裂成「默认事件 parse、`event: tool` 事件不 parse」，增加前端耦合。**doc 02 是契约锚点，应定最干净的契约**，而不是把旧前端的解析习惯固化进后端。
2. **「全面改用」= 统一采纳**：用户明确要「全面改用 `ServerSentEvent`」。A 是最彻底的统一形态——每个事件都走同一条 `data=` 路径。B 保留旧线材的「工具名不带引号」怪癖，是用新对象包装旧 quirk，并非真正的「全面」。
3. **契合官方惯用法**：FastAPI 官方 SSE 教程对字符串类值统一用 `data=`，`raw_data=` 留给 `[DONE]`/日志行等真·非 JSON 负载。工具名是字符串，归 `data=`。B 把 `raw_data=` 用在一个「本可以是普通字符串」的值上，偏离官方意图。
4. **不只是风格升级，是真增益**：`EventSourceResponse` 开箱即用提供保活 ping / 防缓存 / 防代理缓冲（见 §2）。当前手写 `StreamingResponse` 没有这些——一旦上线到有 Nginx 或带超时的反代后面，流式体验可能被缓冲破坏。这次升级顺带把这点也修了。

> **关于 doc 03 的适配**：A 会让工具名带引号（`data: "search_papers"`），与负责 doc 03 的 peer 刚提交（`e04d4e8`）的解析器当前行为不同（其工具分支用原始 `dataLine`、不 `JSON.parse`）。**这是预期内的契约演进**——后端是锚点，前端适配后端。doc 03 的工具分支需加一句 `JSON.parse`（或与文字分支合并成统一 parse）。这部分**不由本会话改 doc 03 文件**（避免与 peer 的文件编辑冲突），而是通过 Orca 通知 peer 按新契约调整（见 §4.4）。

## 4. 改动清单

### 4.1 `backend/src/agentic_search/api/routes.py`（参考实现）

- 删除 `import json`、`from fastapi.responses import StreamingResponse`。
- 新增 `from fastapi.sse import EventSourceResponse, ServerSentEvent`。
- `query` 端点：路由函数本身改为异步生成器，签名加 `response_class=EventSourceResponse`，去掉内层 `event_stream()` 闭包，`yield ServerSentEvent(...)`。所有事件统一用 `data=`。

改后形态：

```python
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import AIMessageChunk, HumanMessage

from agentic_search.agents.graph import build_graph
# …其余 import 不变…

@router.post("/query", response_class=EventSourceResponse)
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    try:
        async for chunk, metadata in graph.astream(
            {"messages": [HumanMessage(content=req.question)]},
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue                              # 跳过 ToolMessage 等非 LLM chunk
            if chunk.content:                         # 文字 token：JSON 编码传输
                yield ServerSentEvent(data=chunk.content)
            elif chunk.tool_call_chunks:              # LLM 决定调工具
                for tc in chunk.tool_call_chunks:
                    if tc.get("name"):
                        yield ServerSentEvent(event="tool", data=tc["name"])
    except Exception as e:
        yield ServerSentEvent(data=f"[错误：{e}]")
```

### 4.2 `任务文档/02-LangGraph-Agent.md`（6 处触点）

| # | 位置（行号近似） | 当前 | 改为 |
|---|---|---|---|
| 1 | §8.1 代码块（L535-557） | `StreamingResponse` + f-string | 上面的 `EventSourceResponse` + `ServerSentEvent`（统一 `data=`）版本 |
| 2 | §8.1 说明段（L559-561）「本项目用两种事件…工具名无需 JSON 包裹」 | 描述手写帧 + 「工具名无需 JSON」 | 改述：`ServerSentEvent.data=` **总**做 JSON 序列化（字符串加引号、非 ASCII 转义 `\uXXXX`），保证多行/特殊字符安全传输；**所有事件（含工具名）统一走 `data=`**，前端对任意 `data:` 行一律 `JSON.parse` 还原。点明「单一规则」是这个契约的核心优势 |
| 3 | §8.1 末尾 📖 链接（L697） | 链向 StreamingResponse 文档 | 链向 FastAPI 官方 SSE 教程 `https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/`（已确认存在，含 `EventSourceResponse`/`ServerSentEvent`/`raw_data` 三节） |
| 4 | 第 10 步验证 ③④ 注释 + 验证标准（L776-777, L803） | 「`data: "..."` 行就是文字 token…`event: tool` 行是工具调用」 | 注明 raw 输出里文字与工具名均为 JSON 编码（中文显 `\uXXXX`、工具名带引号），前端 `JSON.parse` 后正常。**验证命令本身不改**（仍 `httpx.stream` + `iter_lines`） |
| 5 | 完成检查（L881） | 「文字 token 逐个到达（`data: "..."` 行）」 | 同步：`data:` 行统一为 JSON 编码（文字含转义、工具名带引号），`event: tool` 标记工具调用 |
| 6 | 技术概念 SSE 段（L54）末句「…用 FastAPI 的 `StreamingResponse` 返回 `text/event-stream`」 | 提到 `StreamingResponse` | 改为 `EventSourceResponse` + `ServerSentEvent`，点明这是 FastAPI 的 SSE 原语（结构化事件对象，替代手写帧） |

> 技术概念段对 SSE 线材格式（`event:`/`data:`/`\n\n`）的讲解**保留**——学生仍需理解协议本身；改动只是把「手写帧」换成「`ServerSentEvent` 对象被框架序列化成同样的帧」。

### 4.3 不动的部分

- `main.py`：`app.include_router(router)` 不受影响，无需改动。
- `任务文档/03-HTML前端.md`：**本会话不改文件**（避免与 peer 文件编辑冲突）。契约适配由 peer 完成（见 §4.4）。
- 模块 1、4 的文档：与 SSE 无关。
- pyproject.toml：`fastapi>=0.141.1` 已满足，无需动。

### 4.4 doc 03 peer 协调（通过 Orca，不改文件）

负责 doc 03 的 omp agent（终端 `term_1d1d12c4-94c8-47f3-8b2f-dc43f6c76ec2`）刚提交 `e04d4e8`，其 `askQuestion` 解析器（L745-751）当前：工具分支用原始 `dataLine`（不 `JSON.parse`）、文字分支 `JSON.parse(dataLine)`。

方案 A 下新契约要求**前端对任意 `data:` 行一律 `JSON.parse`**，故 peer 需调整 doc 03 的工具分支：把 `${dataLine}` 改为 `${JSON.parse(dataLine)}`（或把工具/文字合并成统一先 parse 再分支）。将通过 Orca `terminal send` 向该终端发一条简短契约说明，内容：
- 后端 `/api/query` 已改用 `ServerSentEvent`（`response_class=EventSourceResponse`）。
- **所有 `data:` 字段均为 JSON 编码**：字符串带引号、中文为 `\uXXXX`、工具名也带引号（`data: "search_papers"`）。
- 前端：对任意 `data:` 行一律 `JSON.parse` 还原（含 `event: tool` 的工具名）。doc 03 工具分支需相应加 `JSON.parse`。

## 5. 验证计划

1. **静态**：改后 `routes.py` 用 `uv run python -c "import agentic_search.api.routes"` 无报错；Pylance 无新增告警。
2. **单元**（TestClient，不启动真服务）：构造一个 yield 两个 `ServerSentEvent`（文字 + 工具）的最小端点，断言 raw body 含 `data: "\u` 与 `event: tool\ndata: "search_papers"`（**带引号**）。
3. **端到端**（启动真服务，步骤 10 验证 ③④）：
   - `uv run uvicorn agentic_search.main:app --reload --port 8000`
   - `httpx.stream("POST", "/api/query", json={...}, timeout=60)` 逐行打印，确认：文字 `data:` 行（JSON 编码、含转义）、`event: tool` 行（工具名**带引号**）均按预期到达。
   - 用 doc 03 的前端 `askQuestion`（peer 适配后版本）实跑一次，确认中文正常显示、工具状态行显示 `🔧 调用工具：search_papers`（不带引号，`JSON.parse` 之后）——**这一步同时验证与 doc 03 的契约一致性**。
4. **回归**：`uv run pytest tests/ -v` 全绿（`test_query_validation` 验 422 不受影响）。

## 6. 风险与边界

- **中文转义的观感**：raw 调试输出里文字变 `\uXXXX`、工具名带引号，可能让调试者疑惑。属正常 JSON 行为，前端 `JSON.parse` 还原；第 10 步注释会点明，作为「JSON 序列化」的教学点而非缺陷。
- **契约演进需 peer 同步**：A 让工具名带引号，doc 03 peer 现有解析器需加 `JSON.parse`。已纳入 §4.4 协调流程；这是后端作锚点的预期成本，不是缺陷。
- **`EventSourceResponse` 用法陷阱**：必须用「异步生成器 + `response_class=`」模式，不能 `return EventSourceResponse(gen)`。这是已验证的运行时事实，文档代码块按此形态书写。
- **不引入 `raw_data=`**：本设计明确不用 `raw_data=`（理由见 §3.2），文档说明段会点明 `raw_data=` 的真实用途（哨兵值/日志行），避免学生误把工具名塞进去。
