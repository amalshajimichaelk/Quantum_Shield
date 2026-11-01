"""Data structures for benchmark records and size comparisons."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkExecutionRecord:
    group: str
    operation: str
    median_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float
    p95_ms: float
    stdev_ms: float
    runs: int

