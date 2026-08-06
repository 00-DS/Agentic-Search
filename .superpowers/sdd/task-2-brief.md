# Task 2: 02-LangGraph-Agent.md — 四工具新签名 + 所有引用更新

## Files
- Modify: `任务文档/02-LangGraph-Agent.md`

## Interfaces
- Consumes: Task 1 的 `parse_pdf(path) -> str`、`store_document(doc_id, filename, text)`、`list_documents() -> list[dict]`、`read_document(doc_id) -> dict`（返回完整文档记录含 text 字段）
- Produces: `list_papers()`、`read_paper(doc_id, start_line, end_line)`、`search_papers(pattern, doc_id)`、`extract_abstract(doc_id)` 四个 `@tool` 工具

## 改动点（按文档结构从上到下）

### Step 1: 学习目标第 3 条（line 9）

把 `实现四个论文导航工具（list_papers/list_sections/read_section/search_sections）` 改为 `实现四个论文导航工具（list_papers/read_paper/search_papers/extract_abstract）`

### Step 2: ReAct 概念段落（line 20）

把 `用 list_papers/list_sections/read_section/search_sections 自主探索论文语料库` 改为 `用 list_papers/read_paper/search_papers/extract_abstract 自主探索论文语料库`

### Step 3: tool_calls JSON 示例（line 31）

把 `"function": {"name": "search_sections"` 改为 `"function": {"name": "search_papers"`

### Step 4: mermaid 流程图（lines 84-87）

把 `执行工具（read_section 等）` 改为 `执行工具（read_paper 等）`

把 `services/documents.py<br/>list_documents / read_section` 改为 `services/documents.py<br/>list_documents / read_document`

### Step 5: 前置要求（line 100）

把 `parse_pdf（返回 sections 数组）、store_document、list_documents、read_document、read_section 已实现且测试通过` 改为 `parse_pdf（返回完整纯文本）、store_document、list_documents、read_document 已实现且测试通过`

### Step 6: ReAct 设计说明段落（lines 108-113）

整段替换为：

```markdown
本模块的 Agent 不写死「先读全文再回答」，而是一个 **ReAct 循环**：LLM 拿到问题后，自主决定调用哪个论文导航工具、调用几次、何时认为证据足够、直接作答。它对标 omp/hermes 探索本地代码库的能力——`list_papers` 相当于 `glob`（看有哪些论文），`read_paper` 相当于 `read :50-100`（按行号取片段），`search_papers` 相当于 `grep`（正则定位行号），`extract_abstract` 相当于 `summarizeCode()`（读取时的概览便利），对象从代码换成了论文。

三个逼出 agentic 行为的设计约束：

1. **没有「读整篇论文」的工具**。agent 必须先 `search_papers` 定位行号、再 `read_paper` 按行号取片段——这是「按需取片段」的强约束，既逼出真正的多轮探索，也是多论文场景下不撑爆上下文窗口的根本保障。
2. **`search_papers` 用正则、不用 embedding**。对齐 omp `grep`：参数是正则 `pattern`（不是语义 query），返回命中行+行号+上下文。智能来自 LLM 自主迭代构造正则。**不用向量库、不做 embedding。**
3. **`extract_abstract` 是读取时工具，不是上传预处理**。对齐 omp 的 `summarizeCode()`：agent 按需调用，从完整文本里正则提取 abstract 段落。不在上传时预计算。
```

### Step 7: 目录结构注释（line 143）

把 `parse_pdf 切章节 / list / read / read_section` 改为 `parse_pdf 转纯文本 / list / read_document`

### Step 8: 第 6 步 tools.py 整段重写（lines 368-460）

整段替换为：

```markdown
## 第 6 步：论文导航工具集

这是 agent 的「手和眼」——四个工具，对标 omp 探索代码库的 `glob`/`read`/`grep`/`summarize`。用 LangChain 的 `@tool` 装饰器声明：装饰器会从函数的**类型注解 + docstring** 自动生成工具 schema，告诉 LLM「这个工具叫什么、接收什么参数、干什么」——这正是第 5 步装饰器概念的又一次「点亮」。

新建 `agents/tools.py`：

```python
# agents/tools.py —— 教学示例：四个论文导航工具
import re
from langchain.tools import tool
from agentic_search.services.documents import (
    list_documents, read_document, _documents_collection,
)


def _get_doc_text(doc_id: str) -> str:
    """按 doc_id 取出整篇文档的完整文本。找不到抛 KeyError。"""
    doc = _documents_collection.find_one({"doc_id": doc_id})
    if doc is None:
        raise KeyError(f"文档不存在: {doc_id}")
    return doc["text"]


@tool
def list_papers() -> list[dict]:
    """列出语料库中所有论文。返回 [{doc_id, filename}]，不带正文。
    对标 omp 的 glob：只列有哪些文件，不返回内容——判断相关性靠后续自主探索。
    """
    return list_documents()


@tool
def read_paper(doc_id: str, start_line: int = 1, end_line: int = 50) -> str:
    """读取指定论文的指定行号范围。返回原始文本行。
    对标 omp 的 read :50-100：按行号取片段，而不是返回全文。
    """
    text = _get_doc_text(doc_id)
    lines = text.split("\n")
    # 行号是 1-indexed，列表是 0-indexed
    return "\n".join(lines[start_line - 1 : end_line])


@tool
def search_papers(pattern: str, doc_id: str = "") -> list[dict]:
    """跨语料库（或指定论文）用正则搜索内容。返回 [{doc_id, line_number, line, snippet}]。
    对标 omp 的 grep：参数是正则 pattern（不是语义 query），命中后 agent 通常再调
    read_paper 按行号深入——搜索只给位置和片段，不给全文。
    """
    regex = re.compile(pattern)
    hits = []
    docs = [_documents_collection.find_one({"doc_id": doc_id})] if doc_id else list(_documents_collection.find({}))
    for d in docs:
        if d is None:
            continue
        for i, line in enumerate(d["text"].split("\n"), 1):
            if regex.search(line):
                hits.append({"doc_id": d["doc_id"], "line_number": i, "line": line})
    return hits


@tool
def extract_abstract(doc_id: str) -> str:
    """提取论文的 Abstract 段落。agent 按需调用，快速判断论文是否相关。
    对标 omp 的 summarizeCode()：读取时的概览便利，不是上传预处理。
    """
    text = _get_doc_text(doc_id)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip().lower() == "abstract":          # "abstract" 独立成段才算数
            # 收集其下方第一个非空自然段
            for j in range(i + 1, len(lines)):
                para = lines[j].strip()
                if para:                                  # 找到非空行，收集到空行为止
                    end = j + 1
                    while end < len(lines) and lines[end].strip():
                        end += 1
                    return "\n".join(lines[j:end])
            return "Abstract 标题下方无内容"
    return "未找到独立 Abstract 段落"
```

四工具与 omp 的对应关系：

| 工具 | 签名 | 返回 | 对应 omp |
|------|------|------|----------|
| `list_papers` | `() -> list[dict]` | 语料库所有论文：`doc_id` + `filename`（**不带正文**） | `glob` |
| `read_paper` | `(doc_id, start_line?, end_line?) -> str` | 指定行号范围的原始文本 | `read :50-100` |
| `search_papers` | `(pattern, doc_id?) -> list[dict]` | 正则命中的 `doc_id`+`line_number`+`line` | `grep` |
| `extract_abstract` | `(doc_id) -> str` | Abstract 段落（或未找到提示） | `summarizeCode()` |

**为什么 `search_papers` 用正则、不用 embedding？** 这是对齐 omp `grep` 的核心决策，也是 agentic search 与旧时代 RAG 的根本区别。embedding/向量库会：① 引入额外的 embedding 模型依赖与首次下载；② 上传时对每段文本做向量入库的额外流程；③ 让搜索结果受模型质量制约、不可解释。正则命中是人能读懂的精确匹配，智能来自 LLM 自主迭代构造正则（先搜 `dataset|corpus|benchmark`，看结果再逼近），不是预计算的语义相似度。本项目严格对齐 omp 范式——**正则匹配、零额外依赖、结果可解释**。

**为什么 `extract_abstract` 是工具、不是上传预处理？** 对齐 omp 的 `summarizeCode()`：它是**读取时的可选便利**，agent 按需调用，不是入库步骤。上传时只做格式转换（PDF → 纯文本），不做任何内容分析。提取逻辑也极简：从头找第一个独立成段的 "abstract" 行，取其下方第一个非空自然段。鲁棒性靠一个检查保证——只有 "abstract" 单独占一行才算数（排除 "In this abstract, we..." 这类误命中）。

**验证**：

```bash
cd backend
uv run python -c "from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract; print([t.name for t in [list_papers, read_paper, search_papers, extract_abstract]])"
```

看到四个工具名即正确。
```

### Step 9: 第 7 步 build_graph 工具列表更新（lines 474, 480）

把 `from agentic_search.agents.tools import list_papers, list_sections, read_section, search_sections` 改为 `from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract`

把 `tools = [list_papers, list_sections, read_section, search_sections]` 改为 `tools = [list_papers, read_paper, search_papers, extract_abstract]`

### Step 10: 全文检查残留

确保全文无 `list_sections`/`read_section`/`search_sections`/`section_id`/`sections` 残留。

### Step 11: Commit

```bash
cd "D:\Python\Common\Agentic Search"
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 四工具新签名——list_papers/read_paper/search_papers/extract_abstract"
```

## Global Constraints

- **仅文档范围**：只编辑 `任务文档/02-LangGraph-Agent.md`，绝不碰 `backend/` 代码。
- **纯新版本，零历史包袱**：不出现"旧版"/"原来"/"之前"/"不再"/"改用"等对比性措辞。
- **无 embedding/向量库**。
- **四工具签名（全项目统一）**：`list_papers() -> list[dict]` / `read_paper(doc_id, start_line=1, end_line=50) -> str` / `search_papers(pattern, doc_id="") -> list[dict]` / `extract_abstract(doc_id) -> str`
- **MessagesState**：02 用标准 `MessagesState`（不自定义 AgentState）。
- **装饰器 cross-reference 网保持完整**：02 @retry（第5步）→ 02 @tool（第6步）→ 02 @router（第9步）。
