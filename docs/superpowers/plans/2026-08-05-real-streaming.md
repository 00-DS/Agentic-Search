# 真实流式输出重设计 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 02/03 教学文档中的假流式（`graph.invoke()` 等完再切块）改为基于 `graph.astream(stream_mode="messages")` 的真实 token 流式，采用 SSE 命名事件协议。

**Architecture:** 后端用 `graph.astream(stream_mode="messages")` 逐 token yield `AIMessageChunk`，通过 SSE 命名事件格式化（文字 token = JSON 字符串值放 `data:` 行，工具调用 = `event: tool` 行）。前端用 `fetch` + `ReadableStream.getReader()` 按 `\n\n` 切分 SSE 帧，解析 `event:`/`data:` 行。

**Tech Stack:** LangGraph `astream(stream_mode="messages")`、FastAPI `StreamingResponse`、SSE 命名事件协议、fetch + ReadableStream + TextDecoder

## Global Constraints

- **纯文档更新，不写实现代码**：所有改动只修改 `任务文档/` 下的 `.md` 文件和 `backend/src/agentic_search/api/routes.py`（教学文档的配套代码文件，文档内容即代码）。不改 `agents/graph.py`（graph 结构不变，只需 `astream` 替代 `invoke` 的调用方在 routes.py）。
- **纯新版本，零历史包袱**：不出现「旧版」「原来」「之前」「不再」「改用」「已删除」等对比性措辞。
- **数据契约**：`doc_id`/`filename`（NOT `id`/`name`）、`text` 字段名（NOT `markdown`）、`datetime.now(timezone.utc)`。
- **DeepSeek 统一**：`base_url=https://api.deepseek.com`、`model=deepseek-v4-flash`、`model_provider=openai`。
- **工具 docstring 自描述**：`@tool` 的 docstring 是 LLM 看到的 schema。
- **语气正式，不使用比喻，逻辑清晰，简洁明了**。先给结论。
- **LLM 调用参数全部从 config.py 的 settings 读取**，不硬编码。

---

### Task 1: 02 Step 8.1 后端代码——假流式改为真流式

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md` 行 491-514（import 块）+ 行 522-553（8.1 小节：代码块 + SSE 概念段）

**Interfaces:**
- Consumes: spec `docs/superpowers/specs/2026-08-05-real-streaming-design.md` 后端代码段
- Produces: 02 文档 Step 8.1 的后端代码从 `graph.invoke()` 假流式改为 `graph.astream(stream_mode="messages")` 真流式

- [ ] **Step 1: 修改 import 块（行 491-514）**

在现有 import 块中，`from langchain_core.messages import HumanMessage`（行 500）改为同时导入 `AIMessageChunk`：

```python
from langchain_core.messages import HumanMessage, AIMessageChunk
```

`import json`（行 493）保留——新代码仍用 `json.dumps`。

- [ ] **Step 2: 替换 8.1 小节的代码块（行 526-551）**

将旧的假流式代码块（行 526-551）整体替换为以下新代码块：

````markdown
```python
@router.post("/query")
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    async def event_stream():
        try:
            async for chunk, metadata in graph.astream(
                {"messages": [HumanMessage(content=req.question)]},
                stream_mode="messages"
            ):
                if not isinstance(chunk, AIMessageChunk):
                    continue                    # 跳过 ToolMessage 等非 LLM chunk
                if chunk.content:               # 文字 token
                    yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
                elif chunk.tool_call_chunks:     # LLM 决定调工具
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            yield f"event: tool\ndata: {tc['name']}\n\n"
        except Exception as e:
            yield f"data: {json.dumps(f'[错误：{e}]', ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```
````

- [ ] **Step 3: 替换 SSE 概念段（行 553）**

将旧的 SSE 概念段（行 553，一句话）替换为以下新概念段：

```markdown
SSE（Server-Sent Events）是一种服务器向浏览器单向推送数据的 HTTP 协议格式。每条事件由若干行组成：`event:` 行声明事件类型（可省略，省略时为默认事件），`data:` 行携带数据，事件之间以空行 `\n\n` 分隔。

本项目用两种事件：文字 token 是默认事件（`data: "你"\n\n`），数据是 JSON 字符串值——`json.dumps` 转义了文字中的换行，防止 SSE 帧被撕裂；工具调用用命名事件（`event: tool\ndata: search_papers\n\n`），工具名是简单标识符，无需 JSON 包裹。流结束时后端关闭连接，前端 `reader.read()` 收到 `done: true` 即知结束——不需要单独的结束事件。

**为什么用 `fetch` 而非 `EventSource` 消费 SSE？** 浏览器原生的 `EventSource` API 只支持 GET 请求，无法在请求体中发送问题内容。本项目用 POST 提交问题，因此用 `fetch` + `ReadableStream.getReader()` 手动读取并解析 SSE 帧——这正是 ChatGPT、Claude.ai 等现代 AI 产品的做法。
```

- [ ] **Step 4: 提交**

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): Step 8.1 假流式改为 graph.astream 真流式 + SSE 命名事件"
```

---

### Task 2: 02 curl 验证段 + 学习目标行更新

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md` 行 12（学习目标）+ 行 688-691（curl 示例）+ 行 703（验证清单项）+ 行 782（最终验证清单项）

**Interfaces:**
- Consumes: Task 1 的新后端代码（产出 SSE 命名事件而非 JSON 包装的假流式）
- Produces: 02 文档的验证段与新协议一致

- [ ] **Step 1: 更新学习目标第 6 项（行 12）**

行 12 当前：
```markdown
6. 用 `uv run uvicorn` 启动 API 服务，并通过 `curl` 验证 SSE 流式 agent 问答
```
保持不变——「SSE 流式」描述仍准确。

- [ ] **Step 2: 更新 curl 示例注释（行 688）**

行 688 当前注释：
```markdown
# ③ 提问（SSE 流式）—— -N 禁用缓冲，逐行看到流式输出；读哪篇论文由 agent 决定
```
替换为：
```markdown
# ③ 提问（SSE 流式）—— -N 禁用缓冲，逐 token 看到流式输出；event: tool 行标记工具调用
```

- [ ] **Step 3: 更新验证清单项（行 703）**

行 703 当前：
```markdown
- `/api/query` 返回多行 SSE 数据（`data: {...}`），含 agent 基于论文内容的回答；服务端终端可看到 `[retry]` 重试日志与 agent 多轮工具调用（`list_papers`/`search_papers`/`read_paper`）的轨迹。
```
替换为：
```markdown
- `/api/query` 返回 SSE 流：文字 token 逐个到达（`data: "..."` 行），`event: tool` 行标记工具调用；服务端终端可看到 `[retry]` 重试日志与 agent 多轮工具调用的轨迹。
```

- [ ] **Step 4: 更新最终验证清单项（行 782）**

行 782 当前：
```markdown
- [ ] `curl -N -X POST .../api/query -d '{"question":"..."}'` 返回 SSE 流，含 agent 基于论文内容的回答（服务端终端可看到多轮工具调用日志）
```
替换为：
```markdown
- [ ] `curl -N -X POST .../api/query -d '{"question":"..."}'` 返回 SSE 流，文字 token 逐个到达（非等待后一次性弹出），`event: tool` 行标记工具调用
```

- [ ] **Step 5: 提交**

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): curl 验证段对齐 SSE 命名事件协议"
```

---

### Task 3: 03 Step 5.1 新增「为什么用 fetch 而非 EventSource」

**Files:**
- Modify: `任务文档/03-HTML前端.md` 行 704-706（5.1 小节）

**Interfaces:**
- Consumes: 02 Step 8.1 的 SSE 命名事件协议（Task 1 产出）
- Produces: 03 前端文档讲解为什么用 fetch 消费 SSE

- [ ] **Step 1: 替换 5.1 小节（行 704-706）**

行 704-706 当前：
```markdown
### 5.1 为什么 fetch 能流式

`fetch` 的 `response.body` 是一个 `ReadableStream`，可以拿到一个 `reader`，**一边接收一边读**——这正是流式所需的。
```
替换为：
```markdown
### 5.1 为什么用 fetch 而非 EventSource

浏览器原生有一个 `EventSource` API 专门消费 SSE 流，但它有一个致命限制：**只支持 GET 请求**。本项目的提问接口是 POST（需要在请求体中发送问题内容），`EventSource` 用不了。

因此用 `fetch` + `ReadableStream` 手动消费 SSE 流——这正是 ChatGPT、Claude.ai 等现代 AI 产品的做法。`fetch` 的 `response.body` 是一个 `ReadableStream`，可以拿到一个 `reader`，**一边接收一边读**。区别在于：`EventSource` 自动解析 SSE 帧；用 `fetch` 时需要自己按 `\n\n` 切分帧、解析 `event:`/`data:` 行（下一步的代码）。
```

- [ ] **Step 2: 提交**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): Step 5.1 新增为什么用 fetch 而非 EventSource"
```

---

### Task 4: 03 Step 5.2 前端代码——裸 append 改为 SSE 帧解析循环

**Files:**
- Modify: `任务文档/03-HTML前端.md` 行 708-743（5.2 小节：代码块 + 逐段讲解 + MDN 链接）

**Interfaces:**
- Consumes: 02 Step 8.1 的 SSE 命名事件协议（Task 1 产出）：文字 token = `data: "..."`（JSON 字符串值），工具调用 = `event: tool\ndata: 工具名`
- Produces: 03 前端能正确解析 SSE 帧、逐字渲染、显示工具状态

- [ ] **Step 1: 替换 5.2 代码块（行 710-734）**

将旧的代码块（行 710-734）整体替换为：

````markdown
```javascript
// 这是教学示例
async function askQuestion() {
  const question = questionInput.value;
  if (!question.trim()) return;

  appendMessage("user", question);          // 先显示用户的问题
  const aiEl = appendMessage("assistant", "");// 创建空的 AI 气泡，拿引用待填充

  const res = await fetch("http://localhost:8000/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: question }),
  });

  const reader = res.body.getReader();       // 1. 拿到流的读取器
  const decoder = new TextDecoder();          // 2. 字节 → 文字的解码器
  let buf = "";                               // 3. 跨包拼接的不完整帧缓冲区

  while (true) {
    const { done, value } = await reader.read();  // 4. 读一块字节
    if (done) break;                              // 5. 连接关闭，流结束
    buf += decoder.decode(value, { stream: true }); // 6. 解码并拼入缓冲区
    const frames = buf.split("\n\n");             // 7. SSE 帧以空行分隔
    buf = frames.pop();                           // 8. 最后一段可能不完整，留到下次
    for (const frame of frames) {
      if (!frame.trim()) continue;
      let event = "token";                        // 无 event: 行 = 默认 = 文字
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5);
      }
      if (event === "token") {
        aiEl.textContent += JSON.parse(data);     // 9. JSON 字符串值 → 原始文字
      } else if (event === "tool") {
        // 10. 显示工具调用状态，如「正在调用 search_papers...」
      }
    }
  }
}
```
````

- [ ] **Step 2: 替换逐段讲解（行 736-741）**

将旧的逐段讲解（行 736-741）替换为：

```markdown
逐段讲解：
- `JSON.stringify({...})`：提问接口接收 JSON，需要先序列化成字符串，并设 `Content-Type: application/json`
- `res.body` 是 `ReadableStream`，`.getReader()` 返回一个读取器
- `decoder.decode(value, { stream: true })`：网络传输的是**字节**，需要 `TextDecoder` 转成中文字符串。`{ stream: true }` 是流式模式——中文字符的 UTF-8 编码可能被网络包边界截断，这个选项让解码器等待完整字符再返回
- `buf.split("\n\n")`：SSE 协议规定每个事件以空行 `\n\n` 结尾，按它切分出完整帧
- `buf = frames.pop()`：一个网络包可能包含半个帧、一个完整帧、或多个帧。`pop()` 取出最后一段（可能不完整），留到下次 `read()` 拼接——这是流式解析的标准技巧
- `event:` 行声明事件类型（省略时为 `token` 即文字）；`data:` 行携带数据
- `JSON.parse(data)`：后端用 `json.dumps` 转义了文字中的换行等特殊字符，这里还原。文字 token 的 `data` 是一个 JSON 字符串值（如 `"你好"`），`JSON.parse` 后得到原始文字
- `event === "tool"`：工具调用事件，`data` 是工具名（如 `search_papers`）。这里可以更新 UI 显示 agent 正在探索论文
```

- [ ] **Step 3: 保留 MDN 链接（行 743）**

行 743 的 MDN ReadableStream 链接保持不变。

- [ ] **Step 4: 提交**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): Step 5.2 裸 append 改为 SSE 帧解析循环"
```

---

### Task 5: 03 Step 5.3 验证段更新

**Files:**
- Modify: `任务文档/03-HTML前端.md` 行 762-769（验证小节）

**Interfaces:**
- Consumes: Task 4 的新前端代码（SSE 帧解析循环）
- Produces: 03 验证段与新代码一致

- [ ] **Step 1: 更新验证小节（行 762-769）**

行 762-769 当前：
```markdown
### 验证

1. 确保后端 `POST /api/query` 已启动且返回流式响应
2. 先上传一篇 PDF（步骤 4）
3. 在输入框打字提问，回车或点发送
4. 应该看到 AI 回答**逐字出现**，而非一次性弹出

> **如果后端还没实现流式接口**：可先临时把 `askQuestion` 改成非流式（`await res.json()` 一次性取结果再显示），等 [模块 2](./02-LangGraph-Agent.md) 完成后切回流式。
```
替换为：
```markdown
### 验证

1. 确保后端 `POST /api/query` 已启动且返回 SSE 流式响应
2. 先上传一篇 PDF（步骤 4）
3. 在输入框打字提问，回车或点发送
4. 应该看到 AI 回答**逐字出现**，而非一次性弹出（`ReadableStream` + SSE 帧解析生效）
5. 如果 agent 调用了工具（如 `search_papers`），应能看到工具调用状态提示
```

删除旧的「如果后端还没实现流式接口」提示块——该提示针对的是旧版裸 append 写法，新版用 SSE 帧解析，临时降级为非流式的建议已不适用。

- [ ] **Step 2: 提交**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): Step 5.3 验证段对齐 SSE 帧解析"
```

---

### Task 6: 03 FAQ 段更新

**Files:**
- Modify: `任务文档/03-HTML前端.md` 行 875-877（FAQ「流式提问不工作」）

**Interfaces:**
- Consumes: Task 4 的新前端代码
- Produces: FAQ 与新代码一致

- [ ] **Step 1: 更新 FAQ（行 875-877）**

行 875-877 当前：
```markdown
### Q：流式提问不工作（一次性返回 / 卡住）

确认三点：① 后端 `/api/query` 返回的是流式响应（`StreamingResponse`），而非普通 JSON；② 前端用 `res.body.getReader()` 逐块读，而非 `await res.json()` 一次性读；③ 没有把响应包进一个会等完整结果的封装里。
```
替换为：
```markdown
### Q：流式提问不工作（一次性返回 / 卡住 / 乱码）

确认四点：① 后端 `/api/query` 返回的是 SSE 流式响应（`StreamingResponse` + `text/event-stream`），而非普通 JSON；② 前端用 `res.body.getReader()` 逐块读，而非 `await res.json()` 一次性读；③ `decoder.decode(value, { stream: true })` 不能漏 `stream: true`，否则中文字符跨包截断会乱码；④ `buf.split("\n\n")` 后 `frames.pop()` 留不完整帧——如果漏了这步，最后一段不完整的帧会解析失败。
```

- [ ] **Step 2: 提交**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): FAQ 流式排错更新（stream:true + frames.pop）"
```

---

### Task 7: backend/routes.py 同步代码改动

**Files:**
- Modify: `backend/src/agentic_search/api/routes.py` 行 7-8（import）+ 行 23-45（query 函数 + _sse 函数）

**Interfaces:**
- Consumes: spec 后端代码段
- Produces: backend 代码与 02 文档 Step 8.1 一致

- [ ] **Step 1: 修改 import（行 7-8）**

行 7 当前：
```python
from fastapi.responses import StreamingResponse
```
行 8 当前：
```python
from langchain_core.messages import HumanMessage
```
行 8 改为：
```python
from langchain_core.messages import HumanMessage, AIMessageChunk
```

- [ ] **Step 2: 替换 query 函数（行 23-40）**

将行 23-40（`@router.post("/query")` 到 `return StreamingResponse(...)`）替换为：

```python
@router.post("/query")
async def query(req: QueryRequest):
    """向 Agent 提问，以 SSE 流式返回回答。读哪篇论文由 agent 自主决定。"""
    async def event_stream():
        try:
            async for chunk, metadata in graph.astream(
                {"messages": [HumanMessage(content=req.question)]},
                stream_mode="messages"
            ):
                if not isinstance(chunk, AIMessageChunk):
                    continue
                if chunk.content:
                    yield f"data: {json.dumps(chunk.content, ensure_ascii=False)}\n\n"
                elif chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            yield f"event: tool\ndata: {tc['name']}\n\n"
        except Exception as e:
            yield f"data: {json.dumps(f'[错误：{e}]', ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 3: 删除 _sse 函数（行 42-45）**

将行 42-45（`def _sse(...)` 整个函数）删除——新代码不再使用 `_sse` 辅助函数。

- [ ] **Step 4: 提交**

```bash
git add backend/src/agentic_search/api/routes.py
git commit -m "refactor(backend): routes.py 假流式改为 graph.astream 真流式 + SSE 命名事件"
```

---

### Task 8: 最终一致性检查

**Files:**
- Read-only: `任务文档/02-LangGraph-Agent.md`、`任务文档/03-HTML前端.md`、`backend/src/agentic_search/api/routes.py`

- [ ] **Step 1: 检查 02 与 backend 代码一致性**

对比 `任务文档/02-LangGraph-Agent.md` Step 8.1 的代码块与 `backend/src/agentic_search/api/routes.py` 的 `query` 函数——两者必须逐行一致（文档是教学真理，代码对齐文档）。

- [ ] **Step 2: 检查 02 与 03 协议一致性**

02 后端 yield 的 SSE 帧格式（`data: "..."` + `event: tool\ndata: ...`）必须与 03 前端解析逻辑（`split("\n\n")` + `event:`/`data:` 行解析 + `JSON.parse`）完全匹配。

- [ ] **Step 3: 检查无历史性措辞**

grep 02 和 03 中是否有「旧版」「原来」「之前」「不再」「改用」「已删除」等措辞。如有，改为纯新版本表述。

- [ ] **Step 4: 检查跨文档 SSE 概念一致**

02 的 SSE 概念段（fetch vs EventSource、两种事件）与 03 的 5.1 小节（fetch vs EventSource）措辞一致，不矛盾。

- [ ] **Step 5: 提交（如有修复）**

```bash
git add -A
git commit -m "docs: 流式重设计最终一致性检查"
```
