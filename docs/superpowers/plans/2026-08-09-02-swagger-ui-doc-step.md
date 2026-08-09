# doc 02 新增「Swagger UI / redoc」教学步骤 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 doc 02 新增独立教学步骤「用 FastAPI 自带文档界面直观感受你的 API」，填补「只提 /docs、从不教怎么用」的 gap，建立「启动 → 手动直观感受 → 写自动化测试」的教学脉络。

**Architecture:** 纯文档新增。插入新第 11 步（介绍 /redoc 只读文档 + /docs 交互式 Swagger UI 的分工，在 /docs 里逐个试 4 个端点，SSE 端点带局限说明），当前第 11 步（pytest）重编号为第 12 步，完成检查补 /redoc 条目。不改任何代码（/docs 与 /redoc 是 FastAPI 默认行为）。

**Tech Stack:** Markdown 教学文档。

**Spec:** `docs/superpowers/specs/2026-08-09-02-swagger-ui-doc-step-design.md`

## Global Constraints

- **纯文档，不改代码**（`main.py`、`routes.py` 等全不动——`/docs` 与 `/redoc` 是 FastAPI 默认挂载）。
- **文档政策**：只写「为什么这样」，禁否定措辞「不使用 XXX」。（注：「Swagger 等整段跑完、不是逐字流式」是客观事实陈述，不属禁用模式。）
- 行号为近似值——以内容定位为准（grep 关键短语），不盲目按行号切割。
- 所有改动在 `任务文档/02-LangGraph-Agent.md` 一个文件内。

## File Structure

- `任务文档/02-LangGraph-Agent.md` — 唯一改动文件：插入新第 11 步 + 当前第 11 步重编号为 12 + 完成检查更新。

---

## Task 1: 新增第 11 步 + 重编号 + 完成检查更新

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md`（L804 后插入、L806/808/835 重编号、L880 更新）

**Interfaces:** 无（纯文档）。

- [ ] **Step 1: 在 L804 的 `---` 之后、L806 `## 第 11 步：编写测试（pytest）` 之前，插入新第 11 步**

在 L805（空行）之后、L806 之前插入以下完整内容（含末尾的 `---` 分隔）：

```markdown
## 第 11 步：用 FastAPI 自带文档界面直观感受你的 API

启动服务后，你已经用第 10 步的 `httpx` 命令验证了每个端点能跑。FastAPI 还提供更直观的方式——两个自动生成的 API 文档界面，零额外代码。这一步先用它们**手动感受一遍**，下一步（第 12 步）再把验证固化成 pytest 自动化测试。

### 11.1 两个文档界面：/redoc 与 /docs

FastAPI 从你的**类型标注 + Pydantic 模型**自动生成一份 OpenAPI 规范（描述 REST API 的标准格式），并据此提供**两个**界面，分工不同：

- **`http://localhost:8000/redoc`** —— **文档视图**（只读）。三栏布局：左侧端点目录、中间参数/响应结构详情、右侧示例。适合**通读全部 API 长什么样**，排版漂亮，但发不了请求。
- **`http://localhost:8000/docs`** —— **交互视图**（Swagger UI）。每个端点能展开 → 点 **Try it out** → 填参数 → **Execute** → 看真实返回的 JSON / SSE。适合**实际试一遍**。

两个界面背后共用同一份 `/openapi.json`（你可以直接访问这个 URL 看原始 JSON 规范）。改了代码 → 规范更新 → 两个界面同步更新，零维护成本。日常调试用 `/docs`（能试请求）；想看全貌或分享给别人读用 `/redoc`（排版好）。

> 📖 FastAPI 自动文档官方教程：[https://fastapi.tiangolo.com/zh/tutorial/first-steps/#interactive-api-docs](https://fastapi.tiangolo.com/zh/tutorial/first-steps/#interactive-api-docs)

### 11.2 在 /docs 里逐个试你的 4 个端点

打开 `http://localhost:8000/docs`，点开每个端点 → **Try it out** → 填参数 → **Execute**，亲眼确认每个端点能正常工作：

- **GET /api/documents** —— 返回 JSON 文档列表（第一次为空数组 `[]`，上传 PDF 后能看到条目）。
- **POST /api/ingest** —— 在请求体里上传一个 PDF 文件 → 返回 `{"doc_id": "...", "filename": "..."}`。
- **POST /api/consolidate** —— 填 `session_id` → 返回 `{"status": "pending", "l2_id": ""}`（模块 4 才接入真实整合逻辑，现在诚实返回 `pending`）。
- **POST /api/query** —— 填问题（如「你好」）→ **等几秒**（agent 在跑 ReAct 循环）→ 返回一整段 SSE 文本。

### 11.3 /api/query 在 Swagger 里的样子（一个要注意的局限）

`/api/query` 的 Execute 会**等 agent 完整跑完后**，一次性把全部 SSE 帧文本显示出来——你会看到一长串 `data: "\u4f60\u597d"` 这样的行，这就是 SSE 流的 wire 格式（第 8 步讲过）。

注意：**Swagger 会等整段跑完才一次性显示，而不是逐字流式出现**。要感受「逐字打字」的流式体验，用第 10 步的 `httpx.stream` 命令、或模块 3 的前端界面。Swagger 在这里的价值是**验证端点能跑 + 直观看到 wire 格式全文**，而非看流式动画。

### 11.4 为什么 Pydantic 模型这么重要——第二个回报

注意面板里每个端点的请求/响应结构——`QueryRequest` 的 `question` 字段、`IngestResponse` 的 `doc_id`/`filename`——这些全来自第 7 步 `schemas.py` 里定义的 Pydantic 模型。这就是「认真定义模型」的第二个回报：除了第 7 步讲过的自动校验（缺字段返回 422），还自动变成了这个**人能读的交互文档**。改模型，面板同步更新——你定义一次，校验与文档两处受益。

现在你已经亲手试过每个端点、确认它们正常工作。下一步（第 12 步）把这些手动验证**固化成 pytest 自动化测试**——把「每次改代码手动点一遍」升级成「每次改代码自动跑一遍」。

---
```

- [ ] **Step 2: 重编号当前第 11 步 → 第 12 步**

- L806：`## 第 11 步：编写测试（pytest）` → `## 第 12 步：编写测试（pytest）`
- L808：`### 11.1 测试图逻辑` → `### 12.1 测试图逻辑`
- L835：`### 11.2 测试 API 接口` → `### 12.2 测试 API 接口`

> 已 grep 确认全文无其它对「第 11 步」「11.1」「11.2」的交叉引用，重编号零散落。

- [ ] **Step 3: 更新完成检查（L880）**

当前 L880：`- [ ] 访问 http://localhost:8000/docs 能看到 4 个端点的交互式文档`

改为：`- [ ] 访问 http://localhost:8000/docs 和 /redoc，分别看到交互式 API 文档（能 Try it out）与只读文档视图`

- [ ] **Step 4: 通读复核**

手动复核三点：
1. **新第 11 步衔接**：第 10 步末尾 → 新第 11 步（开篇承接「第 10 步已用 httpx 验证、这里用更直观的界面」）→ 第 12 步（开篇承接「把这些手动验证固化成 pytest」），三条脉络连贯。
2. **重编号无残留**：grep 全文「第 11 步」「11.1」「11.2」「11.3」「11.4」，确认新第 11 步用的是 11.x（无残留旧 pytest 内容用 11.x 编号），旧 pytest 内容已全改 12.x。
3. **禁否定措辞**：新增内容里无「不使用 XXX」。「Swagger 等整段跑完、不是逐字流式」属客观事实陈述。

- [ ] **Step 5: 提交**

```bash
cd "D:/Python/Common/Agentic Search"
git add "任务文档/02-LangGraph-Agent.md"
git commit -m "docs(02): 新增第 11 步——Swagger UI / redoc 直观感受 API

填补「只提 /docs、从不教怎么用」的 gap，建立「启动 → 手动直观
感受 → 写自动化测试」的脉络。双 URL 对比（redoc 只读文档 / docs
交互式），4 个端点全试，SSE 端点带 Swagger 局限说明。当前 pytest
步骤重编号为第 12 步。纯文档新增，不改代码。"
```

---

## Self-Review

**1. Spec coverage：**
- spec §4.1 新增第 11 步（5 段内容）→ Task 1 Step 1。注：spec 写 5 段（① 双 URL + ② 逐个试 + ③ SSE 局限 + ④ 呼应 schemas + ⑤ 小结）；plan 把 ① 拆成 11.1（双 URL）+ 11.2（逐个试）、③ 为 11.3、④⑤ 合并进 11.4。内容等价，子节号更规整（11.1–11.4）。✅
- spec §4.2 重编号 → Task 1 Step 2。✅
- spec §4.3 完成检查更新 → Task 1 Step 3。✅
- spec §4.4 可选交叉引用（L492）→ 未纳入（可选项，YAGNI——L492 已提到 /docs，不强求加交叉引用）。明确标注为有意省略。
- spec §4.5 不动代码 → Global Constraints 明确。✅
- spec §5 验证计划 → Task 1 Step 4（通读复核：衔接 + 重编号 + 否定措辞）。事实核查（启动服务亲访问）可选，因 spec §2 已 TestClient 验证两 URL 活着。

**2. Placeholder scan：** 无 TBD/TODO；每步含具体内容或命令；新第 11 步完整成文。

**3. Type consistency：** 子节号 11.1–11.4 内部一致；与重编号后第 12 步（12.1/12.2）不冲突；完成检查措辞与 11.1 双 URL 描述一致。
