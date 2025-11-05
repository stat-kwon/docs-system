"""파일명 생성을 담당한다."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


@dataclass
class FilenameResult:
    filename: str
    template: str
    path: str
    full_path: str
    needs_suffix: bool
    safe_title: str
    project_folder: str | None = None
    structure_files: Dict[str, str] | None = None


class FilenameService:
    def __init__(self, docs_root: Path, config: Dict[str, Any], logger) -> None:
        self._docs_root = docs_root
        self._config = config
        self._logger = logger

    def generate(self, scenario: str, title: str, **kwargs: Any) -> FilenameResult:
        scenarios = self._config.get("scenarios", {})
        if scenario not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario}")

        rule = scenarios[scenario]
        template = rule.get("filename_template")
        if not template:
            raise ValueError(f"No filename template for scenario: {scenario}")

        safe_title = self._slugify(title)
        params: Dict[str, Any] = {"title": safe_title}

        now = kwargs.get("date") or datetime.now()
        if hasattr(now, "strftime"):
            params["date"] = now.strftime("%Y%m%d")
            params["time"] = now.strftime("%H%M")
            params["datetime"] = now.strftime("%Y%m%d-%H%M")
        else:
            params["date"] = str(now)[:10].replace("-", "")
            params["time"] = "0000"
            params["datetime"] = f"{params['date']}-0000"

        if rule.get("needs_suffix"):
            params["suffix"] = self._find_next_suffix(scenario, params["date"], safe_title, template)

        if scenario == "project":
            project_name = safe_title
            params["project_name"] = project_name
            filename = template.format(**params)
            path_template = rule.get("path", "")
            path = path_template.format(project_name=project_name)
            full_path = self._docs_root / path / filename
            structure = {
                key: value.format(project_name=project_name)
                for key, value in (rule.get("create_structure") or {}).items()
            } or None
            self._logger.info("Generated project structure for: %s", project_name)
            return FilenameResult(
                filename=filename,
                template=template,
                path=path,
                full_path=str(full_path),
                needs_suffix=rule.get("needs_suffix", False),
                safe_title=safe_title,
                project_folder=str(self._docs_root / path),
                structure_files=structure,
            )

        if "project_name" in kwargs:
            params["project_name"] = self._slugify(str(kwargs["project_name"]))

        path_template = rule.get("path", "")
        if "{project_name}" in path_template:
            params.setdefault("project_name", "untitled")
            path = path_template.format(project_name=params["project_name"])
        else:
            path = path_template

        filename = template.format(**params)
        full_path = self._docs_root / path / filename
        self._logger.info("Generated filename: %s at %s", filename, path)
        return FilenameResult(
            filename=filename,
            template=template,
            path=path,
            full_path=str(full_path),
            needs_suffix=rule.get("needs_suffix", False),
            safe_title=safe_title,
        )

    def _find_next_suffix(self, scenario: str, date: str, title: str, template: str) -> str:
        suffix_chars = (self._config.get("suffix") or {}).get("chars", "abcdefghij")
        rule = self._config["scenarios"][scenario]
        path = self._docs_root / rule.get("path", "")
        if not path.exists():
            self._logger.debug("Path does not exist, using suffix 'a': %s", path)
            return "a"

        for suffix in suffix_chars:
            params = {"date": date, "title": title, "suffix": suffix}
            try:
                candidate = template.format(**params)
            except KeyError:
                candidate = f"개념-{date}{suffix}-{title}.md"
            if not (path / candidate).exists():
                self._logger.debug("Found available suffix: %s", suffix)
                return suffix

        self._logger.warning("All suffixes used for %s-%s, using 'z'", date, title)
        return "z"

    @staticmethod
    def _slugify(text: str) -> str:
        normalised = unicodedata.normalize("NFKC", text)
        normalised = re.sub(r"\s+", "-", normalised)
        normalised = re.sub(r"[^\w\-가-힣ㄱ-ㅎㅏ-ㅣ]", "", normalised)
        normalised = re.sub(r"-+", "-", normalised).strip("-")
        return normalised or "untitled"
