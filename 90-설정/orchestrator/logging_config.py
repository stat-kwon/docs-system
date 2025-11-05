"""로깅 설정 유틸리티."""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """환경 변수 기반의 로거를 생성한다."""
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False
    return logger
