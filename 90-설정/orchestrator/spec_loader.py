"""Spec 및 Validator 번들을 로드한다."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class LoadedBundle:
    files: List[str]
    details: List[dict]
    content: str
    lines: int


class SpecLoader:
    def __init__(self, spec_root: Path, logger) -> None:
        self._spec_root = spec_root
        self._logger = logger

    def load(self, relative_paths: List[str] | None) -> LoadedBundle:
        files: List[str] = []
        details: List[dict] = []
        merged_content = []
        total_lines = 0

        for rel_path in relative_paths or []:
            spec_path = self._spec_root / rel_path
            if not spec_path.exists():
                self._logger.warning("Spec file not found: %s", rel_path)
                continue

            try:
                content = spec_path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover - 파일 읽기 실패시 경고
                self._logger.error("Failed to load spec %s: %s", rel_path, exc)
                continue

            line_count = len(content.splitlines())
            files.append(rel_path)
            details.append(
                {
                    "filename": rel_path,
                    "path": str(spec_path),
                    "lines": line_count,
                }
            )
            merged_content.append(f"\n## ===== {rel_path} =====\n\n{content}\n")
            total_lines += line_count
            self._logger.info("Loaded spec %s (%s lines)", rel_path, line_count)

        return LoadedBundle(
            files=files,
            details=details,
            content="".join(merged_content),
            lines=total_lines,
        )
