# parse_pdf 字节流优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把模块 2 的 ingest 端点从临时文件方案改为字节流方案，干掉 tempfile/try-finally/os.unlink 那 12 行，让 parse_pdf 契约收 bytes。

**Architecture:** 改动分两轨——教学文档（02 文档 8.2 节用对比式教学）+ 代码（documents.py / test_documents.py / routes.py 同步）。01 文档不回溯。

**Tech Stack:** pymupdf 1.28.0（`open(stream=, filetype=)`）、pytest、FastAPI、Markdown 文档

## Global Constraints

- **01 文档不改动**——`任务文档/01-Python文档工具.md` 一字不动
- **parse_pdf 新契约**：`def parse_pdf(pdf_bytes: bytes) -> str`，内部 `pymupdf.open(stream=pdf_bytes, filetype="pdf")`
- **不加空字节守卫**——pymupdf 自带 `EmptyFileError`（空字节）/ `FileDataError`（损坏字节），重复校验砍掉
- **文档无「不使用XXX」措辞**（项目策略）
- pymupdf 1.28.0，`open()` 签名 `(filename=None, stream=None, filetype=None, ...)`

---

## 文件结构

| 文件 | 责任 | 改动类型 |
|------|------|----------|
| `backend/src/agentic_search/services/documents.py` | `parse_pdf` 改收 bytes | 修改 |
| `backend/test/test_documents.py` | 两条 parse_pdf 测试同步 | 修改 |
| `backend/src/agentic_search/api/routes.py` | 删死导入 `os`/`tempfile` | 修改 |
| `任务文档/02-LangGraph-Agent.md` | 8.2 节整段重写 + 导入块清理 | 修改 |

---

### Task 1: parse_pdf 改字节流 + 测试同步

**Files:**
- Modify: `backend/src/agentic_search/services/documents.py:10-16`
- Modify: `backend/test/test_documents.py:4-11`

**Interfaces:**
- Produces: `parse_pdf(pdf_bytes: bytes) -> str`——收 PDF 字节流，返回纯文本字符串。内部用 `pymupdf.open(stream=pdf_bytes, filetype="pdf")`。空字节由 pymupdf 抛 `pymupdf.EmptyFileError`。

- [ ] **Step 1: 改 parse_pdf 实现**

把 `backend/src/agentic_search/services/documents.py` 的 `parse_pdf`（当前 line 10-16）从：

```python
def parse_pdf(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{path}")
    with pymupdf.open(p) as doc:
        parts = [page.get_text("text") for page in doc]    
    return "\n".join(parts)
```

改为：

```python
def parse_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流提取纯文本（不读文件、不落盘）。"""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text("text") for page in doc)
```

`Path` 导入（line 2）保留——其他函数可能用。若改完确认无其他引用，删 `from pathlib import Path`。

- [ ] **Step 2: 更新 test_parse_pdf_return_string**

`backend/test/test_documents.py` 的 `test_parse_pdf_return_string`（当前 line 4-7）改为传 bytes：

```python
def test_parse_pdf_return_string():
    from pathlib import Path
    pdf_path = r"D:\Python\Common\Agentic Search\任务文档\TiMem Temporal-Hierarchical Memory Consolidation for Long-Horizon Conversational Agents.pdf"
    result = parse_pdf(Path(pdf_path).read_bytes())
    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 3: 替换 test_parse_pdf_file_not_found**

把 `test_parse_pdf_file_not_found`（当前 line 9-11）——

```python
def test_parse_pdf_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_pdf("nonexistent_file.pdf")
```

替换为：

```python
def test_parse_pdf_empty_bytes_raises():
    """空字节流应被 pymupdf 拒绝。"""
    import pymupdf
    with pytest.raises(pymupdf.EmptyFileError):
        parse_pdf(b"")
```

- [ ] **Step 4: 运行测试验证**

Run: `cd backend && uv run pytest test/test_documents.py -v`
Expected: 全部 PASSED（含新的 `test_parse_pdf_empty_bytes_raises`）。若 `Path` 导入相关报错，按 Step 1 备注处理。

- [ ] **Step 5: Commit**

```bash
cd backend
git add src/agentic_search/services/documents.py test/test_documents.py
git commit -m "refactor: parse_pdf 改收 bytes（pymupdf stream=），删临时文件契约"
```

---

### Task 2: routes.py 清理死导入

**Files:**
- Modify: `backend/src/agentic_search/api/routes.py:2-3`

**Interfaces:**
- Consumes: Task 1 的 `parse_pdf(pdf_bytes)`
- 无新增产出

- [ ] **Step 1: 删死导入**

`backend/src/agentic_search/api/routes.py` 当前 line 2-3：

```python
import os
import tempfile
```

这两个导入在当前代码里无任何使用（ingest 端点尚未实现，query 端点不用它们）。整行删除 line 2 和 line 3。

保留 `from pathlib import Path`（line 4）——文档里的 ingest 端点用 `Path(file.filename).stem`，未来实现需要。

- [ ] **Step 2: 验证导入干净**

Run: `cd backend && uv run python -c "from agentic_search.api.routes import router; print('OK')"`
Expected: 输出 `OK`，无 ImportError。

- [ ] **Step 3: Commit**

```bash
cd backend
git add src/agentic_search/api/routes.py
git commit -m "chore: 删 routes.py 死导入 os/tempfile"
```

---

### Task 3: 02 文档 8.2 节整段重写（对比式教学）

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md:558-590`（8.2 节：代码块 + 设计说明）

**Interfaces:**
- 纯文档改动，无代码接口。遵循奶妈级教学：笨办法（完整代码 + 逐行注释）→ 点破根因 → 优化。

- [ ] **Step 1: 重写 8.2 节**

把 `任务文档/02-LangGraph-Agent.md` 的 8.2 节（当前 line 558-590）整段替换为下面的内容。保留 `### 8.2 POST /api/ingest（上传 PDF）` 标题与 `### 8.3` 之间的边界。

```markdown
### 8.2 POST /api/ingest（上传 PDF）

这个端点接收用户上传的 PDF，把里面的文字"抠"出来，存进 MongoDB。看起来简单，但藏着一个值得深究的设计问题——我们先看最直觉的写法，再看它为什么啰嗦、以及怎么把它塌缩掉。

#### 笨办法：临时文件（先理解，不必写进项目）

上传的文件经 `await file.read()` 读进内存，得到一串字节流（`bytes`）。而模块 1 的 `parse_pdf` 收的是**文件路径**，不是字节流——

```python
def parse_pdf(path: str | Path) -> str:   # ← 模块 1 的契约：收路径
    with pymupdf.open(p) as doc:
        ...
```

手里是字节，要的是路径——错位出现了。最直觉的解法：把字节先写成一个临时文件，拿到路径喂给 `parse_pdf`，用完再删：

```python
@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    pdf_bytes = await file.read()                         # ① 读字节到内存

    # ② 把字节写成临时文件，纯粹是为了给 parse_pdf 一个"路径"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name                               # 拿到临时文件路径
    try:
        text = parse_pdf(tmp_path)                        # ③ 喂路径给 parse_pdf
    finally:
        os.unlink(tmp_path)                               # ④ 用完即删

    doc_id = Path(file.filename).stem
    store_document(doc_id, file.filename, text)
    return IngestResponse(doc_id=doc_id, filename=file.filename)
```

逐行看为什么每步都"必要"：

- `tempfile.NamedTemporaryFile(...)`：操作系统在临时目录建一个唯一名字的文件，返回路径。`suffix=".pdf"` 让扩展名是 `.pdf`（有些库靠扩展名判格式）。
- `delete=False`：默认 `delete=True` 会在 `with` 块结束时自动删文件——但我们要在 `with` 块**外面**用它，所以必须关掉自动删除。
- `try / finally`：`finally` 块**无论成功还是抛异常都一定执行**，保证临时文件绝不会泄漏。即使 `parse_pdf` 崩溃，`os.unlink` 也会删掉临时文件。
- `os.unlink(tmp_path)`：手动删除临时文件（因为关掉了自动删除）。

四步、12 行，只为完成"字节 → 文本"。功能正确，但啰嗦——而且它把一个错误的前提当成了理所当然。

#### 点破根因：问题不在 pymupdf

上面这套临时文件的绕路，建立在一个注释上：

```python
# ② pymupdf 的 open() 需要文件路径：写入临时文件   ← 这句话是错的
```

**pymupdf 的 `open()` 从来就不"需要"文件路径。** 它的签名是：

```python
pymupdf.open(filename=None, stream=None, filetype=None, ...)
```

`stream=` 参数**直接吃字节流**——传 `pymupdf.open(stream=pdf_bytes, filetype="pdf")` 就能解析内存里的字节，不需要任何文件路径。`stream=` 一直都在。

那临时文件那 12 行是为啥？**根因是 `parse_pdf` 的契约收路径**。手里是字节，`parse_pdf` 要路径，错位逼出了临时文件。改契约，错位消失，12 行全消失。

#### 优化：parse_pdf 改收字节

回到 `services/documents.py`，把模块 1 的 `parse_pdf` 从"收路径"改为"收字节"：

```python
def parse_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流提取纯文本（不读文件、不落盘）。"""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text("text") for page in doc)
```

变化只有两处：入参 `path` → `pdf_bytes`；内部 `pymupdf.open(p)` → `pymupdf.open(stream=pdf_bytes, filetype="pdf")`。原来那三行 `Path` / `exists` / `FileNotFoundError` 全删——文件不存在的语义交给调用方的 `read_bytes()` 自然抛 `FileNotFoundError`。

> **关于错误处理**：`parse_pdf` 不再手动检查"文件存在"，但 pymupdf 自己会拒绝非法输入——空字节抛 `pymupdf.EmptyFileError`，损坏字节抛 `pymupdf.FileDataError`。不需要我们再加一层校验，简单优先。
>
> **同步更新模块 1 的测试**：`parse_pdf` 改了契约，`test_documents.py` 里两条测试要跟着改——`test_parse_pdf_return_string` 调用改为传 `Path(path).read_bytes()`；`test_parse_pdf_file_not_found` 换成 `test_parse_pdf_empty_bytes_raises`，断言 `pymupdf.EmptyFileError`。

#### 优化后的 ingest：12 行 → 4 行

契约改完，ingest 端点塌缩成：

```python
@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """上传 PDF，提取纯文本并存入 MongoDB（零文件系统依赖）。"""
    pdf_bytes = await file.read()             # ① 读字节
    text = parse_pdf(pdf_bytes)               # ② 直接喂字节，无临时文件
    doc_id = Path(file.filename).stem         # ③ 派生 doc_id
    store_document(doc_id, file.filename, text)  # ④ 存 MongoDB
    return IngestResponse(doc_id=doc_id, filename=file.filename)
```

`tempfile` / `try/finally` / `os.unlink` 全部消失——没有临时文件要写，自然没有要删。这才是"零文件系统依赖"真正兑现的样子。

**设计说明——为什么 PDF 不落盘，且转换与存储分两个函数？**

- **零文件系统依赖**：PDF 字节流直接交给 `parse_pdf`（内部 `pymupdf.open(stream=...)`），全程不碰磁盘。没有 `data/raw/` 目录，没有临时文件，所有持久化数据集中在 MongoDB。
- **职责分离**：`parse_pdf` 只做「PDF → 纯文本」提取（纯函数，便于单元测试）；`store_document` 只做「写入 MongoDB documents 集合」。两者解耦后，换存储后端只需改 `store_document`，`parse_pdf` 不动。
- **doc_id 由文件名派生**：`Path(file.filename).stem` 取主文件名作为文档唯一标识，与模块 1 的 `read_document(doc_id)`、`list_documents()` 保持一致。
```

- [ ] **Step 2: 验证文档无「不使用XXX」措辞**

检查刚写入的 8.2 节是否含「不使用」「不再使用」「无需使用」等措辞。若命中，改写为正面表述（如"改收字节"而非"不使用路径"）。

- [ ] **Step 3: Commit**

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): 8.2 节改字节流——对比式教学（笨办法→根因→优化，12→4 行）"
```

---

### Task 4: 02 文档导入块清理

**Files:**
- Modify: `任务文档/02-LangGraph-Agent.md:497-499`（routes.py 代码块的导入部分）

**Interfaces:**
- 纯文档改动。与 Task 2 的代码改动对齐——文档里的 routes.py 导入块也要删 `os`/`tempfile`。

- [ ] **Step 1: 删文档导入块里的 os/tempfile**

`任务文档/02-LangGraph-Agent.md` 第 8 步开头的 routes.py 代码块（line 495-518），当前 line 497-499 是：

```python
import json
import os
import tempfile
```

删掉 `import os` 和 `import tempfile` 两行，保留 `import json` 和 `from pathlib import Path`。改完后该段是：

```python
# api/routes.py —— 教学示例：4 个 HTTP 端点
import json
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
...
```

- [ ] **Step 2: Commit**

可与 Task 3 合并提交（同一文件连续改动），或单独提交：

```bash
git add 任务文档/02-LangGraph-Agent.md
git commit -m "docs(02): routes.py 导入块删 os/tempfile（与代码同步）"
```

---

## Self-Review

**1. Spec coverage:**
- parse_pdf 新契约（bytes + stream=）→ Task 1 ✓
- ingest 临时文件删除 → Task 1 改契约即消除（代码）+ Task 3 文档展示 ✓
- 不加空字节守卫 → Task 1 实现不含守卫 ✓
- routes.py 导入清理 → Task 2（代码）+ Task 4（文档）✓
- 测试同步 → Task 1 Steps 2-3 ✓
- 8.2 节对比式教学（笨办法→根因→优化）→ Task 3 ✓
- 01 文档不回溯 → 全局约束，无 Task 触碰 01 ✓
- 奶妈级教学（完整代码 + 逐行注释）→ Task 3 含完整代码块 + 逐行解释 ✓

**2. Placeholder scan:** 无 TBD/TODO/「适当处理」。每个 Step 含完整代码 ✓

**3. Type consistency:** `parse_pdf(pdf_bytes: bytes)` 在 Task 1（定义）、Task 3（文档代码块）一致；`pymupdf.open(stream=, filetype="pdf")` 在 Task 1 + Task 3 一致；`EmptyFileError` 在 Task 1 Step 3 + Task 3 文档一致 ✓
