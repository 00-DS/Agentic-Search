# Task 1 Report: 01-Python文档工具.md — 加入论文导航工具集

## 状态
✅ **完成并已提交**。13 个步骤全部应用，文档内部一致性保持。

## Commit
```
3178633 docs(01): 加入论文导航工具集（agents/tools.py 四工具），平衡 01/02 内容量
1 file changed, 134 insertions(+), 14 deletions(-)
```

## 改动摘要（按 brief 13 步）
1. **Step 1** — `pyproject.toml` 依赖数组加 `"langchain"`（行 203）。
2. **Step 2** — `mkdir`/`touch` 命令加 `agents/`（行 249、252）。
3. **Step 3** — 项目结构树 `services/` 由末子项改为 `├──`，新增 `agents/` 块含 `tools.py`（行 141-146）。
4. **Step 4** — mermaid 图加 `Tools["Agent 工具<br/>tools.py"]` 节点 + `Services --> Tools` / `Tools -->|"调用"| Services` 连线（行 104-114）。
5. **Step 5** — 学习目标加第 6 条（@tool 装饰器，行 16）。
6. **Step 6** — 插入完整新「步骤 4：`agents/tools.py` 论文导航工具集」（行 515-620）：含 `_get_doc_text` + 四个 `@tool` 工具完整源码、omp 对应表、两条 why 段、验证命令。
7. **Step 7** — 旧 Step 4→**步骤 5：编写测试**，旧 Step 5→**步骤 6：集成验证**。
8. **Step 8** — 完成检查加 `agents/tools.py` 四工具条目（行 780）。
9. **Step 9** — 下一步段落改为「全部底层能力…Agent 将用 `build_graph()` 把四个工具组装成 ReAct 循环」（行 863）。
10. **Step 10** — 技术概念加「LangChain `@tool` 装饰器」小节（行 79-81）。
11. **Step 11** — 模块结构描述「三个部分」→「四个部分…Agent 导航工具」（行 98）。
12. **Step 12** — 产出段落加「、Agent 导航工具（`agents/tools.py`）」（行 18）。
13. **Step 13** — ✅ 已 commit。

## 验证
- 新 Step 4 代码围栏配平：` ```python `(523)↔` ``` `(596)、` ```bash `(613)↔` ``` `(616)。
- 四工具签名与 brief/全局约束一致：`list_papers()` / `read_paper(doc_id, start_line=1, end_line=50)` / `search_papers(pattern, doc_id="")` / `extract_abstract(doc_id)`。
- 标题链连贯：步骤 1→2→3→4(tools)→5(tests)→6(integration)，无编号空洞。

## 超出 brief 字面的连带一致性修复（已做，供 reviewer 裁决）
brief 字面只点名了两个 H2 标题改名，但为保证「纯新版本、零历史包袱」的内部一致，补做了 brief 未逐条列出、但属同一改动逻辑必然的 4 处：
1. 子章节 `#### 4.1`→`#### 5.1`、`#### 4.2`→`#### 5.2`（否则子章节号会与父步骤号脱节，文档自相矛盾）。
2. 完成检查的 `pyproject.toml` 依赖清单加 `langchain`（否则刚加的依赖在检查表里缺失）。
3. 「每个 Python 子包（…）」一句加 `agents/`（否则 mkdir 加了 agents 但说明没列）。
- 若 reviewer 认为应严格只改 brief 点名项，可回退这 4 处。

## 已知 / 遗留
- brief Step 6 末尾有一行孤立的 ` ``` `（明显是复制残留的代码围栏闭合符），已**主动剔除**——否则会在文档里产生一个悬空围栏破坏渲染。
- 本任务仅改 01 文档；02 的旧 Step 6（论文导航工具集）的**删除**由 Task 2 负责，本任务不触碰 02。
- `read_document` 在新 `tools.py` import 列表中存在但未被四个工具直接调用（仅 `list_documents`、`_documents_collection` 被用）。这是 brief 给定的源码原样，保持不变。

## 关注点（给 reviewer / Main）
- 01 现已引入 `langchain` 依赖与 `@tool`，是装饰器网络的起点（后续 02 `@retry`/`@router.post`、04 `@dataclass`），叙事已通过 @tool 小节与 blockquote 埋好伏笔。
- 01 与 02 的内容平衡：01 现为「文档地基 + Agent 导航工具」，02 待 Task 2 收敛为「组装图 + API」。
