"""PQC Migration Readiness Assessment Service for analyzing cryptographic inventory."""
from __future__ import annotations

import json
from typing import Any

from models.migration import (
    AssetAssessmentResult,
    AssetInventoryItem,
    MigrationReportSummary,
)

CRQC_HORIZON_YEARS = 8  # Estimated years until Cryptographically Relevant Quantum Computer (approx 2034)
DEFAULT_MIGRATION_YEARS = 3  # Estimated years required to complete enterprise migration


def assess_asset(item: AssetInventoryItem) -> AssetAssessmentResult:
    """Analyze a single asset against quantum threats, Mosca's theorem, and NIST PQC guidance."""
    alg_upper = item.current_algorithm.upper()
    cat_upper = item.category.upper()

    is_pqc_ready = any(pqc_term in alg_upper for pqc_term in ["ML-KEM", "ML-DSA", "SLH-DSA", "HYBRID"])
    is_asymmetric_classical = any(
        term in alg_upper
        for term in ["RSA", "ECDSA", "ECDH", "X25519", "ED25519", "DIFFIE", "DH", "DSA", "P-256", "P-384", "P-521"]
    )
    is_weak_symmetric = any(term in alg_upper for term in ["3DES", "DES", "RC4", "BLOWFISH", "AES-128"])
    is_strong_symmetric = any(term in alg_upper for term in ["AES-256", "CHACHA20", "AES256"])

    quantum_vulnerable = False
    threat_description = "Safe"
    risk_level = "LOW"
    hndl_exposed = False
    mosca_breach = False
    urgency = "MONITOR / MAINTAIN"
    recommended_rep = "Maintain current implementation"
    size_expansion = "No impact"
    technical_rationale = ""

    # Evaluate Mosca's Theorem: X + Y > Z
    X = item.confidentiality_lifetime_years
    Y = DEFAULT_MIGRATION_YEARS
    Z = CRQC_HORIZON_YEARS
    if (X + Y) > Z:
        mosca_breach = True

    if is_pqc_ready:
        quantum_vulnerable = False
        threat_description = "Resistant to Shor and Grover attacks (Lattice / Hybrid Construction)"
        risk_level = "PQC-READY"
        urgency = "MONITOR / MAINTAIN"
        recommended_rep = "Maintain PQC deployment. Plan for FIPS 203/204 formal certification."
        size_expansion = "Already accommodates PQC key and ciphertext/signature dimensions."
        technical_rationale = (
            f"Asset '{item.application_name}' is already utilizing post-quantum / hybrid protection. "
            "No immediate migration required."
        )

    elif is_asymmetric_classical:
        quantum_vulnerable = True
        threat_description = "Shor's Algorithm: solvable in polynomial time O((log N)^3) on a fault-tolerant quantum computer."

        is_key_exchange = "KEY" in cat_upper or "EXCHANGE" in cat_upper or "TRANSIT" in item.usage_type.upper()
        is_internet_exposed = "PUBLIC" in item.network_exposure.upper() or "INTERNET" in item.network_exposure.upper()

        if is_key_exchange and (is_internet_exposed or item.confidentiality_lifetime_years >= 7):
            hndl_exposed = True
            risk_level = "CRITICAL"
            urgency = "IMMEDIATE"
            recommended_rep = "ML-KEM-768 (NIST FIPS 203) or Hybrid X25519 + ML-KEM-768"
            size_expansion = (
                "Public key expands to 1,184 B (ML-KEM) or 1,216 B (Hybrid). "
                "Ciphertext expands to 1,088 B. Verify TLS/packet MTU limits."
            )
            technical_rationale = (
                f"High risk of 'Harvest Now, Decrypt Later' (HNDL). Traffic recorded today can be retroactively "
                f"decrypted when a quantum computer arrives. Because data lifetime ({X} yrs) + migration time ({Y} yrs) > {Z} yrs, "
                "confidentiality is compromised unless hybrid or PQC key encapsulation is introduced immediately."
            )
        elif "SIGN" in cat_upper or "SIGN" in item.usage_type.upper():
            hndl_exposed = False  # Signatures protect authenticity/integrity, not confidentiality
            if item.confidentiality_lifetime_years > 10 or "FIRMWARE" in item.application_name.upper():
                risk_level = "HIGH"
                urgency = "NEAR-TERM (1-2 YEARS)"
            else:
                risk_level = "MEDIUM"
                urgency = "PLANNED (3-5 YEARS)"
            recommended_rep = "ML-DSA-65 (NIST FIPS 204) or SLH-DSA-SHA2-128s (NIST FIPS 205)"
            size_expansion = (
                "Signature expands to 3,309 B (ML-DSA-65) vs 64 B (Ed25519) or 256 B (RSA-2048). "
                "Public key expands to 1,952 B. Accommodate storage and certificate chain limits."
            )
            technical_rationale = (
                "Quantum computers can forge digital signatures in polynomial time using Shor's algorithm. "
                "Long-lived verification roots, code signing certificates, and legal notarization must transition "
                "to ML-DSA before quantum computers become operational."
            )
        else:
            risk_level = "HIGH" if mosca_breach else "MEDIUM"
            urgency = "NEAR-TERM (1-2 YEARS)" if mosca_breach else "PLANNED (3-5 YEARS)"
            recommended_rep = "ML-KEM-768 or ML-DSA-65 depending on handshake role"
            size_expansion = "Accommodate lattice parameter expansion in handshake protocol."
            technical_rationale = "Classical public-key cryptography must be phased out according to NIST and CISA timelines."

    elif is_weak_symmetric:
        quantum_vulnerable = True
        threat_description = "Legacy algorithm vulnerability + Grover's quadratic speedup reduces effective key length to <= 64 bits."
        risk_level = "HIGH"
        urgency = "IMMEDIATE"
        recommended_rep = "AES-256-GCM (NIST SP 800-38D)"
        size_expansion = "128-bit authentication tag (16 bytes) per ciphertext container."
        technical_rationale = (
            f"Algorithm '{item.current_algorithm}' is legacy-deprecated and completely insecure in both classical "
            "and quantum environments. Migrate to AES-256-GCM immediately."
        )

    elif is_strong_symmetric:
        quantum_vulnerable = False
        threat_description = "Grover's algorithm reduces 256-bit keys to 128-bit quantum security, remaining computationally unbreakable."
        risk_level = "LOW"
        urgency = "MONITOR / MAINTAIN"
        recommended_rep = "Retain AES-256-GCM; review random IV/nonce generation policies."
        size_expansion = "Zero expansion (retain existing AEAD parameters)."
        technical_rationale = (
            "AES-256 remains quantum-resistant. Grover's algorithm achieves only a quadratic speedup (O(2^(k/2))), "
            "leaving AES-256 with an effective 128-bit security margin, which is universally considered safe."
        )

    else:
        # Default fallback
        quantum_vulnerable = False
        threat_description = "Standard cryptographic primitive"
        risk_level = "MEDIUM"
        urgency = "PLANNED (3-5 YEARS)"
        recommended_rep = "Review against NIST SP 800-131A Rev 2"
        size_expansion = "N/A"
        technical_rationale = "Review cryptographic algorithm implementation details and lifecycle."

    return AssetAssessmentResult(
        asset_id=item.id,
        application_name=item.application_name,
        current_algorithm=item.current_algorithm,
        quantum_vulnerable=quantum_vulnerable,
        vulnerability_threat=threat_description,
        risk_level=risk_level,
        hndl_exposed=hndl_exposed,
        mosca_breach=mosca_breach,
        migration_urgency=urgency,
        recommended_replacement=recommended_rep,
        size_expansion_impact=size_expansion,
        technical_rationale=technical_rationale,
    )


def assess_inventory(items: list[AssetInventoryItem]) -> MigrationReportSummary:
    """Analyze a collection of inventory assets and formulate an aggregate migration posture."""
    results = [assess_asset(item) for item in items]

    total = len(results)
    vuln_count = sum(1 for r in results if r.quantum_vulnerable)
    pqc_count = sum(1 for r in results if r.risk_level == "PQC-READY")
    critical_count = sum(1 for r in results if r.risk_level == "CRITICAL")
    high_count = sum(1 for r in results if r.risk_level == "HIGH")
    med_count = sum(1 for r in results if r.risk_level == "MEDIUM")
    low_count = sum(1 for r in results if r.risk_level in ("LOW", "PQC-READY"))
    hndl_count = sum(1 for r in results if r.hndl_exposed)

    # Compute posture score (0 - 100):
    # Perfect score: 100% PQC-ready or low risk. Deduct heavily for critical and high.
    if total > 0:
        penalty = (critical_count * 30 + high_count * 15 + med_count * 5) / total
        posture_score = max(0, min(100, int(100 - penalty)))
    else:
        posture_score = 100

    return MigrationReportSummary(
        total_assets=total,
        quantum_vulnerable_count=vuln_count,
        pqc_ready_count=pqc_count,
        critical_priority_count=critical_count,
        high_priority_count=high_count,
        medium_priority_count=med_count,
        low_priority_count=low_count,
        hndl_vulnerable_count=hndl_count,
        assets=results,
        overall_posture_score=posture_score,
    )


def load_inventory_from_json(json_str: str) -> list[AssetInventoryItem]:
    """Parse a JSON string into a list of AssetInventoryItem objects."""
    data = json.loads(json_str)
    if not isinstance(data, list):
        raise ValueError("Cryptographic inventory JSON must be a list of asset objects.")
    return [AssetInventoryItem.from_dict(entry) for entry in data]


def export_report_to_json(summary: MigrationReportSummary) -> str:
    """Export the migration assessment report as structured JSON."""
    data = {
        "summary": {
            "total_assets": summary.total_assets,
            "overall_posture_score": summary.overall_posture_score,
            "quantum_vulnerable_count": summary.quantum_vulnerable_count,
            "pqc_ready_count": summary.pqc_ready_count,
            "critical_priority_count": summary.critical_priority_count,
            "high_priority_count": summary.high_priority_count,
            "medium_priority_count": summary.medium_priority_count,
            "low_priority_count": summary.low_priority_count,
            "hndl_vulnerable_count": summary.hndl_vulnerable_count,
        },
        "assets": [
            {
                "asset_id": a.asset_id,
                "application_name": a.application_name,
                "current_algorithm": a.current_algorithm,
                "quantum_vulnerable": a.quantum_vulnerable,
                "vulnerability_threat": a.vulnerability_threat,
                "risk_level": a.risk_level,
                "hndl_exposed": a.hndl_exposed,
                "mosca_breach": a.mosca_breach,
                "migration_urgency": a.migration_urgency,
                "recommended_replacement": a.recommended_replacement,
                "size_expansion_impact": a.size_expansion_impact,
                "technical_rationale": a.technical_rationale,
            }
            for a in summary.assets
        ],
    }
    return json.dumps(data, indent=2)


def export_report_to_markdown(summary: MigrationReportSummary) -> str:
    """Format the assessment summary into an executive Markdown report."""
    md = [
        "# Q-SHIELD Post-Quantum Cryptography Migration Readiness Report",
        "",
        f"**Overall Quantum Safety Posture:** {summary.overall_posture_score} / 100",
        f"- **Total Assessed Assets:** {summary.total_assets}",
        f"- **Quantum-Vulnerable Assets:** {summary.quantum_vulnerable_count}",
        f"- **Harvest-Now-Decrypt-Later (HNDL) Vulnerable:** {summary.hndl_vulnerable_count}",
        f"- **Critical Urgency Migrations:** {summary.critical_priority_count}",
        f"- **High Urgency Migrations:** {summary.high_priority_count}",
        f"- **PQC-Ready Assets:** {summary.pqc_ready_count}",
        "",
        "## Priority Breakdown",
        "",
        "| Asset ID | Application | Current Algorithm | Risk Level | Urgency | Recommended Replacement |",
        "|---|---|---|---|---|---|",
    ]
    for a in summary.assets:
        md.append(
            f"| `{a.asset_id}` | {a.application_name} | `{a.current_algorithm}` | **{a.risk_level}** | {a.migration_urgency} | {a.recommended_replacement} |"
        )
    md.extend([
        "",
        "## Detailed Technical Rationales",
        "",
    ])
    for a in summary.assets:
        md.extend([
            f"### {a.asset_id}: {a.application_name}",
            f"- **Threat Mechanism:** {a.vulnerability_threat}",
            f"- **Mosca's Condition (X + Y > Z):** {'Triggered (Mandatory Immediate Plan)' if a.mosca_breach else 'Not Triggered'}",
            f"- **Size & Bandwidth Expansion:** {a.size_expansion_impact}",
            f"- **Rationale:** {a.technical_rationale}",
            "",
        ])
    return "\n".join(md)

