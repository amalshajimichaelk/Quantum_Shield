"""Q-SHIELD Quantum Computing Engine: Shor's Factoring Algorithm using Qiskit 2.x and AerSimulator."""
from quantum.circuits import build_inverse_qft, build_shor_circuit
from quantum.order_finding import execute_order_finding
from quantum.postprocessing import process_measurement_counts
from quantum.quantum_utils import circuit_to_ascii, classical_order, continued_fraction_order, is_coprime
from quantum.shor import ShorResult, run_shor_factorization

__all__ = [
    "ShorResult",
    "run_shor_factorization",
    "build_shor_circuit",
    "build_inverse_qft",
    "execute_order_finding",
    "process_measurement_counts",
    "circuit_to_ascii",
    "classical_order",
    "continued_fraction_order",
    "is_coprime",
]

