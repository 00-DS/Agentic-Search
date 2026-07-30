from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

_converter = None

def _get_covnerter() -> PdfConverter:
    global _converter
    if _converter is None:
        _converter = PdfConverter(
            artifact_dict=create_model_dict()
        )
    return _converter

def parse_pdf(pdf_path: str | Path) -> str:
    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在：{pdf_path}")
    converter = _get_covnerter()
    rendered = converter(str(p))
    return rendered.markdown
