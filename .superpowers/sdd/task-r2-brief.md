# Task 2: 02-LangGraph-Agent.md — 删 Step 6 + 重编号 + 引用更新

## 目标
02 的 Step 6（论文导航工具集）已移到 01。02 删除该步骤，后续步骤重编号（7→6, 8→7, ..., 12→11），更新所有内部交叉引用。02 的定位变为「组装 ReAct agent 图 + FastAPI API」。

## Files
- Modify: `任务文档/02-LangGraph-Agent.md`

## 改动点

### Step 1: 删除第 6 步（论文导航工具集）

删除从 `## 第 6 步：论文导航工具集` 到下一个 `## 第 7 步` 之前的全部内容（含分隔线 `---`）。

### Step 2: 重编号所有后续步骤

- `## 第 7 步：组装 ReAct agent 图` → `## 第 6 步：组装 ReAct agent 图`
- `## 第 8 步：Pydantic 数据模型` → `## 第 7 步：Pydantic 数据模型`
- `## 第 9 步：HTTP 路由` → `## 第 8 步：HTTP 路由`
- `## 第 10 步：瘦入口` → `## 第 9 步：瘦入口`
- `## 第 11 步：启动服务` → `## 第 10 步：启动服务`
- `## 第 12 步：编写测试` → `## 第 11 步：编写测试`
- 子步骤编号同步：`### 12.1` → `### 11.1`, `### 12.2` → `### 11.2`
- 路由子步骤：`### 9.1` → `### 8.1`, `### 9.2` → `### 8.2`, `### 9.3` → `### 8.3`, `### 9.4` → `### 8.4`

### Step 3: 更新 Step 5 装饰器段落的 cross-reference

把当前 line 365 的：
```
> 装饰器是本模块的**主讲解入口**。后续会两次「点亮」同一个机制：第 6 步的 LangChain `@tool`（把函数注册成 agent 工具）、第 9 步的 FastAPI `@router.post`（把函数注册成 HTTP 路由），以及模块 4 的标准库 `@dataclass`——都是装饰器，只是来自不同的库。
```
改为：
```
> 装饰器在[模块 1](./01-Python文档工具.md) 已通过 LangChain `@tool`（把函数注册成 agent 工具）首次介绍。本步手写自定义 `@retry`，是装饰器的第二次「点亮」。后续还有第 8 步的 FastAPI `@router.post`（把函数注册成 HTTP 路由），以及模块 4 的标准库 `@dataclass`——都是装饰器，只是来自不同的库。
```

### Step 4: 更新 build_graph（旧 Step 7→新 Step 6）中的引用

- `# ① 工具集（第 6 步定义）` → `# ① 工具集（模块 1 定义）`
- `把第 6 步四个 @tool 函数的 schema 注入 LLM` → `把模块 1 四个 @tool 函数的 schema 注入 LLM`
- `具体怎么包到 .invoke() 上，在第 7 步图组装里展开` → `具体怎么包到 .invoke() 上，在第 6 步图组装里展开`（这是 Step 5 里的引用，line 314）
- `第 7 步用 llm_with_tools.invoke 展开` → `第 6 步用 llm_with_tools.invoke 展开`（Step 5 里的注释，line 360）
- `真实写法见第 7 步` → `真实写法见第 6 步`（Step 5 里的引用，line 355）
- `这正是第 5 步埋下的 @retry 与第 7 步图组装的衔接点` → `这正是第 5 步埋下的 @retry 与第 6 步图组装的衔接点`

### Step 5: 更新 build_graph 里的「逐点拆解」段落

`把第 2 步的桩函数换成真 agent` — 保持引用第 2 步（Hello World，编号不变）
`第 6 步四个 @tool 函数` → `模块 1 的四个 @tool 函数`
`第 2 步手写的 get_time 桩` — 保持（第 2 步不变）

### Step 6: 更新学习目标

把 line 9：
```
3. 实现四个**论文导航工具**（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`），理解 agent 如何像 omp/hermes 用 `glob`/`read`/`grep` 自主探索代码库那样，探索论文语料库
```
改为：
```
3. 用 `build_graph()` 把[模块 1](./01-Python文档工具.md) 的四个论文导航工具组装成一个 **ReAct 循环**——理解 agent 如何像 omp/hermes 用 `glob`/`read`/`grep` 自主探索代码库那样，探索论文语料库
```

### Step 7: 更新前置条件

在 line 100 之后加一条：
```
- `agents/tools.py` 中四个 `@tool` 工具（`list_papers`/`read_paper`/`search_papers`/`extract_abstract`）已实现
```

### Step 8: 更新目录结构注释（line ~143）

在目录结构里，`documents.py` 下面加一行注释标明 tools.py 来自模块 1：
```
    │       └── documents.py     # 模块 1 已实现：parse_pdf / list_documents / read_document
    ├── agents/
    │   ├── __init__.py
    │   ├── tools.py             # 模块 1 已实现：list_papers / read_paper / search_papers / extract_abstract
    │   └── graph.py             # 本模块创建：ReAct agent 图
```

### Step 9: 更新核心设计段落（line ~108-116）

核心设计段落中 `三个逼出 agentic 行为的设计约束` 不需要改（约束本身不变）。但确认没有引用已删除的 Step 6。

### Step 10: 更新 02 Step 1 依赖安装

02 的 Step 1.2 现在只安装 agent 图相关依赖。确认 `langchain` 已由模块 1 安装，这里可能不再需要重复列出——检查并按需调整。

### Step 11: 完成检查更新

确认完成检查中引用的步骤编号都更新了。

### Step 12: Commit

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 删论文导航工具集（移至 01），重编号 Step 7-12→6-11"
```

## Global Constraints
- 纯新版本，零历史包袱。
- @tool 不在 02 引入（已在 01），02 的装饰器起点是 @retry。
- 四工具签名不变。
- 装饰器网络：01 @tool → 02 @retry（第5步）→ 02 @router（第8步）→ 04 @dataclass。
