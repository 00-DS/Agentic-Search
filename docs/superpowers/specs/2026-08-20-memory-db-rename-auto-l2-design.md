# 记忆层第三版：db.py 更名 + L2 阈值自动触发（设计）

日期：2026-08-20　状态：待用户审阅

## 背景与动因

本轮由用户两个问题触发，过程中暴露一个真实的循环导入 bug：

1. **章节归属错位**：§2.7 `get_memories_for_context`（memory.py 内容）排在 §2.5/2.6 store.py 小节之后，阅读顺序断裂。
2. **L1 淹没 L2**：`get_memories_for_context` 的注入窗口（limit=20）按时间倒序取数，若长期不手动整合，窗口内可能全是 L1、没有 L2——会话摘要永远进不了上下文。L2 纯手动触发在教学上可接受，但需要一个自动兜底。
3. **循环导入 bug（现行拆分契约的缺陷）**：memory.py 运行时调 `load_memories` → import store；store.py 运行时构造 `Memory(**doc)` → import memory。双侧运行时依赖，先加载任一侧即 `ImportError`。现行文档「依赖单向 memory.py → store.py」与 §2.5.3 代码自相矛盾。

## 用户裁决（约束条件）

- 「新堆积 L1」用 **timestamp 对比**度量（晚于现有 L2 的 L1 条数），零新字段。
- 阈值 = **10**；`get_memories_for_context` 窗口 = **2×阈值联动派生**（一个常量定节奏）。
- `get_memories_for_context` **下沉存储文件**（它是数据库操作），文件**更名 db.py**（数据库操作的统称）。
- 自动触发**不设独立函数**，在 `graph.py` 的 `store_memory` 节点内联一段代码——触发时机是编排策略，归图；加工能力归记忆层。
- 手动按钮保留（立即整合，不必等攒满）；L5 仍纯手动。

## 设计

### 文件结构（依赖严格单向 memory.py → db.py → MongoDB）

```
memory/
├── memory.py   # 记忆加工（LLM 侧，纯进出）：extract_l1 / consolidate_l2 / consolidate_profile
│               #   对 db.py 的依赖只有一行：from agentic_search.memory.db import Memory
└── db.py       # 数据库操作（Mongo 侧，零 LLM）：Memory dataclass + 连接初始化 + save_memory/
                #   load_memories + upsert_l2/upsert_profile + get_memories_for_context
                #   + L2_TRIGGER_THRESHOLD = 10
```

- **Memory dataclass 随迁 db.py**（断环关键）：db.py 的 `load_memories` 运行时要构造 `Memory(**doc)`，Memory 留在 memory.py 则反向依赖回归。叙事：「Memory = memories 集合文档的 Python 形态」，数据结构与存取同文件。
- **memory.py 三函数全部纯进出**：数据进（参数）、Memory 出（返回值），不碰库、不碰集合句柄。存储访问全部经函数参数或返回值发生。
- 端点 `/api/consolidate` 与图节点各自 import 所需（routes 调 memory.py 的加工函数 + db.py 的取数/写入；图节点同理），端点/图零集合引用不变。

### 第 2 步章节重排（按文件归属连续）

```
2.1 Memory dataclass（db.py）
2.2 extract_l1           ┐
2.3 consolidate_l2       ├ memory.py（加工）
2.4 consolidate_profile  ┘
2.5 数据库操作 memory/db.py（连接初始化 + save_memory/load_memories）
2.6 幂等写入 upsert_l2 / upsert_profile（db.py）
2.7 记忆注入 get_memories_for_context（db.py，含阈值常量与 2× 联动——收尾，引出第 4 步注入）
```

讲解顺序 = 先加工后存储（依赖反序）；代码块归属标注全部随迁（memory.py 标注 5 处 → 2.2-2.4 保留 3 处，Memory/注入 2 处改 db.py；store.py 标注 6 处全改 db.py）；两个前置节的「memory.py 文件头」示例改为一行 `from agentic_search.memory.db import Memory`；import 清单两行改向。

### L2 自动触发（store_memory 节点内联）

`memory/db.py`：

```python
L2_TRIGGER_THRESHOLD = 10   # 新增 L1 攒够 10 条 → 自动整合 L2

def get_memories_for_context(session_id: str, limit: int = 2 * L2_TRIGGER_THRESHOLD) -> list[Memory]:
    ...
```

`graph.py` store_memory 节点（extract_l1 落库之后追加）：

```python
# —— L2 自动触发：新增 L1（timestamp 晚于现有 L2）达阈值则重整合 ——
l1s = load_memories(state["session_id"], level="L1")
l2s = load_memories(state["session_id"], level="L2")
new_l1 = l1s if not l2s else [m for m in l1s if m.timestamp > l2s[0].timestamp]
if len(new_l1) >= L2_TRIGGER_THRESHOLD:
    upsert_l2(consolidate_l2(l1s))   # 全部 L1 重整合，幂等更新同一条
```

- **联动不变量（写入文档叙事）**：窗口 = 2×阈值 → L2 每次整合刷新 timestamp，其后最多再攒 10 条新 L1 才再触发 → L2 恒在 20 条注入窗口内。「L1 淹没 L2」由构造消解，注入端无需给 L2 特殊配额。
- 触发时机（策略）在图，加工与写入（能力）在记忆层；手动按钮走端点，两处触发点对称。
- 阈值是模块常量（非 Settings 配置）——节奏值，非环境差异项。

### 叙事同步（04 内）

- 学习目标：L2「均手动触发」→「阈值自动 + 手动兜底」，L5 仍手动。
- 触发机制表（§93 附近）：教学列改「阈值自动（新增 L1 ≥ 10）+ 手动按钮即时；L5 纯手动」。
- 差异表：L2 触发行改「TiMeM 空闲超时扫描 vs 教学 阈值自动 + 手动按钮」。
- FAQ：新增「为什么窗口是 2×阈值？」（联动不变量一段话）。
- 第 4 步 store_memory 节点讲解改写（含内联触发段与策略/能力分工一句话）。
- 第 6 步测试：L2 自动触发为图行为，不进零 LLM 单测清单，改为完成检查场景项（连续对话新增 ≥10 条事实后 L2 自动出现、二次触发为更新而非新增）。

## 改动文件清单

| 文件 | 改动 |
|---|---|
| 任务文档/04-TMT记忆系统.md | 章节重排 2.1-2.7、代码块归属标注、store.py→db.py 全局、前置节文件头、store_memory 内联触发、联动不变量叙事、触发机制表/学习目标/差异表/FAQ/完成检查/测试清单 |
| AGENTS.md | 「记忆层双文件」条目重写（db.py 命名、Memory 随迁、纯进出、内联触发、阈值联动）；重要文件表；陷阱 4；记忆端点契约条目微调 |
| 任务文档/概念速查.md | TMT 词条双文件名改 db.py；PyMongo 词条 `memory/store.py` → `memory/db.py` |
| 任务文档/项目概览.md | 4 处 store.py → db.py + memory.py 职责描述微调 |
| 任务文档/01-Python文档工具.md | L174 双文件名同步 |
| 任务文档/02-LangGraph-Agent.md | 目录树 2 行（store.py→db.py）。**02 冻结令的例外申报**：仅改树内文件名 2 行，其余零触碰 |

## 非目标

- 不改 Memory 四字段契约、集合名、幂等键、端点总数、SSE 契约、前端按钮。
- 不引入任何配置项（阈值/窗口均为模块常量）。
- 不改用户已写代码（用户按文档自行迁移）。
