"""컨텍스트 사용량을 계산한다."""
from __future__ import annotations

from typing import Dict

from .spec_loader import LoadedBundle

ORIGINAL_PROMPT_LINES = 1392


def summarize(spec_bundle: LoadedBundle, validator_bundle: LoadedBundle, target: int) -> Dict[str, int]:
    spec_lines = spec_bundle.lines
    validator_lines = validator_bundle.lines
    total = spec_lines + validator_lines
    saved_percent = (
        round((ORIGINAL_PROMPT_LINES - total) * 100 / ORIGINAL_PROMPT_LINES)
        if total
        else 0
    )

    return {
        "specs": spec_lines,
        "validators": validator_lines,
        "total": total,
        "target_total": target,
        "original_lines": ORIGINAL_PROMPT_LINES,
        "saved_percent": saved_percent,
    }
