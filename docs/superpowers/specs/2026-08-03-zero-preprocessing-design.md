# 设计：零预处理架构——去掉 section 切分，完整文本 + 行号工具

> 日期：2026-08-03
> 状态：已确认
> 范围：`任务文档/` 下全部 `.md` 教学文档

---

## 1. 背景与问题

当前 01 在上传时用 `get_text("dict")` 提取版式结构、用标题字号启发式把论文切成 `sections` 数组存入 MongoDB。这是一层**预处理**——在上传时分析内容、切分章节、结构化存储。

这与 omp 的文件读取模型根本冲突。源码核实（`can1357/oh-my-pi` `docs/tools/read.md`）：

- omp 的文件以**原始形态**存在磁盘上，不做任何入库预处理
- `read` 通过 `streamLinesFromFile()` 按行号 `:50-100` 流式读取原始文件
- `grep` 用 Rust ripgrep 正则搜索原始文件内容，返回匹配行+行号+上下文
- `summarizeCode()` 是**读取时的可选便利**（仅对 <2MiB 文件），不是入库步骤

预处理不仅不必要，还会降低效果：标题启发式可能切错位置，切分后丢失跨章节上下文，agent 被迫在预切的片段里搜索而非自主定位。智能应来自 LLM 的自主迭代搜索策略，不是预计算的结构化切分。

## 2. 核心原则

**上传时零预处理。** PDF → `get_text("text")` 纯文本 → 完整存入 MongoDB。与 omp 文件原始存盘完全同构。

文本在 MongoDB 里是完整形态，agent 用工具现取现读。

## 3. 工具集设计（四工具，全项目统一）

```python
list_papers() -> list[dict]                            # [{doc_id, filename}]
read_paper(doc_id, start_line=1, end_line=50) -> str   # 按行号范围读原始文本
search_papers(pattern, doc_id="") -> list[dict]        # [{doc_id, line_number, line, snippet}]
extract_abstract(doc_id) -> str                         # 提取 abstract 段落
```

### 3.1 list_papers

对齐 omp `glob`。只返回 `doc_id` + `filename`，不返回任何内容。判断论文相关性靠 agent 自主探索。

### 3.2 read_paper

对齐 omp `read :50-100`。参数 `start_line` / `end_line` 是行号（1-indexed），默认返回前 50 行。底层从 MongoDB 取出完整 `text`，按 `\n` 分割后切片。返回的是原始文本行——agent 看到的是论文的真实排版。

### 3.3 search_papers

对齐 omp `grep`。参数是正则 `pattern`（不是语义 query），可选 `doc_id` 限定单篇。遍历文档文本的每一行，用 `re.search(pattern, line)` 匹配，返回 `line_number` + 原始行内容 + 上下文片段。agent 拿到行号后再用 `read_paper` 深入。

**不用 embedding、不用向量库。** 正则匹配是人能读懂的精确匹配，智能来自 LLM 自主迭代构造正则。

### 3.4 extract_abstract

对齐 omp `summarizeCode()` 的角色——一个**读取时的概览便利**，agent 按需调用，不是上传预处理。

提取逻辑（最简方案）：

```
1. 从 MongoDB 取出完整 text，按 \n 分割成行
2. 从头扫描，找第一行满足 line.strip().lower() == "abstract"
   （鲁棒性：只有 "abstract" 独立成段才算数，排除 "In this abstract..." 误命中）
3. 找到 → 收集其下方第一个非空自然段（连续非空行，直到空行）
4. 没找到 → 返回 "未找到独立 Abstract 段落"
```

## 4. services/documents.py 函数签名

```python
parse_pdf(path) -> str                    # get_text("text") → 完整纯文本
store_document(doc_id, filename, text)    # 写入 MongoDB
list_documents() -> list[dict]            # → [{doc_id, filename}]
read_document(doc_id) -> dict             # → {doc_id, filename, text, uploaded_at}
```

**MongoDB schema**：`{doc_id, filename, text, uploaded_at}`——扁平文档，`text` 是完整纯文本。无 `sections` 数组，无 `section_id`/`title`/`level`。

## 5. omp 对齐映射

| omp 工具 | 本项目工具 | 对齐点 |
|---|---|---|
| 文件原始存盘 | text 完整存 MongoDB | 零预处理 |
| `glob` → 路径列表 | `list_papers` → `[{doc_id, filename}]` | 只列不读 |
| `read :50-100` → 原始行 | `read_paper(doc_id, 50, 100)` → 原始文本 | 按行号取 |
| `grep pattern` → 匹配行+行号 | `search_papers(pattern)` → 匹配行+行号 | 正则搜索 |
| `summarizeCode()`（读取时） | `extract_abstract`（agent 按需调） | 读取时概览 |

## 6. 删除清单

| 删除项 | 原因 |
|---|---|
| `get_text("dict")` | 改用 `get_text("text")`，不需要版式结构 |
| `_extract_sections()` + 标题启发式 | 不做切分 |
| `sections` 数组 / `section_id`/`title`/`level` | 扁平 `text` 替代 |
| `read_section(doc_id, section_id)` | `read_paper(doc_id, start_line, end_line)` 替代 |
| `list_sections(doc_id)` 工具 | `extract_abstract` + `read_paper` 替代 |
| `search_sections(pattern)` | `search_papers(pattern)` 替代 |
| 字号/spans/blocks 版式教学 | `get_text("text")` 不需要 |

## 7. 受影响文件

| 文件 | 改动规模 | 说明 |
|---|---|---|
| 01-Python文档工具.md | 大改 | 步骤 3+3.1 重写（parse_pdf 简化、删 _extract_sections、schema 扁平化），技术概念删版式教学，学习目标/函数表更新 |
| 02-LangGraph-Agent.md | 大改 | 第 6 步工具定义全换（四工具新签名），ReAct 图/diagram 更新，所有工具引用、对应关系表、设计说明更新 |
| 概念速查.md | 中改 | pymupdf 条目（删 dict/版式，改 text）、MongoDB 条目（schema 扁平化）、LangGraph/Agent 条目（工具名）、Agent 条目（搜索策略轨迹） |
| 项目概览.md | 中改 | 架构图、数据流图、工具列表、技术栈表、M1 描述 |
| 00-开始指南.md | 小改 | 学习路径工具名 |

## 8. 文档写法铁律

**纯新版本，零历史包袱。** 文档中不出现任何与旧架构相关的说明——不写"旧版"/"原来"/"之前"/"不再"/"改用"等对比性措辞。读者看到的是这套架构从第一天就长这样。每个概念只按当前设计讲解一次。

## 9. 验收标准

1. `grep -rn "section\|sections\|section_id" 任务文档/` → 0（含概念速查/项目概览/00）
2. `grep -rn "get_text.*dict\|dict.*get_text\|标题启发式\|heading\|span\|block.*type\|字号" 任务文档/` → 0
3. `grep -rn "list_sections\|read_section\|search_sections" 任务文档/` → 0
4. `grep -rn "list_papers\|read_paper\|search_papers\|extract_abstract" 任务文档/` → 四工具全在
5. `grep -rn "extract_abstract" 任务文档/02-LangGraph-Agent.md` → ≥1（工具有定义）
6. 01 `parse_pdf` 用 `get_text("text")`，schema 是扁平 `{doc_id, filename, text, uploaded_at}`
7. 文档无"旧版"/"原来"/"之前"/"不再"对比性措辞
