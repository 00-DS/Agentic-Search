# 真实流式输出重设计

## 问题

当前 `/api/query` 是假流式：`graph.invoke()` 阻塞等整个 ReAct 循环跑完（20-30 秒），拿到完整答案字符串后切成 20 字段段推送。用户体验：长时间空白 → 突然一次性弹出全部文字。

此外，前端 03 Step 5.2 有两个 bug：① 不解析 SSE 帧，把 `data: {"type":"token",...}` 的 JSON 外壳当可见文字追加；② `TextDecoder.decode()` 缺 `{ stream: true }`，中文跨网络包截断时乱码。

## 目标

真实 token 流式：DeepSeek 每生成一个 token，立即流经 LangChain → LangGraph → FastAPI → 浏览器，用户看到文字逐字出现。同时推送工具调用事件（"正在搜索论文..."），让 ReAct agent 的自主探索过程对用户可见。

## 调研依据

| 来源 | 结论 |
|---|---|
| omp `provider-streaming-internals.md` | omp 在 provider 边缘解码 SSE；交互式 TUI 进程内零序列化；RPC 模式用 NDJSON over stdio |
| omp `StreamMessagesHandler.on_llm_new_token` 源码 | LangGraph `stream_mode="messages"` 通过 callback 逐 token emit `AIMessageChunk` |
| Vercel AI SDK v5 | 从自造格式回归 SSE 标准（`text/event-stream`） |
| Claude.ai / OpenAI API | SSE 命名事件 over POST+fetch（不用 EventSource，因为 EventSource 只支持 GET） |

## 技术方案：SSE 命名事件 over POST+fetch

### 传输机制

FastAPI `StreamingResponse`（自动 chunked）+ 前端 `fetch` + `ReadableStream.getReader()`。不用 `EventSource`（只支持 GET，无法 POST 发送问题内容）。

### 事件协议（两种事件）

| 传输内容 | 含义 |
|---|---|
| `data: "你"\n\n` | 文字 token（JSON 字符串值，前端 `JSON.parse` 还原） |
| `event: tool\ndata: search_papers\n\n` | 工具调用（工具名，无 JSON 包裹） |
| 连接关闭 | 流结束（无单独 done 事件，连接关闭即终止信号） |
| `data: "[错误：...]"\n\n` + 连接关闭 | 错误（文字形式显示，无单独 error 事件） |

**设计决策**：
- 文字 token 用 `json.dumps(text)` 而非裸文本：LLM 生成的 Markdown 含 `\n`（代码块、段落分隔），裸放 `data:` 行会撕裂 SSE 帧。`json.dumps` 转义换行，是换行转义的最小正确解。
- 工具名用裸文本（无 JSON）：工具名是简单标识符，不含特殊字符，无需转义。
- 无 `done` 事件：`graph.astream()` 循环结束 → `event_stream()` 返回 → HTTP 连接关闭 → 前端 `reader.read()` 得到 `done: true`。连接关闭是天然结束信号，单独发 `done` 是冗余。
- 无 `error` 事件：`@retry` 重试耗尽后抛异常，在 `event_stream()` 的 try/except 里用默认事件发一句错误文字，前端像普通回答一样显示。

### 后端代码（02 Step 8.1 + backend/routes.py）

需新增 import：`import json` 和 `from langchain_core.messages import AIMessageChunk`（`HumanMessage`、`StreamingResponse` 已有 import 保留）。

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

**关键机制**：
- `graph.astream(stream_mode="messages")`：LangGraph 通过 `StreamMessagesHandler.on_llm_new_token` callback 逐 token emit `AIMessageChunk`（源码验证）。每个 `AIMessageChunk.content` 是 DeepSeek 刚吐出的真 token。
- `isinstance(chunk, AIMessageChunk)` 过滤：`stream_mode="messages"` 还会 emit `ToolMessage`（工具返回的论文片段），不过滤会把中间数据当答案流给用户。
- `chunk.content` vs `chunk.tool_call_chunks` 判别：文字 token 的 `content` 有值且 `tool_call_chunks` 为空；工具调用的 `content` 为空且 `tool_call_chunks` 有值（验证确认）。
- 工具执行期间（ToolNode 跑工具）不 yield，流自然暂停，前端显示工具状态；工具返回后 LLM 继续，文字 token 继续流。

**删除的旧代码**：
- `_sse()` 辅助函数（封装一行字符串拼接的冗余抽象）
- `for i in range(0, len(answer), 20)` 假分块循环
- `graph.invoke()` 同步阻塞调用
- `result = ...` / `answer = result["messages"][-1].content` 中间变量

### 前端代码（03 Step 5.2）

```javascript
const reader = res.body.getReader();
const decoder = new TextDecoder();
let buf = '';

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });  // stream:true 防中文截断
    const frames = buf.split('\n\n');                  // SSE 帧以空行分隔
    buf = frames.pop();                                // 最后不完整的帧留在 buffer
    for (const frame of frames) {
        if (!frame.trim()) continue;
        let event = 'token';                           // 无 event: 行 = 默认 = 文字
        let data = '';
        for (const line of frame.split('\n')) {
            if (line.startsWith('event:')) event = line.slice(6).trim();
            else if (line.startsWith('data:')) data = line.slice(5);
        }
        if (event === 'token') aiEl.textContent += JSON.parse(data);
        else if (event === 'tool') /* 显示工具状态，如 "正在调用 search_papers..." */;
    }
}
```

**关键机制**：
- `split('\n\n')` + `buf = frames.pop()`：SSE 帧边界处理。一个网络包可能包含半个帧、一个完整帧、或多个帧。`pop()` 把最后不完整的帧留在 buffer 等下次拼接。
- `{ stream: true }`：TextDecoder 的流式模式。中文 UTF-8 编码可能被网络包边界截断，`stream: true` 让解码器等待完整字符。
- `JSON.parse(data)`：还原后端 `json.dumps` 转义的换行/特殊字符。

## 文档改动范围

| 文件 | 改动内容 |
|---|---|
| `任务文档/02-LangGraph-Agent.md` Step 8.1 | 后端代码从假流式改为 `graph.astream()` 真流式 + SSE 命名事件格式化 |
| `任务文档/02-LangGraph-Agent.md` SSE 技术概念段 | 讲解 SSE 命名事件 + 为什么用 fetch 而非 EventSource |
| `任务文档/02-LangGraph-Agent.md` curl 验证段 | `-N` 逐行看到真流式 token |
| `任务文档/03-HTML前端.md` Step 5.1 | 新增：为什么用 fetch 而非 EventSource 消费 SSE |
| `任务文档/03-HTML前端.md` Step 5.2 | 前端从裸 append 字节改为 SSE 帧解析循环 |
| `backend/src/agentic_search/api/routes.py` | 同步代码改动 |

## 验证标准

```bash
# curl -N 看到真流式：token 逐个到达（而非 30 秒后一次性弹出）
curl -N -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "这篇论文的核心方法是什么？"}'
```

期望输出：
```text
data: "这"
data: "篇"
event: tool
data: search_papers
data: "论"
data: "文"
...
```

成功标准：
- [ ] curl 看到文字 token 逐个到达，而非等待后一次性弹出
- [ ] curl 看到 `event: tool` 行标记工具调用
- [ ] 前端 AI 回复逐字出现
- [ ] 前端显示工具调用状态（"正在调用 search_papers..."）
- [ ] 前端正确渲染 Markdown（含换行的回答不乱码）
