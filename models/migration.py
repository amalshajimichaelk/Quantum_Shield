"""Data models for Cryptographic Inventory and PQC Migration Readiness Assessment."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssetInventoryItem:
    """Represents a cryptographic asset in an organization's digital estate."""

    id: str
    application_name: str
    current_algorithm: str
    category: str  # "Key Exchange", "Digital Signature", "Symmetric Encryption", "Hashing"
    key_size: int
    usage_type: str
    data_classification: str
    confidentiality_lifetime_years: int
    network_exposure: str
    constraints: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssetInventoryItem:
        return cls(
            id=str(data.get("id", "UNKNOWN")),
            application_name=str(data.get("application_name", "Unnamed Application")),
            current_algorithm=str(data.get("current_algorithm", "Unknown")),
            category=str(data.get("category", "General")),
            key_size=int(data.get("key_size", 0)),
            usage_type=str(data.get("usage_type", "Standard")),
            data_classification=str(data.get("data_classification", "Internal")),
            confidentiality_lifetime_years=int(data.get("confidentiality_lifetime_years", 5)),
            network_exposure=str(data.get("network_exposure", "Internal")),
            constraints=str(data.get("constraints", "")),
        )


@dataclass
class AssetAssessmentResult:
    """Individual assessment findings and migration roadmap for an asset."""

    asset_id: str
    application_name: str
    current_algorithm: str
    quantum_vulnerable: bool
    vulnerability_threat: str  # "Shor's Algorithm (Polynomial Time)", "Grover's Algorithm (Quadratic)", "Safe"
    risk_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "PQC-READY"
    hndl_exposed: bool  # Harvest Now Decrypt Later
    mosca_breach: bool  # X + Y > Z condition met
    migration_urgency: str  # "IMMEDIATE", "NEAR-TERM (1-2 YEARS)", "PLANNED (3-5 YEARS)", "MONITOR / MAINTAIN"
    recommended_replacement: str
    size_expansion_impact: str
    technical_rationale: str


@dataclass
class MigrationReportSummary:
    """Aggregated organizational risk profile and migration readiness posture."""

    total_assets: int
    quantum_vulnerable_count: int
    pqc_ready_count: int
    critical_priority_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    hndl_vulnerable_count: int
    assets: list[AssetAssessmentResult] = field(default_factory=list)
    overall_posture_score: int = 0  # 0 to 100 (100 = fully quantum safe)

