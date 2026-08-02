# 论文 Agentic Search 重设计（任务文档更新）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `任务文档/` 中固定线性图的「单文档问答」升级为 LLM 自主工具循环的「论文 Agentic Search」——02 重写为 ReAct agent，01 加结构化提取（pymupdf dict + 标题启发式），03 去掉文档选择下拉框，04 记忆节点改挂 agent 循环前后，概念速查/项目概览/00 同步更新。

**Architecture:** 02 从线性图 `analyze_intent → read_and_answer` 重写为 ReAct 循环（`llm_call` ↔ `tool_node` + 条件边路由），LLM 自主调四个论文导航工具（`list_papers`/`list_sections`/`read_section`/`search_sections`）。搜索走正则（Python `re`），对齐 omp/hermes 的精确匹配范式，**无 embedding、无向量库**。01 的 `parse_pdf` 切 `get_text("dict")` + 标题字号启发式，MongoDB schema 加 `sections` 字段（废弃 `markdown`）。`/api/query` 不再收 `doc_id`，agent 自己决定读哪篇/哪些。

**Tech Stack:** pymupdf（`get_text("dict")` 结构化提取）、LangChain（`bind_tools`/`ToolNode`/`MessagesState`/`init_chat_model`）、LangGraph（StateGraph + `add_conditional_edges` 条件边）、Python 标准库 `re`（正则搜索）

## Global Constraints

- **范围：仅改 `任务文档/` 下的 `.md` 文件。`backend/` 实现代码一律不动。** 每个文件改完即 commit。
- **范式铁律：无 embedding、无向量库、无 LLM 预计算摘要。** `search_sections` 用 Python 标准库 `re` 跑正则，零额外依赖。这是对齐 omp/hermes 探索范式的核心——智能来自 LLM 自主迭代构造正则 + 选择性读取，不是预计算语义相似度。
- **工具集签名（四工具，全项目统一，不可在各文档间漂移）：**
  - `list_papers() -> list[PaperMeta]`：返回 `[{doc_id, filename}]`，对齐 omp `glob` 只返回路径不返回内容。**不带摘要。**
  - `list_sections(doc_id) -> list[Section]`：返回 `[{section_id, title, level}]`，论文特有。
  - `read_section(doc_id, section_id) -> str`：返回该章节正文，对齐 omp `read`。
  - `search_sections(pattern: str, doc_id: str = "") -> list[Hit]`：返回 `[{doc_id, section_id, snippet}]`（命中片段+上下文），`pattern` 是正则，对齐 omp `grep`。`doc_id` 可选，空则跨语料库搜。
- **MongoDB schema（01 定义，02 工具消费，全项目统一）：** `documents` 集合文档结构为 `{doc_id, filename, sections: [{section_id, title, level, text}], uploaded_at}`。**无 `summary`、无 `markdown` 字段**（旧 `markdown` 全文字段废弃，由 `sections[*].text` 拼接取代）。短论文无标题时整体作为 `section_id=0, title="(全文)", level=0` 的兜底 section。
- **`/api/query` 契约：** `QueryRequest` 只剩 `question: str`，**删除 `doc_id` 字段**。响应仍是 SSE 流式文本。
- **LangChain 引入：** 新 02 用 LangChain 的 `init_chat_model`/`bind_tools`/`ToolNode`/`MessagesState`，不用裸 httpx。旧 02 的 httpx「客户端 vs 服务端」教学点降级到概念速查/02 技术概念段落一次性讲解保留，但 agent 实现层切 LangChain。
- **教学锚点保留（不可丢失）：** `@retry` 装饰器（包在 LLM 调用上）、TypedDict State（强化为 `MessagesState` 带 messages reducer）、StateGraph/Node/Edge 概念。**新增：** 条件边 `add_conditional_edges`、`bind_tools`/`ToolNode`/ReAct 循环。
- **跨模块 cross-reference 完整性：** 装饰器教学网（02 的 `@retry` ↔ 04 的 `@dataclass` ↔ 02 第9步的 `@router` ↔ 概念速查条目）改动时全部检查，不可破坏。
- **依赖项更新：** `pyproject.toml` 示例加 `langchain`/`langchain-openai`/`langgraph`；**不加 `chromadb`、不加 embedding 库**。
- **DeepSeek 统一：** LLM 举例统一 DeepSeek（`base_url=https://api.deepseek.com`、`model=deepseek-v4-flash`），不出现智谱/OpenAI/glm/gpt。

---

## Task 1: `01-Python文档工具.md` — parse_pdf 结构化提取 + schema 升级

**Files:**
- Modify: `任务文档/01-Python文档工具.md`

**Interfaces:**
- Consumes: spec §4.2（MongoDB schema）、§2.2（pymupdf dict 结构）
- Produces: 01 的 `parse_pdf` 切 `get_text("dict")`；MongoDB schema 加 `sections`（废弃 `markdown`）；`list_documents`/`read_document` 返回新结构。下游 Task 2（02 工具）依赖此 schema。

- [ ] **Step 1: 改技术栈行（第 2 行附近）**

确认技术栈含 `pymupdf`（已有）。无改动则跳过。

- [ ] **Step 2: 改学习目标第 4 条（第 14 行附近）**

原文提及「把 PDF 提取的纯文本全文存入 MongoDB」。改为强调结构化提取：`4. 使用 **pymupdf + PyMongo** 在 services/documents.py 中实现 parse_pdf（结构化提取，切分章节）、list_documents、read_document、read_section 四个文档工具函数，把按章节切分的文本存入 MongoDB`

- [ ] **Step 3: 重写 §技术概念「pymupdf」段（约第 50-54 行）**

把现有 pymupdf 段落中「纯文本提取」「全文交给 LLM」「刻意选最简提取」的叙事，改为：pymupdf 通过 `page.get_text("dict")` 返回四层结构（page→blocks→lines→spans），每个 span 带 `size`(字号)/`font`/`flags`。本项目用此结构做**标题启发式**（span 字号大于正文中位数 → 标题），把论文切成 `sections`（章节），供 agent 按需取片段。保留「为什么需要 PDF→文字」通论，但删除「读全文进 128K 窗口」论证（那是旧线性图的设计依据，已被 agent 按需取片段取代）。

**新增讲解点：** 标题启发式——这是真实工程里常见的启发式算法，讲清「字号大于正文 → 标题」的判据，以及「未检测出任何标题 → 整篇作为兜底 section」的边界处理。

- [ ] **Step 4: 重写 `parse_pdf` 函数（约第 396-405 行）**

原文：
```python
def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF 文件，使用 pymupdf 提取纯文本（图片等非文字内容丢弃）。"""
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    doc = pymupdf.open(p)
    parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(parts)
```

改为返回 `list[dict]`（sections 列表）：
```python
def parse_pdf(pdf_path: str | Path) -> list[dict]:
    """读取 PDF，用 pymupdf dict 提取结构化文本，按标题启发式切分章节。

    返回 sections 列表，每项 {"section_id", "title", "level", "text"}。
    图片等非文字内容（block type=1）自动丢弃。
    """
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    doc = pymupdf.open(p)
    sections = _extract_sections(doc)   # 见下方启发式实现
    doc.close()
    if not sections:                    # 兜底：未检测出任何标题
        return [{"section_id": 0, "title": "(全文)", "level": 0,
                 "text": "\n".join(page.get_text() for page in doc)}]
    return sections
```

并在 `parse_pdf` 下方给出 `_extract_sections` 的教学示例（遍历 blocks/spans，收集字号，算中位数，把大于中位数的 span 当标题，按标题切块）。标注这是简化启发式，生产可更精细。

- [ ] **Step 5: 改 `store_document` / schema 说明（约第 408-412 行）**

原文的「无需缓存」「错误处理」「图片丢弃」三条讲解保留。**新增一条**讲 schema：`store_document` 现在存 `{doc_id, filename, sections: [...], uploaded_at}`，不再存单一 `markdown` 字段。

- [ ] **Step 6: 改 `read_document` 与新增 `read_section`**

`read_document(doc_id)` 现在返回 sections 拼接全文（`\n\n`.join 各 section text）——保留作为「读全文」的便利函数。**新增** `read_section(doc_id, section_id)`：按 `doc_id` 查 MongoDB，从 `sections` 数组取指定 `section_id` 的 `text` 返回。这是 02 agent 工具的底层依赖。

- [ ] **Step 7: 改 MongoDB schema 示例与 Compass 查看（约第 138 行、数据存储段）**

原文提及 `markdown` 字段处，改为 `sections` 字段。文档结构示例从 `{doc_id, filename, markdown, uploaded_at}` 改为 `{doc_id, filename, sections: [{section_id, title, level, text}], uploaded_at}`。

- [ ] **Step 8: 改 pyproject.toml 依赖示例（约第 180 行）**

确认有 `pymupdf`。无 `chromadb`、无 embedding 库。

- [ ] **Step 9: grep 一致性扫描**

在 `01-Python文档工具.md` 内 grep `markdown`（应为 0 处，或仅历史说明）、`get_text("text")`（应为 0）、`get_text()` 无参（应为 0，现都用 `"dict"`）。

- [ ] **Step 10: Commit**

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): parse_pdf 结构化提取（get_text dict + 标题启发式 + sections schema）"
```

---

## Task 2: `02-LangGraph-Agent.md` — 重写为 ReAct Agent（第一部分：概念 + 工具）

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`（全文重写学习目标、技术概念、模块结构、工具定义）

**Interfaces:**
- Consumes: spec §2.1（LangGraph agent 形态）、§2.3（omp 工具范式）、§3（工具集）、Task 1 的 schema
- Produces: 02 的工具定义（`list_papers`/`list_sections`/`read_section`/`search_sections`）、agent 用 LangChain `@tool` 装饰器声明。Task 3（图 + 路由）依赖这些工具。

> ⚠️ 这是最大的 task。02 共 881 行，大部分要重写。本 task 聚焦**概念层 + 工具定义层**；图组装与 API 路由放 Task 3。

- [ ] **Step 1: 重写学习目标（第 3-12 行）**

旧 6 条目标围绕线性图。重写为反映 agent 范式：
1. 理解 **LangGraph agent**：StateGraph、Node、Edge、**条件边**（`add_conditional_edges`）、State（TypedDict + messages reducer）
2. 用 `bind_tools` + `ToolNode` 构建 **ReAct 循环**——LLM 自主决定调哪个工具、调几次、何时回答
3. 实现四个**论文导航工具**（`list_papers`/`list_sections`/`read_section`/`search_sections`），理解 agent 如何像 omp/hermes 探索代码库那样探索论文
4. 理解 **Python 装饰器**：从自定义 `@retry` 到 LangChain `@tool`、FastAPI `@router`、标准库 `@dataclass`
5. 用 `init_chat_model`（LangChain）替代裸 httpx 调 DeepSeek，理解 tool calling 协议
6. 用 `uv run uvicorn` 启动，`curl` 验证 SSE 流式 agent 问答

- [ ] **Step 2: 重写技术概念段（第 15-31 行）**

删除「Agent 工作流是 LLM 驱动的处理流程……LangGraph 把这个流程组织为图结构」旧叙事。重写：
- **LangGraph**：StateGraph/Node/Edge/State 基础（保留），强调**条件边**是 agent 的关键（线性图是退化特例）
- **ReAct agent**：LLM + 工具循环（Reasoning + Acting）。对标 omp 用 `read`/`grep`/`glob` 自主探索代码库——本项目 agent 用论文导航工具自主探索论文语料库
- **工具调用协议（tool calling）**：LLM 在响应里返回 `tool_calls`（函数名+参数 JSON），LangGraph 的 `ToolNode` 解析执行、结果作为 `ToolMessage` 回灌，LLM 再决策。这是为什么用 LangChain 而非裸 httpx——`bind_tools`/`ToolNode` 封装了这整套胶水
- **httpx vs LangChain 取舍**：保留 httpx 是什么的讲解（客户端 vs FastAPI 服务端），但说明 agent 层切到 LangChain 是因为 tool calling 协议复杂度
- **装饰器**：保留现有装饰器段落（指向第 5 步 `@retry`、第 9 步 `@router`、模块 4 `@dataclass`）

- [ ] **Step 3: 重写模块结构 mermaid 图（第 39-57 行）**

旧图标 `Routes → Graph → Docs` 线性调用。改为体现 agent 循环：
```
Browser → Routes → Agent(llm_call ↔ tool_node) → Docs/Memory
```
tool_node 调用 01 的 `read_section`/`search_sections` 等。

- [ ] **Step 4: 重写第 1-4 步（前置准备、依赖、State、Hello World）**

- 第 1 步（前置）：更新依赖列表，加 `langchain`/`langchain-openai`/`langgraph`
- 第 2 步（目录与依赖）：`pyproject.toml` 示例加 LangChain 三件套
- 第 3 步（State）：TypedDict 改为带 `messages` reducer 的 `MessagesState` 或自定义。讲解 LangGraph 消息合并语义（`add_messages` reducer）。**保留** partial-update 教学
- 第 4 步（Hello World）：旧版用线性两节点演示。改为最小 agent 演示——一个 dummy 工具 + `llm_call`/`tool_node`/`should_continue` 三件套，跑通 ReAct 循环

- [ ] **Step 5: 重写第 5 步「插曲：装饰器」+ @retry（第 286-352 行）**

保留 `@retry` 装饰器完整教学（这是核心教学点，不可丢）。但上下文改为：`@retry` 现在包在**所有 LLM 调用**上（agent 的 `llm_call` 节点内部）。`@functools.wraps`、带参装饰器、`functools.wraps` 保留原函数信息的讲解全部保留。

- [ ] **Step 6: 新增「论文导航工具集」节（替换旧第 5/6 步的 analyze_intent/read_and_answer）**

定义四个工具，用 LangChain `@tool` 装饰器。每个工具给完整教学示例代码：

```python
from langchain.tools import tool
from agentic_search.services.documents import list_documents, read_section as _read_section
import re

@tool
def list_papers() -> list[dict]:
    """列出语料库中所有论文。返回 [{doc_id, filename}]。"""
    return [{"doc_id": d["doc_id"], "filename": d["filename"]} for d in list_documents()]

@tool
def list_sections(doc_id: str) -> list[dict]:
    """列出一篇论文的目录（章节标题与层级）。返回 [{section_id, title, level}]。"""
    doc = _get_doc(doc_id)
    return [{"section_id": s["section_id"], "title": s["title"], "level": s["level"]} for s in doc["sections"]]

@tool
def read_section(doc_id: str, section_id: int) -> str:
    """读取指定论文的指定章节正文。"""
    return _read_section(doc_id, section_id)

@tool
def search_sections(pattern: str, doc_id: str = "") -> list[dict]:
    """跨语料库（或指定论文）用正则搜索章节内容。返回 [{doc_id, section_id, snippet}]。"""
    # 遍历 sections，对每个 text 跑 re.search，命中返回 snippet
    ...
```

讲清四工具与 omp `glob`/`read`/`grep` 的对应关系。**强调**：`search_sections` 用正则不用 embedding（对齐 omp 范式）。

- [ ] **Step 7: grep 一致性扫描（02 第一部分）**

在 02 内 grep：`analyze_intent`（应为 0，除非历史说明）、`read_and_answer`（0）、`_read_first_document`（0）、`httpx.post`（应为 0，agent 用 LangChain）、`doc_id.*question|question.*doc_id`（QueryRequest 旧签名，Task 3 改）。

- [ ] **Step 8: Commit（02 第一部分，WIP）**

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 重写学习目标/技术概念/工具集（agent 范式，第一部分）[WIP]"
```

---

## Task 3: `02-LangGraph-Agent.md` — 重写为 ReAct Agent（第二部分：图 + 路由 + 验证）

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`（图组装、API 路由、验证、常见问题、延伸阅读）

**Interfaces:**
- Consumes: Task 2 的四工具定义、spec §2.1（agent 图形态）
- Produces: 完整可运行的 agent 图 + `/api/query` 新契约（无 doc_id）。Task 4/5 依赖此契约。

- [ ] **Step 1: 重写 `build_graph()`（约第 461-476 行）**

旧版两节点线性图。改为 agent 循环：
```python
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain.chat_models import init_chat_model

tools = [list_papers, list_sections, read_section, search_sections]
llm = init_chat_model("deepseek-v4-flash", ...)  # DeepSeek 配置
llm_with_tools = llm.bind_tools(tools)

def llm_call(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: MessagesState):
    return "tool_node" if state["messages"][-1].tool_calls else END

def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("tool_node", ToolNode(tools))
    builder.add_edge(START, "llm_call")
    builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    builder.add_edge("tool_node", "llm_call")
    return builder.compile()
```

讲解：条件边 `add_conditional_edges` 是 agent 的心脏——`should_continue` 看 `tool_calls` 决定循环还是结束。对标 omp 的探索循环。

- [ ] **Step 2: 重写 `api/schemas.py`（约第 521-524 行）**

`QueryRequest` 删除 `doc_id` 字段：
```python
class QueryRequest(BaseModel):
    """POST /api/query 的请求体。"""
    question: str           # 只剩问题；读哪篇由 agent 决定
```

- [ ] **Step 3: 重写 `api/routes.py` 的 query 端点（约第 568-600 行）**

旧版 `read_and_answer` 全文进 prompt。改为调 agent 图，SSE 流式返回 agent 最终回答。讲解 agent 的 `stream`/`invoke` 如何对接 StreamingResponse。

- [ ] **Step 4: 保留第 9 步 FastAPI 路由讲解 + `@router` 装饰器呼应（约第 589 行）**

保留「APIRouter 路由分组」设计说明。保留 `@router.post`/`@router.get` 是装饰器的呼应（指向第 5 步 `@retry`）。这是装饰器 cross-reference 网的一环，不可破坏。

- [ ] **Step 5: 更新验证段（约第 490-506 行）**

旧版验证 `graph.invoke({"question": "..."})`。改为 agent 版：传 `{"messages": [HumanMessage(content="...")]}`，观察 agent 多轮工具调用日志。加一条：故意问跨论文问题，观察 agent 调 `list_papers` → `search_sections` → `read_section` 的探索轨迹。

- [ ] **Step 6: 更新常见问题与延伸阅读（文末）**

加 LangChain/LangGraph 文档链接。删除已不适用的 FAQ（如全文窗口论证）。

- [ ] **Step 7: grep 一致性扫描（02 全文）**

grep `analyze_intent|read_and_answer|_read_first_document|doc_id.*=.*""|httpx\.post` → 全 0。grep `chroma|embedding|向量` → 全 0（除非否定句）。grep `bind_tools|ToolNode|add_conditional_edges` → 应存在。

- [ ] **Step 8: Commit（02 完成）**

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 重写为 ReAct agent（图组装+条件边+API 契约），第二部分完成"
```

---

## Task 4: `03-HTML前端.md` — 去掉文档选择，配合新 query 契约

**Files:**
- Modify: `任务文档/03-HTML前端.md`

**Interfaces:**
- Consumes: Task 3 的新 `/api/query` 契约（无 doc_id）
- Produces: 03 前端无文档下拉框，`askQuestion()` fetch body 只发 question。

- [ ] **Step 1: 改学习目标（如有提及文档选择）**

确认学习目标不依赖「文档下拉框」教学。

- [ ] **Step 2: 删除文档选择下拉框的 HTML（`<select id="doc-list">` 相关）**

grep `doc-list` 定位。删除下拉框控件。UI 改为纯提问输入框——用户只管问，agent 自己找论文。保留上传按钮（`/api/ingest` 不变）。

- [ ] **Step 3: 改 `askQuestion()` 的 fetch body（`app.js` 教学示例）**

原文 `body: JSON.stringify({ question, doc_id })`。改为 `body: JSON.stringify({ question })`。

- [ ] **Step 4: 改 `loadDocuments()` 相关（如前端不再需要列文档）**

若 `GET /api/documents` 仍保留（供 agent 工具用，但前端不再展示下拉框），说明：前端不再调 `loadDocuments()` 渲染下拉框，该端点转为 agent 工具的后端依赖。

- [ ] **Step 5: 改模块结构 mermaid 图与数据流描述**

旧图标「下拉框选择 doc_id」。改为「用户提问 → agent 自主探索」。

- [ ] **Step 6: 改「为什么前端排在模块 2 之后」段（约第 60 行）**

确认仍成立（前端需后端 agent 能响应）。措辞从「响应 4 个 API 端点」调整为「响应 agent 问答」。

- [ ] **Step 7: grep 一致性扫描**

grep `doc_id|doc-list|loadDocuments` → 确认下拉框逻辑已清除（`loadDocuments` 若保留供其他用途则说明）。

- [ ] **Step 8: Commit**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): 去掉文档选择下拉框，query 契约去掉 doc_id（配合 agent 自主探索）"
```

---

## Task 5: `04-TMT记忆系统.md` — 记忆节点挂 agent 循环前后

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`

**Interfaces:**
- Consumes: Task 3 的 agent 图结构
- Produces: 04 的 `retrieve_memory`/`store_memory` 挂在 agent 循环开始前/结束后。

- [ ] **Step 1: 改记忆节点拓扑说明（约第 143 行「集成到 LangGraph 图」）**

原文「集成到 LangGraph 图（retrieve_memory + store_memory 节点）」。改为明确拓扑：`retrieve_memory` 是 agent 循环**开始前**的节点（把相关 L1/L2 记忆注入 `messages` 上下文，再进 `llm_call`）；`store_memory` 是循环**结束、`__end__` 前**的节点（提取 L1 事实写入）。即「记忆包裹 agent 循环」。

- [ ] **Step 2: 改 `@dataclass` 装饰器呼应（约第 123 行）**

确认 `@dataclass` 也是装饰器的呼应仍成立（指向 02 的 `@retry`）。装饰器 cross-reference 网不可破坏。

- [ ] **Step 3: 确认 L2 整合端点不变**

`POST /api/consolidate` 契约不变。仅确认措辞与新 agent 架构一致。

- [ ] **Step 4: grep 一致性扫描**

grep `analyze_intent|read_and_answer` → 0。确认 `@dataclass` 呼应在。

- [ ] **Step 5: Commit**

```bash
git add 任务文档/04-TMT记忆系统.md
git commit -m "docs(04): 记忆节点挂 agent 循环前后（retrieve 在前，store 在后）"
```

---

## Task 6: 跨文档同步（概念速查 + 项目概览 + 00-开始指南）

**Files:**
- Modify: `任务文档/概念速查.md`、`任务文档/项目概览.md`、`任务文档/00-开始指南.md`

**Interfaces:**
- Consumes: Task 1-5 的全部改动
- Produces: 概念速查/项目概览/00 与新 agent 范式一致。

- [ ] **Step 1: 概念速查 — 更新现有条目 + 新增**

- **LangGraph 条目**：从「线性图 analyze_intent → read_and_answer」改为「ReAct agent 循环（llm_call ↔ tool_node + 条件边）」
- **Agentic Search 条目**：更新本项目用法，强调 agent 自主探索论文语料库（对标 omp/hermes）
- **FastAPI 条目**：确认 `@router` 装饰器讲解仍成立
- **装饰器条目**：确认仍存在且指向 02 第 5 步 `@retry`
- **httpx 条目**（若有）：保留客户端 vs 服务端讲解，但标注 agent 层用 LangChain
- **新增「ReAct」「tool calling」「条件边」相关概念**（可选，按概念速查体例）
- **删除**：任何「读全文进 128K 窗口」「不做关键词检索」旧论证（那是线性图设计依据，已过时）

- [ ] **Step 2: 项目概览 — 更新架构与模块描述**

- **系统架构 mermaid**（第 18-31 行）：`Routes → Graph` 改为 `Routes → Agent(llm_call ↔ tool_node)`
- **文件结构**（第 60-92 行）：`agents/graph.py` 描述从「LangGraph 图 + 节点 + State」改为「ReAct agent + 4 工具 + 条件边」
- **M1 学习目标**（第 111 行）：加「ReAct agent / 工具调用 / 条件边」
- **数据流-提问流程**（第 205-221 行）：从「analyze_intent → read_and_answer」改为「agent ReAct 循环（list_papers/search_sections/read_section）」
- **API 设计表**（第 154-159 行）：`/api/query` 请求体从 `{question, doc_id}` 改为 `{question}`
- **技术栈表**（第 243-255 行）：加 `langchain`/`langgraph`；确认无 chroma/embedding

- [ ] **Step 3: 00-开始指南 — 更新学习路径与项目介绍**

- **学习路径**（第 27-39 行）：模块 2 描述从「LangGraph 编排分析意图→读文档→回答」改为「LangGraph ReAct agent，LLM 自主调工具探索论文」
- **项目概述**（第 5 行）：确认「带记忆的论文问答助手」仍准确
- **「准备 LLM API Key」**（第 92-100 行）：DeepSeek 配置不变

- [ ] **Step 4: 全局 grep 一致性扫描**

跨 `任务文档/` 全部 grep：
- `analyze_intent|read_and_answer|_read_first_document` → 应为 0（除非历史/否定说明）
- `chroma|embedding|向量库` → 应为 0（除非否定句「无向量库」）
- `doc_id.*=.*""` （QueryRequest 旧默认值）→ 0
- `读全文|128K|全文进.*窗口` → 检查每处，确认已更新为 agent 按需取片段叙事
- `bind_tools|ToolNode|add_conditional_edges|list_papers|search_sections` → 应在 02/概念速查/项目概览存在

- [ ] **Step 5: 装饰器 cross-reference 网完整性检查**

确认五处装饰器呼应仍在且互相指向：
1. 概念速查「装饰器」条目 → 02 第 5 步
2. 02 技术概念段落 → 第 5 步、第 9 步、模块 4
3. 02 第 5 步「插曲：什么是装饰器」+ `@retry`
4. 02 第 9 步 `@router` 呼应
5. 04 `@dataclass` 呼应 → 02 `@retry`

- [ ] **Step 6: Commit**

```bash
git add 任务文档/概念速查.md 任务文档/项目概览.md 任务文档/00-开始指南.md
git commit -m "docs(sync): 概念速查/项目概览/00 同步 agent 范式（ReAct + 工具 + 条件边）"
```

---

## 验收标准（全部 task 完成后）

1. `grep -rn "analyze_intent\|read_and_answer\|_read_first_document" 任务文档/` → 0 命中（或仅否定说明）
2. `grep -rn "chroma\|embedding\|向量库" 任务文档/` → 仅否定句（「无向量库」）
3. `grep -rn "doc_id.*=.*\"\"" 任务文档/` → 0（QueryRequest 无 doc_id 默认值）
4. 02 含 `bind_tools`/`ToolNode`/`add_conditional_edges`/`list_papers`/`search_sections`
5. 01 的 `parse_pdf` 用 `get_text("dict")`，MongoDB schema 含 `sections`
6. 装饰器 cross-reference 五处完整
7. 03 无 `doc-list` 下拉框
8. 项目概览/概念速查/00 与 agent 范式一致
