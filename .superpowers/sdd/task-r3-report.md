# Task 3 报告：同步三份总览文档的模块边界

**状态**：✅ 完成
**Commit**：`e5104e1` — `docs(全局): 同步模块边界——agents/tools.py 归入模块 1`
**改动量**：3 files, +16 / -13

## 背景

模块再平衡后，`agents/tools.py`（四个 `@tool` 导航工具：`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）从模块 2 移入模块 1。模块 2 现聚焦于 `build_graph()` 组装 ReAct 图 + FastAPI API 层。三份总览文档（概念速查 / 项目概览 / 开始指南）此前仍把工具归属于模块 2，且项目概览的目录树与职责表完全遗漏了 `tools.py`。

## 具体修改

### 任务文档/概念速查.md
1. **装饰器条目（本项目用法）**：`@tool` 由「模块 2 的 LangChain `@tool`」改为「**模块 1** 的 LangChain `@tool`」，并按装饰器网络顺序重排——① 模块 1 `@tool` → ② 模块 2 `@retry` → ③ 模块 2 `@router` → ④ 模块 4 `@dataclass`。
2. **装饰器条目（延伸阅读）**：新增「[模块 1 第 4 步]（LangChain `@tool` 的实现）」链接，与已有的「模块 2 第 5 步（`@retry`）」并列。
- Agentic Search 条目（graph.py = 模块 2，描述循环与工具调用，未错误归属工具定义）与 LangGraph 条目（描述 bind_tools/ToolNode 组装）经核实无需改动。

### 任务文档/项目概览.md
1. **文件结构树**：补上 `agents/tools.py`（标注「模块 1」），`graph.py` 注释从「+ 4 工具 + 条件边」修正为「+ 条件边（模块 2）」——工具定义不再挂在 graph.py 上。
2. **各层职责一览**：新增 `agents/tools.py` 条目；`graph.py` 改为「`bind_tools` 绑定 `tools.py` 的四个导航工具」。
3. **M1 学习目标**：加入「Agent 导航工具（`@tool`）」。
4. **M1 内容列表**：新增第 3 项 `agents/tools.py`（`@tool` 声明四工具），`graph.py` 降为第 4 项并改为「组装」措辞，后续项重新编号。
5. **M1 产出**：补「论文导航工具（4 个 `@tool`）」。

### 任务文档/00-开始指南.md
1. **「你将学到什么」表**：模块 1 行从「文档处理工具 + pytest 测试」补为「+ Agent 导航工具（`@tool`）」。
2. **学习路径·模块 1**：补「并用 `@tool` 装饰器实现四个论文导航工具」。
3. **学习路径·模块 2**：措辞从「用 LangGraph 搭一个 ReAct agent——LLM 自主调 list_papers...等工具」改为「把**模块 1 的四个工具**组装成 ReAct agent——LLM 自主调这些工具」，明确模块 2 是组装而非定义。

## 验证

- `grep` 全三文件：无残留「模块 2 ... `@tool`」错误归属（两条命中均为修正后的正确排列：模块 1 `@tool` + 模块 2 `@retry` 同行，属误报）。
- `grep` 确认 `tools.py` 已出现在项目概览的目录树、职责表、M1 内容、技术栈表四处。
- 无残留 graph.py「+ 4 工具」字样。

## 关注点 / 备注

- **两套「模块」概念并存**：项目概览用 M1/M2/M3 做后端/前端/记忆的高层分组（M1=后端=教学模块 01+02），而教学文档用 模块 1/2/3/4。本次再平衡在项目概览的 M1（后端）内部生效——`tools.py` 与 `graph.py` 同属后端 M1，只是教学归属从 02 移到 01。目录树中为两者标注了「模块 1/模块 2」以显式反映教学边界，未改动 M1/M2/M3 高层分组。
- 概念速查的 Agentic Search、LangGraph、pymupdf、数据存储等条目引用工具时只说「agent 经 read_paper/search_papers」等用法，未绑定模块号，无需改动。
