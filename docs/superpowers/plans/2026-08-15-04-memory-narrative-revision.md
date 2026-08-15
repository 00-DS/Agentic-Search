# 模块 4 记忆叙事修订（业界对照，零向量依赖）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修订 `任务文档/04-TMT记忆系统.md` 的记忆注入叙事——以 **TiMeM 为参考**（三层结构的出处）、**omp 为标杆**（工程实践校验对象），把"方案 A 是将就、检索是正道"反转为"分层配额注入与业界标杆同构"，实现与依赖零改动。

**Architecture:** 只改 04 一个文件的叙事文字（学习目标/注入策略小节/FAQ/差异表及散落的"方案 B"提法），依据 spec `docs/superpowers/specs/2026-08-15-04-memory-narrative-industry-alignment-design.md`。叙事层次：TiMeM 提供参考结构 → omp 提供标杆验证（两阶段管线/MEMORY.md 注入与本模块逐一对应）→ 其余一线工具佐证"通行做法"。

## Global Constraints

- 只改 `任务文档/04-TMT记忆系统.md`；不改任何代码/依赖/端点/前端；不动 01-03。
- 零向量依赖表述：涉及"无 embedding"处用肯定式（如"零向量依赖""纯文本注入"），全文禁用否定措辞（"不使用/不采用/不用"，含无空格"不用"）。
- 业界对照表必须含 oh-my-pi 与 hermes-agent 两行，引用格式为"仓库名 + 文件路径"（如 `packages/coding-agent/src/memories/`）。
- 函数签名、代码块、端点契约一律保持原样（本计划只动叙事文字与表格）。
- 每个 Task 结束 commit，消息前缀 `docs(04):`。
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
