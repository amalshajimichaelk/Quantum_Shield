import math
import os
import sys
from fractions import Fraction
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import quantum as qm


# ------------------------------------------------ Deterministic Mathematical Tests
def test_coprime_validation():
    assert qm.is_coprime(2, 15) is True
    assert qm.is_coprime(7, 15) is True
    assert qm.is_coprime(8, 15) is True
    assert qm.is_coprime(11, 15) is True
    assert qm.is_coprime(13, 15) is True

    # Non-coprimes
    assert qm.is_coprime(3, 15) is False
    assert qm.is_coprime(5, 15) is False
    assert qm.is_coprime(15, 15) is False
    assert qm.is_coprime(1, 15) is False


def test_classical_order_finding():
    # 2^4 = 16 = 1 mod 15
    assert qm.classical_order(2, 15) == 4
    # 7^4 = 2401 = 1 mod 15
    assert qm.classical_order(7, 15) == 4
    # 8^4 = 4096 = 1 mod 15
    assert qm.classical_order(8, 15) == 4
    # 11^2 = 121 = 1 mod 15
    assert qm.classical_order(11, 15) == 2
    # 13^4 = 28561 = 1 mod 15
    assert qm.classical_order(13, 15) == 4


def test_continued_fraction_recovery():
    # Phase 0.25 -> 1/4, r=4
    frac, r = qm.continued_fraction_order(0.25, 15)
    assert frac == Fraction(1, 4) and r == 4

    # Phase 0.75 -> 3/4, r=4
    frac, r = qm.continued_fraction_order(0.75, 15)
    assert frac == Fraction(3, 4) and r == 4

    # Phase 0.50 -> 1/2, r=2
    frac, r = qm.continued_fraction_order(0.50, 15)
    assert frac == Fraction(1, 2) and r == 2


def test_postprocessing_with_mock_counts():
    # Ideal probability distribution for N=15, a=2 (phases 0, 1/4, 1/2, 3/4)
    # Binary representation of 4 counting qubits:
    # 0 = 0000, 4 = 0100, 8 = 1000, 12 = 1100
    mock_counts = {"0000": 250, "0100": 250, "1000": 250, "1100": 250}
    best_order, factors, detailed = qm.process_measurement_counts(
        mock_counts, num_counting_qubits=4, a=2, N=15
    )
    assert best_order in (2, 4)
    assert factors == (3, 5)
    assert factors[0] * factors[1] == 15


# ------------------------------------------------ Quantum Circuit Structural Tests
def test_circuit_qubits_and_registers():
    # 4 counting qubits + 4 work qubits = 8 qubits
    circ = qm.build_shor_circuit(N=15, a=2, num_counting_qubits=4)
    assert circ.num_qubits == 8
    assert circ.num_clbits == 4
    assert circ.depth() > 0

    # Ensure measurements are placed
    ops = [instr.operation.name for instr in circ.data]
    assert "measure" in ops
    assert "h" in ops


def test_invalid_parameters_raise():
    with pytest.raises(ValueError, match="supports N=15"):
        qm.build_shor_circuit(N=21, a=2)

    with pytest.raises(ValueError, match="coprime"):
        qm.build_shor_circuit(N=15, a=3)


# ------------------------------------------------ Qiskit Aer Simulator Integration Tests
def test_shor_aer_simulator_execution():
    result = qm.run_shor_factorization(N=15, a=2, shots=1024, num_counting_qubits=4)

    assert result.algorithm_name.startswith("Shor's Factoring")
    assert result.target_number == 15
    assert result.selected_base == 2
    assert result.num_qubits == 8
    assert result.circuit_depth > 0
    assert result.measurement_shots == 1024
    assert sum(result.measurement_counts.values()) == 1024

    # Execution time must be recorded and non-negative
    assert result.execution_time_ms > 0
    assert "Aer" in result.simulator_name

    # Check factorization outcome
    assert result.success is True
    assert result.verified_factorization == (3, 5)
    assert result.verified_factorization[0] * result.verified_factorization[1] == 15
    assert 3 in result.candidate_factors
    assert 5 in result.candidate_factors


def test_shor_rejection_of_non_coprime():
    result = qm.run_shor_factorization(N=15, a=5)
    assert result.success is False
    assert result.verified_factorization is None
    assert "coprime" in result.explanation.lower()

