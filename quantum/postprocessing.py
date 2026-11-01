"""Classical post-processing for Shor's algorithm measurement outcomes."""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any


def analyze_measurement(
    bitstring: str,
    count: int,
    total_shots: int,
    num_counting_qubits: int,
    a: int,
    N: int,
) -> dict[str, Any]:
    """Analyze an individual measured bitstring and attempt factor extraction."""
    m_int = int(bitstring, 2)
    phase = m_int / (2 ** num_counting_qubits)
    frac = Fraction(phase).limit_denominator(N)
    candidate_r = frac.denominator
    probability = count / total_shots

    order_valid = False
    candidate_factors: list[int] = []
    verified_factors: tuple[int, int] | None = None
    status_note = ""

    if m_int == 0:
        status_note = "Phase 0 (trivial measurement: yields no order information)"
    elif candidate_r <= 1:
        status_note = f"Candidate order r={candidate_r} is trivial (denominator <= 1)"
    else:
        # Check if candidate_r is a valid order
        if pow(a, candidate_r, N) == 1:
            order_valid = True
            status_note = f"Valid order: {a}^{candidate_r} ≡ 1 (mod {N})"
        else:
            # Check small multiples of candidate_r (e.g. 2*r) in case of common factor cancellation
            for mult in (2, 3):
                if pow(a, candidate_r * mult, N) == 1:
                    candidate_r = candidate_r * mult
                    order_valid = True
                    status_note = f"Valid order (recovered from multiple): {a}^{candidate_r} ≡ 1 (mod {N})"
                    break

        if order_valid:
            if candidate_r % 2 != 0:
                status_note += f" | Order r={candidate_r} is odd, cannot compute a^(r/2)"
            else:
                half_power = candidate_r // 2
                base_pow = pow(a, half_power, N)
                if (base_pow + 1) % N == 0:
                    status_note += f" | a^(r/2) ≡ -1 (mod {N}) (trivial factorization condition)"
                else:
                    f1 = math.gcd(base_pow - 1, N)
                    f2 = math.gcd(base_pow + 1, N)
                    factors = set()
                    for f in (f1, f2):
                        if 1 < f < N and N % f == 0:
                            factors.add(f)
                            factors.add(N // f)
                    if factors:
                        candidate_factors = sorted(factors)
                        p, q = candidate_factors[0], candidate_factors[-1]
                        if p * q == N and p > 1 and q > 1:
                            verified_factors = (min(p, q), max(p, q))
                            status_note += f" | Successfully factored {N} = {verified_factors[0]} × {verified_factors[1]}"
        else:
            status_note = f"Candidate r={candidate_r} does not satisfy {a}^r ≡ 1 (mod {N})"

    return {
        "bitstring": bitstring,
        "integer_value": m_int,
        "count": count,
        "probability": round(probability, 4),
        "phase": round(phase, 4),
        "fraction": str(frac),
        "candidate_r": candidate_r,
        "order_valid": order_valid,
        "candidate_factors": candidate_factors,
        "verified_factors": verified_factors,
        "status_note": status_note,
    }


def process_measurement_counts(
    counts: dict[str, int],
    num_counting_qubits: int,
    a: int,
    N: int,
) -> tuple[int | None, tuple[int, int] | None, list[dict[str, Any]]]:
    """Process all measurement outcomes, extract candidate orders, and determine verified factors.
    
    Returns:
    - best_order: The most reliable non-trivial order r recovered, or None.
    - final_factors: (p, q) such that p * q == N with p, q > 1, or None.
    - detailed_breakdown: List of parsed measurement records sorted by measurement frequency.
    """
    total_shots = sum(counts.values())
    detailed = []

    best_order: int | None = None
    final_factors: tuple[int, int] | None = None

    # Sort counts by descending frequency
    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    for bitstring, count in sorted_counts:
        rec = analyze_measurement(bitstring, count, total_shots, num_counting_qubits, a, N)
        detailed.append(rec)

        if rec["order_valid"] and best_order is None:
            best_order = rec["candidate_r"]

        if rec["verified_factors"] is not None and final_factors is None:
            final_factors = rec["verified_factors"]

    return best_order, final_factors, detailed

