"""Shor's Factoring Algorithm implementation and orchestration for Q-SHIELD."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from quantum.circuits import build_shor_circuit
from quantum.order_finding import execute_order_finding
from quantum.postprocessing import process_measurement_counts
from quantum.quantum_utils import circuit_to_ascii, is_coprime


@dataclass
class ShorResult:
    """Structured result schema for Shor's quantum factoring execution."""

    algorithm_name: str
    target_number: int
    selected_base: int
    estimated_order: int | None
    candidate_factors: list[int]
    verified_factorization: tuple[int, int] | None
    num_qubits: int
    circuit_depth: int
    gate_count: dict[str, int]
    measurement_shots: int
    measurement_counts: dict[str, int]
    execution_time_ms: float
    simulator_name: str
    transpiled_circuit_metadata: dict[str, Any]
    success: bool
    explanation: str
    detailed_measurements: list[dict[str, Any]] = field(default_factory=list)
    circuit_ascii: str = ""


def run_shor_factorization(
    N: int = 15,
    a: int = 2,
    shots: int = 1024,
    num_counting_qubits: int = 4,
    use_elementary_gates: bool = True,
) -> ShorResult:
    """Execute Shor's factoring algorithm on the Qiskit Aer simulator.
    
    1. Validates input coprime base a and composite N.
    2. Constructs Quantum Phase Estimation circuit for modular order finding.
    3. Transpiles and simulates circuit on AerSimulator.
    4. Gathers physical circuit statistics (depth, qubits, gate counts).
    5. Applies continued fractions to measurement outcomes to recover order r.
    6. Computes gcd(a^(r/2) ± 1, N) to derive non-trivial factors.
    7. Formulates complete educational explanation and verification record.
    """
    if N != 15:
        return ShorResult(
            algorithm_name="Shor's Factoring Algorithm (Qiskit 2.x)",
            target_number=N,
            selected_base=a,
            estimated_order=None,
            candidate_factors=[],
            verified_factorization=None,
            num_qubits=0,
            circuit_depth=0,
            gate_count={},
            measurement_shots=shots,
            measurement_counts={},
            execution_time_ms=0.0,
            simulator_name="Qiskit Aer Simulator",
            transpiled_circuit_metadata={},
            success=False,
            explanation=f"Demonstration circuit supports N=15. Target integer N={N} exceeds current educational simulation bounds.",
        )

    if not is_coprime(a, N):
        return ShorResult(
            algorithm_name="Shor's Factoring Algorithm (Qiskit 2.x)",
            target_number=N,
            selected_base=a,
            estimated_order=None,
            candidate_factors=[],
            verified_factorization=None,
            num_qubits=0,
            circuit_depth=0,
            gate_count={},
            measurement_shots=shots,
            measurement_counts={},
            execution_time_ms=0.0,
            simulator_name="Qiskit Aer Simulator",
            transpiled_circuit_metadata={},
            success=False,
            explanation=f"Base a={a} is not coprime to N={N}. Shor's algorithm requires gcd(a, N) = 1.",
        )

    # 1. Build circuit
    circuit = build_shor_circuit(
        N=N,
        a=a,
        num_counting_qubits=num_counting_qubits,
        use_elementary_gates=use_elementary_gates,
    )
    circuit_ascii = circuit_to_ascii(circuit)

    # 2. Transpile and execute on Aer
    exec_data = execute_order_finding(
        circuit=circuit,
        shots=shots,
        backend_name="aer_simulator",
    )

    # 3. Classical post-processing
    counts = exec_data["counts"]
    best_order, verified_factors, detailed = process_measurement_counts(
        counts=counts,
        num_counting_qubits=num_counting_qubits,
        a=a,
        N=N,
    )

    success = verified_factors is not None and (verified_factors[0] * verified_factors[1] == N)
    candidate_factors_all = []
    for d in detailed:
        for f in d.get("candidate_factors", []):
            if f not in candidate_factors_all:
                candidate_factors_all.append(f)

    if success and verified_factors is not None:
        p, q = verified_factors
        explanation = (
            f"Quantum order finding successfully estimated order r={best_order} for {a}^x ≡ 1 (mod {N}). "
            f"Because r is even ({best_order}), the semi-classical split a^(r/2) = {a}^{best_order//2} = {pow(a, best_order//2)} "
            f"yielded gcd({pow(a, best_order//2)} - 1, {N}) = {p} and gcd({pow(a, best_order//2)} + 1, {N}) = {q}. "
            f"Verified factorization: {p} × {q} = {N}."
        )
    else:
        explanation = (
            f"Simulation executed {shots} shots across {circuit.num_qubits} qubits. "
            f"Measurement counts did not isolate an even non-trivial order yielding non-trivial factors. "
            f"Quantum phase estimation is probabilistic; retrying or increasing shots is recommended."
        )

    return ShorResult(
        algorithm_name="Shor's Factoring Algorithm (Qiskit 2.x)",
        target_number=N,
        selected_base=a,
        estimated_order=best_order,
        candidate_factors=sorted(candidate_factors_all),
        verified_factorization=verified_factors,
        num_qubits=exec_data["num_qubits"],
        circuit_depth=exec_data["circuit_depth"],
        gate_count=exec_data["original_gate_counts"],
        measurement_shots=shots,
        measurement_counts=counts,
        execution_time_ms=exec_data["execution_time_ms"],
        simulator_name=exec_data["simulator_name"],
        transpiled_circuit_metadata={
            "transpiled_depth": exec_data["transpiled_depth"],
            "transpiled_gate_counts": exec_data["transpiled_gate_counts"],
            "transpiled_total_gates": exec_data["transpiled_total_gates"],
            "transpile_time_ms": exec_data["transpile_time_ms"],
            "total_time_ms": exec_data["total_time_ms"],
        },
        success=success,
        explanation=explanation,
        detailed_measurements=detailed,
        circuit_ascii=circuit_ascii,
    )

