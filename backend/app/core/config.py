"""Load config.yaml with env-var substitution for secrets."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"
_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _substitute_env(value: Any) -> Any:
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            return os.environ.get(match.group(1), "")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value


@lru_cache
def get_settings() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _substitute_env(raw)


def get_database_url() -> str:
    cfg = get_settings()["database"]
    if cfg["driver"] == "mysql":
        m = cfg["mysql"]
        return (
            f"mysql+pymysql://{m['user']}:{m['password']}"
            f"@{m['host']}:{m['port']}/{m['database']}"
        )
    path = Path(cfg["sqlite"]["path"])
    if not path.is_absolute():
        path = CONFIG_PATH.parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def get_assets_root() -> Path:
    """Resolved path for course assets (audio, PPTX, etc.)."""
    path = Path(get_settings()["storage"]["assets_root"])
    if not path.is_absolute():
        path = CONFIG_PATH.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path
