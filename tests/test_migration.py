import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.migration import AssetInventoryItem
from services.migration_service import (
    assess_asset,
    assess_inventory,
    export_report_to_json,
    export_report_to_markdown,
    load_inventory_from_json,
)


def test_load_sample_inventory():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample-data", "crypto-inventory.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        items = load_inventory_from_json(f.read())

    assert len(items) == 7
    assert any(i.current_algorithm == "RSA-2048" for i in items)
    assert any("ML-KEM" in i.current_algorithm for i in items)


def test_assess_rsa_key_exchange():
    item = AssetInventoryItem(
        id="TEST-01",
        application_name="API Gateway",
        current_algorithm="RSA-2048",
        category="Key Exchange",
        key_size=2048,
        usage_type="Data In-Transit (TLS)",
        data_classification="Financial",
        confidentiality_lifetime_years=10,
        network_exposure="Public Internet",
    )
    result = assess_asset(item)

    assert result.quantum_vulnerable is True
    assert result.risk_level == "CRITICAL"
    assert result.hndl_exposed is True
    assert result.mosca_breach is True
    assert "ML-KEM" in result.recommended_replacement


def test_assess_aes256_symmetric():
    item = AssetInventoryItem(
        id="TEST-02",
        application_name="Database",
        current_algorithm="AES-256-GCM",
        category="Symmetric Encryption",
        key_size=256,
        usage_type="Data At-Rest",
        data_classification="Patient Data",
        confidentiality_lifetime_years=30,
        network_exposure="Internal",
    )
    result = assess_asset(item)

    assert result.quantum_vulnerable is False
    assert result.risk_level == "LOW"
    assert "Retain" in result.recommended_replacement


def test_assess_pqc_hybrid():
    item = AssetInventoryItem(
        id="TEST-03",
        application_name="Uplink",
        current_algorithm="Hybrid (X25519 + ML-KEM-768)",
        category="Key Exchange",
        key_size=1216,
        usage_type="Messaging",
        data_classification="Top Secret",
        confidentiality_lifetime_years=50,
        network_exposure="Public",
    )
    result = assess_asset(item)

    assert result.quantum_vulnerable is False
    assert result.risk_level == "PQC-READY"
    assert "Maintain" in result.recommended_replacement


def test_assess_inventory_aggregation():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample-data", "crypto-inventory.json")
    with open(sample_path, "r", encoding="utf-8") as f:
        items = load_inventory_from_json(f.read())

    summary = assess_inventory(items)

    assert summary.total_assets == 7
    assert summary.quantum_vulnerable_count >= 4
    assert summary.pqc_ready_count >= 1
    assert summary.critical_priority_count >= 1
    assert summary.overall_posture_score < 100

    # Test JSON and Markdown exports
    json_out = export_report_to_json(summary)
    assert "overall_posture_score" in json_out
    parsed = json.loads(json_out)
    assert len(parsed["assets"]) == 7

    md_out = export_report_to_markdown(summary)
    assert "# Q-SHIELD" in md_out
    assert "ASSET-001" in md_out


def test_invalid_inventory_rejection():
    with pytest.raises(ValueError):
        load_inventory_from_json('{"not": "a list"}')

