## Task 6: 跨文档同步（概念速查 + 项目概览 + 00-开始指南）

**Files:**
- Modify: `任务文档/概念速查.md`、`任务文档/项目概览.md`、`任务文档/00-开始指南.md`

**Interfaces:**
- Consumes: Task 1-5 的全部改动
- Produces: 概念速查/项目概览/00 与新 agent 范式一致。

- [ ] **Step 1: 概念速查 — 更新现有条目 + 新增**

- **LangGraph 条目**：从「线性图 analyze_intent → read_and_answer」改为「ReAct agent 循环（llm_call ↔ tool_node + 条件边）」
- **Agentic Search 条目**：更新本项目用法，强调 agent 自主探索论文语料库（对标 omp/hermes）
- **FastAPI 条目**：确认 `@router` 装饰器讲解仍成立
- **装饰器条目**：确认仍存在且指向 02 第 5 步 `@retry`
- **httpx 条目**（若有）：保留客户端 vs 服务端讲解，但标注 agent 层用 LangChain
- **新增「ReAct」「tool calling」「条件边」相关概念**（可选，按概念速查体例）
- **删除**：任何「读全文进 128K 窗口」「不做关键词检索」旧论证（那是线性图设计依据，已过时）

- [ ] **Step 2: 项目概览 — 更新架构与模块描述**

- **系统架构 mermaid**（第 18-31 行）：`Routes → Graph` 改为 `Routes → Agent(llm_call ↔ tool_node)`
- **文件结构**（第 60-92 行）：`agents/graph.py` 描述从「LangGraph 图 + 节点 + State」改为「ReAct agent + 4 工具 + 条件边」
- **M1 学习目标**（第 111 行）：加「ReAct agent / 工具调用 / 条件边」
- **数据流-提问流程**（第 205-221 行）：从「analyze_intent → read_and_answer」改为「agent ReAct 循环（list_papers/search_sections/read_section）」
- **API 设计表**（第 154-159 行）：`/api/query` 请求体从 `{question, doc_id}` 改为 `{question}`
- **技术栈表**（第 243-255 行）：加 `langchain`/`langgraph`；确认无 chroma/embedding

- [ ] **Step 3: 00-开始指南 — 更新学习路径与项目介绍**

- **学习路径**（第 27-39 行）：模块 2 描述从「LangGraph 编排分析意图→读文档→回答」改为「LangGraph ReAct agent，LLM 自主调工具探索论文」
- **项目概述**（第 5 行）：确认「带记忆的论文问答助手」仍准确
- **「准备 LLM API Key」**（第 92-100 行）：DeepSeek 配置不变

- [ ] **Step 4: 全局 grep 一致性扫描**

跨 `任务文档/` 全部 grep：
- `analyze_intent|read_and_answer|_read_first_document` → 应为 0（除非历史/否定说明）
- `chroma|embedding|向量库` → 应为 0（除非否定句「无向量库」）
- `doc_id.*=.*""` （QueryRequest 旧默认值）→ 0
- `读全文|128K|全文进.*窗口` → 检查每处，确认已更新为 agent 按需取片段叙事
- `bind_tools|ToolNode|add_conditional_edges|list_papers|search_sections` → 应在 02/概念速查/项目概览存在

- [ ] **Step 5: 装饰器 cross-reference 网完整性检查**

确认五处装饰器呼应仍在且互相指向：
1. 概念速查「装饰器」条目 → 02 第 5 步
2. 02 技术概念段落 → 第 5 步、第 9 步、模块 4
3. 02 第 5 步「插曲：什么是装饰器」+ `@retry`
4. 02 第 9 步 `@router` 呼应
5. 04 `@dataclass` 呼应 → 02 `@retry`

- [ ] **Step 6: Commit**

```bash
git add 任务文档/概念速查.md 任务文档/项目概览.md 任务文档/00-开始指南.md
git commit -m "docs(sync): 概念速查/项目概览/00 同步 agent 范式（ReAct + 工具 + 条件边）"
```

---

## 验收标准（全部 task 完成后）

1. `grep -rn "analyze_intent\|read_and_answer\|_read_first_document" 任务文档/` → 0 命中（或仅否定说明）
2. `grep -rn "chroma\|embedding\|向量库" 任务文档/` → 仅否定句（「无向量库」）
3. `grep -rn "doc_id.*=.*\"\"" 任务文档/` → 0（QueryRequest 无 doc_id 默认值）
4. 02 含 `bind_tools`/`ToolNode`/`add_conditional_edges`/`list_papers`/`search_sections`
5. 01 的 `parse_pdf` 用 `get_text("dict")`，MongoDB schema 含 `sections`
6. 装饰器 cross-reference 五处完整
7. 03 无 `doc-list` 下拉框
8. 项目概览/概念速查/00 与 agent 范式一致
