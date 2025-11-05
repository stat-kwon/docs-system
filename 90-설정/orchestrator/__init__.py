"""오케스트레이터 서비스 팩토리."""
from __future__ import annotations

from pathlib import Path

from .attachment_service import AttachmentService
from .config_loader import ConfigBundle, ConfigLoader
from .filename_service import FilenameService
from .logging_config import setup_logging
from .spec_loader import SpecLoader
from .template_service import TemplateService
from .workflow_service import WorkflowService

__all__ = [
    "AttachmentService",
    "ConfigBundle",
    "ConfigLoader",
    "FilenameService",
    "SpecLoader",
    "TemplateService",
    "WorkflowService",
    "setup_logging",
    "build_services",
]


def build_services(config_path: Path):
    logger = setup_logging("zettelkasten.orchestrator")
    loader = ConfigLoader(logger)
    bundle = loader.load(config_path)

    spec_root = bundle.docs_root / "90-설정" / "specs"
    spec_loader = SpecLoader(spec_root, logger)
    filename_service = FilenameService(bundle.docs_root, bundle.raw, logger)
    template_service = TemplateService(bundle.docs_root, logger)
    workflow = WorkflowService(bundle, spec_loader, filename_service, template_service, logger)
    attachments = AttachmentService(bundle.docs_root, bundle.raw, logger)

    return bundle, workflow, attachments, logger
