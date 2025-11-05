#!/usr/bin/env python3
"""워크플로 전용 CLI."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from orchestrator import build_services


def _parse_key_values(pairs: list[str] | None) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Zettelkasten Workflow CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    workflow_parser = subparsers.add_parser("workflow", help="시나리오 워크플로우 실행")
    workflow_parser.add_argument("scenario", help="rules.yaml에 정의된 시나리오 키")
    workflow_parser.add_argument("title", nargs="?", help="파일명을 생성할 제목")
    workflow_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        help="추가 파라미터 (key=value)",
    )

    attach_parser = subparsers.add_parser(
        "process-attachments", help="첨부파일을 이동 및 링크 업데이트"
    )
    attach_parser.add_argument("filepath", help="Markdown 파일 경로")
    attach_parser.add_argument("--dry-run", action="store_true", help="실행 대신 분석만 수행")

    args = parser.parse_args()

    config_path = Path(__file__).parent / "rules.yaml"
    try:
        _bundle, workflow, attachments, _logger = build_services(config_path)
    except Exception as exc:  # pragma: no cover - 초기화 실패시 메시지
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 1

    if args.command == "workflow":
        overrides = _parse_key_values(args.overrides)
        try:
            result = workflow.run(args.scenario, args.title, **overrides)
            payload = {
                "scenario": result.scenario,
                "specs": result.specs,
                "template": asdict(result.template) if result.template else None,
                "filename": asdict(result.filename) if result.filename else None,
                "auto_execute": result.auto_execute,
                "validation_rules": result.validation_rules,
                "validator_specs": result.validator_specs,
                "context_lines": result.context_lines,
                "timestamp": result.timestamp,
                "read_only": result.read_only,
            }
        except Exception as exc:  # pragma: no cover - 런타임 실패시 메시지
            payload = {"error": str(exc)}
    elif args.command == "process-attachments":
        payload = attachments.execute(args.filepath, dry_run=args.dry_run)
    else:  # pragma: no cover - argparse가 이미 제한하지만 안전장치
        payload = {"error": f"Unknown command: {args.command}"}

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if "error" not in payload else 1


if __name__ == "__main__":  # pragma: no cover - CLI 진입점
    sys.exit(main())
