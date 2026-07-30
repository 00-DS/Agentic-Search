## Task 2: `01-Python文档工具.md` — parse_pdf spec 与测试

**Files:**
- Modify: `任务文档/01-Python文档工具.md`（§3.1、§3.2 注释、§4.1、§步骤5）

- [ ] **Step 1: 整段重写 §3.1 `parse_pdf(pdf_path)`（约第 340-425 行，到 `### 3.2` 前）**

替换为：

````markdown
### 3.1 `parse_pdf(pdf_path)`

**功能定义**：

```python
def parse_pdf(pdf_path: str | Path) -> str:
    """读取 PDF 文件，使用 pymupdf 提取纯文本（图片等非文字内容丢弃）。"""
```

输入：PDF 文件路径（如 `"paper.pdf"`，可放在 `backend/` 下任意位置）。输出：提取后的纯文本，页与页之间用空行拼接。

**pymupdf 基础用法**（官方文档：https://pymupdf.readthedocs.io/）。核心是「打开文档 → 逐页取文字」：

```python
import pymupdf

doc = pymupdf.open("example.pdf")   # 打开文档
parts = []
for page in doc:                    # 逐页迭代
    parts.append(page.get_text())   # get_text() 默认只返回文字
text = "\n".join(parts)             # 页间空行拼接
```

关键概念：`pymupdf.open(path)` 打开 PDF（返回 Document 对象）；`for page in doc` 遍历每一页；`page.get_text()` 提取该页**文字**（默认不输出图片、矢量图等非文字内容，"丢弃"天然成立）；`"\n".join(...)` 把各页文字用空行拼成一段连续文本。

> 现代导入写 `import pymupdf`（pymupdf ≥1.23.8 的官方推荐别名）。旧代码里的 `import fitz` 仍可用，但官方文档统一用 `import pymupdf`，本项目也用这个。

**转换效果**。假设 PDF 中有：

```
1 Introduction
Transformers have revolutionized NLP...
```

pymupdf 提取后得到的是**纯文本**（无 `#` 标题标记、无 Markdown 表格重建）：

```
1 Introduction

Transformers have revolutionized NLP...
```

文字内容原样保留，但文档的**逻辑结构标记**（标题层级、表格格式、公式）不复存在。对本项目而言这足够——全文交给 LLM 做语义理解，模型能从文字本身读出章节含义。

**你需要实现的逻辑**：检查文件是否存在 → 打开 PDF → 逐页提取文字 → 关闭文档 → 返回拼接结果。以下是**教学示例，展示核心逻辑，非完整实现**：

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

讲解要点：

- **无需缓存 converter**：marker-pdf 之类工具初始化要加载模型、开销大，需用模块级缓存；pymupdf 的 `open()` 是轻量操作，每次调用即可，无需缓存层。
- **错误处理**：路径不存在时抛出 `FileNotFoundError` 并附上具体路径，便于排查。调用方（[模块 3](./03-LangGraph-Agent.md) 的 API 层）可以捕获此异常并向用户返回友好提示。
- **图片等非文字内容**：`get_text()` 默认不输出，无需额外处理即满足"只留文字"的要求。

**测试你的函数**：准备任意一个 PDF 文件，放在 `backend/` 下：

```bash
uv run python -c "from agentic_search.services.documents import parse_pdf; print(parse_pdf('你的文件.pdf')[:200])"
```

**验证**：输出 PDF 提取后的纯文本前 200 个字符，而非报错。注意输出是连续纯文本，不含 `#` 标题标记。
````

- [ ] **Step 2: 改 store_document 示例注释（第 454 行附近）**

原文：`            "markdown": markdown,                   # marker-pdf 转出的完整 Markdown 全文`
改为：`            "markdown": markdown,                   # pymupdf 提取的完整纯文本全文`

- [ ] **Step 3: 重写 §4.1 测试（约第 551-579 行，`#### 4.1` 到 `#### 4.2` 前）**

替换为：

````markdown
#### 4.1 测试 `parse_pdf`

`parse_pdf` 是纯提取函数（输入文件路径、输出纯文本字符串），不依赖 MongoDB，测试最直接：

```python
from agentic_search.services.documents import parse_pdf
import pytest


def test_parse_pdf_returns_string():
    """parse_pdf 应返回字符串。"""
    result = parse_pdf("test_sample.pdf")
    assert isinstance(result, str)
    assert len(result) > 0  # 不应为空


def test_parse_pdf_file_not_found():
    """传入不存在的路径应抛出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        parse_pdf("nonexistent_file.pdf")
```

> 你需要准备一个测试用 PDF（放在 `backend/` 目录下，命名为 `test_sample.pdf`）。可创建一个简单文本文档导出为 PDF，或使用任何已有论文 PDF。`parse_pdf` 不依赖 MongoDB，故可独立测试。

注意：提取结果是纯文本，不再断言含 `#` 之类结构标记——pymupdf 输出不含这些。
````

- [ ] **Step 4: 改 §步骤5 集成验证示例（第 647-648 行）**

原文：
```
# 1. 将一个 PDF 转换为 Markdown
markdown = parse_pdf('你的文件.pdf')
print(f'转换完成，Markdown 长度: {len(markdown)} 字符')
```
改为：
```
# 1. 将一个 PDF 提取为纯文本
markdown = parse_pdf('你的文件.pdf')
print(f'提取完成，文本长度: {len(markdown)} 字符')
```

- [ ] **Step 5: Commit**

```bash
cd "D:/Python/Common/Agentic Search"
git add 任务文档/01-Python文档工具.md
git commit -m "docs(01): rewrite parse_pdf spec and tests for pymupdf"
```

---
