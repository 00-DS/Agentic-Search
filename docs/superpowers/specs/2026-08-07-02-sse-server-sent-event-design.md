# 设计：模块 02 §8.1 SSE 改用 `fastapi.sse.ServerSentEvent`

- 日期：2026-08-07
- 锚点：**`任务文档/02-LangGraph-Agent.md` 是后端 SSE 契约的权威来源**。前端（doc 03）依后端契约实现，不反向。
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
yield f"event: tool\ndata: {tc['name']}\n\n"                            # 工具调用（工具名作裸字符串）
```

两个问题：① 用过时的手写 SSE 帧，FastAPI 0.141.1 已提供 `fastapi.sse` 原语（`ServerSentEvent` + `EventSourceResponse`）；② 工具调用事件把工具名当作**裸字符串**塞进 `data:`——这与 LLM streaming 的业界标准协议（Vercel AI SDK / OpenAI / LangChain，见 §3.2 证据）不符，业界统一用**结构化 JSON 对象**传工具调用。

## 2. 关键技术事实（均已运行时验证）

### 2.1 `EventSourceResponse` 用法（源码：`fastapi/sse.py`）

- `EventSourceResponse` 是 `StreamingResponse` 的薄子类，`media_type = "text/event-stream"`，docstring 原文：「serves mainly as a marker and sets the correct `Content-Type`」。
- **正确用法是「路径操作函数本身声明为异步生成器 + `response_class=EventSourceResponse`」**，直接 `yield ServerSentEvent(...)`——不是在函数体里 `return EventSourceResponse(...)`（那样路由返回的是协程而非可迭代对象，触发 `TypeError: 'coroutine' object is not iterable`，已实测复现）。
- `EventSourceResponse` 不需要显式传 `media_type`（子类已设）。
- **开箱即用的 SSE 最佳实践**（官方教程「技术细节」节）：15 秒无消息自动发保活 `:` 注释 ping（防代理超时）、自动设 `Cache-Control: no-cache`（防缓存）、自动设 `X-Accel-Buffering: no`（防 Nginx 缓冲）。当前手写 `StreamingResponse` 无这些。

### 2.2 `ServerSentEvent` 字段（源码：`fastapi/sse.py`，Pydantic 模型）

| 字段 | 语义 | 线材格式（端到端 TestClient 实测） |
|---|---|---|
| `data=` | **总**做 JSON 序列化（`json.dumps(jsonable_encoder(x))`，源码 `fastapi/routing.py:_serialize_sse_item`，**无** `ensure_ascii=False`）。docstring 原文：「**All `data` values including plain strings are JSON-serialized**」「you can pass any JSON-serializable value, including Pydantic models」。字符串加引号、非 ASCII 转义 `\uXXXX`、dict/对象成 JSON 对象。 | `data="你好"` → `data: "\u4f60\u597d"`；`data={"name":"x"}` → `data: {"name": "x"}` |
| `raw_data=` | 把字符串**原样**放进 `data:`，不编码。官方教程**原文限定三类用途**：「发送不进行 JSON 编码的数据……预格式化文本、日志行、特殊『哨兵』值（如 `[DONE]`）」。与 `data=` 互斥。**本设计不使用**（工具名不属于这三类，见 §3.2）。 | `raw_data="[DONE]"` → `data: [DONE]` |
| `event=` | 事件类型名 → `event:` 行。 | `event: tool` |
| `id=` / `retry=` / `comment=` | 本端点不使用。 | — |

`_serialize_sse_item` 源码注释原话：`# For ServerSentEvent items we skip stream_item_field validation (the user may mix types intentionally)` —— 混用 `data=`/`raw_data=` 在运行时允许，但官方按字段语义区分类别。

### 2.3 A-struct 实测线材格式（本设计的契约，TestClient 端到端）

```
data: "\u4f60\u597d"                          ← ServerSentEvent(data="你好")（文字 token）

event: tool
data: {"name": "search_papers"}               ← ServerSentEvent(event="tool", data={"name": ...}）（工具调用）
```

`Content-Type: text/event-stream; charset=utf-8`，`status: 200`。raw 字节实测：`b'data: "\\u4f60\\u597d"\n\nevent: tool\ndata: {"name": "search_papers"}\n\n'`。

## 3. 决策：方案 A-struct（工具调用作为结构化 JSON 对象，统一走 `data=`）

### 3.1 方案对比

- **方案 A-struct（选定）**：文字 token 用 `data=chunk.content`（字符串，JSON 编码）；工具调用用 `data={"name": tc["name"]}`（dict，JSON 编码成对象）。所有事件统一走 `data=`，前端对任意 `data:` 行一律 `JSON.parse`。
- **方案 A-lite（`data=tc["name"]` 字符串）**：方向对（FastAPI 主路径 + JSON），但工具事件只是带引号字符串，不是业界标准的结构化对象。
- **方案 B（`raw_data=tc["name"]`）**：工具名作原始字符串。被 FastAPI 官方对 `raw_data=` 的限定用途 + 三路业界证据否定（见 §3.2），弃。
- **方案 C（维持现状）**：手写帧 + 裸字符串工具名。过时且非标准。

### 3.2 选 A-struct 的证据

**FastAPI 官方立场**（直接证据）：
- `ServerSentEvent` docstring：「`data=` 总做 JSON 序列化，可传任何 JSON 可序列化值，包括 Pydantic 模型/dict」→ dict 是 `data=` 的一等用法。
- 官方教程把 `raw_data=` 限定为「预格式化文本/日志行/哨兵值（`[DONE]`）」。工具名不属于这三类 → 不该走 `raw_data=`（否 B）。

**业界 LLM-streaming 协议立场**（三路 source-verified，librarian `history://ToolCallWireFormat`）——「工具调用事件」在 wire 上**全部作为结构化 JSON 对象**，无一用裸字符串：

| 来源 | 工具调用事件的 wire 格式 | 工具名位置 |
|---|---|---|
| Vercel AI SDK v3 | `data: {"type":"tool-input-available","toolName":"getWeather","input":{...}}` | JSON `toolName` 字段 |
| OpenAI streaming tool_calls | `data: {...,"delta":{"tool_calls":[{"function":{"name":"get_weather",...}}]}}` | 嵌套 JSON `function.name` |
| LangChain astream_events v2 | 事件 dict 的 `name` 字段 + `data.input`/`data.output` | JSON `name` 字段 |

三者唯一的原始字符串用法都是流终止哨兵 `data: [DONE]`（恰好对应 `raw_data=` 用途）。librarian 原话：本项目当前「工具名作裸字符串」是「非标准异类，三个权威来源全部反对」。

**结论**：A-struct 是 FastAPI 官方主路径（`data=` dict）+ 业界标准（工具调用结构化对象）的交集，即真正的「官方规范方式」。本设计采用最小但正确的结构化形态 `{"name": tc["name"]}`——暂不传 `args`/`toolCallId`（流式 args 增量拼接超 doc 02 教学范围），但 dict 结构为未来加这些字段留了自然扩展点，不是 YAGNI。

## 4. 改动清单

### 4.1 `backend/src/agentic_search/api/routes.py`（参考实现）

- 删除 `import json`、`from fastapi.responses import StreamingResponse`。
- 新增 `from fastapi.sse import EventSourceResponse, ServerSentEvent`。
- `query` 端点：路由函数本身改为异步生成器，签名加 `response_class=EventSourceResponse`，去掉内层 `event_stream()` 闭包，`yield ServerSentEvent(...)`。

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
                        yield ServerSentEvent(event="tool", data={"name": tc["name"]})
    except Exception as e:
        yield ServerSentEvent(data=f"[错误：{e}]")
```

### 4.2 `任务文档/02-LangGraph-Agent.md`（6 处触点）

| # | 位置（行号近似） | 当前 | 改为 |
|---|---|---|---|
| 1 | §8.1 代码块（L535-557） | `StreamingResponse` + f-string（工具名裸字符串） | 上面的 `EventSourceResponse` + `ServerSentEvent`（工具调用 `data={"name": ...}` 结构化对象）版本 |
| 2 | §8.1 说明段（L559-561）「本项目用两种事件…工具名无需 JSON 包裹」 | 描述手写帧 + 「工具名无需 JSON」 | 改述：`ServerSentEvent.data=` **总**做 JSON 序列化（字符串加引号、非 ASCII 转义 `\uXXXX`、dict 成 JSON 对象）；**两类事件统一走 `data=`**：文字 token 传字符串、工具调用传 `{"name": ...}` 结构化对象（对齐 Vercel/OpenAI/LangChain 把工具调用作结构化对象的惯例）。前端对任意 `data:` 行一律 `JSON.parse`（文字得字符串、工具事件得对象取 `.name`） |
| 3 | §8.1 末尾 📖 链接（L697） | 链向 StreamingResponse 文档 | 链向 FastAPI 官方 SSE 教程 `https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/`（已确认存在，含 `EventSourceResponse`/`ServerSentEvent`/`raw_data` 三节） |
| 4 | 第 10 步验证 ③④ 注释 + 验证标准（L776-777, L803） | 「`data: "..."` 行就是文字 token…`event: tool` 行是工具调用」 | 注明 raw 输出：文字为 `data: "\uXXXX"`（JSON 编码）、工具为 `event: tool\ndata: {"name": "..."}`（结构化 JSON 对象）。**验证命令本身不改**（仍 `httpx.stream` + `iter_lines`） |
| 5 | 完成检查（L881） | 「文字 token 逐个到达（`data: "..."` 行）」 | 同步：`data:` 统一为 JSON（文字含转义、工具为 `{"name":...}` 对象），`event: tool` 标记工具调用 |
| 6 | 技术概念 SSE 段（L54）末句「…用 FastAPI 的 `StreamingResponse` 返回 `text/event-stream`」 | 提到 `StreamingResponse` | 改为 `EventSourceResponse` + `ServerSentEvent`，点明这是 FastAPI 的 SSE 原语（结构化事件对象，替代手写帧） |

> 技术概念段对 SSE 线材格式（`event:`/`data:`/`\n\n`）的讲解**保留**——学生仍需理解协议本身；改动只是把「手写帧」换成「`ServerSentEvent` 对象被框架序列化成同样的帧」。

### 4.3 不动的部分

- `main.py`：`app.include_router(router)` 不受影响，无需改动。
- `任务文档/03-HTML前端.md`：**本会话不改文件**（避免与 peer 文件编辑冲突）。契约适配由 peer 完成（见 §4.4）。
- 模块 1、4 的文档：与 SSE 无关。
- pyproject.toml：`fastapi>=0.141.1` 已满足，无需动。

### 4.4 doc 03 peer 协调（通过 Orca，不改文件）

负责 doc 03 的 omp agent（终端 `term_1d1d12c4-94c8-47f3-8b2f-dc43f6c76ec2`）刚提交 `e04d4e8`，其 `askQuestion` 解析器（L745-751）当前：工具分支用原始 `dataLine`（不 `JSON.parse`）、文字分支 `JSON.parse(dataLine)`。

A-struct 新契约要求**前端对任意 `data:` 行一律 `JSON.parse`**：文字得字符串、工具事件得对象。doc 03 工具分支需调整为：`const tool = JSON.parse(dataLine); status.textContent = 🔧 调用工具：${tool.name}`（或工具/文字合并成统一先 parse 再按 `eventType` 分支取值）。将通过 Orca `terminal send` 向该终端发简短契约说明，内容：
- 后端 `/api/query` 已改用 `ServerSentEvent`（`response_class=EventSourceResponse`）。
- **所有 `data:` 字段均为 JSON 编码**：文字 `data: "\u4f60\u597d"`、工具 `event: tool\ndata: {"name": "search_papers"}`（结构化对象）。
- 前端：对任意 `data:` 行一律 `JSON.parse`；工具事件 parse 后取 `.name`。doc 03 工具分支需相应调整。

## 5. 验证计划

1. **静态**：改后 `routes.py` 用 `uv run python -c "import agentic_search.api.routes"` 无报错；Pylance 无新增告警。
2. **单元**（TestClient，不启动真服务）：构造一个 yield 文字 token + 工具调用 `ServerSentEvent` 的最小端点，断言 raw body 含 `data: "\u`（文字转义）与 `event: tool\ndata: {"name": "search_papers"}`（结构化对象）。**此断言已实测通过**（见 §2.3）。
3. **端到端**（启动真服务，步骤 10 验证 ③④）：
   - `uv run uvicorn agentic_search.main:app --reload --port 8000`
   - `httpx.stream("POST", "/api/query", json={...}, timeout=60)` 逐行打印，确认：文字 `data:` 行（JSON 编码含转义）、`event: tool` 行（`data: {"name": ...}` 结构化对象）均按预期到达。
   - 用 doc 03 前端 `askQuestion`（peer 适配后版本）实跑一次，确认中文正常显示、工具状态行显示 `🔧 调用工具：search_papers`——**同时验证与 doc 03 契约一致**。
4. **回归**：`uv run pytest tests/ -v` 全绿（`test_query_validation` 验 422 不受影响）。

## 6. 风险与边界

- **中文转义 + 结构化对象的观感**：raw 调试输出里文字是 `\uXXXX`、工具是 `{"name": "..."}` 对象，与「裸文字」观感不同。属正常 JSON 行为，前端 `JSON.parse` 还原；第 10 步注释会点明，作为「SSE 传结构化数据」的教学点。
- **契约演进需 peer 同步**：A-struct 把工具事件从裸字符串升级为结构化对象，doc 03 peer 现有解析器需 `JSON.parse` 后取 `.name`。已纳入 §4.4 协调流程；这是后端作锚点的预期成本。
- **`EventSourceResponse` 用法陷阱**：必须用「异步生成器 + `response_class=`」模式，不能 `return EventSourceResponse(gen)`。已验证的运行时事实，文档代码块按此形态书写。
- **不引入 `raw_data=`**：本设计明确不用 `raw_data=`（理由见 §3.2），文档说明段会点明 `raw_data=` 的真实用途（哨兵值/日志行），避免学生误把工具名塞进去。
- **暂不传 `args`/`toolCallId`**：doc 02 的工具事件只用于前端显示工具名状态行，`{"name": ...}` 是最小正确结构；流式 args 增量拼接超 doc 02 范围（属后续增强，dict 结构已为此留扩展点）。
