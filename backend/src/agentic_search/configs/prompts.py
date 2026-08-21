from pathlib import Path

import yaml

PROMPTS: dict[str, str] = yaml.safe_load(
    Path(__file__).with_name("prompts.yaml").read_text(encoding="utf-8")
)
