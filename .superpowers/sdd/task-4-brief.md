## Task 4: `03-HTML前端.md` — 去掉文档选择，配合新 query 契约

**Files:**
- Modify: `任务文档/03-HTML前端.md`

**Interfaces:**
- Consumes: Task 3 的新 `/api/query` 契约（无 doc_id）
- Produces: 03 前端无文档下拉框，`askQuestion()` fetch body 只发 question。

- [ ] **Step 1: 改学习目标（如有提及文档选择）**

确认学习目标不依赖「文档下拉框」教学。

- [ ] **Step 2: 删除文档选择下拉框的 HTML（`<select id="doc-list">` 相关）**

grep `doc-list` 定位。删除下拉框控件。UI 改为纯提问输入框——用户只管问，agent 自己找论文。保留上传按钮（`/api/ingest` 不变）。

- [ ] **Step 3: 改 `askQuestion()` 的 fetch body（`app.js` 教学示例）**

原文 `body: JSON.stringify({ question, doc_id })`。改为 `body: JSON.stringify({ question })`。

- [ ] **Step 4: 改 `loadDocuments()` 相关（如前端不再需要列文档）**

若 `GET /api/documents` 仍保留（供 agent 工具用，但前端不再展示下拉框），说明：前端不再调 `loadDocuments()` 渲染下拉框，该端点转为 agent 工具的后端依赖。

- [ ] **Step 5: 改模块结构 mermaid 图与数据流描述**

旧图标「下拉框选择 doc_id」。改为「用户提问 → agent 自主探索」。

- [ ] **Step 6: 改「为什么前端排在模块 2 之后」段（约第 60 行）**

确认仍成立（前端需后端 agent 能响应）。措辞从「响应 4 个 API 端点」调整为「响应 agent 问答」。

- [ ] **Step 7: grep 一致性扫描**

grep `doc_id|doc-list|loadDocuments` → 确认下拉框逻辑已清除（`loadDocuments` 若保留供其他用途则说明）。

- [ ] **Step 8: Commit**

```bash
git add 任务文档/03-HTML前端.md
git commit -m "docs(03): 去掉文档选择下拉框，query 契约去掉 doc_id（配合 agent 自主探索）"
```

---

