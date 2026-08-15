# 模块 4 记忆叙事修订：业界对照（无 embedding）设计

日期：2026-08-15
状态：待用户批准

## 交付物

**修订 `任务文档/04-TMT记忆系统.md` 的记忆注入叙事**——实现零改动，只改"方案 A/B 怎么讲"。
依据：oh-my-pi（`can1357/oh-my-pi`）与 hermes-agent（`NousResearch/hermes-agent`）源码调研 + 此前 Codex/Claude Code/Cline/Gemini CLI 调研。

## 背景与动机

现行 04 把注入策略讲成"方案 A（直接注入）是记忆量少时的将就，方案 B（相关性检索）是将来正道"。
业界实证恰好相反：一线 agent 工具的核心记忆链路**全部是"LLM 提炼摘要 + 文件/SQLite 存储 + 启动注入"，
零 embedding**；embedding 检索只是可选插件后端。用户据此决策：教学版走业界思路，引入 embedding 属于老套的 RAG 方法论。

### 业界实证表（写入 04 的素材，全部源码级）

| 工具 | 长期记忆机制 | 检索 | embedding |
|---|---|---|---|
| oh-my-pi | 启动时两阶段 LLM 管线：逐会话提取 → 跨会话整合 → `MEMORY.md` + skills，会话开始注入 | memory:// 按需读 | 默认无；可选 mnemopi 后端（bge/e5 向量存自有 SQLite，`noEmbeddings:true` 可关） |
| hermes-agent | `MEMORY.md`（agent 自记事实）+ `USER.md`（用户画像），冻结快照注入 system prompt | SQLite FTS5 BM25（含 CJK trigram），零 LLM 零向量 | 内置无；外部插件（mem0 等）内才有 |
| OpenAI Codex CLI | `AGENTS.md` 逐层拼接注入 | ripgrep 字面量正则 | 无 |
| Claude Code | `CLAUDE.md` 四级层级 + auto memory（`MEMORY.md` 索引前 200 行注入） | 模型自读 markdown | 无 |
| Cline / Gemini CLI | `.clinerules`/`GEMINI.md` 文件注入 | 无 / MemTool 写回 | 无 |
| TiMeM（记忆产品参照） | L1-L5 分层提炼 | 双通道：余弦×0.9 + BM25×0.1 | 有（Qwen3-Embedding + Qdrant） |

**结构性巧合（教学锚点）**：omp 的 Phase1→Phase2 记忆管线 ≈ 本模块 extract_l1→consolidate_l2；
hermes 的 `USER.md` ≈ 本模块 L5 profile。三层设计与业界同构。

## 设计（04 文档三处修订）

### 1. 注入策略小节重写（替换现行方案 A/B 对比表）

新叙事：**分层注入（本模块采用）= 与业界一线 agent 同构的做法**——profile（全局画像）+ 本会话
L1/L2 最近 N 条，配额制注入；对应 omp 的 "Memory Guidance 注入"、hermes 的 "MEMORY.md/USER.md
冻结快照注入"、Claude Code 的 "MEMORY.md 前 200 行"。

原方案 B 表格改为"业界对照表"（上文实证表精简为 5-6 行），TiMeM 行标注它是**记忆产品**的路线
（海量记忆长期个性化），而非 coding agent 主流。

### 2. FAQ「将来记忆多了怎么办」改写

单路径改为双路径，且顺序反转：
- **agent 路线（业界做法，优先）**：加注入配额/压缩（hermes FTS5 BM25 式全文检索、omp/claude 式
  摘要压缩）——仍是零 embedding；
- **记忆产品路线（可选）**：TiMeM 式双通道检索——语义向量（0.9）+ BM25（0.1），需 embedding 服务
  与向量存储；即便如此 omp 的 mnemopi 后端也只把向量存进自有 SQLite，而非引入独立向量数据库。

`get_memories_for_context` 函数名仍是"接口预替"的教学点，保留一句话提及。

### 3. 差异说明表补一行

| 差异点 | TiMeM | 本教学版 | 合理性 |
|---|---|---|---|
| 检索 | 双通道（向量+BM25，Qdrant） | 配额注入（无检索） | 与 omp/hermes/Codex/Claude Code 核心 memory 链路同构；embedding 属可选插件层 |

### 明确不做（YAGNI）

- 不引入 embedding/向量/bge-m3/vLLM/jieba/rank_bm25 任何依赖与代码。
- 不改 store.py 任何函数签名与行为；不改端点/前端/测试章节。
- 不动 01-03 文档。

## 验收标准

1. 04 全文无"方案 B 是将来正道/记忆量上来再换检索"式表述；注入策略以业界同构为主线。
2. 业界对照表至少含 omp 与 hermes 两行，引用可定位（仓库名+文件路径）。
3. 措辞政策不变（只写为什么/如何用，无否定式——"无 embedding"表述用"零向量依赖"等肯定式改写）。
