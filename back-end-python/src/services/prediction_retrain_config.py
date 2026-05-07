# -*- coding: utf-8 -*-
"""Prediction retraining switches loaded from the project .env file."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is optional at import time
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"

if load_dotenv and DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH, override=False)


def parse_env_bool(name: str, default: bool = True) -> bool:
    """Parse boolean .env values, accepting the common typo 'flase' as false."""
    raw = os.getenv(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "flase", "no", "n", "off"}:
        return False
    return default


AIR_COMBINATION_RETRAIN_AFTER_14_DAYS = parse_env_bool(
    "AIR_COMBINATION_RETRAIN_AFTER_14_DAYS",
    default=True,
)
WATER_COMBINATION_RETRAIN_AFTER_14_DAYS = parse_env_bool(
    "WATER_COMBINATION_RETRAIN_AFTER_14_DAYS",
    default=True,
)
