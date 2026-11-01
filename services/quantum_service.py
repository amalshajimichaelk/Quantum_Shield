"""Quantum threat service running Shor's factoring simulation."""
from __future__ import annotations

import quantum as qm
from quantum.shor import ShorResult


def run_quantum_threat_experiment(
    N: int = 15,
    a: int = 2,
    shots: int = 1024,
) -> ShorResult:
    """Execute Shor's factoring experiment on the local Aer quantum simulator."""
    return qm.run_shor_factorization(N=N, a=a, shots=shots)

