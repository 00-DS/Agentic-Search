# 记忆层 db.py 更名 + L2 阈值自动触发 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准 spec（`docs/superpowers/specs/2026-08-20-memory-db-rename-auto-l2-design.md`，commit `91c41e8`）修订教学文档：`memory/store.py` 更名 `memory/db.py`、Memory dataclass 随迁断环、store_memory 节点内联 L2 阈值自动触发、注入窗口 2×阈值联动，并同步周边文档。

**Architecture:** 纯文档任务（教学文档定契约，用户自己落码）。04 为主战场；AGENTS.md/概念速查/项目概览/01 同步；02 只改目录树 2 行（冻结例外已在 spec 申报）。所有编辑给出逐行 old→new，验收用 grep 计数 + 围栏平衡 + git diff 行数。

**Tech Stack:** Markdown 教学文档；grep/awk 验收；git 提交（前缀 `docs(04):` / `docs:`）。

## Global Constraints

- 本计划只改文档，不碰 `backend/` 任何代码（用户自行迁移）。
- 02 文档冻结令的**唯一例外**：目录树 L148-149 两行（store.py→db.py），其余零触碰。
- 图节点名 `store_memory`/`retrieve_memory` 不改（02 前向引用契约）。
- Memory 四字段、集合名 `memories`、幂等键、端点总数 4、SSE 契约、前端按钮 id 全部不动。
- 措辞：只写「为什么/如何用」；中文弯引号；禁否定式技术选型表述。
- 编辑 04 的 FAQ/检查表区时先 read 锚定行号，改完立刻数计数（历史上该区多次错插/顶条）。
- 每个任务结束跑该任务的 grep 验收；全部完成后提交。

---

### Task 1: 04 第 2 步引言 + 两个前置节（import 改向、文件头示例）

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`（L109-116、L123、L151-164、L272 附近）

**Interfaces:**
- Produces: 全文后续任务引用的定稿表述——memory.py = 加工（extract_l1/consolidate_l2/consolidate_profile，纯进出）；db.py = 数据库操作（Memory + CRUD + upsert + 注入取数 + L2_TRIGGER_THRESHOLD）；依赖单向 `memory.py → db.py`。

- [ ] **Step 1: 改第 2 步标题与引言（L109-116）**

原文（现行）：

```markdown
## 第 2 步：实现记忆层 `memory/`——`memory.py`（加工）与 `store.py`（存储）

记忆层拆两个文件，各管一件事：**`memory/memory.py` = 记忆加工**（Memory 数据结构、LLM 提取与整合、上下文注入取数），**`memory/store.py` = 记忆存储**（MongoDB 读写与幂等写入）。通过包化 import 暴露：

```python
from agentic_search.memory.memory import Memory, extract_l1, consolidate_l2, consolidate_profile, get_memories_for_context
from agentic_search.memory.store import save_memory, load_memories, upsert_l2, upsert_profile
```
```

替换为：

```markdown
## 第 2 步：实现记忆层 `memory/`——`memory.py`（加工）与 `db.py`（数据库操作）

记忆层拆两个文件，各管一件事：**`memory/memory.py` = 记忆加工**（LLM 提取与整合——三个函数全部纯进出：数据进、Memory 出，不碰数据库），**`memory/db.py` = 数据库操作**（Memory 数据结构、MongoDB 读写、幂等写入、注入取数）。通过包化 import 暴露：

```python
from agentic_search.memory.memory import extract_l1, consolidate_l2, consolidate_profile
from agentic_search.memory.db import Memory, save_memory, load_memories, upsert_l2, upsert_profile, get_memories_for_context, L2_TRIGGER_THRESHOLD
```
```

- [ ] **Step 2: 改 LLM 前置节两处**

L123 注释行：`# services/llm.py —— 模块级 LLM 客户端，graph 与 store 共用` → `# services/llm.py —— 模块级 LLM 客户端，graph 与记忆层共用`。

L153 引导句：`...均来自这里；\`store.py\` 只管存储，不碰 LLM）` → `...均来自这里；\`db.py\` 只管数据库，不碰 LLM）`。

- [ ] **Step 3: 改 memory.py 文件头示例（L155-162）**

原文：

```python
# memory/memory.py 文件头部
import json
from datetime import datetime, timezone

from agentic_search.memory.store import load_memories
from agentic_search.services.llm import call_llm
```

替换为：

```python
# memory/memory.py 文件头部
import json
from datetime import datetime, timezone

from agentic_search.memory.db import Memory
from agentic_search.services.llm import call_llm
```

（memory.py 的加工函数纯进出，不调 load_memories——取数由调用方（端点/图节点）先做；它对 db.py 的依赖只有 Memory 数据结构一行。）

- [ ] **Step 4: 改依赖方向句（L164）与 prompts 前置句（L272）**

L164 原文：`依赖方向单一：\`memory.py\` → \`store.py\`（取数走存储函数）→ MongoDB；\`api/routes.py\` 两者都调；图节点只调 \`memory.py\`。`

替换为：`依赖方向单一：\`memory.py\` → \`db.py\`（只用 Memory 数据结构）→ MongoDB；\`api/routes.py\` 与图节点按需两者都调——加工找 \`memory.py\`，存取找 \`db.py\`。`

L272 原文：`...文件头部相应加 \`from agentic_search.configs.prompts import PROMPTS\`（存储层 store.py 零 LLM 依赖，用不到它）。`

替换为：`...文件头部相应加 \`from agentic_search.configs.prompts import PROMPTS\`（\`db.py\` 零 LLM 依赖，用不到它）。`

- [ ] **Step 5: 验收 + 提交**

```bash
cd "D:/Python/Common/Agentic Search"
grep -n "memory\.store\|store\.py" 任务文档/04-TMT记忆系统.md | grep -v "store_memory"
# 预期：仅剩 §2.5-2.7 区（Task 3 处理），引言/前置节零命中
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md   # 预期 1
```

提交：`git add 任务文档/04-TMT记忆系统.md && git commit -m "docs(04): 第2步引言与前置节改 db.py 契约（依赖单向 memory.py→db.py）"`

---

### Task 2: 04 §2.1 Memory dataclass 归属 db.py

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md` §2.1（约 L274-295）

**Interfaces:**
- Produces: Memory 定义在 db.py 的叙事锚点（Task 3 的 db.py 文件头删除 Memory import 依赖此叙事支撑）。

- [ ] **Step 1: 改代码块标注（L277）**

`# memory/memory.py —— 教学示例：展示核心字段，非完整实现` → `# memory/db.py —— 教学示例：展示核心字段，非完整实现`

- [ ] **Step 2: 讲解区补「为何在 db.py」**

在 L290（`session_id` 讲解行）之后、L291（`asdict()` 讲解行）之前插入一行：

```markdown
- **Memory 放 db.py**：`load_memories` 读库时要构造 `Memory(**doc)`——数据结构与存取同文件，即「memories 集合文档的 Python 形态」；若放在 memory.py，db.py 就得反向 import，循环回归。
```

- [ ] **Step 3: 验收 + 提交**

```bash
grep -c "^# memory/db.py" 任务文档/04-TMT记忆系统.md   # 预期 1（此时仅 §2.1）
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md   # 预期 1
```

提交：`git commit -am "docs(04): Memory dataclass 随迁 db.py（断环叙事）"`

---

### Task 3: 04 §2.5-2.7 更名 db.py + 阈值常量 + 2×联动

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md` §2.5-2.7（约 L404-528）

**Interfaces:**
- Consumes: Task 1/2 的 db.py 契约表述。
- Produces: `L2_TRIGGER_THRESHOLD = 10` 常量与 `get_memories_for_context(session_id, limit=2*L2_TRIGGER_THRESHOLD)` 签名（Task 4 图代码引用）。

- [ ] **Step 1: §2.5 标题与 2.5.1 文件头**

L404 标题：`### 2.5 记忆存储 \`memory/store.py\`（PyMongo CRUD）` → `### 2.5 数据库操作 \`memory/db.py\`（连接初始化 + CRUD）`

L406 小节题：`#### 2.5.1 连接初始化（store.py 文件头部）` → `#### 2.5.1 连接初始化（db.py 文件头部）`

文件头代码块（现行 L408-420）：

```python
# memory/store.py 文件头部 —— 存储层只管 MongoDB 读写，不碰 LLM
from dataclasses import asdict

from pymongo import MongoClient

from agentic_search.configs.config import settings
from agentic_search.memory.memory import Memory

_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_memories_collection = _db["memories"]   # 私有成员：仅 store.py 内部使用，端点/工具层零引用
```

替换为：

```python
# memory/db.py 文件头部 —— 数据库操作层只管 MongoDB 读写，不碰 LLM
from dataclasses import asdict

from pymongo import MongoClient

from agentic_search.configs.config import settings

_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_memories_collection = _db["memories"]   # 私有成员：仅 db.py 内部使用，端点/图节点零引用
```

（删 `from agentic_search.memory.memory import Memory` 行——Memory 已定义在本文件 §2.1；保留 `asdict`，save_memory 与两个 upsert 都用它。）

- [ ] **Step 2: 2.5.1 讲解行（L423）**

`...同一规范——集合句柄是存储层（store.py）的实现细节，端点与图节点只调存储函数，从不直接碰集合。` → `...同一规范——集合句柄是数据库操作层（db.py）的实现细节，端点与图节点只调 db.py 函数，从不直接碰集合。`

- [ ] **Step 3: 2.5.2/2.5.3/2.5.4/2.6 标注与标题**

- L428 标注 `# memory/store.py` → `# memory/db.py`（save_memory 块）
- L436 标注 `# memory/store.py` → `# memory/db.py`（load_memories 块）
- L454 尾句 `查询三要素（过滤/排序/限量）全收在存储层这一个函数里` → `查询三要素（过滤/排序/限量）全收在 db.py 这一个函数里`
- L459 标注 `# memory/store.py` → `# memory/db.py`（update_one 块）
- L469 标题：`### 2.6 幂等写入：\`upsert_l2(l2)\` 与 \`upsert_profile(profile)\`（\`memory/store.py\`）` → `### 2.6 幂等写入：\`upsert_l2(l2)\` 与 \`upsert_profile(profile)\`（\`memory/db.py\`）`
- L471 引导句：`...封装在存储层（store.py），返回落库文档的...` → `...封装在数据库操作层（db.py），返回落库文档的...`
- §2.6 代码块标注（约 L470）`# memory/store.py —— 教学示例...` → `# memory/db.py —— 教学示例...`
- L499 讲解：`MongoDB 访问全部收在存储层（store.py）函数里` → `MongoDB 访问全部收在 db.py 函数里`
- L501 讲解：`import 清单的 store.py 一行（\`save_memory, load_memories, upsert_l2, upsert_profile\`）` → `import 清单的 db.py 一行`

- [ ] **Step 4: §2.7 重写（标注 + 常量 + 联动签名 + 讲解）**

代码块整体替换为：

```python
# memory/db.py —— 教学示例：展示核心逻辑，非完整实现
L2_TRIGGER_THRESHOLD = 10   # 新增 L1 攒够 10 条 → store_memory 节点自动整合 L2（见第 4 步）

def get_memories_for_context(session_id: str, limit: int = 2 * L2_TRIGGER_THRESHOLD) -> list[Memory]:
    """取全局画像 + 该会话最近 N 条记忆（L1+L2），按时间倒序，配额注入，业界同构。

    profile 在前（全局唯一一条）；本会话记忆按时间倒序取最近 limit 条。
    跨会话记忆由 profile 承担：其他会话的 L1/L2 留在库中，作为下次整合画像的素材。
    """
    memories = load_memories(level="L5")                            # 全局至多一条画像
    memories += load_memories(session_id=session_id, limit=limit)   # 本会话 L1+L2，时间倒序取前 N
    return memories
```

讲解区（逐段讲解）替换为四条：

```markdown
**逐段讲解：**
- **纯组合**：两次 `load_memories` 调用分别取「全局画像」与「本会话最近 N 条」——查询三要素（过滤/排序/限量）复用 §2.5.3 的能力，本函数只做配额编排。
- **`load_memories(level="L5")` 在最前**：画像是最稳定的背景知识，放列表头部，注入 prompt 时格式化为独立一段（见第 4 步）。
- **窗口 = 2×阈值联动**：`limit` 缺省由 `2 * L2_TRIGGER_THRESHOLD` 派生——L2 每次整合都刷新 timestamp，其后最多再攒阈值条新 L1 就再次触发整合，因此 L2 恒在注入窗口内，「L1 堆积淹没 L2」由构造消解，注入端无需给 L2 特殊配额。
- **其他会话的记忆自然被过滤**：第二次调用查询条件是 `session_id` 等值匹配，跨会话的记忆只有画像这一条通道进入上下文。
```

（「验证：会话 A...」段落保留原样。）

- [ ] **Step 5: 验收 + 提交**

```bash
grep -c "^# memory/db.py" 任务文档/04-TMT记忆系统.md   # 预期 7（2.1 + 2.5.1 + 2.5.2 + 2.5.3 + 2.5.4 + 2.6 + 2.7）
grep -n "store\.py\|memory\.store" 任务文档/04-TMT记忆系统.md | grep -v store_memory   # 预期空
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md   # 预期 1
```

提交：`git commit -am "docs(04): §2.5-2.7 更名 db.py；注入窗口 2×阈值联动 + L2_TRIGGER_THRESHOLD"`

---

### Task 4: 04 第 4 步 store_memory 节点内联自动触发

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md` 第 4 步（约 L625 附近的 store_memory 条目）

**Interfaces:**
- Consumes: Task 3 的 `L2_TRIGGER_THRESHOLD`、`consolidate_l2`、`upsert_l2`、`load_memories`。
- Produces: 无（文档终点形态）。

- [ ] **Step 1: 改写 store_memory 条目并新增代码块**

原文（L625，单条 bullet）：

```markdown
- **store_memory 节点**（循环结束后）：把本轮对话传给 `memory.py` 的 `extract_l1(history, session_id, recent_l1)` 提取原子事实，经 `save_memory` 存入 MongoDB。**注意**：`recent_l1` 用 `load_memories(session_id, level="L1")` 取最近几条传入，让历史去重在每轮提取时生效。此节点只产生副作用（写库），返回 `{"messages": []}`。
```

替换为（bullet + 代码块 + 一行分工说明）：

```markdown
- **store_memory 节点**（循环结束后）：提取本轮 L1 落库，随后内联执行 **L2 自动触发**——新增 L1 攒够阈值就把该会话全部 L1 重整合为一条 L2。此节点只产生副作用（写库），返回 `{"messages": []}`。

```python
def store_memory(state):
    """提取 L1 落库 + L2 自动触发（新增 L1 达阈值则重整合）。"""
    session_id = state["session_id"]
    history = {"user": ..., "agent": ...}                          # 取最后一对 user/agent 消息
    recent_l1 = load_memories(session_id, level="L1", limit=10)    # 历史去重窗口
    for m in extract_l1(history, session_id, recent_l1):
        save_memory(m)

    # —— L2 自动触发：新增 L1（timestamp 晚于现有 L2）达阈值则重整合 ——
    l1s = load_memories(session_id, level="L1")
    l2s = load_memories(session_id, level="L2")
    new_l1 = l1s if not l2s else [m for m in l1s if m.timestamp > l2s[0].timestamp]
    if len(new_l1) >= L2_TRIGGER_THRESHOLD:
        upsert_l2(consolidate_l2(l1s))   # 全部 L1 重整合，幂等更新同一条
    return {"messages": []}
```

**触发时机与加工能力的分工**：何时整合（阈值判定、timestamp 对比）是编排策略，写在图节点；怎么整合（`consolidate_l2`）与怎么落库（`upsert_l2`）是记忆层能力。手动按钮走端点调同一套能力（第 3 步），两处触发点对称——按钮是不必等攒满的即时兜底。
```

- [ ] **Step 2: 第 4 步验证段补一句（L629 末尾追加）**

在「**验证：** 会话 A 连续两轮提问...」条目末尾追加：`同一会话累计新增 ≥10 条 L1 后不点按钮，Compass 中该会话 L2 自动出现/刷新（自动触发生效）。`

- [ ] **Step 3: 验收 + 提交**

```bash
grep -c "L2_TRIGGER_THRESHOLD" 任务文档/04-TMT记忆系统.md   # 预期 5（2.7 注释 + 2.7 签名 + 2.7 讲解 + 第4步代码 + 第4步前文）
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md   # 预期 1
```

提交：`git commit -am "docs(04): store_memory 节点内联 L2 阈值自动触发（策略在图、能力在记忆层）"`

---

### Task 5: 04 叙事同步（目标/触发表/FAQ/差异表/测试/检查表）

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`（L11-14、L97、L698、L716、L722 后、L731、L733 后、L759）

**Interfaces:**
- Consumes: Task 3/4 的联动表述。
- Produces: 定稿叙事。

- [ ] **Step 1: 学习目标（L11-14）**

- L11：`**L2 会话摘要**与**L5 用户画像**（均手动触发）` → `**L2 会话摘要**（阈值自动触发 + 手动兜底）与**L5 用户画像**（手动触发）`
- L12：`与本教学项目的手动按钮触发` → `与本教学项目的阈值自动触发与手动按钮`
- L14：`手动、即时地触发整合并保证幂等` → `即时触发整合并保证幂等`

- [ ] **Step 2: 触发机制表（L97）**

`| L2 触发器 | \`SessionMemoryScanner\` 每 10 分钟扫描，会话 idle ≥10 分钟视为结束 | 前端「整合会话记忆」按钮 |` → `| L2 触发器 | \`SessionMemoryScanner\` 每 10 分钟扫描，会话 idle ≥10 分钟视为结束 | 新增 L1 达阈值自动触发（store_memory 节点内联）+ 前端按钮即时兜底 |`

- [ ] **Step 3: FAQ 两处（先 read 锚定！）**

- L731：`\`get_memories_for_context\` 的 \`limit\`（默认 20）已限制` → `\`get_memories_for_context\` 的 \`limit\`（默认 2×L2_TRIGGER_THRESHOLD = 20）已限制`
- 在 L731 条目（「注入的历史记忆太多撑爆上下文？」）之后插入新条目（注意前后空行）：

```markdown
**为什么注入窗口是阈值的两倍？** L2 每次整合都刷新 timestamp；窗口 = 2×阈值意味着下一次自动触发前，L2 之后最多积压阈值条新 L1——L2 恒在最近 20 条窗口内，注入永远不会只剩 L1。一个常量（`L2_TRIGGER_THRESHOLD`）同时定节奏与窗口，联动由构造保证。
```

- [ ] **Step 4: 差异表（L759）**

`| 整合触发 | 空闲超时扫描 + 跨月回填 | 两个手动按钮 | 即时可观察、可调试；机制对比本身就是学习目标 |` → `| 整合触发 | 空闲超时扫描 + 跨月回填 | 阈值自动（新增 L1 ≥ 10）+ 手动按钮兜底 | 保留「无需人工干预」语义，又即时可观察、可调试；机制对比本身就是学习目标 |`

- [ ] **Step 5: 第 6 步测试说明与完成检查**

- L698 后追加一行测试要点：`- 注入窗口联动：\`get_memories_for_context\` 缺省 limit = 2×L2_TRIGGER_THRESHOLD（静态断言常量关系，零 LLM）`
- L698 行本身不动；**L2 自动触发不进单测清单**（图行为，涉及真 LLM），在 L704 段后补一句：`L2 阈值自动触发是图内编排行为且涉及真 LLM，归入完成检查的场景验证，不进本文件单测。`
- L716 检查项替换为：`- [ ] \`memory/memory.py\` 实现 \`extract_l1\`（官方移植 + recent_l1 去重）、\`consolidate_l2\`（守卫）、\`consolidate_profile\`；\`memory/db.py\` 实现 \`Memory\`、\`save_memory\`/\`load_memories\`、\`upsert_l2\`/\`upsert_profile\`、\`get_memories_for_context\`（含 \`L2_TRIGGER_THRESHOLD\` 联动）`
- 在 L717（Agent 图扩展项）之后插入：`- [ ] 同一会话累计新增 ≥10 条 L1 后无需点按钮，该会话 L2 自动出现/刷新；再次触发为更新而非新增`

- [ ] **Step 6: 验收 + 提交**

```bash
grep -c "^\*\*为什么注入窗口" 任务文档/04-TMT记忆系统.md        # 预期 1
grep -c "^\*\*.*？\*\*" 任务文档/04-TMT记忆系统.md              # 预期 11（原 10 + 新 1）
grep -c "^- \[ \]" 任务文档/04-TMT记忆系统.md                   # 预期 11（原 10 + 新 1）
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md # 预期 1
```

提交：`git commit -am "docs(04): 叙事同步——阈值自动触发 + 2×联动窗口（目标/触发表/FAQ/差异表/检查表）"`

---

### Task 6: 周边文档同步（AGENTS/概念速查/项目概览/01/02）

**Files:**
- Modify: `AGENTS.md`（L35、L79-80、L101、L116）
- Modify: `任务文档/概念速查.md`（L268、L368）
- Modify: `任务文档/项目概览.md`（L30、L77-78、L103、L156-160）
- Modify: `任务文档/01-Python文档工具.md`（L174）
- Modify: `任务文档/02-LangGraph-Agent.md`（仅 L148-149）

**Interfaces:**
- Consumes: Task 1-5 定稿契约。

- [ ] **Step 1: AGENTS.md**

- L35 目录树行 → `    memory/        空占位包（模块4 目标产物 memory.py 记忆加工 + db.py 数据库操作，文档已定稿，见 任务文档/04-TMT记忆系统.md）`
- L79 记忆层条目整行替换为：

```markdown
- **记忆层双文件（模块 4 文档定稿，代码待实现）**：`memory/memory.py`（记忆加工，纯进出零 Mongo）= `extract_l1`(每轮自动)/`consolidate_l2`/`consolidate_profile`(按钮触发)；`memory/db.py`（数据库操作，零 LLM）= Memory dataclass + `_client`/`_db`/私有 `_memories_collection`（对齐 `_documents_collection` 规范）+ `save_memory`/`load_memories`(sort/limit)/`upsert_l2`/`upsert_profile`(幂等，返回 `_id`)/`get_memories_for_context`(配额注入，limit=2×L2_TRIGGER_THRESHOLD 联动)/`L2_TRIGGER_THRESHOLD=10`。依赖严格单向 `memory.py → db.py`（memory.py 只 import Memory）；routes 与图节点两者都调。L2 触发 = store_memory 节点内联阈值判定（timestamp 对比）+ 端点按钮兜底。Memory 四字段 `{level, content, timestamp, session_id}`，L5 `session_id=None`（幂等键 `level="L5"`）；L2 幂等键 `{session_id, level}`。零向量依赖。
```

- L80 端点契约条目中 `（循环后，extract_l1）` → `（循环后，extract_l1 + L2 阈值自动触发内联）`
- L81 LLM 共享条目：`（store.py 零 LLM 依赖）` → `（\`db.py\` 零 LLM 依赖）`
- L101 文件表行：`memory.py/store.py 双文件函数签名` → `memory.py/db.py 双文件函数签名、prompts.yaml、L2 阈值自动触发`
- L116 陷阱 4：`_memories_collection\` 私有化收在 store.py、加工/存储勿混放` → `_memories_collection\` 私有化收在 db.py、Memory 亦定义在 db.py（断环）、加工/数据库操作勿混放`

- [ ] **Step 2: 概念速查.md**

- L268：`后端 \`memory/store.py\` 与 \`services/documents.py\` 通过 PyMongo 操作 MongoDB` → `后端 \`memory/db.py\` 与 \`services/documents.py\` 通过 PyMongo 操作 MongoDB`
- L368 整段替换为：

```markdown
**本项目用法**：记忆层分两个文件——`backend/src/agentic_search/memory/memory.py` 负责**记忆加工**（L1 每轮对话后由 LLM 自动提取原子事实）；`backend/src/agentic_search/memory/db.py` 负责**数据库操作**（Memory 数据结构、MongoDB 读写、注入取数，`memories` 集合）。L2 整合由阈值自动触发（新增 L1 ≥ 10 时 store_memory 节点内联重整合）+ 前端按钮手动兜底（同一 `/api/consolidate` 端点，请求体 `level` 区分）；L5 是全局唯一的用户画像（跨会话记忆由它承担，纯手动触发）。TiMem 论文中的 L3/L4 因与 L2 同构而被省略，详见[模块 4](./04-TMT记忆系统.md)。
```

- [ ] **Step 3: 项目概览.md**

- L30：`│   └─ TMT 记忆             # memory/memory.py（加工）+ memory/store.py（存储）` → `│   └─ TMT 记忆             # memory/memory.py（加工）+ memory/db.py（数据库操作）`
- L77-78 树两行 → `│   │   │   ├── memory.py           # TMT 记忆加工（L1/L2/L5 提取/整合）` 与 `│   │   │   └── db.py               # TMT 记忆数据库操作（Memory + MongoDB 读写 + 注入取数）`
- L103：`- \`memory/memory.py\` — TMT 记忆加工（L1 事实提取 + L2 会话整合 + L5 用户画像）；\`memory/store.py\` — 记忆存储（MongoDB 读写，PyMongo CRUD）。` → `- \`memory/memory.py\` — TMT 记忆加工（L1 事实提取 + L2 会话整合 + L5 用户画像）；\`memory/db.py\` — 数据库操作（Memory + MongoDB 读写 + 幂等写入 + 注入取数）。`
- L156-160 M4 内容：条目 1/2 改为 `1. **memory/memory.py** — L1 事实提取、L2 会话摘要、L5 画像整合（LLM 加工，纯进出）。` `2. **memory/db.py** — 数据库操作（Memory + MongoDB 读写 + 幂等写入 + 注入取数，含 L2 阈值自动触发的常量）。`；产出句 `**产出**：\`memory/memory.py\` + \`memory/db.py\`，实现 L1 事实提取（每轮自动）+ L2 会话整合（阈值自动 + 手动触发）+ L5 画像（手动触发）。`

- [ ] **Step 4: 01 与 02**

- 01 L174：`memory/memory.py\` 与 \`memory/store.py\`` → `memory/memory.py\` 与 \`memory/db.py\``
- 02 L148-149（冻结例外，仅此两行）：`│   ├── memory.py        # 模块 4 实现：L1/L2/L5 记忆加工（提取/整合/注入取数）` → `│   ├── memory.py        # 模块 4 实现：L1/L2/L5 记忆加工（提取/整合）`；`│   └── store.py         # 模块 4 实现：记忆存储（MongoDB 读写）` → `│   └── db.py            # 模块 4 实现：记忆数据库操作（MongoDB 读写 + 注入取数）`

- [ ] **Step 5: 验收 + 提交**

```bash
grep -rn "store\.py" AGENTS.md 任务文档/概念速查.md 任务文档/项目概览.md 任务文档/01-Python文档工具.md 任务文档/02-LangGraph-Agent.md | grep -v documents
# 预期空
git diff --numstat 任务文档/02-LangGraph-Agent.md   # 预期 2 行内改动（1+/1- 或 2+/2-）
```

提交：`git commit -am "docs: 周边文档同步 db.py 更名与 L2 阈值自动触发叙事"`

---

### Task 7: 全量验收

**Files:** 无新改动（只读验收）。

- [ ] **Step 1: 04 终检**

```bash
cd "D:/Python/Common/Agentic Search"
grep -n "store\.py\|memory\.store" 任务文档/04-TMT记忆系统.md | grep -v store_memory   # 空
grep -c "^# memory/db.py" 任务文档/04-TMT记忆系统.md    # 7
grep -c "^# memory/memory.py" 任务文档/04-TMT记忆系统.md # 4（前置文件头 + 2.2/2.3/2.4）
grep -c "L2_TRIGGER_THRESHOLD" 任务文档/04-TMT记忆系统.md # 5
grep -c "^\*\*.*？\*\*" 任务文档/04-TMT记忆系统.md       # 11
grep -c "^- \[ \]" 任务文档/04-TMT记忆系统.md            # 11
awk '/^```/{c++} END{print (c%2==0)}' 任务文档/04-TMT记忆系统.md  # 1
```

- [ ] **Step 2: 周边终检 + 提交历史**

```bash
grep -rn "store\.py" AGENTS.md 任务文档/*.md | grep -v documents   # 空
git log --oneline -6   # 六个 docs 提交
```

无新提交（本任务只验收）。
