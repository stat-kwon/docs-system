"""첨부파일 처리 로직."""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AttachmentAnalysis:
    attachments_found: int
    attachments: List[str]
    suggestions: List[Dict[str, Any]]
    commands: Dict[str, Any] | None
    updated_links: Dict[str, str] | None


class AttachmentService:
    def __init__(self, docs_root: Path, config: Dict[str, Any], logger) -> None:
        self._docs_root = docs_root
        self._config = config
        self._logger = logger

    def analyze(self, content: str) -> AttachmentAnalysis:
        attach_cfg = self._config.get("attachments", {})
        base_path = attach_cfg.get("base_path", "80-보관/첨부파일")
        date_format = attach_cfg.get("date_format", "%Y%m%d")

        today = datetime.now().strftime(date_format)
        attach_dir = self._docs_root / base_path / today

        patterns = [
            r"!\[([^\]]*)\]\(([^)]+)\)",
            r"!\[\[([^\]]+)\]\]",
            r"<img[^>]+src=[\"\']([^\"\'\']+)[\"\']",
        ]

        attachments: List[str] = []
        suggestions: List[Dict[str, Any]] = []

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                file_path = match[1] if isinstance(match, tuple) and len(match) == 2 else match
                if not isinstance(file_path, str):
                    continue
                if not any(
                    file_path.lower().endswith(ext)
                    for ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
                ):
                    continue

                attachments.append(file_path)
                if file_path.startswith(("http://", "https://", "/")):
                    continue

                filename = Path(file_path).name
                new_path = f"../../{base_path}/{today}/{filename}"
                suggestions.append(
                    {
                        "original": file_path,
                        "suggested": new_path,
                        "full_path": str(attach_dir / filename),
                    }
                )

        commands = None
        updated_links = None
        if suggestions:
            commands = {
                "create_dir": f"mkdir -p {attach_dir}",
                "move_files": [f"mv '{s['original']}' '{s['full_path']}'" for s in suggestions],
            }
            updated_links = {s["original"]: s["suggested"] for s in suggestions}

        return AttachmentAnalysis(
            attachments_found=len(attachments),
            attachments=attachments,
            suggestions=suggestions,
            commands=commands,
            updated_links=updated_links,
        )

    def execute(self, filepath: str, dry_run: bool = False) -> Dict[str, Any]:
        file_path = Path(filepath)
        if not file_path.exists():
            return {"error": f"File not found: {filepath}"}

        content = file_path.read_text(encoding="utf-8")
        analysis = self.analyze(content)
        if analysis.attachments_found == 0:
            return {
                "success": True,
                "message": "No attachments found in the file",
                "attachments_found": 0,
            }

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "attachments_found": analysis.attachments_found,
                "analysis": analysis.__dict__,
            }

        executed: List[str] = []
        failed: List[str] = []

        if analysis.suggestions:
            target_dir = Path(analysis.suggestions[0]["full_path"]).parent
            target_dir.mkdir(parents=True, exist_ok=True)
            executed.append(f"Created directory: {target_dir}")
            self._logger.info("Created directory: %s", target_dir)

        for suggestion in analysis.suggestions:
            original = Path(suggestion["original"])
            target = Path(suggestion["full_path"])
            if not original.exists():
                failed.append(f"File not found: {original}")
                continue

            try:
                shutil.move(str(original), str(target))
                executed.append(f"Moved: {original} -> {target}")
                self._logger.info("Moved file: %s -> %s", original, target)
            except Exception as exc:  # pragma: no cover
                failed.append(f"Failed to move {original}: {exc}")
                self._logger.error("Failed to move %s: %s", original, exc)

        if analysis.updated_links:
            updated_content = content
            for original, replacement in analysis.updated_links.items():
                updated_content = updated_content.replace(original, replacement)
            file_path.write_text(updated_content, encoding="utf-8")
            executed.append(f"Updated links in {filepath}")
            self._logger.info("Updated links in %s", filepath)

        return {
            "success": not failed,
            "executed": executed,
            "failed": failed,
            "attachments_found": analysis.attachments_found,
        }
