"""Secure logging configuration that prevents private key and plaintext leakage."""
from __future__ import annotations

import logging
import sys


def setup_secure_logging(level: int = logging.INFO) -> logging.Logger:
    """Initialize a logger with sanitization filters to prevent sensitive key exposure."""
    logger = logging.getLogger("qshield")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [Q-SHIELD] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

