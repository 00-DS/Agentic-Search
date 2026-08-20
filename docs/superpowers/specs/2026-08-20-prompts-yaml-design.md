# 设计：prompt 集中管理（configs/prompts.yaml）+ persona 注入

> 日期：2026-08-20
> 背景：store.py 的记忆 prompt 与 agent persona（心智模型）目前硬编码/缺失。用户决策：集中到一个 yaml，运行时注入；persona 一并做；**02 文档零改动**，全部落在 04。
> 前置：`services/llm.py` 共享客户端设计（2026-08-20-llm-shared-module-design.md）已实施（commit f269fe0..172e94f）。
> 分工：§1–§3 是代码形态约定（用户实现 store.py/graph.py 时照此落码）；§4 是本次文档改动（由助手执行）；§5 测试随用户实现落地。

## 问题

1. `memory/store.py` 的 `extract_l1` 内联三引号 prompt（约 20 行）；`consolidate_l2`/`consolidate_profile` 的 prompt 在 04 文档示例中同样内联——调话术要动代码。
2. agent 至今无 persona：`llm_call` 直接 `invoke(state["messages"])`，回答语言/角色边界全靠模型默认。

## 方案（已批准：方案 1，yaml + 加载器）

### 1. 文件与加载


`configs/prompts.yaml`，四个键，yaml 块标量 `|`：

```yaml
# configs/prompts.yaml —— 全部 LLM 话术集中于此，调话术零代码改动
persona: |
  你是 Agentic Search，一个论文问答助手。用户会上传论文 PDF，你通过工具
  （list_papers / read_paper / search_paper / extract_abstract）阅读和检索论文，
  回答用户关于论文的问题。始终用中文回答；引用论文内容时注明出自哪篇文件。
l1_extract: |
  你是记忆提取器。从以下对话中提取值得长期记住的原子事实。
  ……（6 类范围、统一标准、忽略项——正文与现行 04 §2.2 一致）
  已有记忆（若本轮事实与以下已有记忆重复，跳过，不要重复输出）：
  {recent_block}
  对话：User：{user}  Agent：{agent}
  以 JSON 数组输出：["事实1", "事实2", ...]
l2_consolidate: |
  你是记忆整合器。将以下原子事实整合为一段会话摘要。
  规则：合并重复、提取主题、保留关键细节，输出 100 字以内的摘要文字。
  事实列表：
  {facts}
l5_profile: |
  你是画像整合器。基于会话摘要更新用户画像。
  画像维度：身份与背景、偏好与倾向、长期关注话题、关键决策、重要事实。
  规则：合并新信息、修正已过时的描述、保留仍然成立的内容，输出 150 字以内的画像文字。
  历史画像：
  {previous_block}

  会话摘要：
  {summaries}
```

加载器 `configs/prompts.py`（模块级单例，与 `settings`/`_memories_collection` 同模式）：

```python
from pathlib import Path

import yaml

PROMPTS: dict[str, str] = yaml.safe_load(
    Path(__file__).with_name("prompts.yaml").read_text(encoding="utf-8")
)
```

- 占位符 = Python `str.format` 约定：`{recent_block}` `{user}` `{agent}` `{facts}` `{previous_block}` `{summaries}`。prompt 内字面 `{`/`}` 需双写 `{{`/`}}`（现行 prompt 无字面大括号，规则写进 04 FAQ）。
- `retrieve_memory` 的注入格式化（"用户画像（跨会话长期记忆）："等标签 + 记忆列表拼接）留在代码——那是消息拼装而非 LLM prompt，动态逻辑归代码。
- 依赖：`pyyaml` 由传递依赖转正为直接依赖（`uv add pyyaml`；uv.lock 已含 6.0.3）。
- 叙事：TiMeM 生产实现即 `config/prompts.yaml` 集中管理——教学版与生产同构。

### 2. store.py 调用点（内联 prompt 全删）

```python
from agentic_search.configs.prompts import PROMPTS

# extract_l1 内：
prompt = PROMPTS["l1_extract"].format(recent_block=recent_block, **history)
# consolidate_l2 内：
prompt = PROMPTS["l2_consolidate"].format(facts=facts)
# consolidate_profile 内：
prompt = PROMPTS["l5_profile"].format(previous_block=previous_block, summaries=summaries)
```

### 3. persona 注入（graph.py，04 第 4 步范围）

```python
from langchain_core.messages import SystemMessage
from agentic_search.configs.prompts import PROMPTS

@retry(max_attempts=3)
def llm_call(state):
    messages = [SystemMessage(content=PROMPTS["persona"])] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
```

- 每轮前置、存于调用而不入 state：persona（恒定身份）与 `retrieve_memory` 的记忆 SystemMessage（动态背景）职责正交，消息序恒为 `[persona, 记忆, 对话...]`。
- `store_memory` 提取事实用最后一对 user/agent 消息，persona SystemMessage 不干扰。
- 02 文档零改动：persona 属模块 4 的图演进，走 `/api/consolidate` 占位转正与 llm.py 提升的同一先例（04 指示改模块 2 的文件，02 保持模块 2 时点状态）。

### 4. 文档落点

| 文件 | 改动 |
|---|---|
| `任务文档/04-TMT记忆系统.md` | ① 前置小节扩为两节：llm.py（已有）+「prompt 集中管理」新前置节（prompts.yaml 四键全文 + prompts.py 加载器 + pyyaml 转正说明）；② §2.2–2.4 三处内联 prompt 换 `PROMPTS[...].format(...)` 调用（"Prompt 设计要点"讲解保留，指向 yaml 键）；③ 第 4 步补 persona 注入代码段与"恒定身份 vs 动态背景"讲解；④ FAQ +1「为什么 prompt 放 yaml？」（调话术零代码 + TiMeM 生产同构 + 字面大括号双写规则）；⑤ 完成检查 +2（prompts.yaml 四键就位；问「你是谁」persona 生效） |
| `任务文档/02-LangGraph-Agent.md` | **零改动**（用户明确要求） |
| `AGENTS.md` | 代码约定 +1 行：LLM 话术集中 `configs/prompts.yaml`，`PROMPTS` 模块级单例（`configs/prompts.py`），占位符走 `str.format`（字面大括号双写）；persona 由模块 4 引入，在 `llm_call` 每轮前置 SystemMessage（存于调用不入 state） |

### 5. 测试与验收

静态测试（零 LLM，进 `tests/test_memory.py` 或独立小节）：

```python
def test_prompts_keys():
    assert set(PROMPTS) == {"persona", "l1_extract", "l2_consolidate", "l5_profile"}

def test_prompt_placeholders():
    PROMPTS["l1_extract"].format(recent_block="x", user="u", agent="a")
    PROMPTS["l2_consolidate"].format(facts="x")
    PROMPTS["l5_profile"].format(previous_block="x", summaries="x")
    PROMPTS["persona"].format()  # 无占位符，可安全 format
```

验收：
1. `grep -rn 'f"""' backend/src` 零命中（内联 prompt 清零）。
2. 上述两个测试通过。
3. 前端问「你是谁」——回答体现 persona（中文、论文助手身份）。
4. 04 FAQ/完成检查条目数与围栏平衡完好（编辑后例行复查）。
