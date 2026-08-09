# §8.1 SSE 改用 `fastapi.sse.ServerSentEvent` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把模块 02 §8.1 的 `/api/query` SSE 端点从「`StreamingResponse` + 手写 f-string 帧」升级到 FastAPI 官方 SSE 原语（`EventSourceResponse` + `ServerSentEvent`），并把工具调用事件从「裸字符串」改为「结构化 JSON 对象」，对齐 Vercel/OpenAI/LangChain 业界惯例。

**Architecture:** 路由函数本身改为异步生成器、加 `response_class=EventSourceResponse`，直接 `yield ServerSentEvent(...)`。文字 token 走 `data=chunk.content`（字符串，JSON 编码），工具调用走 `data={"name": ...}`（dict，JSON 编码成对象），`raw_data=` 不用（仅留给 `[DONE]` 哨兵）。所有技术事实已 TestClient 端到端实测。

**Tech Stack:** FastAPI 0.141.1（`fastapi.sse`）· LangGraph `astream` · pytest + TestClient

**Spec:** `docs/superpowers/specs/2026-08-07-02-sse-server-sent-event-design.md`

## Global Constraints

- 所有 `uv` 命令从 `backend/` 目录运行（venv 在那）。Python `>=3.12`。
- FastAPI 版本 `>=0.141.1`（`pyproject.toml` 已锁定，`fastapi.sse` 可用，无需改依赖）。
- 数据契约全局字段名 `doc_id` / `filename`（本计划不动这些，仅 SSE）。
- API 验证用 `uv run python -c '...'` + httpx，**不用 curl**（PowerShell 三个坑）。
- `main.py` 不动（`app.include_router(router)` 与 SSE 无关）。
- **doc 03 文件本会话不改**（另一个 omp agent 负责，避免编辑冲突；契约适配通过 Orca 通知，见 Task 4）。

## File Structure

- `backend/src/agentic_search/api/routes.py` — 改：`query` 端点换 `EventSourceResponse`/`ServerSentEvent`，删 `json`/`StreamingResponse` import。其余 3 个端点不动。
- `backend/tests/test_api.py` — 改：新增 SSE wire-format 测试（断言文字转义 + 工具调用结构化对象）。
- `任务文档/02-LangGraph-Agent.md` — 改：6 处触点（§8.1 代码 + 说明、📖 链接、第 10 步验证注释/标准、完成检查、技术概念 SSE 段）。
- `backend/src/agentic_search/main.py` — 不动。

---

## Task 1: routes.py — query 端点换 SSE 原语（TDD）

**Files:**
- Modify: `backend/src/agentic_search/api/routes.py`（`query` 端点 L21-41 + import L1-6）
- Test: `backend/tests/test_api.py`（追加 SSE wire-format 测试）

**Interfaces:**
- Consumes: `graph.astream(..., stream_mode="messages")`（LangGraph，不变）；`AIMessageChunk`/`HumanMessage`（不变）。
- Produces: `POST /api/query` 现返回 `EventSourceResponse`，wire 格式：
  - 文字 token：`data: "\u4f60\u597d"`（JSON 编码，中文 ASCII 转义）
  - 工具调用：`event: tool\ndata: {"name": "search_papers"}`（结构化 JSON 对象）
  - 错误：`data: "[错误：...]"`
  - Content-Type: `text/event-stream; charset=utf-8`

- [ ] **Step 1: 写失败测试（SSE wire 格式断言）**

追加到 `backend/tests/test_api.py`（文件末尾，现有 `client = TestClient(app)` 在顶部复用）：

```python
def test_query_sse_wire_format():
    """query 端点应返回 SSE 流：文字 token JSON 编码（带转义）、工具调用为结构化 JSON 对象。

    直接测 astream 不可行（依赖真 LLM），改用一个最小 stub app 验证 wire 序列化——
    确保 routes.py 用的是 ServerSentEvent(data=...) / data={"name":...} 模式，
    而非旧的手写 f-string 帧。
    """
    from fastapi import FastAPI
    from fastapi.sse import EventSourceResponse, ServerSentEvent
    from fastapi.testclient import TestClient as _TC

    stub = FastAPI()

    @stub.post("/query", response_class=EventSourceResponse)
    async def q():
        yield ServerSentEvent(data="你好")
        yield ServerSentEvent(event="tool", data={"name": "search_papers"})

    resp = _TC(stub).post("/query")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    # 文字 token：JSON 编码、中文 ASCII 转义
    assert 'data: "\\u4f60\\u597d"' in body
    # 工具调用：结构化 JSON 对象（不是裸字符串）
    assert 'event: tool\ndata: {"name": "search_papers"}' in body
    # 不应是旧的裸字符串格式
    assert "data: search_papers" not in body
```

> 注意：此测试用 stub app（避免真 LLM），但它复刻 routes.py 必须采用的模式。routes.py 若仍用手写 f-string，`import` 与结构都对不上，靠 Task 1 Step 3 的源码审查保证 routes.py 实际走 `ServerSentEvent`。

- [ ] **Step 2: 运行测试，确认 stub 测试通过（验证我们对 wire 格式的断言本身正确）**

Run: `cd backend && uv run pytest tests/test_api.py::test_query_sse_wire_format -v`
Expected: PASS（stub 用 `ServerSentEvent` 正确产出目标 wire 格式）。若 FAIL，先修正对 wire 格式的断言期望——这是后续改 routes.py 的基准。

- [ ] **Step 3: 改 routes.py 的 import**

`backend/src/agentic_search/api/routes.py` 当前 L1-6：

```python
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk, HumanMessage
```

改为（删 `import json` 与 `StreamingResponse`，加 `fastapi.sse`）：

```python
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import AIMessageChunk, HumanMessage
```

- [ ] **Step 4: 改 query 端点为异步生成器 + `ServerSentEvent`**

当前 L21-41（`query` 函数整体，含内层 `event_stream()` 闭包与 `return StreamingResponse(...)`）替换为：

```python
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

关键变化：① 路由本身是异步生成器（不再有内层 `event_stream` 闭包）；② `response_class=EventSourceResponse`；③ 不再 `return EventSourceResponse(...)`（那会触发 `TypeError: 'coroutine' object is not iterable`）；④ 工具调用 `data={"name": ...}`（dict，结构化对象），不是 `raw_data=` 也不是 `data=tc["name"]`（裸字符串）。

- [ ] **Step 5: 静态验证 import 无误**

Run: `cd backend && uv run python -c "import agentic_search.api.routes; print('ok')"`
Expected: 打印 `ok`，无报错。若报 `ImportError`，检查 `fastapi.sse` 路径（已确认 0.141.1 可用）。

- [ ] **Step 6: 运行 API 回归测试（422 校验不受影响）**

Run: `cd backend && uv run pytest tests/test_api.py -v`
Expected: `test_documents_endpoint`、`test_query_validation`、`test_query_sse_wire_format` 全 PASS。`test_query_validation` 仍应 422（缺 `question`）。注意：`test_documents_endpoint`/`test_query_validation` 连真 MongoDB，若本地无 `mongod`，这两个会 FAIL 属环境问题，**只要 `test_query_sse_wire_format` PASS + import 无误即视为 Task 1 通过**。

- [ ] **Step 7: 提交**

```bash
cd "D:/Python/Common/Agentic Search"
git add backend/src/agentic_search/api/routes.py backend/tests/test_api.py
git commit -m "refactor(02): query 端点改用 fastapi.sse.ServerSentEvent

文字 token 走 data=（JSON 编码、中文 ASCII 转义），工具调用走
data={\"name\":...}（结构化 JSON 对象，对齐 Vercel/OpenAI/LangChain）。
删 StreamingResponse + 手写 SSE f-string。wire 格式 TestClient 验证通过。"
```

---

## Task 2: 端到端实跑验证（真服务）

**Files:** 无文件改动（仅运行验证）

**Interfaces:** 消费 Task 1 产出的新 query 端点。

> 依赖外部服务（`mongod` 运行 + `LLM_API_KEY` 在 `backend/.env`）。若环境不具备，记为阻塞，跳过但标注——Task 1 的 stub 测试已覆盖 wire 格式核心。

- [ ] **Step 1: 启动后端**

Run: `cd backend && uv run uvicorn agentic_search.main:app --reload --port 8000`
Expected: uvicorn 正常监听，无启动报错（确认 `EventSourceResponse` 作为 `response_class` 被 FastAPI 接受）。

- [ ] **Step 2: 流式提问，肉眼核对 wire 格式**

新开终端，Run（不要 curl）：

```bash
cd backend
uv run python -c '
import httpx
with httpx.stream("POST", "http://localhost:8000/api/query", json={"question": "TiMem的核心方法是什么？"}, timeout=60) as r:
    for line in r.iter_lines():
        if line:
            print(line)
'
```

Expected（核对三点）：
- 文字行形如 `data: "\uXXXX..."`（JSON 编码、中文转义）——不是旧的 `data: TiMem...` 裸文字。
- 工具行形如 `event: tool` 紧跟 `data: {"name": "search_papers"}`——工具名是结构化对象，不是裸字符串。
- `Content-Type` 是 `text/event-stream`（用 `print(r.headers.get("content-type"))` 可查）。

agent 多轮调工具 + 最终纯文字回答均按预期到达即通过。`Ctrl+C` 中断。

- [ ] **Step 3: 若 Step 1-2 跑通，无需额外提交**（验证不产 commit）。若环境不具备，跳过本 Task 并在交付说明里注明「端到端验证因缺 mongod/LLM key 未跑，wire 格式由 stub 测试保证」。

---

## Task 3: doc 02 文档同步（6 处触点）

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`（L54、L535-561、L697、L776-777、L803、L881）

**Interfaces:** 文档与 Task 1 的代码保持一致（code is truth，doc 反映 code）。

> 文档政策（项目约定）：只写「为什么这样」，禁用「不使用 XXX」否定措辞。

- [ ] **Step 1: 技术概念 SSE 段（L54）—— 末句 StreamingResponse → EventSourceResponse**

L54 当前末句：`第 8 步的 `/api/query` 端点用 FastAPI 的 `StreamingResponse` 返回 `text/event-stream` 格式的 SSE 流。`

改为：`第 8 步的 `/api/query` 端点用 FastAPI 的 `ServerSentEvent` 事件对象（经 `EventSourceResponse` 按序返回）产出 `text/event-stream` 格式的 SSE 流——`ServerSentEvent` 是 FastAPI 的 SSE 原语，把每个事件封装成结构化对象，由框架序列化成 wire 帧，替代手写字符串拼接。`

（该段前半对 `event:`/`data:`/`\n\n` 协议本身的讲解保留不动。）

- [ ] **Step 2: §8.1 代码块（L535-557）—— 换成 ServerSentEvent 版本**

把整个代码块（从 ```` ```python ```` 到对应 ```` ``` ````，即 L535-557）替换为与 Task 1 Step 4 完全一致的代码（路由生成器 + `EventSourceResponse` + `ServerSentEvent`，工具调用 `data={"name": tc["name"]}`）。代码内容直接复制 Task 1 Step 4 的最终代码块。

- [ ] **Step 3: §8.1 说明段（L561）—— 重写「两种事件」描述**

L561 当前：「本项目用两种事件：文字 token 是默认事件（`data: "你"\n\n`），数据是 JSON 字符串值——`json.dumps` 转义了文字中的换行，防止 SSE 帧被撕裂；工具调用用命名事件（`event: tool\ndata: search_papers\n\n`），工具名是简单标识符，无需 JSON 包裹。流结束时后端关闭连接，前端 `reader.read()` 收到 `done: true` 即知结束——不需要单独的结束事件。」

改为：

> 本项目用两类事件，都经 `ServerSentEvent` 的 `data=` 字段产出，框架统一做 JSON 序列化（字符串加引号、非 ASCII 字符转义为 `\uXXXX`、dict 编码成 JSON 对象）。这保证了多行文字、特殊字符安全传输——SSE 帧不会被换行撕裂。文字 token 是默认事件（`data: "\u4f60\u597d"`）；工具调用是命名事件（`event: tool`），`data` 是结构化对象 `{"name": "search_papers"}`——把工具名放在对象字段里，对齐 Vercel AI SDK、OpenAI streaming、LangChain 把工具调用作为结构化 JSON 对象传输的惯例（这些协议唯一的原始字符串用法是流终止哨兵 `data: [DONE]`，对应 `ServerSentEvent` 的另一个字段 `raw_data=`，本端点用不到）。
>
> 前端的处理规则因此很统一：对任意 `data:` 行一律 `JSON.parse`——文字事件得到字符串、工具事件得到对象、按 `event:` 是否为 `tool` 分支。流结束时后端关闭连接，前端 `reader.read()` 收到 `done: true` 即知结束——不需要单独的结束事件。

- [ ] **Step 4: 📖 链接（L697）—— 换成官方 SSE 教程**

L697 当前：`> 📖 FastAPI StreamingResponse 文档：[https://fastapi.tiangolo.com/zh/advanced/custom-response/](https://fastapi.tiangolo.com/zh/advanced/custom-response/)`

改为：`> 📖 FastAPI SSE（ServerSentEvent / EventSourceResponse）官方教程：[https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/](https://fastapi.tiangolo.com/zh/tutorial/server-sent-events/)`

- [ ] **Step 5: 第 10 步验证 ③④ 注释（L776-777）—— 更新 wire 描述**

L776-777 当前（③ 的两行注释）：

```bash
# ③ 提问（SSE 流式）——逐行读取，看到 data: 行就是文字 token、event: tool 行是工具调用
#    timeout=60 因为 agent 要多轮调用工具才回答，默认 5 秒不够
```

改为：

```bash
# ③ 提问（SSE 流式）——逐行读取：data: 行是 JSON 编码（文字形如 data: "\u4f60\u597d"），
#    event: tool 行紧跟 data: {"name":"工具名"}（结构化对象）；timeout=60 因 agent 多轮调工具，默认 5 秒不够
```

（验证命令 L778-794 本身不改——仍 `httpx.stream` + `iter_lines`。④ 的注释 L786-787 一并套用同样描述。）

- [ ] **Step 6: 验证标准（L803）—— 更新 wire 描述**

L803 当前：`- `/api/query` 返回 SSE 流：文字 token 逐个到达（`data: "..."` 行），`event: tool` 行标记工具调用；服务端终端可看到 `[retry]` 重试日志与 agent 多轮工具调用的轨迹。`

改为：`- `/api/query` 返回 SSE 流：文字 token 逐个到达（`data: "\uXXXX"` 行，JSON 编码），`event: tool` 行标记工具调用（紧跟 `data: {"name": "..."}` 结构化对象）；服务端终端可看到 `[retry]` 重试日志与 agent 多轮工具调用的轨迹。`

- [ ] **Step 7: 完成检查（L881）—— 更新 wire 描述**

L881 当前：`- [ ] `uv run python -c '...'`（httpx.stream）调用 `/api/query` 返回 SSE 流，文字 token 逐个到达（`data: "..."` 行），`event: tool` 行标记工具调用`

改为：`- [ ] `uv run python -c '...'`（httpx.stream）调用 `/api/query` 返回 SSE 流，文字 token 逐个到达（`data: "\uXXXX"` JSON 编码行），`event: tool` 行标记工具调用（`data: {"name": "..."}` 结构化对象）`

- [ ] **Step 8: 通读改动后的 §8.1 + 技术概念 SSE 段，确认无矛盾、无否定措辞**

手动复核：① §8.1 代码块与说明段描述一致；② 说明段无「不使用 raw_data」之类否定句（已用「本端点用不到」的正面陈述）；③ 技术概念段与 §8.1 用词一致（都用 `ServerSentEvent`/`EventSourceResponse`）。

- [ ] **Step 9: 提交**

```bash
cd "D:/Python/Common/Agentic Search"
git add "任务文档/02-LangGraph-Agent.md"
git commit -m "docs(02): §8.1 SSE 改用 fastapi.sse.ServerSentEvent，工具调用结构化

6 处触点同步：§8.1 代码块换 EventSourceResponse+ServerSentEvent、说明段
重写为「data= 统一 JSON 编码、工具调用结构化对象」、📖 链接改官方 SSE
教程、第10步验证/完成检查/技术概念段 wire 描述同步。"
```

---

## Task 4: 通过 Orca 通知 doc 03 peer 新 SSE 契约

**Files:** 无文件改动（仅通过 Orca 发消息给负责 doc 03 的 omp agent）

**Interfaces:** 向 peer 同步 Task 1 产出的新 wire 契约。

> peer 终端（从 `orca terminal list` 获取）：`term_1d1d12c4-94c8-47f3-8b2f-dc43f6c76ec2`。peer 刚提交 `e04d4e8`，其 `askQuestion` 工具分支（doc 03 L745-748）当前用原始 `dataLine`（不 `JSON.parse`）。新契约要求前端对任意 `data:` 行一律 `JSON.parse`。

- [ ] **Step 1: 确认 peer 终端仍活跃**

Run: `orca terminal list --worktree "232c7924-908b-4910-9c3f-70c14e933a02::D:/Python/Common/Agentic Search" --json`
确认 `term_1d1d12c4-94c8-47f3-8b2f-dc43f6c76ec2` 在列表且 `connected: true`。若已不在，用 `orca worktree ps --json` 找到当前活跃的 doc 03 omp agent 终端 handle 替代。

- [ ] **Step 2: 向 peer 终端发送契约说明**

Run（`<HANDLE>` 替换为 Step 1 的 handle）：

```bash
orca terminal send --terminal <HANDLE> --enter --text "【SSE 契约更新通知 — 来自 doc 02 side】后端 /api/query 已改用 fastapi.sse.ServerSentEvent（response_class=EventSourceResponse）。新 wire 契约：所有 data: 字段均为 JSON 编码 —— 文字 token 形如 data: \"\\u4f60\\u597d\"（中文 ASCII 转义）、工具调用是 event: tool 紧跟 data: {\"name\": \"search_papers\"}（结构化 JSON 对象，工具名在 .name 字段，不再带引号裸字符串）。前端规则：对任意 data: 行一律 JSON.parse；工具事件 parse 后取 .name 显示。doc 03 步骤 5.2 工具分支需相应把原始 dataLine 改成 JSON.parse(dataLine).name（或工具/文字合并成统一先 parse 再按 eventType 分支）。doc 02 侧已定稿，请按此契约适配 doc 03。" --json
```

Expected: 返回 `delivered: true`（或等价成功）。若 `failed`（peer 已离开），记为「peer 不可达，契约已记入 spec §4.4，后续由人工转达」。

- [ ] **Step 3: 不提交**（本 Task 不产文件改动、不产 commit；消息送达即完成）。

---

## Self-Review（写完后自查）

**1. Spec coverage：**
- spec §2 技术事实 → 由 Task 1 Step 3-4 的代码实现（`EventSourceResponse`/`ServerSentEvent`，工具 `data={"name":...}`）覆盖；stub 测试断言实测 wire。
- spec §3 决策 A-struct → Task 1 Step 4 的 `data={"name": tc["name"]}` 覆盖。
- spec §4.1 routes.py 改动 → Task 1（import + query 端点）完整覆盖。
- spec §4.2 doc 02 六触点 → Task 3 Step 1-7 一一对应（L54 / L535-557 / L561 / L697 / L776-777 / L803 / L881）。
- spec §4.3 不动部分（main.py / doc 03 文件 / pyproject）→ Global Constraints 明确。
- spec §4.4 peer 协调 → Task 4 覆盖。
- spec §5 验证计划 → Task 1 Step 6（stub 单元）+ Task 2（端到端）+ Task 1 Step 5（静态 import）覆盖。
- spec §6 风险 → 均在对应 Task 的步骤注释里点明（陷阱「不能 return EventSourceResponse」在 Task 1 Step 4；中文转义观感在 Task 3 Step 3）。
- 无遗漏。

**2. Placeholder scan：** 无 TBD/TODO；每步含具体代码或命令；`<HANDLE>` 在 Task 4 是占位符但有 Step 1 明确给出获取方法（非「稍后填」）。

**3. Type consistency：** `EventSourceResponse`、`ServerSentEvent`、`data={"name": ...}` 在 Task 1、3、4 一致；wire 格式描述（`data: "\uXXXX"` / `data: {"name": "..."}`）在 Task 1 stub 测试、Task 2 核对点、Task 3 文档、Task 4 消息四处一致。
