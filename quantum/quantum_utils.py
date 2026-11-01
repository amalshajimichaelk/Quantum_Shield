"""Quantum arithmetic and circuit utility functions for Q-SHIELD Quantum Threat Lab."""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def is_coprime(a: int, N: int) -> bool:
    """Return True if gcd(a, N) == 1 and 1 < a < N."""
    return 1 < a < N and math.gcd(a, N) == 1


def classical_order(a: int, N: int) -> int | None:
    """Compute the classical multiplicative order r such that a^r = 1 mod N."""
    if not is_coprime(a, N):
        return None
    r = 1
    val = a % N
    while val != 1:
        val = (val * a) % N
        r += 1
        if r > N * 2:
            return None
    return r


def continued_fraction_order(phase: float, N: int) -> tuple[Fraction, int]:
    """Convert a phase estimate theta in [0, 1) to a fraction s/r using continued fractions.
    
    Returns (Fraction(s, r), r).
    """
    frac = Fraction(phase).limit_denominator(N)
    return frac, frac.denominator


def get_available_backends() -> list[dict[str, Any]]:
    """Return list of available local simulation backends."""
    backends = []
    try:
        aer = AerSimulator()
        backends.append({
            "name": "aer_simulator",
            "display_name": "Qiskit Aer Simulator (Local High-Performance)",
            "type": "Simulator",
            "num_qubits": 32,
            "status": "Available",
            "description": "High-performance C++ simulator with Clifford and matrix product support",
        })
    except Exception as exc:
        backends.append({
            "name": "aer_simulator",
            "display_name": "Aer Simulator (Unavailable)",
            "type": "Simulator",
            "num_qubits": 0,
            "status": f"Error: {exc}",
            "description": "Failed to initialize Aer backend",
        })
    return backends


def circuit_to_ascii(circuit: QuantumCircuit, max_width: int = 120) -> str:
    """Render a clean text/ASCII representation of the QuantumCircuit."""
    try:
        return circuit.draw(output="text", max_width=max_width)
    except Exception as e:
        return f"Circuit text drawing unavailable: {e}"

