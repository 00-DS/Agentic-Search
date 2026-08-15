# 模块 4 记忆叙事修订（业界对照，零向量依赖）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修订 `任务文档/04-TMT记忆系统.md` 的记忆注入叙事——以 **TiMeM 为参考**（三层结构的出处）、**omp 为标杆**（工程实践校验对象），把"方案 A 是将就、检索是正道"反转为"分层配额注入与业界标杆同构"，实现与依赖零改动。

**Architecture:** 只改 04 一个文件的叙事文字（学习目标/注入策略小节/FAQ/差异表及散落的"方案 B"提法），依据 spec `docs/superpowers/specs/2026-08-15-04-memory-narrative-industry-alignment-design.md`。叙事层次：TiMeM 提供参考结构 → omp 提供标杆验证（两阶段管线/MEMORY.md 注入与本模块逐一对应）→ 其余一线工具佐证"通行做法"。

## Global Constraints

- 只改 `任务文档/04-TMT记忆系统.md`；不改任何代码/依赖/端点/前端；不动 01-03。
- 零向量依赖表述：涉及"无 embedding"处用肯定式（如"零向量依赖""纯文本注入"），全文禁用否定措辞（"不使用/不采用/不用"，含无空格"不用"）。
- 业界对照表必须含 oh-my-pi 与 hermes-agent 两行，引用格式为"仓库名 + 文件路径"（如 `packages/coding-agent/src/memories/`）。
- 函数签名、代码块、端点契约一律保持原样（本计划只动叙事文字与表格）。
- **命名规范对齐（与 documents.py / AGENTS.md 同一规范）**：service 层集合成员私有化——`memories_collection` 全文改为 `_memories_collection`（对齐 `_documents_collection`）；端点零 Mongo 集合引用——幂等 find/update 逻辑封装为 store.py 函数 `upsert_l2(l2: Memory) -> str` 与 `upsert_profile(profile: Memory) -> str`（内部 find_one + insert_one/update_one，返回 `_id` 字符串），端点只调它们。动词命名沿用项目惯例（verb + 名词：`save_memory`/`load_memories`/`upsert_l2`/`upsert_profile`）。
- 中文排版用弯引号，与全文一致。

---

### Task 1: 注入策略小节重写 + 业界对照表

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md:15`（学习目标 6）与 `:71-93`（记忆注入策略小节）

**Interfaces:**
- Consumes: spec"业界实证表"与"设计（04 文档三处修订）§1"。
- Produces: 新小节标题「记忆注入策略（分层注入，业界同构）」与对照表——Task 2 的 FAQ 措辞需与之呼应。

- [ ] **Step 1: 改学习目标 6（L15）**

原：
```
6. 理解"直接注入历史"（方案 A）与"检索注入"（方案 B）的取舍，以及提取时对比历史窗口（recent_l1）从源头减少重复
```
改为：
```
6. 理解“分层配额注入”为何是业界标杆做法——以 oh-my-pi（omp）为标杆对照本模块的三层设计，同时理解提取时对比历史窗口（recent_l1）从源头减少重复
```
- [ ] **Step 2: 重写注入策略小节（替换 L71-93 的标题+表格+导语，保留"跨会话记忆由 profile 承担"段）**

新内容：

```markdown
### 记忆注入策略（分层注入，以 omp 为标杆）

本模块以 TiMeM 论文为**参考**——三层结构（提取→整合→画像）的出处；工程上的**标杆**是
oh-my-pi（omp）：它的记忆子系统验证了同样的结构在生产级 agent 里怎么落地。注入方式是
**配额制**：profile（全局唯一 1 条）+ 本会话 L1/L2 最近 N 条（≤20），按固定预算注入上下文。

**标杆对照（omp ↔ 本模块）**：

| omp 的实现（`packages/coding-agent/src/memories/`） | 本模块的对应 |
|---|---|
| Phase 1：启动时逐会话提取事实 | `extract_l1`（每轮对话提取） |
| Phase 2：跨会话整合为 `MEMORY.md` + `memory_summary.md` | `consolidate_l2` / `consolidate_profile`（整合为 L2/L5） |
| 会话开始作为 Memory Guidance 块注入 system prompt | `retrieve_memory` 节点注入 SystemMessage |
| 零向量依赖（向量仅可选 mnemopi 插件后端） | 零向量依赖（配额注入） |

同样的模式在其他一线 agent 中一致出现，说明这是通行做法而非本模块的简化：

| 工具 | 长期记忆机制 | 记忆召回方式 |
|---|---|---|
| **hermes-agent** | `MEMORY.md`（agent 自记事实）+ `USER.md`（用户画像）纯文本文件，冻结快照注入 system prompt（`tools/memory_tool.py`） | SQLite FTS5 全文检索（`tools/session_search_tool.py`） |
| OpenAI Codex CLI | `AGENTS.md` 逐层拼接注入（`codex-rs/core/src/agents_md.rs`） | ripgrep 字面量搜索（`codex-rs/rollout/src/search.rs`） |
| Claude Code | `CLAUDE.md` 四级层级 + auto memory，`MEMORY.md` 索引前 200 行启动注入 | 模型自行读取 markdown 文件 |
| Cline / Gemini CLI | `.clinerules` / `GEMINI.md` 文件注入 | 文件按需读取 / MemTool 写回 |

与它们相比，TiMeM 的双通道检索（语义向量 ×0.9 + BM25 ×0.1，Qdrant）属于**记忆产品**
在海量记忆长期个性化场景下的路线——hermes 的 `USER.md` 与本模块的 L5 profile 同构，
印证"用户画像"这一层是 agent 与记忆产品的公共结构。

```
实施说明：上述内容替换 04 文档原 L71-93 的标题、表格与导语；原文“**跨会话记忆由 profile 承担**：……”一段原样保留在表格之后。

- [ ] **Step 3: 同步清理全文"方案 A/方案 B"提法（5 处）**

逐处替换（保留原句其余部分）：
- L197："记忆量少时直接注入全部历史（方案 A）" → "记忆量少时直接注入全部历史"
- L328："方案 A 的落地：全局画像 + 本会话最近 N 条，两类一起返回。" → "分层注入的落地：全局画像 + 本会话最近 N 条，两类一起返回。"
- L333（docstring）："评分留待方案 B。" → "配额注入，业界同构。"
- L434（docstring）："相关度检索留待方案 B。" → "配额注入，业界同构。"
- L564 FAQ 整条改写（见 Task 2）。

- [ ] **Step 4: 验证**

Run: `grep -n "方案 A\|方案 B" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出（FAQ 那处本任务先不处理则允许 L564 命中，Task 2 后应为零；执行时按此顺序核对）。
Run: `grep -n "不使用\|不采用\|不用" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出。
Run: `grep -c "oh-my-pi\|hermes-agent" "任务文档/04-TMT记忆系统.md"`
Expected: ≥2。

- [ ] **Step 5: Commit**

```bash
git add "任务文档/04-TMT记忆系统.md"
git commit -m "docs(04): 注入策略重写——TiMeM 为参考、omp 为标杆的分层注入叙事"
```

---

### Task 2: FAQ 双路径反转 + 差异表补行

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md:564`（FAQ「将来记忆多了怎么办」）与 `:568-576`（差异说明表）

**Interfaces:**
- Consumes: Task 1 的新叙事与对照表；spec"设计 §2/§3"。
- Produces: 最终版 FAQ 与差异表。

- [ ] **Step 1: 改写 FAQ「将来记忆多了怎么办？」（L564）**

原：
```
**将来记忆多了怎么办？** 把 `get_memories_for_context` 的函数体从"最近 N 条"换成"按关键词检索"（方案 B），图编排保持原样——函数名就是为切换预留的接口。
```
改为：
```
**将来记忆多了怎么办？** 两条路线，按产品形态选。**agent 路线（标杆做法，omp/hermes 同款）**：压缩与全文检索——hermes 用 SQLite FTS5 全文检索跨会话对话（`tools/session_search_tool.py`），omp 在上下文逼近上限时用 LLM 摘要压缩历史，全程零向量依赖。**记忆产品路线（可选）**：TiMeM 式双通道检索——语义向量（权重 0.9）+ BM25 关键词（0.1）；即便选这条路，omp 的 mnemopi 后端也只把向量存进自有 SQLite，而非引入独立向量数据库。无论哪条，`get_memories_for_context` 的函数名都是为切换预留的接口，图编排保持原样。
```

- [ ] **Step 2: 差异表补一行（在"去重"行之前插入）**

```markdown
| 检索 | 双通道：语义向量 + BM25（Qdrant） | 配额注入（零向量依赖） | 与标杆 omp 及 hermes/Codex/Claude Code 核心记忆链路同构；向量检索属于记忆产品的可选插件层 |
```

- [ ] **Step 3: 全文终验**

Run: `grep -n "方案 A\|方案 B\|按相关性评分，只注入相关" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出。
Run: `grep -n "不使用\|不采用\|不用" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出。
Run: `grep -c "标杆\|参考" "任务文档/04-TMT记忆系统.md"`
Expected: ≥3（TiMeM 参考 + omp 标杆框架落地）。
Run: `git diff --stat backend/ frontend/ 2>/dev/null; git status --porcelain | grep -v "任务文档/04"`
Expected: 无输出（零代码改动）。

- [ ] **Step 4: Commit**

```bash
git add "任务文档/04-TMT记忆系统.md"
git commit -m "docs(04): FAQ 双路径反转（agent 路线优先）+ 差异表补检索行"
```
---

### Task 3: 命名规范对齐——集合私有化 + 幂等逻辑下沉 store.py

**Files:**
- Modify: `任务文档/04-TMT记忆系统.md`（§2.5 连接初始化、§2.6 注入小节顺延、§3 端点代码、完成检查、散落的 `memories_collection` 提法）

**Interfaces:**
- Consumes: Task 1/2 的叙事；现有 `save_memory`/`load_memories`/`Memory`/`asdict`。
- Produces: `upsert_l2(l2: Memory) -> str`、`upsert_profile(profile: Memory) -> str`（端点教学示例引用）；`_memories_collection` 私有名（store.py 内部专用）。

- [ ] **Step 1: §2.5.1 连接初始化私有化（对齐 documents.py 风格）**

原（约 L286-289）：
```python
client = MongoClient(settings.mongo_url)
db = client[settings.mongo_db]
memories_collection = db["memories"]
```
改为：
```python
_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_memories_collection = _db["memories"]   # 私有成员：仅 store.py 内部使用，端点/工具层零引用
```
并在逐段讲解加一条：
```markdown
- **下划线私有**：`_memories_collection` 与 `services/documents.py` 的 `_documents_collection` 同一规范——集合句柄是 service 层的实现细节，API 层与 agent 工具层只调 service 函数，从不直接碰集合。
```
同时更新 §2.5 内其余引用（`save_memory`/`load_memories`/`update_one` 示例中的 `memories_collection.` → `_memories_collection.`）；`update_one` 小节（2.5.4）补一句说明：该示例展示原子操作本身，实际幂等更新由 `upsert_l2`/`upsert_profile` 封装（见 2.6）。

- [ ] **Step 2: store.py 新增 upsert 小节（插入为 §2.6，原"记忆注入"小节顺延为 §2.7，全文引用同步改号）**

````markdown
### 2.6 幂等写入：`upsert_l2(l2)` 与 `upsert_profile(profile)`

端点需要的“有则更新、无则新建”逻辑封装在 service 层，返回落库文档的 `_id` 字符串：

```python
# 教学示例：展示核心流程，非完整实现
def upsert_l2(l2: Memory) -> str:
    """按 (session_id, level="L2") 幂等写入 L2：已有则更新 content/timestamp，返回 _id。"""
    existing = _memories_collection.find_one(
        {"session_id": l2.session_id, "level": "L2"}
    )
    if existing is None:
        return str(_memories_collection.insert_one(asdict(l2)).inserted_id)
    _memories_collection.update_one(
        {"_id": existing["_id"]},
        {"$set": {"content": l2.content, "timestamp": l2.timestamp}},
    )
    return str(existing["_id"])


def upsert_profile(profile: Memory) -> str:
    """按 level="L5" 全局幂等写入画像：已有则更新 content/timestamp，返回 _id。"""
    existing = _memories_collection.find_one({"level": "L5"})
    if existing is None:
        return str(_memories_collection.insert_one(asdict(profile)).inserted_id)
    _memories_collection.update_one(
        {"_id": existing["_id"]},
        {"$set": {"content": profile.content, "timestamp": profile.timestamp}},
    )
    return str(existing["_id"])
```

**逐段讲解：**
- 与 `services/documents.py` 的分层一致：MongoDB 访问全部收在 service 层函数里，`api/routes.py` 只调用函数。
- 两个函数只差幂等键（`session_id + level` vs 全局 `level`），对应 L2 每会话一条、L5 全局一条的定位。
- §2 开头的 import 清单同步加 `upsert_l2, upsert_profile`。
````

- [ ] **Step 3: §3 端点代码改为纯 service 调用**

原 L5 分支（约 L383-397）替换为：
```python
    if req.level == "L5":
        l2_memories = load_memories(level="L2")
        if not l2_memories:
            raise HTTPException(422, "还没有会话摘要，先整合至少一个会话")
        previous = load_memories(level="L5")
        profile = consolidate_profile(l2_memories, previous[0] if previous else None)
        profile_id = upsert_profile(profile)
        return ConsolidateResponse(status="ok", profile_id=profile_id)
```
原 L2 分支（约 L400-412）替换为：
```python
    l1_memories = load_memories(session_id=req.session_id, level="L1")
    if not l1_memories:
        raise HTTPException(422, "该会话没有 L1 记忆，先对话几轮再整合")
    l2 = consolidate_l2(l1_memories)
    l2_id = upsert_l2(l2)
    return ConsolidateResponse(status="ok", l2_id=l2_id)
```
删除端点代码顶部的 `memories_collection` import；逐段讲解同步：把“幂等检查”条改为“幂等由 service 层 `upsert_l2`/`upsert_profile` 保证——端点只组数据、调函数、返结果，与模块 2 的分层铁律一致”。

- [ ] **Step 4: 散落引用清理与检查表同步**

`grep -n "memories_collection" 任务文档/04-TMT记忆系统.md` 逐处核对：命中必须全部带下划线前缀且都在 store.py 代码块/讲解内；端点/前端/测试章节零出现。完成检查第 1 条（约 L540）补上 `upsert_l2`/`upsert_profile`。

- [ ] **Step 5: 验证**

Run: `grep -n "[^_]memories_collection" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出（无下划线前缀版本零出现）。
Run: `grep -c "upsert_l2\|upsert_profile" "任务文档/04-TMT记忆系统.md"`
Expected: ≥6（定义 2 + import 1 + 端点 2 + 完成检查 1）。
Run: `grep -n "方案 A\|方案 B\|不使用\|不采用\|不用" "任务文档/04-TMT记忆系统.md"`
Expected: 无输出。

- [ ] **Step 6: Commit**

```bash
git add "任务文档/04-TMT记忆系统.md"
git commit -m "docs(04): 命名规范对齐——_memories_collection 私有化 + 幂等下沉 upsert_l2/upsert_profile"
```
