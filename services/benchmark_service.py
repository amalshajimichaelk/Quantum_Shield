"""Benchmark execution and metric consolidation service."""
from __future__ import annotations

from typing import Any
import pandas as pd
import bench


def execute_benchmarks(iterations: int = 50) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run full benchmark suite and return timings, sizes, and machine metadata."""
    timings = bench.run_timings(iterations=iterations)
    sizes = bench.measure_sizes()
    metadata = bench.get_system_metadata(iterations=iterations)
    return timings, sizes, metadata

