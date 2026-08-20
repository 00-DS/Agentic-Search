# 设计：memory/ 拆分——memory.py（记忆加工）+ store.py（记忆存储）

> 日期：2026-08-20
> 背景：04 §2.5 把 Mongo CRUD 与 LLM 记忆加工混在同一个 store.py，职责不清；§2.6 等处"service 层"术语与 02 的项目级分层（services/ 目录）指代冲突，读者无法对应。用户决策：拆两个文件，store.py 专管数据库操作，原 store.py 的记忆加工逻辑改名 memory.py；"service 层"含糊只在 04 文字层面修，不做代码级更新。

## 问题

1. **双职责文件**：04 的 store.py 同时装 LLM 记忆加工（extract_l1/consolidate_l2/consolidate_profile——业务逻辑）与 Mongo CRUD（save/load/upsert——持久化），读者分不清哪是哪。
2. **术语冲突**："service 层"在 02:46 指项目级分层中的 services/ 目录（documents.py）；04 却把 memory/store.py 也称"service 层"（§2.5 L411、§2.6 L451/L482/L563）——同一术语两个所指。

## 方案（已批准）

### 1. 文件与职责（代码形态约定，用户实现时照此落码）

```
backend/src/agentic_search/memory/
├── __init__.py
├── memory.py     # 记忆加工：Memory dataclass、extract_l1、consolidate_l2、
│                 #   consolidate_profile、get_memories_for_context
└── store.py      # 记忆存储：_client/_db/_memories_collection、save_memory、
                  #   load_memories、upsert_l2、upsert_profile
```

- 依赖方向：`memory.py` → `store.py`（`get_memories_for_context` 调 `load_memories`）；`api/routes.py` → 两者；`agents/graph.py` → 只 `memory.py`。无环。
- 接口零变化：函数签名、返回值、集合名 `memories`、幂等键全部原样，只搬家。
- 语义：store = 仓库/存储（持久化），memory = 记忆本身（加工）。

### 2. 04 文档改动（本次执行）

| 位置 | 改动 |
|---|---|
| 第 2 步标题与开头 | 「实现 `memory/store.py`」→「实现记忆层：`memory/memory.py`（加工）与 `memory/store.py`（存储）」；import 清单拆两行：`from agentic_search.memory.memory import Memory, extract_l1, consolidate_l2, consolidate_profile, get_memories_for_context` / `from agentic_search.memory.store import save_memory, load_memories, upsert_l2, upsert_profile` |
| §2.1–2.4、§2.7 | 代码示例头部标注 `# memory/memory.py`；§2.2 讲解中 store.py 头部 import 的表述同步 |
| §2.5 | 标题「MongoDB 存取（PyMongo CRUD）」→「记忆存储 `memory/store.py`（PyMongo CRUD）」；四个小节代码块标注 `# memory/store.py`；`_memories_collection` 讲解改为"存储细节收在 store.py 内部，端点与图节点只调函数、从不碰集合" |
| §2.6 | 标题补文件归属「幂等写入：`upsert_l2` 与 `upsert_profile`（`memory/store.py`）」 |
| "service 层"全部替换（5 处） | 换用二分明确表述：「存储层（store.py，专管 MongoDB 读写）」与「记忆加工（memory.py，专管 LLM 提炼）」；§3.2 L563「幂等由 service 层保证」→「幂等由存储层的 upsert 封装保证」 |
| 前置小节 | store.py 文件头部说明同步为 memory.py 头部（call_llm/json/datetime 归 memory.py；store.py 头部为 pymongo 三行） |
| 第 4 步 / 完成检查 | store_memory 节点讲解 import 路径、检查表第一项拆为两文件表述 |
| FAQ | 视 grep 结果处理 store.py 单文件表述 |

### 3. 周边文档同步（本次执行）

| 文件 | 改动 |
|---|---|
| 概念速查.md | `memory/store.py 实现 L1/L2/L5` → `memory/memory.py`（加工）+ `memory/store.py`（存储）二分；save/load 表述指向 store.py |
| AGENTS.md | 「记忆层分层」条目重写为双文件职责 + 依赖方向（memory.py → store.py → Mongo；graph 只 import memory.py）；重要文件表加 memory.py 行；"service 层"字样替换 |
| 01-Python文档工具.md | L174「`memory/store.py` 由模块 4 创建」→「`memory/memory.py` 与 `memory/store.py` 由模块 4 创建」 |
| 00/02/03 | grep 确认后按需同步（02 目录树 L148 注释、03 如有） |

### 4. 验收

1. 04 内 `grep "service 层"` 零命中。
2. 04 所有代码块的文件归属标注与职责表一致（memory.py：2.1–2.4/2.7；store.py：2.5/2.6）。
3. 函数签名、集合名、幂等键与改前逐字一致（仅文件归属注释变化）。
4. 概念速查 / AGENTS.md / 00/01/02/03 无 store.py 单文件旧表述残留（grep `store.py` 逐处核对归属正确）。
5. FAQ / 完成检查条目数与围栏平衡完好。

## 分工

§1 为代码形态约定（用户实现时落码）；§2–§3 为本次文档改动（助手执行）；§4 随文档改动即时验收。
