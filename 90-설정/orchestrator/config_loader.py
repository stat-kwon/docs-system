"""규칙 파일을 로드하고 보조 정보를 계산한다."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import os
import yaml


@dataclass(frozen=True)
class ConfigBundle:
    raw: Dict[str, Any]
    docs_root: Path
    context_target: int


class ConfigLoader:
    """rules.yaml을 로드하고 파생 설정을 계산한다."""

    def __init__(self, logger) -> None:
        self._logger = logger

    def load(self, config_path: Path) -> ConfigBundle:
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream) or {}
        self._logger.info("Configuration loaded from %s", config_path)

        context_cfg = data.get("context", {}) if isinstance(data, dict) else {}
        target = context_cfg.get("target_total_lines", 270)

        docs_root = self._resolve_docs_root(config_path.parent, data)
        return ConfigBundle(raw=data, docs_root=docs_root, context_target=target)

    def _resolve_docs_root(self, base_dir: Path, data: Dict[str, Any]) -> Path:
        env_root = os.environ.get("DOCS_HOME")
        if env_root:
            docs_root = Path(env_root)
            self._logger.info("Using DOCS_HOME from environment: %s", docs_root)
        else:
            docs_cfg = data.get("docs_root")
            if docs_cfg:
                docs_root = Path(docs_cfg)
                self._logger.info("Using docs_root from config: %s", docs_root)
            else:
                docs_root = base_dir.parent
                self._logger.info("Using fallback docs_root: %s", docs_root)

        if not docs_root.exists():
            self._logger.warning("docs_root does not exist: %s", docs_root)
        return docs_root
