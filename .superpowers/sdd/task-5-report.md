# Task 5 Report — `任务文档/04-TMT记忆系统.md`（记忆节点挂 agent 循环前后）

> ⚠️ **此文件先前内容已废弃并覆盖。** 旧内容是针对 `概念速查.md` 的一份过期报告（引用了不存在的 commit `3a75c8a`，经 `git cat-file -t 3a75c8a` 验证为 `Not a valid object name`）。那属于一次已流产的任务编号周期。本计划（`docs/superpowers/plans/2026-08-02-agentic-search-redesign.md`）中 **Task 5 = 04 记忆节点挂 agent 循环前后**，本报告即针对此任务。

## Brief 来源说明

- `.superpowers/sdd/task-5-brief.md` 同样是过期的概念速查内容，未采用。
- 实际依据：plan 文件 `Task 5` 节（5 步）+ 全局约束 + 任务分派头部说明。

## Steps applied (5/5)

| Plan Step | 动作 | 状态 |
|-----------|------|------|
| 1 — 改记忆节点拓扑说明（约第 143 行「集成到 LangGraph 图」） | 重写「第 4 步：集成到 Agent 图」（实际位于原 line 360-378） | ✅ |
| 2 — 确认 `@dataclass` 装饰器呼应（约第 123 行） | line 123 呼应保留，指向 02 `@retry` | ✅ 已确认 |
| 3 — 确认 L2 整合端点不变 | `/api/consolidate` 全段未动 | ✅ 已确认 |
| 4 — grep 一致性扫描 | 见下方「grep 扫描」 | ✅ |
| 5 — Commit | `633d54b` | ✅ |

## Step 1 详情：拓扑重写（第 4 步）

**旧拓扑（线性图，已删除）：**
```
__start__ → analyze_intent → retrieve_memory → read_and_answer → store_memory → __end__
```
旧文把记忆节点插在两个线性节点之间，且依赖 `SearchState` 的 `retrieved_memories` 字段、把记忆作为「额外上下文加入 LLM prompt」。

**新拓扑（agent ReAct 循环，记忆包裹循环）：**
```
__start__ → retrieve_memory → [ llm_call ⇄ tool_node ] → store_memory → __end__
```
- `retrieve_memory`（循环**开始前**）：调 `memory.retrieve(query)`，把相关 L1/L2 记忆格式化为一条 `SystemMessage` 追加进 State 的 `messages`，再进 `llm_call`——记忆对 agent 透明。
- `store_memory`（循环**结束、`__end__` 前**）：把本轮对话（问题 + agent 最终回答）传给 `extract_l1` 提取事实，存 MongoDB。不修改 `messages`，只产生副作用。
- 条件边：`should_continue` 看到 `tool_calls` → `tool_node`（继续循环）；否则走出循环到 `store_memory`（原直接到 `__end__`，现多走一站）。
- State：`AgentState`（带 `messages`、`question`）再加一个 `session_id` 字段供 store_memory 打 L1 会话标签。废弃 `retrieved_memories` 字段与 `SearchState` 类型名（记忆直接混入 `messages`）。

措辞与 02 一致：复用 `llm_call`/`tool_node`/`should_continue`/`AgentState`/`messages`（这些符号经 grep 02 核实存在：02 line 296 `class AgentState`、501 `llm_call`、507 `should_continue`、531 拓扑图）。

## Step 2 详情：装饰器 cross-reference 网完整

- 04 line 123 `@dataclass 也是装饰器` 呼应 → 指向 02 `@retry`。**保留未动。**
- 02 `@retry` 仍存在（Task 2/3 已提交，f5acecc/d4f3c7c）：02 第 5 步 line 321-374 完整定义 + 第 7 步 line 500-501 `@retry(max_attempts=3)` 包在 `llm_call` 上。**呼应非悬空指针。** ✅
- 全网五处：概念速查条目 / 02 技术概念 / 02 第5步 / 02 第9步 `@router` / 04 `@dataclass` —— 04 这环已确认完好。

## Step 3 详情：`/api/consolidate` 未变

第 3 步（line 301-356）整段未触碰：`@app.post("/api/consolidate")`、`ConsolidateRequest`、`find_one` 幂等检查 + `update_one` 增量更新、前端 `consolidateMemory()` 按钮逻辑全部原样。L2 整合与 agent 拓扑解耦（独立触发路径），故无需改措辞。

## grep 扫描（Step 4）

```
$ grep -nE "analyze_intent|read_and_answer|_read_first_document|retrieved_memories|SearchState" 任务文档/04-TMT记忆系统.md
(no matches)   ✅

$ grep -n "@dataclass" 任务文档/04-TMT记忆系统.md
110:@dataclass          (Memory 类定义)
123:**`@dataclass` 也是装饰器** ... 指向 02 @retry
437:- **Python dataclasses 官方文档** ... @dataclass 装饰器 ...   ✅ 三处均在
```

- 旧线性图节点（`analyze_intent`/`read_and_answer`）= **0**
- 旧 State 概念（`retrieved_memories` 字段、`SearchState` 类型名）= **0**（已随拓扑重写一并清除）
- `@dataclass` 呼应 = **在**（line 110/123/437）

## 同 commit 一并落地的 04 一致性修复

工作树中 04 在本任务前已有未提交改动（模块编号随 02/03 交换同步 + `@dataclass` 呼应新增）。这些改动无其他任务归属（Task 6 只管概念速查/项目概览/00），故随 Task 5 一同提交：
- line 3 前置模块链接修正（03-LangGraph→02-LangGraph，02-HTML→03-HTML）
- line 123 `@dataclass` 呼应新增
- line 307（3.1）、line 341（3.2）模块链接修正

## Diff 规模

`任务文档/04-TMT记忆系统.md` — 14 insertions, 10 deletions（净 +4 行）。改动集中在第 4 步拓扑段 + 散落链接/呼应修正。Memory 数据结构、L1/L2 逻辑、MongoDB CRUD（extract_l1/consolidate_l2/save_memory/load_memories/retrieve）**全部未动**。

## Commit

`633d54b` — `docs(04): 记忆节点挂 agent 循环前后（retrieve 在前，store 在后）`

## 范围遵守

- 仅改 `任务文档/04-TMT记忆系统.md`，backend/ 未动。✅
- 与 T4Implementer（Task 4 = 03 前端）无文件冲突——不同文件。✅
- 装饰器 cross-reference 网（02 @retry ↔ 04 @dataclass ↔ 02 @router）未破坏。✅

## Concerns / 备注

1. **过期 brief/report 文件**：`.superpowers/sdd/task-5-brief.md` 与本报告文件原内容均为概念速查的过期产物（引用不存在的 commit `3a75c8a`）。本报告已覆盖 task-5-report.md；task-5-brief.md 仍过期，但不在本任务改动范围（`任务文档/` only），留给控制器清理。
2. **`session_id` 的归宿**：新拓扑要求 `AgentState` 加 `session_id` 字段。这是对 02（已定稿）的状态扩展；02 当前 `AgentState` 只有 `messages`/`question`（02 line 296-299）。若后续要让 02 的 AgentState 真正带上 session_id，需回头补 02——但 04 文档已用「需再加一个 session_id 字段」的措辞把这点标明，教学上自洽，不算 dangling。属于可选后续，非本任务范围。
3. plan Step 1 给的行号「约第 143 行」是预估，实际目标段在 line 360（第 4 步）。已正确定位并改写，无影响。
