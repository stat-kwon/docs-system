"""워크플로우 조정자."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Tuple

from .config_loader import ConfigBundle
from .context_budget import summarize
from .filename_service import FilenameResult, FilenameService
from .spec_loader import LoadedBundle, SpecLoader
from .template_service import TemplateInfo, TemplateService


@dataclass
class WorkflowResult:
    scenario: str
    specs: Dict[str, Any]
    template: TemplateInfo | None
    filename: FilenameResult | None
    auto_execute: bool
    validation_rules: list
    validator_specs: list
    context_lines: Dict[str, Any]
    timestamp: str
    read_only: bool | None


class WorkflowService:
    def __init__(
        self,
        config: ConfigBundle,
        spec_loader: SpecLoader,
        filename_service: FilenameService,
        template_service: TemplateService,
        logger,
    ) -> None:
        self._config = config
        self._spec_loader = spec_loader
        self._filename_service = filename_service
        self._template_service = template_service
        self._logger = logger

    def run(self, scenario: str, title: str | None = None, **kwargs: Any) -> WorkflowResult:
        scenario_key, scenario_config = self._resolve_scenario(scenario)

        spec_bundle = self._spec_loader.load(scenario_config.get("spec_files"))
        validator_bundle = self._spec_loader.load(scenario_config.get("validator_specs"))
        context_lines = summarize(spec_bundle, validator_bundle, self._config.context_target)

        specs_payload = {
            "scenario": scenario_key,
            "spec_files": spec_bundle.files,
            "spec_details": spec_bundle.details,
            "validator_files": validator_bundle.files,
            "validator_details": validator_bundle.details,
            "spec_content": spec_bundle.content,
            "validator_content": validator_bundle.content,
        }

        template_info = self._template_service.describe(scenario_config.get("template"))

        filename_info = None
        if title:
            filename_info = self._filename_service.generate(scenario_key, title, **kwargs)

        timestamp = datetime.now().isoformat()
        self._logger.info(
            "Workflow prepared for %s (spec lines: %s, validator lines: %s)",
            scenario_key,
            context_lines["specs"],
            context_lines["validators"],
        )

        return WorkflowResult(
            scenario=scenario_key,
            specs={**specs_payload, "context_lines": context_lines},
            template=template_info,
            filename=filename_info,
            auto_execute=scenario_config.get("auto_execute", False),
            validation_rules=scenario_config.get("validation", []),
            validator_specs=validator_bundle.files,
            context_lines=context_lines,
            timestamp=timestamp,
            read_only=scenario_config.get("read_only"),
        )

    def _resolve_scenario(self, scenario: str) -> Tuple[str, Dict[str, Any]]:
        scenarios = self._config.raw.get("scenarios", {})
        if scenario in scenarios:
            return scenario, scenarios[scenario]

        default = next(
            (
                (name, cfg)
                for name, cfg in scenarios.items()
                if isinstance(cfg, dict) and cfg.get("is_default")
            ),
            None,
        )
        if default:
            self._logger.warning("Unknown scenario '%s', falling back to '%s'", scenario, default[0])
            return default

        raise ValueError(f"Unknown scenario: {scenario}")
