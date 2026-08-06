# 设计：parse_pdf 改字节流，干掉临时文件（模块 2 演进式优化）

## 背景

任务文档 `02-LangGraph-Agent.md` 的 8.2 节（POST /api/ingest）当前用临时文件方案处理 PDF 字节流：

```python
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(pdf_bytes)
    tmp_path = tmp.name
try:
    text = parse_pdf(tmp_path)
finally:
    os.unlink(tmp_path)
```

注释写「pymupdf 的 open() 需要文件路径」——**这是事实错误**。pymupdf 1.28.0 的 `open()` 签名是 `(filename=None, stream=None, filetype=None, ...)`，`stream=` 参数直接吃字节流。已验证：`pymupdf.open(stream=pdf_bytes, filetype="pdf")` 与路径方式提取结果完全一致。

临时文件存在的唯一根因：模块 1 的 `parse_pdf` 契约收路径（`parse_pdf(path)`），而 ingest 拿到的是字节流（`await file.read()`）。改 `parse_pdf` 契约收字节，临时文件那 12 行全部消失。

## 设计决策

### 1. 只改模块 2 文档，不回溯模块 1 文档

- 模块 1（`01-Python文档工具.md`）已分发，读者已按其学习并实施了 `parse_pdf(path)`。
- 模块 2（`02-LangGraph-Agent.md`）承担"引导读者优化 parse_pdf 为字节流 + 同步更新测试"的全部职责。
- 教学价值：读者先理解笨办法的啰嗦（临时文件 12 行），再亲历字节流如何让它塌缩成 4 行——通过对比**感受**字节流的优势，而非被告知。

### 2. 8.2 节叙事：对比式优化（奶妈级教学）

保留"笨办法"作为被讨论的对照物，**用说明文字 + 完整 Python 代码**呈现，逐行讲解。结构：

1. **笨办法**：完整临时文件代码 + 逐行注释（tempfile / delete=False / try/finally / os.unlink），让读者理解每一行为什么必要——同时看清它的成本（12 行才完成"字节→文本"）。
2. **点破根因**：问题不在 pymupdf——它的 `open(stream=...)` 一直支持字节流（展示签名）；根因是 `parse_pdf` 收路径。改契约，12 行全消失。
3. **优化**：给出新的 `parse_pdf(pdf_bytes)` 契约 + 实现，指引读者回到 `services/documents.py` 替换。
4. **优化后的 ingest**：4 行最终版，与笨办法对比"12 → 4"。

### 3. parse_pdf 新契约

```python
def parse_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流提取纯文本（不读文件、不落盘）。"""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text("text") for page in doc)
```

- 入参 `path: str | Path` → `pdf_bytes: bytes`。
- 内部 `pymupdf.open(p)` → `pymupdf.open(stream=pdf_bytes, filetype="pdf")`。
- 删 `Path / exists / FileNotFoundError` 三行——文件不存在的语义交给调用方的 `read_bytes()` 自然抛 `FileNotFoundError`。
- **不加空字节守卫**：pymupdf 已对空字节抛 `pymupdf.EmptyFileError: Cannot open empty stream.`，对损坏字节抛 `pymupdf.FileDataError: Failed to open stream`。重复校验砍掉，简单优先。

### 4. 优化后的 ingest 路由

```python
@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """上传 PDF，提取纯文本并存入 MongoDB（零文件系统依赖）。"""
    pdf_bytes = await file.read()
    text = parse_pdf(pdf_bytes)
    doc_id = Path(file.filename).stem
    store_document(doc_id, file.filename, text)
    return IngestResponse(doc_id=doc_id, filename=file.filename)
```

`tempfile` / `try/finally` / `os.unlink` 全删。设计说明里"零文件系统依赖"名副其实。

### 5. routes.py 导入清理

当前文档的导入块含 `import os`、`import tempfile`（8.2 节的临时文件方案用）。优化后这两个导入不再被任何端点使用，从导入块删除。`from pathlib import Path` 保留（ingest 的 `Path(file.filename).stem` 仍用）。

### 6. 测试同步（02 文档指引，改 test_documents.py）

| 测试 | 改动 |
|------|------|
| `test_parse_pdf_return_string` | `parse_pdf(path)` → `parse_pdf(Path(path).read_bytes())` |
| `test_parse_pdf_file_not_found` | 删除；替换为 `test_parse_pdf_empty_bytes_raises`，断言 `pymupdf.EmptyFileError` |

## 改动清单

### 文档（教学材料）

| 文件 | 改动 |
|------|------|
| `任务文档/02-LangGraph-Agent.md` | 8.2 节整段重写（笨办法 + 根因 + 优化 + 测试同步）；导入块（第 8 步开头，约 line 498-499）删 `import os`/`import tempfile` |

**不改动**：`01-Python文档工具.md`（模块 1，已分发）。

### 代码（仓库现状同步）

| 文件 | 当前状态 | 改动 |
|------|----------|------|
| `backend/src/agentic_search/services/documents.py` | `parse_pdf(path)` 收路径（line 10-16） | 改收 bytes，`stream=` 实现 |
| `backend/src/agentic_search/api/routes.py` | 只有 `/query` 端点，无 ingest；`import os/tempfile` 死导入 | 删死导入；如需补 ingest 则用优化版 |
| `backend/test/test_documents.py` | `test_parse_pdf_return_string`(传路径)、`test_parse_pdf_file_not_found`(断言 FileNotFoundError) | 调用改传 bytes；错误测试换 `EmptyFileError` |

> **仓库现状备注**：实际 `routes.py` 当前只有 `/query`，未实现 `/ingest`/`/documents`/`/consolidate`——代码落后于文档。`import os, tempfile` 是已存在的死导入。本次改动清理死导入；ingest 端点是否补入 routes.py 由实现计划决定（文档已教，代码补齐是独立项）。

## 验证

- 仓库层面：`parse_pdf(some_pdf_bytes)` 返回非空 str；`parse_pdf(b"")` 抛 `pymupdf.EmptyFileError`。
- 文档层面：8.2 节的笨办法代码块语法正确、注释准确；优化段清晰展示 12→4 对比；无"不使用XXX"措辞。
