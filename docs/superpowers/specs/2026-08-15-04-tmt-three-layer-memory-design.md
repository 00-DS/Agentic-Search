# 模块 4 教学文档重写设计：TMT 三层记忆（segment / session / profile）

日期：2026-08-15（Karpathy 复审修订）
状态：待用户批准

## 交付物（本次的唯一产出）

**重写 `任务文档/04-TMT记忆系统.md`**——把三层设计写成教学文档。
`任务文档/模块4优化版.md` 只是草稿素材，保持原样、不更新。本次**不写任何代码**；
spec 中的函数签名/端点/测试均为文档中的"教学示例"内容，不是实现计划。
其他教学文档（项目概览等）的联动更新不在本次范围。

## 背景与动机

现有 `模块4优化版.md`（草稿）只覆盖 L1（Fragment）+ L2（Session）两级。经与 TiMeM 源码
（`D:\Hermes\Capybara Workspace\Research\Works\Agentic Search计划\TiMEM`）逐层比对，确定教学版采用
**三层：L1 segment / L2 session / L5 profile**（砍 L3 daily / L4 weekly）。

### TiMeM 源码事实（教学文档"为什么这样简化"的论据）

| 事实 | 证据 |
|---|---|
| L1 segment = 固定 2 轮对话对，无语义切分 | `settings.yaml:258` `fragment_size: 2`；`utils/dataset_parser.py:117` |
| L1 prompt 无分类体系，仅"第三人称改写 + 不重复历史" | `config/prompts.yaml:3-28` |
| 分类提炼在 L3（4 类：Key Events / Attitudes & Preferences / Decision-Making / Emotional State） | `prompts.yaml:55-60` |
| L1 去重 = w=3 同 session 滑窗 + 纯 prompt 指令，零算法保障 | `settings.yaml:244`；`workflows/nodes/memory_indexer.py:265-270` |
| L2 的历史 L2 窗口在生产链路是死代码（`previous_content` 被丢弃） | `memory_generator.py:587,617` |
| L5 只消费下层 content 字符串 + 最近 3 条历史 L5；有 L3 回退先例，对 L4 无 schema 硬依赖（仅 3 处 `level="L4"` 软编码） | `workflows/nodes/unified_processors.py:786,810`；`memory_collector.py` `_collect_l5` |
| `timem/memory/l1~l5_*.py` 全是带 MockLLM 的旧 stub/死代码，生产链路在 `workflows/` + `services/session_memory_scanner.py` | 各文件内 MockLLMAdapter 兜底 |

**砍 L3/L4 结论**：机制上完全可行——L5 不依赖下层的层级身份，只吃摘要文本。代价是 TiMeM 原本在
L3/L4 完成的"画像分类提炼"失去载体，教学版用两项补偿：L1 提取带 6 类范围 + L5 prompt 带画像维度指引。

### 草稿文档的问题清单（重写 04 时逐项修复）

- **P1** 只有两层，无 profile 层 → 04 新增 L5。
- **P2** 学习目标称"跨会话记忆"，但 `get_memories_for_context` 按 session_id 过滤，跨会话记忆永远读不到
  → 注入策略改为：本会话 L1/L2 + 全局 profile，跨会话记忆由 profile 承担。
- **P3** profile（用户级、不属于任何 session）需要与 L1/L2 区分 → 用 `session_id=None` 表达，
  **不加 `user_id` 字段**（教学单用户，多用户时再加——不为没人要求的灵活性加字段）。
- **P4** "6 类提取范围"不是 TiMeM 做法（其 L1 无分类）→ 保留 6 类（砍层后的必要补偿），文档写明这是
  有意偏离及原因。
- **P5** segment 单位：TiMeM = 2 轮对话对，教学版 = 每轮 → 保留每轮，文档写明差异。
- **P6** 去重为 prompt 指令级、非硬保证 → 文档明确表述。
- **P7** `consolidate_l2` 在会话无 L1 时 `l1_memories[0]` IndexError → 教学示例中端点加空列表守卫。
- **P8** 端点返回 timestamp 作 `l2_id`，同秒碰撞 → 改返回 upsert 后的 `_id`。

## 设计（04 文档要教的内容）

### 1. 三层架构与数据流

```
每轮对话 → extract_l1（6 类范围 + recent_l1 w=3 同会话去重）→ 存 L1
按钮「整合会话记忆」→ consolidate_l2（本会话全部 L1 → 1 条 L2，按 session_id 幂等更新）
按钮「整合画像」  → consolidate_profile（跨会话全部 L2 + 旧 profile → 1 条 L5，全局唯一）
提问时注入：profile（1 条）+ 本会话最近 L1/L2（≤20 条）→ SystemMessage
```

**会话边界**（用户定稿）：前端首次加载生成 `crypto.randomUUID()` 存入 `localStorage`，
**刷新不重置**；仅「新会话」按钮清空并重新生成。同一 session_id 归属同批 L1/L2。

**跨会话记忆由 profile 承担**：新会话注入的记忆只有 profile 一条——这是对 P2 的结构性修复，
也让 L2 幂等（每会话至多一条）真正有意义。

### 2. 数据模型（文档中的教学示例）

```python
@dataclass
class Memory:
    level: str              # "L1" | "L2" | "L5"（跳号保留：L3/L4 被砍是可教学的事实）
    content: str
    timestamp: str          # ISO 8601
    session_id: str | None  # L1/L2 必填；L5 为 None（画像不属于任何会话）
```

- L2 幂等键：`{session_id, level: "L2"}`；L5 幂等键：`{level: "L5"}`（全局唯一一条）。
- Mongo 单集合 `agentic_search.memories`，不加索引（教学量级）。

### 3. 函数与端点（文档教学示例的契约）

| 函数 | 说明 |
|---|---|
| `extract_l1(dialogue, session_id, recent_l1)` | 沿用草稿（已对齐 TiMeM w=3 同会话滑窗 + prompt 去重）；6 类范围保留 |
| `consolidate_l2(l1_memories)` | 沿用草稿 + 空列表守卫（P7） |
| `consolidate_profile(l2_memories, previous_profile)` | **新增**：输入跨会话全部 L2 + 现有 L5；prompt 按画像维度（身份/偏好/长期话题/决策/关键信息）合成或更新画像，输出 150 字内 |
| `get_memories_for_context(session_id)` | 返回 `[L5 唯一条] + [本会话 L1/L2 按时间倒序 ≤20]` |
| `save_memory` / `load_memories` | 沿用草稿 |

端点：`POST /api/consolidate`（L2，占位端点转正；空 L1 返回 422）、
`POST /api/consolidate_profile`（L5；空 L2 返回 422）；均幂等，返回 upsert 后的 `_id`（P8）。

`QueryRequest` 加 `session_id: str`；`MemoryState(MessagesState)` 加 `session_id: str`；
graph `get_memories` 节点注入格式区分 profile 与本会话记忆两段。

### 4. 前端（文档教学示例）

- session_id 存 `localStorage`，「新会话」按钮清空重生成并清空聊天区。
- 「整合会话记忆」→ `/api/consolidate`；「整合画像」→ `/api/consolidate_profile`；均提示完成。

### 5. 04 文档结构（重写大纲）

沿用 00-03 系列的模块结构（学习目标 → 模块结构图 → 核心思路 → 分步实现 → 完成检查 → 常见问题 → 延伸阅读）：

1. **学习目标**：三层各一句 + 砍层依据 + 两种触发机制对比（手动按钮 vs TiMeM 自动扫描）。
2. **模块结构 mermaid**：L1 自动 / L2 按钮 / L5 按钮三条链路 + 注入路径。
3. **核心思路**：TMT 五层 → 教学三层映射表；砍 L3/L4 的源码证据表（上文"TiMeM 源码事实"）；
   记忆注入策略（方案 A 直接注入 + 跨会话由 profile 承担）；L2/L5 触发机制对比表。
4. **第 1 步 理解 TMT 思想**：论文阅读引导（沿用草稿）+ 三层概念。
5. **第 2 步 memory/store.py**：Memory dataclass（§2）→ extract_l1（6 类 + recent_l1，沿用草稿）→
   consolidate_l2（守卫）→ **consolidate_profile（新增小节）** → Mongo CRUD → get_memories_for_context（改语义）。
6. **第 3 步 端点**：/api/consolidate 转正 + /api/consolidate_profile 新增，幂等与 _id 返回。
7. **第 4 步 Agent 图集成**：get_memories / store_memory 节点 + MemoryState 扩展。
8. **第 5 步 前端**：session_id 生命周期 + 两个整合按钮 + 新会话按钮。
9. **第 6 步 tests/test_memory.py**：无需 LLM 的部分（往返一致性、排序与 limit、L2/L5 幂等、
   跨会话隔离——注入不含其他会话记忆、端点空输入守卫）；LLM 部分标记集成测试。
10. **完成检查**：草稿检查表 + 三项新增（新会话只带 profile 记忆可答、L5 全局唯一、
    二次点「整合画像」更新而非新增）。
11. **常见问题**：沿用草稿四问 + "L5 何时更新？每次点按钮都用全部 L2 + 旧 L5 重合成"。
12. **有意偏离 TiMeM 的说明**（P4/P5/P6 + 手动触发 + 单集合存储），每条写"为什么偏离仍然合理"。
13. **延伸阅读**：TiMeM 论文/源码（注明生产链路在 `workflows/`，`timem/memory/l*_*.py` 是旧 stub 勿作参考）。

文档措辞政策：只写"为什么这样、如何用"，禁用"不使用 XXX"的否定措辞（AGENTS.md 约定）。

## 明确不做（YAGNI）

- L3/L4 层、评分检索（方案 B）、embedding、向量库、TiMeM 的调度器/回填/补漏检测。
- 多用户体系（`user_id` 字段不加，多用户需求出现时再加）。
- `recent_l2` 滑动窗口注入 L2 prompt（TiMeM 生产链路自己都没接通）。
- 本次不写代码、不动 `模块4优化版.md`、不联动其他教学文档。

## 验收标准（可判定）

1. `任务文档/04-TMT记忆系统.md` 全文体现三层设计与上述大纲，无 P1-P8 残留。
2. 措辞符合"只写为什么/如何用"政策，无否定式表述。
3. 所有 TiMeM 源码引用可在本地仓库定位到（文件+行号或函数名）。
