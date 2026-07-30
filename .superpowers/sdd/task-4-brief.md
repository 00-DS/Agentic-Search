## Task 4: `03-LangGraph-Agent.md` — pymupdf + core→configs + 数据库名

**Files:**
- Modify: `任务文档/03-LangGraph-Agent.md`

- [ ] **Step 1: pymupdf — 引言段（第 88 行）**

原文：`...它直接读取论文全文（marker-pdf 转出的 Markdown），让 LLM 基于全文内容生成回答。`
改为：`...它直接读取论文全文（pymupdf 提取的纯文本），让 LLM 基于全文内容生成回答。`

- [ ] **Step 2: pymupdf — 对比表（第 94 行）**

原文：`| 预处理 | 需切片 + 建向量索引 | 只需 marker-pdf 转 Markdown |`
改为：`| 预处理 | 需切片 + 建向量索引 | 只需 pymupdf 提取纯文本 |`

- [ ] **Step 3: pymupdf — read_and_answer 注释（第 370 行）**

原文：`#    返回 marker-pdf 转换的结构化 Markdown 文本（保留标题层级、段落、表格结构）`
改为：`#    返回 pymupdf 提取的纯文本全文（图片等非文字内容已丢弃）`

- [ ] **Step 4: pymupdf — ingest 注释（第 609、615 行）**

原文：
```
    # ② marker-pdf 的 PdfConverter 需要文件路径：写入临时文件
    ...
    #    # ③ 纯转换：parse_pdf 只负责 marker-pdf 转 Markdown，返回字符串
```
改为：
```
    # ② pymupdf 的 open() 需要文件路径：写入临时文件
    ...
    #    # ③ 纯提取：parse_pdf 只负责 pymupdf 提取纯文本，返回字符串
```

- [ ] **Step 5: pymupdf — §9.2 设计说明（第 630-631 行）**

原文：
```
- **零文件系统依赖**：PDF 字节流写入 `tempfile` 临时文件，marker-pdf 转换后 `os.unlink` 立即删除。...即使转换抛异常，临时文件也会被清理。
- **职责分离**：`parse_pdf` 只做「PDF → Markdown」转换（纯函数...）；`store_document` 只做...
```
改为：
```
- **零文件系统依赖**：PDF 字节流写入 `tempfile` 临时文件，pymupdf 提取后 `os.unlink` 立即删除。...即使提取抛异常，临时文件也会被清理。
- **职责分离**：`parse_pdf` 只做「PDF → 纯文本」提取（纯函数...）；`store_document` 只做...
```

- [ ] **Step 6: core→configs — 读图说明（第 57 行）**

原文：`所有可配置项（LLM 模型名、超时、路径）集中在 `core/config.py`。`
改为：`所有可配置项（LLM 模型名、超时、路径）集中在 `configs/config.py`。`

- [ ] **Step 7: core→configs — 目录树（第 112-113 行）**

原文：
```
├── core/
│   └── config.py        # 本模块新建：配置层（读 .env）
```
改为：
```
├── configs/
│   └── config.py        # 本模块新建：配置层（读 .env）
```

- [ ] **Step 8: core→configs — 依赖表（第 144 行）**

原文：`| `pydantic-settings` | 从 `.env` 读取配置 | `core/config.py` |`
改为：`| `pydantic-settings` | 从 `.env` 读取配置 | `configs/config.py` |`

- [ ] **Step 9: core→configs — §第3步标题与说明（第 206、208 行）**

第 206 行原文：`## 第 3 步：配置层 —— `core/config.py``
改为：`## 第 3 步：配置层 —— `configs/config.py``

第 208 行原文：`...这些可变值集中放到 `core/config.py`，从 `.env` 文件读取。...`
改为：`...这些可变值集中放到 `configs/config.py`，从 `.env` 文件读取。...`

- [ ] **Step 10: core→configs — 代码注释（第 211 行）**

原文：`# core/config.py —— 教学示例：集中管理配置`
改为：`# configs/config.py —— 教学示例：集中管理配置`

- [ ] **Step 11: core→configs — import 注释（第 233 行）**

原文：`# 模块级单例：其他模块 `from agentic_search.core.config import settings` 直接使用`
改为：`# 模块级单例：其他模块 `from agentic_search.configs.config import settings` 直接使用`

- [ ] **Step 12: core→configs — 验证命令（第 255 行）**

原文：`uv run python -c "from agentic_search.core.config import settings; print(settings.llm_model)"`
改为：`uv run python -c "from agentic_search.configs.config import settings; print(settings.llm_model)"`

- [ ] **Step 13: core→configs — analyze_intent import（第 309 行）**

原文：`from agentic_search.core.config import settings`
改为：`from agentic_search.configs.config import settings`

- [ ] **Step 14: 数据库名 — config 默认值（第 226 行）**

原文：`    mongo_db: str = "agentic_search_db"           # 数据库名（记忆与文档均存于此）`
改为：`    mongo_db: str = "agentic_search"              # 数据库名（记忆与文档均存于此）`

- [ ] **Step 15: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/03-LangGraph-Agent.md
git commit -m "docs(03): pymupdf wording, core->configs, db name agentic_search"
```

---
