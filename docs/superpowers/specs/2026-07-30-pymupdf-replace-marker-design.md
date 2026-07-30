# 设计规格：用 pymupdf 替换 marker-pdf

> 日期：2026-07-30
> 范围：**仅修改 `任务文档/` 下的文档**（`backend/` 实现代码不在本次范围）
> 状态：待用户 review

---

## 1. 目标

把教学项目中「PDF → 文本」的实现，从「marker-pdf 调深度学习模型转结构化 Markdown」改为「**pymupdf 逐页 `get_text()` 提取纯文本**」。保持最简：只留文字，图片等非文字内容天然丢弃，不重建表格/公式/标题结构。

## 2. 已锁定的决策

| 项 | 决定 | 理由 |
|---|---|---|
| 改动范围 | 仅 `任务文档/` | 用户明确 |
| 新工具 | pymupdf（现代 `import pymupdf` API，非旧 `import fitz`） | 单一轻量 wheel，无模型下载、无 CUDA、依赖干净；文档明示其对新手友好 |
| 提取粒度 | **纯文本，零结构** | 用户要求"最简单、只留文字"；`page.get_text()` 默认只返文字 |
| 页间分隔 | 页与页之间用空行拼接 | 最简；不加 `---` 等页边界标记 |
| 架构改动 | **零**——保持现有 ingest-time 解析 + MongoDB 存储 + Agent 读已存文本的完整流程 | 与 marker-pdf 换汤不换药，只换 `parse_pdf` 函数体 |
| 叙事处理 | **保留通论 + 标注简化**（用户先前选择） | 保留"结构助 LLM 理解"的通论，加一句"本项目刻意选最简提取"；不删教学价值 |

## 3. pymupdf 基础用法（源码核实）

```python
import pymupdf

doc = pymupdf.open("paper.pdf")   # 打开文档
parts = []
for page in doc:                   # 逐页迭代
    parts.append(page.get_text())  # get_text() 默认只返回文字
md = "\n".join(parts)              # 页间空行拼接
```

- `page.get_text()` 默认提取页内**文字**；图片、矢量图等非文字内容**不进文本**，"丢弃"是天然的、无需任何后处理。
- 现代 API 是 `import pymupdf`（≥1.23.8 官方推荐别名）；旧 `import fitz` 仍可用但非首选，文档统一用 `import pymupdf`。

## 4. `parse_pdf` 函数（核心改动）

`parse_pdf(pdf_path: str | Path) -> str` 的**签名与职责不变**，只换函数体：

```python
from pathlib import Path
import pymupdf

def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF 文件，使用 pymupdf 提取纯文本（图片等非文字内容丢弃）。"""
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    doc = pymupdf.open(p)
    parts = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(parts)
```

与 marker-pdf 旧版的对比：
- 旧版需要模块级缓存 `_converter`（模型加载开销大）；**pymupdf 无此负担**，`open()` 轻量，每次调用即可，缓存层移除。文档要据此删除旧 `_converter`/`_get_converter()` 的整段教学（性能优化那段）。
- 旧版返回**结构化 Markdown**（带 `#` 标题、Markdown 表格）；新版返回**纯文本**，无 `#`、无表格重建。文档的"转换效果对比"小节要改。

## 5. 架构（不变，仅复述确认）

```
上传 PDF → /api/ingest 读字节 → 写临时文件 → parse_pdf(path) → 存 Markdown 进 MongoDB
查询时 → Agent 经 read_document(doc_id) 读已存文本 → 进 LLM 上下文 → 回答
```

- 仍是 **ingest-time 解析 + MongoDB 存储 + Agent 读已存文本**。
- `store_document`/`read_document`/`list_documents` 三函数**完全不变**。
- 「零文件系统依赖」（临时文件 + `os.unlink`）**保持**——pymupdf 收文件路径，与 marker-pdf 一样适配临时文件方案。
- Agent 端（模块 3）**几乎不动**：`read_and_answer` 注释里「marker-pdf 转换的结构化 Markdown」改为「pymupdf 提取的纯文本」即可，逻辑无改。

## 6. 依赖变更

- `backend/pyproject.toml`（文档里的示例）：`marker-pdf` → `pymupdf`。
- 依赖验证命令（`00-开始指南.md`）：`import marker` → `import pymupdf`。
- 文档里"marker-pdf 首次安装下载模型权重"的预警 → 删除（pymupdf 无模型下载）。

## 7. 文档改动地图

| 文档 | 改动 |
|---|---|
| **`01-Python文档工具.md`** | **改动集中处**。① 技术栈行 `marker-pdf` → `pymupdf`。② §marker-pdf 原理段（深度学习版面检测+OCR）→ 改写为 pymupdf 原理（MuPDF 内核、`get_text` 纯文字提取、图片天然丢弃）。③ §`parse_pdf` spec：删除 PdfConverter 示例与 `_converter` 模块级缓存/性能优化整段，换为 §4 的 pymupdf 实现。④ "转换效果对比"：旧"标题→`#`、表格→Markdown 表格"→ 改为"逐页纯文本拼接，无结构"。⑤ 概念条目 + mermaid 图（`marker-pdf → PDF 解析` 节点）→ pymupdf。⑥ 依赖说明（`pyproject.toml` 示例 + 验证命令）。 |
| **`03-LangGraph-Agent.md`** | 轻改。`read_and_answer` 注释「marker-pdf 转换的结构化 Markdown」→「pymupdf 提取的纯文本」；对比表"预处理：marker-pdf 转 Markdown"→"pymupdf 提取文本"；正文逻辑不动。`/api/ingest` 代码不动。 |
| **`概念速查.md`** | `marker-pdf` 概念条目 → 改为 `pymupdf` 条目（MuPDF 内核、纯文本提取、为何对新手友好）；LangGraph 条目里"marker-pdf 转换的 Markdown"措辞同步。 |
| **`项目概览.md`** | 技术栈表 `marker-pdf` 行 → `pymupdf`；数据流图节点名同步；目录结构不变（无新增文件）。 |
| **`00-开始指南.md`** | 依赖清单 `marker-pdf` → `pymupdf`；链接换为 pymupdf 文档；删除"首次安装下载模型权重"预警。 |

## 8. 叙事重写策略（保留通论 + 标注简化）

marker-pdf 文档里"为什么需要结构化而非纯文本 / 现代 LLM 上下文够大直接读全文"的论证**通论部分保留**。新增一处明确标注：

> **本项目为降低门槛刻意选择最简的纯文本提取**（pymupdf）。生产环境若需保留标题层级、表格、公式等结构，可换用更重的工具（如 marker-pdf、MinerU）。对教学而言，纯文本提取零依赖、零模型下载、即装即用，足以演示「全文进 LLM 上下文」的核心思想。

这样既不删教学价值（结构为何重要的通论），又诚实地说明本项目的简化取舍，避免文档自相矛盾（不出现"文档说保留表格、代码却返回纯文本"）。

## 9. 非目标（Out of Scope）

- 不改 `backend/` 实现代码（仅文档）。
- 不做结构化提取（标题/表格/公式）——明确只要纯文本。
- 不保留图片——明确丢弃。
- 不引入 MCP、MinerU、OCR——本方案就是最简。
- 不改 ingest-time 解析 + MongoDB 存储的架构。
