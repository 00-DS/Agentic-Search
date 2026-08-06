# Task R2 Report — 02-LangGraph-Agent.md：删 Step 6 + 重编号 + 引用更新

## 状态
✅ 完成。已提交。

## 提交
- Commit: `5962d7f` — `docs(02): 删论文导航工具集（移至 01），重编号 Step 7-12→6-11`
- Diff: `任务文档/02-LangGraph-Agent.md`，1 file changed, **+28 / −132**（净 −104 行：删 Step 6 共 105 行，前置条件 +1 行）
- 仅改动 `任务文档/02-LangGraph-Agent.md`，未碰其他文件。

## 改动摘要（Brief 12 步 + 3 处补漏）

### 删除与重编号（Brief 1-2）
- 删除整段 `## 第 6 步：论文导航工具集`（原 369-473 行：tools.py 四工具代码、对照表、设计说明、验证）。02 不再定义工具。
- 步骤重编号：第 7→6（build_graph）、8→7（Pydantic）、9→8（HTTP 路由）、10→9（瘦入口）、11→10（启动）、12→11（测试）。
- 子步骤重编号：路由 `9.1-9.4 → 8.1-8.4`；测试 `12.1-12.2 → 11.1-11.2`。

### 装饰器网络（Brief 3，核心难点）
- Step 5 收尾注（原 365 行）改为引用 **模块 1 @tool**：`装饰器在[模块 1] 已通过 LangChain @tool 首次介绍。本步手写自定义 @retry… 后续还有第 8 步的 @router.post…`。
- 最终装饰器链：**模块 1 @tool → 02 第 5 步 @retry → 02 第 8 步 @router → 04 @dataclass**。02 的装饰器起点是 @retry，不再引入 @tool。

### 引用更新（Brief 4-5）
- build_graph 注释：`# ① 工具集（第 6 步定义）` → `# ① 工具集（模块 1 定义）`。
- 逐点拆解：`把第 6 步四个 @tool` → `把模块 1 四个 @tool`。
- Step 5 内引用 `第 7 步图组装` → `第 6 步图组装`（含 314/355/360/528 行）。
- 保留不变的引用：第 2 步（Hello World 桩）、第 4 步（MessagesState）、第 5 步（@retry）——编号未变。

### 其他（Brief 6-11）
- 学习目标 3：`实现四个论文导航工具` → `用 build_graph() 把[模块 1] 的四个工具组装成 ReAct 循环`。
- 前置条件：新增 `agents/tools.py 四个 @tool 工具已实现`（模块 1 产出）。
- 目录结构注释：`tools.py` 标为 `模块 1 已实现`（并调整为 tools.py 在前、graph.py 在后），`documents.py` 注释改为 `parse_pdf / list_documents / read_document`。
- 依赖表：langchain「用在哪」由 `agents/tools.py、agents/graph.py` 改为 `agents/graph.py`（tools.py 已归 01；langchain 仍被 graph.py 的 init_chat_model/bind_tools 使用，故保留）。
- 核心设计段（Brief 9）确认无 Step 6 引用，未改。
- 完成检查段（Brief 11）均为命令式检查、无步骤编号，未改。

### Brief 之外的 3 处补漏（任务要求「更新所有内部交叉引用」）
Brief 未显式列出，但它们引用了被删步骤，必须一并修：
1. 技术概念·装饰器段（原 48 行）：`在第 6 步用 LangChain @tool…在第 9 步发现 @router.post` → 改为 `第 8 步发现 @router.post；[模块 1] 的 @tool… 也是装饰器`。
2. Step 2 代码注释（原 187 行）：`见第 6、7 步` → `见第 6 步`。
3. Step 2 正文（原 236 行）：`（见第 6、7 步）` → `（工具来自[模块 1]，组装见第 6 步）`。

## 验证
grep 全文确认：
- ✅ 无 `第 12 步`，无 `第 6 步：论文导航工具集`，无 `见第 6、7 步`，无 `第 6 步的 LangChain @tool`，无 `第 9 步的 FastAPI`，无旧子步骤 `9.x`/`12.x`，无 `本模块新建…tools`。
- ✅ 标题序列完整：第 1-11 步；子步骤 `1.1-1.2 / 8.1-8.4 / 11.1-11.2`。
- ✅ 残留的 `第 7-11 步` 字样均为重编号后的合法步骤（Pydantic/路由/瘦入口/启动/测试），上下文正确。
- ✅ 装饰器收尾注引用「模块 1 @tool」而非「第 6 步」。

## 关注点 / Concerns
1. **依赖命令未精简**：Brief Step 10 提示「langchain 已由模块 1 安装，可能不再重复列出」。本次仅在依赖表更正了「用在哪」列（去掉 tools.py），保留了 `uv add` 命令中的 langchain/langchain-openai —— 这些仍被 02 的 graph.py 实际使用，且 `uv add` 幂等无害；删它们对只读 02 跳过 01 的学习者有断链风险。若希望严格去重，可后续从 02 的 `uv add` 行移除 langchain（仅留 langgraph/fastapi/uvicorn 等 02 首装项），但需同步调整依赖表措辞。
2. **目录树顺序调整**：按 Brief Step 8 示例将 agents/ 下 tools.py 置于 graph.py 之前（先列模块 1 依赖、后列本模块新建），便于阅读。纯呈现调整。
3. **未运行 lint/格式化**：按约束跳过。Git 提示 LF→CRLF（Windows 正常现象），不影响内容。
