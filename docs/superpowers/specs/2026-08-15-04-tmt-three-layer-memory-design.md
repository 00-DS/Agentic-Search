# 模块 4：TMT 三层记忆系统设计（segment / session / profile）

日期：2026-08-15
状态：已确认（用户批准，含一处修正：session 边界只由「新会话」按钮产生，刷新不重置）

## 背景与动机

现有 `任务文档/模块4优化版.md` 只实现 L1（Fragment）+ L2（Session）两级。经与 TiMeM 源码
（`D:\Hermes\Capybara Workspace\Research\Works\Agentic Search计划\TiMEM`）逐层比对，确定升级为
**三层：L1 segment / L2 session / L5 profile**（砍 L3 daily / L4 weekly），理由与依据如下。

### TiMeM 源码事实（设计依据）

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
L3/L4 完成的"画像分类提炼"失去载体，本设计用两项补偿：L1 提取带 6 类范围 + L5 prompt 带画像维度指引。

### 现有优化版文档的问题清单（本设计逐项修复）

- **P1** 只有两层，无 profile 层 → 本设计新增 L5。
- **P2** 学习目标称"跨会话记忆"，但 `get_memories_for_context` 按 session_id 过滤，跨会话记忆永远读不到
  → 注入策略改为：本会话 L1/L2 + 全局 profile，跨会话记忆由 profile 承担。
- **P3** `Memory` 无 user 维度，profile（用户级、不属于任何 session）装不下 → 加 `user_id` 字段，
  L5 的 `session_id=None`。
- **P4** "6 类提取范围"不是 TiMeM 做法（其 L1 无分类）→ 保留 6 类（砍层后的必要补偿），文档写明这是
  有意偏离及原因。
- **P5** segment 单位：TiMeM = 2 轮对话对，教学版 = 每轮 → 保留每轮，文档写明差异。
- **P6** 去重为 prompt 指令级、非硬保证 → 文档明确表述。
- **P7** `consolidate_l2` 在会话无 L1 时 `l1_memories[0]` IndexError → 端点加空列表守卫。
- **P8** 端点返回 timestamp 作 `l2_id`，同秒碰撞 → 改返回 upsert 后的 `_id`。

## 设计

### 1. 三层架构与数据流

```
每轮对话 → extract_l1（6 类范围 + recent_l1 w=3 同会话去重）→ 存 L1
按钮「整合会话记忆」→ consolidate_l2（本会话全部 L1 → 1 条 L2，按 session_id 幂等更新）
按钮「整合画像」  → consolidate_profile（全部 L2 + 旧 profile → 1 条 L5，按 user_id 幂等更新）
提问时注入：profile（1 条）+ 本会话最近 L1/L2（≤20 条）→ SystemMessage
```

**会话边界**（用户修正后定稿）：前端首次加载生成 `crypto.randomUUID()` 存入 `localStorage`，
**刷新不重置**；仅「新会话」按钮清空并重新生成。同一 session_id 归属同批 L1/L2。

**跨会话记忆由 profile 承担**：新会话注入的记忆只有 profile 一条——这是对 P2 的结构性修复，
也让 L2 幂等（每会话至多一条）真正有意义。

### 2. 数据模型（`memory/store.py`）

```python
@dataclass
class Memory:
    level: str              # "L1" | "L2" | "L5"（跳号保留：L3/L4 被砍是可教学的事实）
    content: str
    timestamp: str          # ISO 8601
    session_id: str | None  # L1/L2 必填；L5 为 None
    user_id: str = "default"  # 教学单用户，字段先留好维度
```

- L2 幂等键：`{session_id, level: "L2"}`；L5 幂等键：`{user_id, level: "L5", session_id: None}`。
- Mongo 单集合 `agentic_search.memories` 不变，不加索引（教学量级）。

### 3. `store.py` 函数与端点

| 函数 | 说明 |
|---|---|
| `extract_l1(dialogue, session_id, recent_l1)` | 不变（已对齐 TiMeM w=3 同会话滑窗 + prompt 去重）；6 类范围保留 |
| `consolidate_l2(l1_memories)` | 加空列表守卫（P7）；prompt 不变 |
| `consolidate_profile(l2_memories, previous_profile)` | **新增**：输入全部 L2 + 现有 L5；prompt 按画像维度（身份/偏好/长期话题/决策/关键信息）合成或更新画像，输出 150 字内 |
| `get_memories_for_context(user_id, session_id)` | 签名扩展：返回 `[该 user 的 L5 唯一条] + [本会话 L1/L2 按时间倒序 ≤20]` |
| `save_memory` / `load_memories` | 不变（`load_memories` 支持 `user_id` 过滤） |

端点（`api/routes.py`）：

- `POST /api/consolidate` —— L2 整合，已存在的占位端点转正；空 L1 时返回 422。
- `POST /api/consolidate_profile` —— **新增** L5 整合；空 L2 时返回 422。
- 两者均幂等（有则 `$set` 更新、无则新建），返回 upsert 后的 `_id`（P8）。

`QueryRequest` 加 `session_id: str`；`MemoryState(MessagesState)` 加 `session_id: str` 与
`user_id: str = "default"`。graph 节点 `get_memories` 改调新签名 `get_memories_for_context(user_id, session_id)`，
注入格式区分 profile 与本会话记忆两段。

### 4. 前端（`frontend/app.js`）

- session_id 存 `localStorage`，「新会话」按钮清空重生成并清空聊天区。
- 「整合会话记忆」按钮 → `POST /api/consolidate`；「整合画像」按钮 → `POST /api/consolidate_profile`；
  均提示完成。

### 5. 教学文档同步（`任务文档/模块4优化版.md` 改写）

1. 三层架构图与 mermaid 更新（加 L5 分支与「整合画像」按钮）。
2. P4：写明"6 类提取是教学版有意偏离（TiMeM L1 无分类），为砍层后给 L5 供料"。
3. P5：写明"segment 单位 = 每轮对话，TiMeM 生产是 2 轮对话对"。
4. P6：去重明确"靠 LLM 遵守指令，非硬保证"。
5. 学习目标"跨会话记忆"改为由 profile 承担的表述；补 L2 → L5 触发链路说明。
6. TiMeM 参考代码路径指向生产链路（`workflows/` + `services/session_memory_scanner.py`），
   标注 `timem/memory/l*_*.py` 为旧 stub 勿作参考。

### 6. 测试（`tests/test_memory.py`）

无需 LLM 的部分：

- Memory dataclass 字段完整性（含 `user_id`、L5 的 `session_id=None`）。
- MongoDB 存取往返一致性。
- `get_memories_for_context`：L5 + 本会话 L1/L2 混合、时间倒序、limit 生效、**不含其他会话记忆**。
- L2 幂等：同会话二次 consolidate 更新而非新增。
- L5 幂等：二次 consolidate_profile 更新而非新增。
- 端点空输入守卫（422）。

L1/L2/L5 的 LLM 调用标记为集成测试（对齐现有 `test_graph.py` 打真 LLM 的做法）。

## 明确不做（YAGNI）

- L3/L4 层、评分检索（方案 B）、embedding、向量库、TiMeM 的调度器/回填/补漏检测。
- 多用户体系（`user_id` 只留字段维度）。
- `recent_l2` 滑动窗口注入 L2 prompt（TiMeM 生产链路自己都没接通）。
