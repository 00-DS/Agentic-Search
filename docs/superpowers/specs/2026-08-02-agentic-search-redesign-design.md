# 论文 Agentic Search 重设计

> 日期：2026-08-02
> 范围：任务文档/ 教学项目——把固定线性图的「单文档问答」升级为 LLM 自主工具循环的「论文 Agentic Search」
> 状态：待 writing-plans 落地

---

## 1. 背景与动机

### 1.1 现状缺陷

当前 02-LangGraph-Agent.md 的图是**写死的线性流程**：

```
__start__ → analyze_intent → read_and_answer → __end__
```

- `doc_id` 由前端下拉框钦定，agent 不参与文档选择
- 两个节点在固定位置被调用，输入输出被代码锁死
- `_read_first_document` 是硬编码 fallback，不是 agent 的自主决策
- `read_and_answer` 把论文**全文**塞进 prompt，在多轮对话 + 记忆累积场景下 context 指数膨胀（全文 + 历史 + TMT 记忆 + reasoning tokens 每轮重发）

这套不是 agentic search——是「对用户钦定单文档做 LLM 问答」。

### 1.2 目标范式

对标 omp / Claude Code 自主探索代码库的方式（用 `read`/`grep`/`glob` 自己决定读什么、搜什么、何时读够），把对象换成论文语料库：给 agent 一组论文导航工具，**LLM 自己决定调哪个、调几次、何时读够了**。

业界把这套叫 "Agentic Search over Documents"（参见 Drata 的 LAD-RAG 文章引用的「RAG Obituary」论点：与其做 RAG 切块检索，不如走 agent + 工具路线）。LangChain 官方 agentic-RAG 教程采用同样的 `bind_tools` + `ToolNode` + 条件边循环。

### 1.3 关键决策

采用 **(III) 推翻式** + **B 路径 + (ii) 契约升级**，不留中间态：

- 02 线性图作废，重写为 ReAct agent
- 01 加结构化提取（pymupdf `get_text("dict")` + 标题启发式，正则搜索用 Python 标准库 `re`，无向量库）
- 03 去掉文档选择下拉框，`/api/query` 不再收 `doc_id`
- 04 记忆系统配合新 agent（基本不动）

## 2. 研究依据

### 2.1 LangGraph agent 标准形态（已查官方文档 docs.langchain.com）

两节点循环：

```
              ┌────── tool_node ────┐
              │                     │
__start__ → llm_call ←──────────────┘   ReAct loop
              │
          (no tool_calls)
              ▼
            __end__
```

- `llm_call`：`llm.bind_tools([...]).invoke(messages)`，LLM 决定调工具还是直接答
- `tool_node`：`ToolNode([...])` 执行 LLM 选中的工具，结果作为 `ToolMessage` 回灌
- 条件边 `should_continue`：检查 `last_message.tool_calls`——有就回 `tool_node`，没有就 `END`
- LLM 自主多轮：路径完全由它定

关键 API（2026 版，已核实）：
```python
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState, StateGraph, START, END

llm_with_tools = llm.bind_tools(tools)
# agent_builder.add_node("llm_call", llm_call)
# agent_builder.add_node("tool_node", ToolNode(tools))
# agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
# agent_builder.add_edge("tool_node", "llm_call")
```

### 2.2 pymupdf 结构化提取（已查官方 Appendix 1）

`page.get_text("dict")` 返回四层结构：
```
page → blocks(≈段落) → lines → spans(同字体属性的字符片段)
```
每个 span 带 `size`(字号)、`font`(字体名)、`flags`(粗体/斜体)、`color`、`bbox`(位置)。

- **段落** = block 天然就有，零成本
- **标题** = 启发式：span `size` 大于正文字号中位数 → 标题；`level` 由相对大小推断
- **性能**：DICT 约 TEXT 的 4×，但 TEXT 处理 1310 页只要 2 秒 → 一篇 10-30 页论文 < 1 秒
- **图片** = block type=1，自动剔除

### 2.3 omp 工具范式（源码核实，can1357/oh-my-pi）

深入研读 omp 仓库（`docs/tools/grep.md`、`docs/tools/read.md`、`docs/tools/glob.md`、`crates/pi-natives/src/grep.rs`、`docs/natives-text-search-pipeline.md`）确认：**omp 的探索工具全部基于精确文本匹配，无任何 embedding / 向量检索**。核心三工具：

- **`grep`**：基于文件内容的正则（RE2 语法，ripgrep 引擎）匹配。返回命中行 + 上下文行（默认前 1 行后 3 行），支持多文件/目录/glob 范围。智能体现在 LLM 自己**迭代构造正则**——先搜宽泛词，看结果再搜更精确的词，逐步逼近目标。
- **`read`**：流式读文件，支持 `:50-100` 行范围选择器；对可解析代码/文档做**结构化摘要**（保留声明、省略体用 `…` 占位，提示「re-read needed ranges」）。对应「不返回全文，按需取片段」。
- **`glob`**：按路径模式（`**/*.ts`）发现文件，纯路径匹配。

hermes 同范式（47 内置工具含 Grep/Glob/Files:read/write/edit/list）。

**关键结论**：agentic search 的智能来自「LLM 自主多轮迭代正则搜索 + 选择性读取」，不是 embedding 语义检索。本设计严格对齐此范式——`search_sections` 用正则，不用向量库。
## 3. 工具集设计

对标 omp 探索代码库的 `glob`/`read`/`grep`，论文 agent 的工具集：

| 工具 | 签名 | 返回 | 对应 omp |
|---|---|---|---|
| `list_papers` | `() -> list[PaperMeta]` | 语料库所有论文：`doc_id` + `filename`（对齐 omp `glob` 只返回路径，不返回内容） | `glob` |
| `list_sections` | `(doc_id) -> list[Section]` | 一篇论文的目录：`section_id` + `title` + 层级（论文特有，因论文有章节结构） | (论文特有) |
| `read_section` | `(doc_id, section_id) -> str` | 该章节正文（对齐 omp `read` 按范围取内容） | `read` |
| `search_sections` | `(pattern, doc_id?) -> list[Hit]` | 跨语料库**正则**搜：返回 `doc_id`+`section_id`+`snippet`（命中片段+上下文），**不返回全文**。`pattern` 为正则表达式；`doc_id` 可选，指定则只搜该篇 | `grep` |

### 3.1 三个逼出 agentic 行为的设计约束

1. **没有 `read_paper(doc_id)`**——不给「偷懒全量读」的口子。agent 必须先 `list_sections` 看目录，再 `read_section` 逐章取。这是「按需取片段」强约束，也是多轮场景下不爆窗口的根本保障。短论文若没检测出章节（启发式未识别出任何标题级 span），01 把整篇文本作为一个 `section_id=0`、`title="(全文)"`、`level=0` 的兜底 section 存入——agent 调 `list_sections` 会看到一个「(全文)」条目，调 `read_section` 拿到全文。这样工具调用协议始终一致，不会因论文长短出现「有的能读有的不能」的分裂。

2. **`search_sections` 用正则、返回位置而非全文**——对齐 omp `grep`：参数是正则 `pattern`（不是 embedding query），返回命中片段 + 上下文（`[{doc_id, section_id, snippet}]`），agent 看到命中后**主动**再调 `read_section` 深入。智能在 LLM 自主迭代构造正则——先搜宽泛词（如 `dataset|corpus|benchmark`），看结果再搜更精确的词，逐步逼近。这是 agentic 的核心：搜索策略由 LLM 在运行时决定，不是预定义的 embedding 相似度。

3. **`list_papers` 不带摘要**——对齐 omp `glob` 只返回路径不返回内容。agent 判断相关性靠**自主探索**：先 `list_papers` 看有哪些（`filename` 通常含论文标题/作者信息），再对感兴趣的 `list_sections` 看目录，再决定 `read_section`。不在上传时预计算 LLM 摘要——那会引入「上传时一次性摘要」的额外复杂度和一次 LLM 调用，且摘要质量不可控；让 agent 自己读章节标题判断相关性更可靠、更 agentic。

### 3.2 `search_sections` 走正则匹配（对齐 omp grep，否决 embedding）

**否决 embedding / 向量库**：这是旧时代 RAG 的思路，与 omp/hermes 的 agentic 探索范式根本不同。omp 的智能来自 LLM 自主迭代构造正则、选择性读取，不是预计算的语义相似度。引入 chroma 会：① 加 embedding 模型依赖 + 首次下载模型文件；② 上传时对每个 section 做 embedding 入库的额外流程；③ 搜索结果受 embedding 模型质量制约、不可解释（正则命中是人能读懂的精确匹配，embedding 相似度是黑盒）。本项目严格对齐 omp 范式——正则匹配，零额外依赖，结果可解释。

**正则匹配实现**：Python 标准库 `re` 即可。`search_sections` 内部对每个 section 的 `text` 字段跑 `re.search(pattern, text)`，命中则返回 `snippet`（命中处 ±一定上下文字符）。跨语料库搜索 = 遍历所有 `documents` 文档的 `sections`，对每个 section 跑正则。数据量级（教学项目，几十篇论文 × 几十 section）下 O(n) 遍历完全够用，无需索引。

### 3.3 agent 探索轨迹示例

用户问「这两篇论文在数据集选择上有什么差异？」：
```
llm_call → list_papers()                                    # 看语料库
llm_call → list_sections(doc_a), list_sections(doc_b)       # 看各自目录
llm_call → search_sections("dataset|corpus|benchmark")     # 正则搜定位
llm_call → read_section(doc_a,"experiments"), read_section(doc_b,"experiments")
llm_call → (no tool_calls) answer                           # 读够了，回答
```
路径完全由 LLM 决定。不同问题走出不同路径——简单问题 2 步收工，跨论文对比 8 步。

## 4. 数据契约变更

### 4.1 `/api/query` 契约

**旧**（作废）：
```python
class QueryRequest(BaseModel):
    question: str
    doc_id: str = ""        # ← 删除
```

**新**：
```python
class QueryRequest(BaseModel):
    question: str           # 只剩问题；读哪篇/哪些由 agent 决定
```

响应仍是 SSE 流式文本（不变）。这条变更连锁影响：旧 02 的 `_read_first_document` fallback、`analyze_intent`/`read_and_answer` 两个写死节点——全部作废，被 agent 循环取代。

### 4.2 01 MongoDB schema

`parse_pdf` 切 `get_text("dict")`，`documents` 集合的文档结构从：
```json
{ "doc_id": "...", "filename": "...", "markdown": "全文纯文本", "uploaded_at": "..." }
```
改成：
```json
  "doc_id": "...",
  "filename": "...",
  "sections": [
    { "section_id": 0, "title": "1 Introduction", "level": 1, "text": "..." },
    { "section_id": 1, "title": "2 Related Work", "level": 1, "text": "..." }
  ],
  "uploaded_at": "..."
}
```

- **标题启发式**：span `size` 大于正文中位数字号 → 标题；`level` 由相对大小推断（最大=h1，次之=h2）。未检测出任何标题级 span 时，整篇作为一个 `section_id=0`、`title="(全文)"`、`level=0` 的兜底 section。
- **无 summary 字段、无向量库**：对齐 omp `glob`（只返回路径）/`grep`（正则匹配），不在上传时预计算 LLM 摘要或 embedding。`search_sections` 运行时对 `sections[*].text` 跑正则即可。

## 5. 模块影响清单

### 5.1 02-LangGraph-Agent.md（重写）

**作废**：
- 线性图 `analyze_intent → read_and_answer`
- `_read_first_document` fallback
- `doc_id` 作为图输入
- 全文塞 prompt 的 `read_and_answer`

**保留**：
- `@retry` 装饰器（包在 LLM 调用上）
- TypedDict State（强化：带 `messages` reducer 的多轮消息合并）
- StateGraph / Node / Edge 概念教学

**新增**：
- 条件边 `add_conditional_edges`（旧 02 没教，这是 LangGraph 真正的难点）
- `bind_tools` + `ToolNode` + ReAct 循环
- 四个论文导航工具
- LLM 自主多轮工具调用

**教学锚点对照**：

| 原语 | 在 agentic 版里怎么出现 | 旧 02 |
|---|---|---|
| StateGraph / State / Node / Edge | 图本身 | ✅ 继承 |
| TypedDict State (partial update) | `MessagesState` 带 messages reducer | ✅ 强化 |
| 条件边 `add_conditional_edges` | `should_continue` 路由 | ❌ 新增价值 |
| `@retry` 装饰器 | 包在 LLM 调用上 | ✅ 保留 |
| `_parse_intent` 练习 | 意图分析内化进 agent 的工具选择 | 转型 |

### 5.2 01-Python文档工具.md（配合改动）

- `parse_pdf`：`get_text("text")` → `get_text("dict")`
- 新增标题启发式（span 字号判定）
- MongoDB schema 升级（加 `sections`，`markdown` 字段废弃；无 summary、无向量库）
- 教学点保留：pymupdf 基础、PDF 不落盘、错误处理、测试

### 5.3 03-HTML前端.md（配合改动）

- **删文档选择下拉框**（`<select id="doc-list">`）
- `askQuestion()` 的 fetch body 去掉 `doc_id`
- UI 改成纯提问输入框——用户只管问，agent 自己找论文
- **不动**：HTML 结构教学、fetch/AJAX 教学、FormData 上传教学、ReadableStream 流式渲染、模块 4 记忆展示


记忆在新 agent 图里的挂法：`retrieve_memory` 是 agent 循环开始前的一个节点（把相关 L1/L2 记忆注入 `messages` 上下文，然后进入 `llm_call`）；`store_memory` 是 agent 循环结束、`__end__` 前的一个节点（把本轮问答提取为 L1 事实写入）。即「记忆包裹 agent 循环」，与旧线性图「记忆夹在 analyze_intent 和 read_and_answer 之间」是同构的拓扑——检索在前、存储在后。L2 整合端点 `/api/consolidate` 不变。具体节点签名与 state 字段在 implementation plan 阶段细化。

## 6. 数据流（重设计后）

### 上传流程

```
PDF → pymupdf dict → 标题启发式切 sections → 直接入 MongoDB（无 LLM 摘要、无 embedding）
```

### 提问流程

```
question → /api/query (无 doc_id)
    → agent ReAct 循环:
        list_papers → (看 filename 决定探索谁)
        list_sections / search_sections → (定位)
        read_section → (取片段)
        ...(LLM 自主多轮)...
        answer (no tool_calls) → SSE 流式回前端
```

## 7. 新增依赖

**LangChain 引入决策**：旧 02 用裸 httpx 调 DeepSeek 是有意的「少一层抽象，你能看到完整请求与响应」教学取舍。新 02 必须引入 LangChain，原因不是「框架崇拜」，而是工具调用（tool calling）协议的复杂度：LLM 在响应里返回 `tool_calls`（结构化的函数名+参数 JSON），需要解析、校验、路由到对应工具、收集结果、再作为 `ToolMessage` 回灌——这一整套 ReAct 循环的胶水代码，自己用裸 httpx 实现是几百行重复造轮子，且对教学是噪声。`bind_tools`/`ToolNode`/`MessagesState` 把这套机制封装成声明式 API，学生注意力能集中在「agent 怎么决策」而非「tool_calls 的 JSON 字段怎么解析」。因此新 02 引入 LangChain，旧 02 的 httpx 在「展示原始 HTTP 往返」这一教学点上以一次性的概念速查 / 技术概念段落保留（仍讲 httpx 是什么、和 FastAPI 的客户端/服务器区别），但 agent 实现层切到 LangChain。这是一个真实的教学取舍：丢掉「裸 HTTP 可见性」，换来「工具调用机制不过载认知」。

**无 chromadb、无 embedding 依赖**：`search_sections` 用 Python 标准库 `re` 跑正则，零额外依赖。

## 8. 教学价值论证

线性图是 agentic 图的**退化特例**（没有条件边、没有循环）。直接教 agentic 版，一次性把条件边、循环、工具调用这些 LangGraph 真正的难点全教了。旧 02 的「先线性后 agentic」过渡不仅没必要，还漏教了条件边——这正是用户判断「线性图不该教」成立的原因。

agentic 范式天然契合「现代化 AI native」的定位：agent 自主探索、按需取片段、多轮工具调用，对标 omp/hermes 探索本地项目文件的能力，但对象是论文。

## 9. 范围外（本次不做）

- 01/02/03/04 四份文档的具体改写逐行计划（implementation plan 阶段）
- 概念速查 / 项目概览 / 开始指南的同步更新（implementation plan 阶段）
- backend/ 实现代码（本次只改 任务文档/，不改实现）
- 多论文对比的 agent 策略调优（MVP 先跑通单论文内探索 + 跨论文选择）
