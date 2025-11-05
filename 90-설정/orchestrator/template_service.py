"""템플릿 정보를 수집한다."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TemplateInfo:
    filename: str
    path: str | None
    lines: int | None
    modified: str | None
    preview: str | None


class TemplateService:
    def __init__(self, docs_root: Path, logger) -> None:
        self._base_dir = docs_root / "90-설정"
        self._logger = logger

    def describe(self, template_file: Optional[str]) -> TemplateInfo | None:
        if not template_file:
            return None

        template_path = self._base_dir / template_file
        if not template_path.exists():
            self._logger.warning("Template not found: %s", template_file)
            return TemplateInfo(
                filename=template_file,
                path=str(template_path),
                lines=None,
                modified=None,
                preview=None,
            )

        text = template_path.read_text(encoding="utf-8")
        lines = len(text.splitlines())
        preview = "\n".join(text.splitlines()[:40])
        modified = template_path.stat().st_mtime
        return TemplateInfo(
            filename=template_file,
            path=str(template_path),
            lines=lines,
            modified=_format_timestamp(modified),
            preview=preview,
        )


def _format_timestamp(timestamp: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(timestamp).isoformat()
