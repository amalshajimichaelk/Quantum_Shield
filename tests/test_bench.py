import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bench


def test_system_metadata():
    meta = bench.get_system_metadata(iterations=10)
    assert "platform" in meta
    assert "python_version" in meta
    assert meta["cpu_count"] >= 1
    assert meta["iterations"] == 10
    assert "cryptography_version" in meta


def test_measure_sizes_completeness():
    df = bench.measure_sizes()
    indexed = df.set_index(["group", "metric"])["bytes"]

    # Classical sizes
    assert indexed[("Classical", "Public key")] == 32
    assert indexed[("Classical", "Ed25519 Public key")] == 32
    assert indexed[("Classical", "Signature (Ed25519)")] == 64
    assert indexed[("Classical", "Private key (X25519)")] == 32
    assert indexed[("Classical", "Private key (Ed25519)")] == 32

    # PQC sizes (FIPS 203 & FIPS 204)
    assert indexed[("ML-KEM-768", "Public key")] == 1184
    assert indexed[("ML-KEM-768", "Private key")] == 2400
    assert indexed[("ML-KEM-768", "Key-exchange data sent (ciphertext)")] == 1088
    assert indexed[("ML-DSA-65", "Public key")] == 1952
    assert indexed[("ML-DSA-65", "Signature")] == 3309
    assert indexed[("ML-DSA-65", "Private key")] == 4032

    # Hybrid sizes
    assert indexed[("Hybrid", "Public key")] == 1184 + 32
    assert indexed[("Hybrid", "Key-exchange data sent (ciphertext)")] == 1088 + 32


def test_run_timings_statistics():
    df = bench.run_timings(iterations=3, payload_sizes=(1024,))
    required_cols = {"group", "operation", "median_ms", "mean_ms", "min_ms", "max_ms", "p95_ms", "stdev_ms", "runs"}
    assert required_cols.issubset(set(df.columns))

    # All timings must be strictly positive
    assert (df["median_ms"] > 0).all()
    assert (df["min_ms"] > 0).all()
    assert (df["max_ms"] >= df["min_ms"]).all()
    assert (df["p95_ms"] >= df["min_ms"]).all()

    # Operations checked
    ops = set(df["operation"])
    assert any("Ed25519" in op for op in ops)
    assert any("ML-DSA-65" in op for op in ops)
    assert any("AES-256-GCM" in op for op in ops)

    # CSV serialization works
    csv_data = df.to_csv(index=False)
    assert "median_ms" in csv_data
    assert len(csv_data) > 200

