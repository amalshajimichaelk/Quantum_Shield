"""Execution and transpilation of the quantum order-finding circuit."""
from __future__ import annotations

import time
from typing import Any
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def execute_order_finding(
    circuit: QuantumCircuit,
    shots: int = 1024,
    backend_name: str = "aer_simulator",
    optimization_level: int = 1,
) -> dict[str, Any]:
    """Transpile and execute the Shor order-finding circuit on the AerSimulator.
    
    Returns execution metadata, measurement counts, gate statistics, and runtime metrics.
    """
    simulator = AerSimulator()

    t_start = time.perf_counter()
    transpiled_circuit = transpile(circuit, simulator, optimization_level=optimization_level)
    transpile_time_ms = (time.perf_counter() - t_start) * 1000.0

    t_exec_start = time.perf_counter()
    job = simulator.run(transpiled_circuit, shots=shots)
    result = job.result()
    execution_time_ms = (time.perf_counter() - t_exec_start) * 1000.0

    counts = result.get_counts(transpiled_circuit)

    # Circuit analytics
    original_gate_counts = dict(circuit.count_ops())
    transpiled_gate_counts = dict(transpiled_circuit.count_ops())

    return {
        "counts": counts,
        "shots": shots,
        "simulator_name": f"Qiskit Aer Simulator ({simulator.name})",
        "num_qubits": circuit.num_qubits,
        "circuit_depth": circuit.depth(),
        "transpiled_depth": transpiled_circuit.depth(),
        "original_gate_counts": original_gate_counts,
        "transpiled_gate_counts": transpiled_gate_counts,
        "total_gates": sum(original_gate_counts.values()),
        "transpiled_total_gates": sum(transpiled_gate_counts.values()),
        "transpile_time_ms": round(transpile_time_ms, 2),
        "execution_time_ms": round(execution_time_ms, 2),
        "total_time_ms": round(transpile_time_ms + execution_time_ms, 2),
        "transpiled_circuit": transpiled_circuit,
    }

