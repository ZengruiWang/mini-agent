from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_RESOURCES_DIR = Path(__file__).resolve().parent


def load_yaml(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = _PROJECT_ROOT / file_path
    with file_path.open() as f:
        return yaml.safe_load(f)


def load_system_prompt(name: str = "default") -> str:
    prompts = load_yaml(_RESOURCES_DIR / "prompts.yaml")
    return prompts["system"][name].strip()


def load_cases(path: str | Path) -> list[dict]:
    return load_yaml(path)
