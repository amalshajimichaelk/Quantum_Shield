"""Quantum circuit construction for Shor's algorithm and Quantum Phase Estimation."""
from __future__ import annotations

import math
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import UnitaryGate


def build_inverse_qft(n_qubits: int) -> QuantumCircuit:
    """Construct an inverse Quantum Fourier Transform (QFT dagger) circuit.
    
    Uses standard Hadamard and controlled-phase (CP) gates with negative angles.
    """
    qc = QuantumCircuit(n_qubits, name="IQFT")
    # Swap qubits to mirror order
    for qubit in range(n_qubits // 2):
        qc.swap(qubit, n_qubits - qubit - 1)
    # Apply controlled phase rotations and Hadamards
    for j in range(n_qubits):
        for m in range(j):
            qc.cp(-math.pi / float(2 ** (j - m)), m, j)
        qc.h(j)
    return qc


def build_cswap_mod15_gate(a: int, power: int) -> QuantumCircuit | None:
    """Construct elementary CSWAP (Fredkin) circuit for a=2 or a=8 mod 15.
    
    4 work qubits represent integers mod 15 in binary:
    |0001> = 1, |0010> = 2, |0100> = 4, |1000> = 8.
    """
    effective_power = power % 4  # Order of 2 and 8 mod 15 is 4
    if effective_power == 0:
        return None  # a^0 mod 15 is Identity (no gates)

    circ = QuantumCircuit(4, name=f"{a}^{power} mod 15")
    if a == 2:
        if effective_power == 1:
            # 1 -> 2, 2 -> 4, 4 -> 8, 8 -> 1
            circ.swap(2, 3)
            circ.swap(1, 2)
            circ.swap(0, 1)
        elif effective_power == 2:
            # 1 -> 4, 2 -> 8, 4 -> 1, 8 -> 2
            circ.swap(0, 2)
            circ.swap(1, 3)
        elif effective_power == 3:
            # 1 -> 8, 2 -> 1, 4 -> 2, 8 -> 4
            circ.swap(0, 1)
            circ.swap(1, 2)
            circ.swap(2, 3)
    elif a == 8:
        if effective_power == 1:
            circ.swap(0, 1)
            circ.swap(1, 2)
            circ.swap(2, 3)
        elif effective_power == 2:
            circ.swap(0, 2)
            circ.swap(1, 3)
        elif effective_power == 3:
            circ.swap(2, 3)
            circ.swap(1, 2)
            circ.swap(0, 1)
    else:
        return None

    return circ


def build_modular_exponentiation_unitary(a: int, power: int, N: int = 15, n_work: int = 4) -> UnitaryGate | None:
    """Generate a unitary permutation operator for x -> (a^(2^power) * x) mod N.
    
    Supports all coprime bases mod 15: a in {2, 7, 8, 11, 13}.
    """
    exp_factor = pow(a, 2 ** power, N)
    if exp_factor == 1:
        return None  # Identity

    dim = 2 ** n_work
    unitary_matrix = np.zeros((dim, dim), dtype=complex)
    for x in range(dim):
        if x < N and math.gcd(x, N) == 1:
            y = (exp_factor * x) % N
            unitary_matrix[y, x] = 1.0
        else:
            unitary_matrix[x, x] = 1.0

    return UnitaryGate(unitary_matrix, label=f"{a}^(2^{power}) mod {N}")


def build_shor_circuit(
    N: int = 15,
    a: int = 2,
    num_counting_qubits: int = 4,
    use_elementary_gates: bool = True,
) -> QuantumCircuit:
    """Build the complete Quantum Phase Estimation / Shor order-finding circuit.
    
    Parameters
    ----------
    N : int
        The composite integer to factor (default: 15).
    a : int
        A base coprime to N (default: 2; supports 2, 7, 8, 11, 13).
    num_counting_qubits : int
        Number of qubits in the counting register (default: 4).
    use_elementary_gates : bool
        If True and a in (2, 8), uses explicit CSWAP (Fredkin) decompositions;
        otherwise uses verified unitary permutation gates.
    """
    if N != 15:
        raise ValueError(f"Demonstration circuit currently supports N=15, received N={N}")
    if math.gcd(a, N) != 1 or a <= 1 or a >= N:
        raise ValueError(f"Base a={a} must be coprime to N={N} and satisfy 1 < a < {N}")

    n_work = 4
    qr_count = QuantumRegister(num_counting_qubits, name="count")
    qr_work = QuantumRegister(n_work, name="work")
    cr = ClassicalRegister(num_counting_qubits, name="meas")
    qc = QuantumCircuit(qr_count, qr_work, cr)

    # 1. Superposition on counting register
    for q in range(num_counting_qubits):
        qc.h(qr_count[q])

    # 2. Initialize work register to |1> = |0001>
    qc.x(qr_work[0])

    # 3. Controlled modular exponentiation
    for j in range(num_counting_qubits):
        if use_elementary_gates and a in (2, 8):
            power_val = 2 ** j
            mod_circ = build_cswap_mod15_gate(a, power_val)
            if mod_circ is not None:
                # Add controlled version of the subcircuit
                c_gate = mod_circ.to_gate().control(1)
                qc.append(c_gate, [qr_count[j]] + [qr_work[w] for w in range(n_work)])
        else:
            u_gate = build_modular_exponentiation_unitary(a, j, N, n_work)
            if u_gate is not None:
                c_gate = u_gate.control(1)
                qc.append(c_gate, [qr_count[j]] + [qr_work[w] for w in range(n_work)])

    # 4. Inverse Quantum Fourier Transform
    iqft = build_inverse_qft(num_counting_qubits)
    qc.append(iqft.to_gate(), [qr_count[q] for q in range(num_counting_qubits)])

    # 5. Measurement of counting register
    qc.measure(qr_count, cr)

    return qc

