# 设计：模块 02 §8.1 SSE 改用 `fastapi.sse.ServerSentEvent`

- 日期：2026-08-07
- 范围：仅 `任务文档/02-LangGraph-Agent.md`（文档）+ `backend/src/agentic_search/api/routes.py`（参考实现）
- 不在范围内：`任务文档/03-HTML前端.md`（另一个 omp agent 负责，已提交 e04d4e8）

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

**官方文档对方案 B 的背书**：FastAPI 官方 SSE 教程的 POST 示例里直接用 `ServerSentEvent(raw_data="[DONE]", event="done")` 传哨兵值——与本设计的 `ServerSentEvent(event="tool", raw_data=tc["name"])`（工具名作标识符走 `raw_data=`）是同一个模式。

`ServerSentEvent` 字段（源码：`fastapi/sse.py`，Pydantic 模型）：

| 字段 | 语义 | 线材格式（端到端 TestClient 实测） |
|---|---|---|
| `data=` | **总**做 JSON 序列化（`json.dumps(jsonable_encoder(x))`，源码 `fastapi/routing.py`，**无** `ensure_ascii=False`）。字符串会被加引号，非 ASCII 转义为 `\uXXXX`。 | `ServerSentEvent(data="你好")` → `data: "\u4f60\u597d"` |
| `raw_data=` | 把字符串**原样**放进 `data:` 字段，不加引号、不转义。文档原话：「用于非 JSON 负载（HTML 片段、CSV 行等）」。与 `data=` 互斥。 | `ServerSentEvent(event="tool", raw_data="search_papers")` → `event: tool\ndata: search_papers` |
| `event=` | 事件类型名 → `event:` 行。 | `event: tool` |
| `id=` / `retry=` / `comment=` | 本端点不使用。 | — |

实测线材格式（TestClient `POST`，`response_class=EventSourceResponse`）：

```
data: "\u4f60\u597d"          ← ServerSentEvent(data="你好")：转义、加引号

event: tool
data: "search_papers"         ← ServerSentEvent(event="tool", data="search_papers")：加引号

event: tool
data: read_paper              ← ServerSentEvent(event="tool", raw_data="read_paper")：原样、不加引号
```

`Content-Type: text/event-stream; charset=utf-8`，`status: 200`。

## 3. 决策：方案 B（`data=` 用于文字，`raw_data=` 用于工具名）

### 3.1 方案对比

- **方案 A（`data=` 一统天下）**：文字与工具名都用 `data=`。最「统一」，但工具名会被加引号（`data: "search_papers"`）。
- **方案 B（按字段语义分别用，推荐）**：文字 token 用 `data=`（需要 JSON 编码以安全承载多行/特殊字符），工具名用 `raw_data=`（工具名是简单标识符，天然是非 JSON 的原始字符串）。
- **方案 C（维持现状）**：不改。文档与代码继续手写 SSE 帧，与现代 FastAPI 惯用法脱节。

### 3.2 选 B 的四条理由

1. **`raw_data=` 是为这种场景设计的字段**——文档明确写「用于非 JSON 负载」。工具名是标识符，不是 JSON 值；用 `raw_data=` 正是它的设计意图，不是 hack。方案 B 同样是「全面改用 `ServerSentEvent`」（每个事件都是 `ServerSentEvent` 对象），只是按字段语义选用，而非把所有东西塞进 `data=`。
2. **零跨文档冲突**：另一个 omp agent 刚提交（`e04d4e8`）的 `03-HTML前端.md` SSE 解析器（L745-751）对工具行用原始字符串、对文字行做 `JSON.parse`。方案 B 的线材格式与当前**逐字节一致**（工具事件不变，文字事件从字面 `你好` 变为 `\u4f60\u597d`，但 `JSON.parse('"\u4f60\u597d"')` 正确还原为 `你好`）。用户明确要求「别和另一个 agent 搞冲突」——方案 B 让 doc 03 **零改动**。方案 A 会让工具名带引号，破坏 doc 03 的工具显示，需要对方返工。
3. **教学价值更高**：B 在一处同时教 `data=`（JSON 序列化）与 `raw_data=`（原始字符串）两个字段，且让学生看到「工具名 vs 文字 token」两种负载性质如何映射到两个字段——比 A 的「一律 `data=`」信息密度更高。
4. **不只是风格升级，是真增益**：`EventSourceResponse` 开箱即用提供保活 ping / 防缓存 / 防代理缓冲（见 §2）。当前手写 `StreamingResponse` 没有这些——一旦上线到有 Nginx 或带超时的反代后面，流式体验可能被缓冲破坏。这次升级顺带把这点也修了。

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
                        yield ServerSentEvent(event="tool", raw_data=tc["name"])
    except Exception as e:
        yield ServerSentEvent(data=f"[错误：{e}]")
```

### 4.2 `任务文档/02-LangGraph-Agent.md`（6 处触点）

| # | 位置（行号近似） | 当前 | 改为 |
|---|---|---|---|
| 1 | §8.1 代码块（L535-557） | `StreamingResponse` + f-string | 上面的 `EventSourceResponse` + `ServerSentEvent` 版本 |
| 2 | §8.1 说明段（L559-561）「本项目用两种事件…工具名无需 JSON 包裹」 | 描述手写帧 + 「工具名无需 JSON」 | 改述：`ServerSentEvent.data=` **总**做 JSON 序列化（字符串加引号、非 ASCII 转义 `\uXXXX`，保证多行/特殊字符安全传输，前端 `JSON.parse` 还原）；`raw_data=` 把字符串原样放进 `data:`（工具名是标识符，走 `raw_data=`）。点明「前端对 `data:` 一律 `JSON.parse`；工具名走 `raw_data=` 因此前端直接用」 |
| 3 | §8.1 末尾 📖 链接（L697） | 链向 StreamingResponse 文档 | 链向 FastAPI 官方 SSE 教程 `https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/`（已确认存在，含 `EventSourceResponse`/`ServerSentEvent`/`raw_data` 三节，正是本项目所用的 API） |
| 4 | 第 10 步验证 ③④ 注释 + 验证标准（L776-777, L803） | 「`data: "..."` 行就是文字 token…`event: tool` 行是工具调用」 | 注明 raw 输出里文字现为 `\uXXXX` 转义（前端 `JSON.parse` 后正常显示中文），工具行格式不变。**验证命令本身不改**（仍 `httpx.stream` + `iter_lines`） |
| 5 | 完成检查（L881） | 「文字 token 逐个到达（`data: "..."` 行）」 | 同步：`data:` 行为 JSON 编码（含转义），`event: tool` 行为工具调用 |
| 6 | 技术概念 SSE 段（L54）末句「第 8 步的 `/api/query` 端点用 FastAPI 的 `StreamingResponse` 返回 `text/event-stream`」 | 提到 `StreamingResponse` | 改为 `EventSourceResponse` + `ServerSentEvent`，点明这是 FastAPI 的 SSE 原语（结构化事件对象，替代手写帧） |

> 技术概念段对 SSE 线材格式（`event:`/`data:`/`\n\n`）的讲解**保留**——学生仍需理解协议本身；改动只是把「手写帧」换成「`ServerSentEvent` 对象被框架序列化成同样的帧」。

### 4.3 不动的部分

- `main.py`：`app.include_router(router)` 不受影响，无需改动。
- `任务文档/03-HTML前端.md`：方案 B 下线材格式兼容，**零改动**（已核对 L745-751 解析器）。
- 模块 1、4 的文档：与 SSE 无关。
- pyproject.toml：`fastapi>=0.141.1` 已满足，无需动。

## 5. 验证计划

1. **静态**：改后 `routes.py` 用 `uv run python -c "import agentic_search.api.routes"` 无报错；Pylance 无新增告警。
2. **单元**（TestClient，不启动真服务）：构造一个 yield 两个 `ServerSentEvent`（文字 + 工具）的最小端点，断言 raw body 含 `data: "\u` 与 `event: tool\ndata: search_papers`（不带引号）。
3. **端到端**（启动真服务，步骤 10 验证 ③④）：
   - `uv run uvicorn agentic_search.main:app --reload --port 8000`
   - `httpx.stream("POST", "/api/query", json={...}, timeout=60)` 逐行打印，确认：文字 `data:` 行（JSON 编码、含转义）、`event: tool` 行（工具名不带引号）均按预期到达。
   - 用 doc 03 的前端 `askQuestion` 实跑一次，确认中文正常显示、工具状态行显示 `🔧 调用工具：search_papers`（不带引号）——**这一步同时验证与 doc 03 的兼容性**。
4. **回归**：`uv run pytest tests/ -v` 全绿（`test_query_validation` 验 422 不受影响）。

## 6. 风险与边界

- **中文转义的观感**：raw 调试输出里文字变成 `\uXXXX`，可能让调试者疑惑。属正常 JSON 行为，前端 `JSON.parse` 还原；第 10 步注释会点明，作为「JSON 序列化」的教学点而非缺陷。
- **不引入 `raw_data=` 的误用**：仅工具名用 `raw_data=`；文字 token 必须用 `data=`（否则丢掉 JSON 编码，多行文字会撕裂 SSE 帧）——文档说明段会强调这一约束。
- **`EventSourceResponse` 用法陷阱**：必须用「异步生成器 + `response_class=`」模式，不能 `return EventSourceResponse(gen)`。这是已验证的运行时事实，文档代码块按此形态书写。
