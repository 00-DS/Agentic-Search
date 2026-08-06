# Task 1: 01-Python文档工具.md — 加入论文导航工具集（新 Step 4）

## 目标
把 02 第 6 步「论文导航工具集」整段搬到 01，作为新 Step 4。01 的定位从「文档地基」变为「文档地基 + Agent 导航工具」——所有 agent 需要的底层能力都在 01 完成。

## Files
- Modify: `任务文档/01-Python文档工具.md`

## 改动点

### Step 1: pyproject.toml 加 langchain 依赖（line ~190）

在 dependencies 数组里加：
```toml
    "langchain",                    # LangChain：@tool 装饰器（把函数注册成 agent 工具）
```

### Step 2: Step 1.5 创建目录结构加 agents/（line ~237）

在 mkdir 命令加 `agents`：
```bash
mkdir -p src/agentic_search/configs src/agentic_search/services src/agentic_search/agents
touch src/agentic_search/configs/__init__.py src/agentic_search/services/__init__.py src/agentic_search/agents/__init__.py
```

### Step 3: 项目结构树加 agents/tools.py（line ~135-140）

在 `services/` 块之后加 `agents/` 块：
```
│       ├── agents/
│       │   ├── __init__.py
│       │   └── tools.py        # 本模块创建：Agent 论文导航工具（list_papers/read_paper/search_papers/extract_abstract）
```

### Step 4: 模块结构 mermaid 图更新（lines 91-115）

在 Services 之后加 Tools 层。修改 mermaid 图，在 `Services` 节点下方加一个 `Tools` 节点：
```
    Services["文档服务<br/>documents.py"]
    Tools["Agent 工具<br/>tools.py"]
```
连线：`Services --> Tools`，`Tools -->|"调用"| Services`

### Step 5: 学习目标更新（lines 9-15）

在学习目标最后加一条：
```
6. 使用 **LangChain `@tool` 装饰器** 在 `agents/tools.py` 中实现四个论文导航工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`），理解装饰器如何从类型注解 + docstring 自动生成工具 schema
```

### Step 6: 插入新 Step 4 — 论文导航工具集（在当前 Step 4 测试之前，即 line ~503 之前）

插入以下完整内容作为新 Step 4（当前 Step 4 测试变 Step 5，当前 Step 5 集成验证变 Step 6）：

```markdown
## 步骤 4：`agents/tools.py` — 论文导航工具集

Agent 的「手和眼」——四个工具，对标 omp 探索代码库的 `glob`/`read`/`grep`/`summarize`。用 LangChain 的 `@tool` 装饰器声明：装饰器会从函数的**类型注解 + docstring** 自动生成工具 schema，告诉 LLM「这个工具叫什么、接收什么参数、干什么」。

> **`@tool` 是什么？** 它是装饰器（decorator）的一种——`@` 语法糖给函数套一层额外逻辑。`@tool` 做的事是：接收下面的函数，从它的参数类型注解和 docstring 提取出工具名、参数描述、用途说明，自动生成一份 LLM 能读懂的 schema。函数体一行没改，但它已经变成了一个「LLM 可以调用的工具」。后续[模块 2](./02-LangGraph-Agent.md) 还会两次「点亮」同一个装饰器机制：`@retry`（自定义重试装饰器）和 `@router.post`（FastAPI 路由注册），以及模块 4 的标准库 `@dataclass`——都是装饰器，只是来自不同的库。

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
    """跨语料库（或指定论文）用正则搜索内容。返回 [{doc_id, line_number, line}]。
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

**为什么 `search_papers` 用正则、不用 embedding？** 这是对齐 omp `grep` 的核心决策。embedding/向量库会引入额外依赖、上传时做向量入库、让搜索结果不可解释。正则命中是人能读懂的精确匹配，智能来自 LLM 自主迭代构造正则——**正则匹配、零额外依赖、结果可解释**。

**为什么 `extract_abstract` 是工具、不是上传预处理？** 对齐 omp 的 `summarizeCode()`：它是**读取时的可选便利**，agent 按需调用，不是入库步骤。上传时只做格式转换（PDF → 纯文本），不做任何内容分析。

**验证**：

```bash
cd backend
uv run python -c "from agentic_search.agents.tools import list_papers, read_paper, search_papers, extract_abstract; print([t.name for t in [list_papers, read_paper, search_papers, extract_abstract]])"
```

看到四个工具名即正确。
```

### Step 7: 旧 Step 4（测试）改为 Step 5，旧 Step 5（集成验证）改为 Step 6

把 `## 步骤 4：编写测试` → `## 步骤 5：编写测试`
把 `## 步骤 5：集成验证` → `## 步骤 6：集成验证`

### Step 8: 完成检查更新

在完成检查里加一条：
```
- [ ] `backend/src/agentic_search/agents/tools.py` 包含四个 `@tool` 工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）
```

### Step 9: 下一步段落更新

把当前的下一段改为：
```
本模块完成了后端包的全部底层能力：包化布局、配置层、文档服务、Agent 导航工具。在[模块 2：LangGraph Agent](./02-LangGraph-Agent.md) 中，Agent 将用 `build_graph()` 把本模块产出的四个工具组装成一个 ReAct 循环，并通过 FastAPI 把它暴露为 HTTP API。
```

### Step 10: 技术概念段落加 @tool 简介

在技术概念部分（在 pytest 段之后），加一个简短段落：

```markdown
### LangChain `@tool` 装饰器

**装饰器（decorator）** 是「在不改写函数体的前提下，给函数套一层额外逻辑」的语法，`@` 只是语法糖。LangChain 的 `@tool` 装饰器从函数的类型注解和 docstring 自动生成工具 schema，让 LLM 能「看到」这个工具的名字、参数、用途。本模块用它把四个普通函数（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）注册成 agent 可调用的工具。[模块 2](./02-LangGraph-Agent.md) 还会用 `@retry`（自定义重试）和 `@router.post`（FastAPI 路由）两次「点亮」同一个装饰器机制。
```

### Step 11: 模块结构描述更新

把当前 line 93 `本模块在后端包中建立三个部分：包化骨架、配置层、文档服务` 改为：
`本模块在后端包中建立四个部分：包化骨架、配置层、文档服务、Agent 导航工具`

### Step 12: 模块产出段落更新

更新 line 17 的产出描述，加 agents/tools.py：
在 `services/documents.py`）之后加 `、Agent 导航工具（`agents/tools.py`）`

### Step 13: Commit

```bash
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): 加入论文导航工具集（agents/tools.py 四工具），平衡 01/02 内容量"
```

## Global Constraints
- 纯新版本，零历史包袱。
- @tool 装饰器在本模块首次引入，是装饰器网络的起点。
- 四工具签名不变：list_papers() / read_paper(doc_id, start_line=1, end_line=50) / search_papers(pattern, doc_id="") / extract_abstract(doc_id)
