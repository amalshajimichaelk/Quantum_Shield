"""Real cryptographic measurements only: wall-clock timing and serialized byte sizes."""
from __future__ import annotations

import os
import platform
import statistics
import time
from datetime import datetime
from typing import Any, Callable

import cryptography
import pandas as pd
import pqcrypto
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pqcrypto.kem import ml_kem_768 as kem
from pqcrypto.sign import ml_dsa_65 as dsa

import qs_crypto as qc


def get_system_metadata(iterations: int = 50) -> dict[str, Any]:
    """Capture environment and hardware context for reproducible benchmarks."""
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor() or "Unknown AMD64/x86_64",
        "cpu_count": os.cpu_count() or 1,
        "cryptography_version": getattr(cryptography, "__version__", "Unknown"),
        "pqcrypto_version": getattr(pqcrypto, "__version__", "1.0.0"),
        "timestamp": datetime.now().isoformat(),
        "iterations": iterations,
    }


def _percentile(data: list[float], p: float) -> float:
    """Calculate the p-th percentile of a sorted list."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p
    lower = int(idx)
    upper = min(lower + 1, len(sorted_data) - 1)
    weight = idx - lower
    return sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight


def _time(fn: Callable[[], Any], n: int) -> dict[str, Any]:
    for _ in range(3):  # warm-up (not recorded): avoids cold-start/page-fault skew
        fn()
    samples: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - t0) / 1e6)  # ms
    return {
        "median_ms": statistics.median(samples),
        "mean_ms": statistics.fmean(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "p95_ms": _percentile(samples, 0.95),
        "stdev_ms": statistics.stdev(samples) if n > 1 else 0.0,
        "runs": n,
    }


def _time_interleaved(fns: dict[str, Callable[[], Any]], n: int) -> dict[str, dict[str, Any]]:
    """Time several callables round-robin in shuffled order each iteration."""
    import random

    for fn in fns.values():
        for _ in range(3):
            fn()
    samples: dict[str, list[float]] = {k: [] for k in fns}
    order = list(fns)
    for _ in range(n):
        random.shuffle(order)
        for k in order:
            t0 = time.perf_counter_ns()
            fns[k]()
            samples[k].append((time.perf_counter_ns() - t0) / 1e6)
    return {
        k: {
            "median_ms": statistics.median(v),
            "mean_ms": statistics.fmean(v),
            "min_ms": min(v),
            "max_ms": max(v),
            "p95_ms": _percentile(v, 0.95),
            "stdev_ms": statistics.stdev(v) if n > 1 else 0.0,
            "runs": n,
        }
        for k, v in samples.items()
    }


def run_timings(iterations: int = 50, payload_sizes: tuple[int, ...] = (1024, 1024 * 1024)) -> pd.DataFrame:
    """Benchmark all supported classical and post-quantum cryptographic primitives."""
    ident = qc.generate_identity("bench")
    pub = ident.public()
    rows: list[dict[str, Any]] = []

    def add(group: str, op: str, fn: Callable[[], Any], n: int = iterations):
        rows.append({"group": group, "operation": op, **_time(fn, n)})

    # 1. Key generation
    add("Classical", "Key generation (X25519)", qc.x25519_keygen)
    add("Classical", "Key generation (Ed25519)", qc.ed25519_keygen)
    add("ML-KEM-768", "Key generation", kem.keygen)
    add("Hybrid", "Key generation (X25519 + ML-KEM)", lambda: (qc.x25519_keygen(), kem.keygen()))
    add("ML-DSA-65", "Key generation", dsa.keygen)

    # 2. Raw KEM operations
    pk, sk = kem.keygen()
    ct, _ = kem.encaps(pk)
    add("ML-KEM-768", "Encapsulation", lambda: kem.encaps(pk))
    add("ML-KEM-768", "Decapsulation", lambda: kem.decaps(sk, ct))

    # 3. Raw X25519 Key Agreement
    x_sk, x_pk = qc.x25519_keygen()
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    x_pub_obj = X25519PublicKey.from_public_bytes(x_pk)
    add("Classical", "X25519 shared secret derivation", lambda: x_sk.exchange(x_pub_obj))

    # 4. Full key establishment incl. HKDF, sender and recipient
    for mode, name in (("classical", "Classical"), ("pqc", "ML-KEM-768"), ("hybrid", "Hybrid")):
        add(name, "Key establishment (sender, incl. HKDF)", lambda m=mode: qc.establish(m, pub))
        _, fields = qc.establish(mode, pub)
        add(name, "Key recovery (recipient, incl. HKDF)", lambda m=mode, f=fields: qc.recover(m, ident, f))

    # 5. Raw Symmetric Encryption: AES-256-GCM
    aes_key = os.urandom(32)
    sample_nonce = os.urandom(12)
    sample_pt = os.urandom(1024)
    sample_ct = AESGCM(aes_key).encrypt(sample_nonce, sample_pt, b"bench_aad")
    add("Classical", "AES-256-GCM Encrypt 1 KiB (raw AEAD)", lambda: AESGCM(aes_key).encrypt(sample_nonce, sample_pt, b"bench_aad"))
    add("Classical", "AES-256-GCM Decrypt 1 KiB (raw AEAD)", lambda: AESGCM(aes_key).decrypt(sample_nonce, sample_ct, b"bench_aad"))

    # 6. Full encrypt / decrypt pipeline per payload size
    for size in payload_sizes:
        data = os.urandom(size)
        label = f"{size // 1024} KiB" if size < 1024 * 1024 else f"{size // (1024 * 1024)} MiB"
        n = iterations if size <= 1024 else max(20, iterations // 2)
        names = {"classical": "Classical", "pqc": "ML-KEM-768", "hybrid": "Hybrid"}
        blobs = {m: qc.encrypt(m, pub, data) for m in names}
        for op, fns in (
            ("Encrypt", {m: (lambda m=m: qc.encrypt(m, pub, data)) for m in names}),
            ("Decrypt", {m: (lambda m=m: qc.decrypt(ident, blobs[m])) for m in names}),
        ):
            for m, r in _time_interleaved(fns, n).items():
                rows.append({"group": names[m], "operation": f"{op} {label} (full pipeline)", **r})

    # 7. Classical Digital Signatures: Ed25519
    ed_sk, ed_pk = qc.ed25519_keygen()
    msg_1k = os.urandom(1024)
    ed_sig = qc.ed25519_sign(ed_sk, msg_1k)
    add("Classical", "Sign 1 KiB (Ed25519)", lambda: qc.ed25519_sign(ed_sk, msg_1k))
    add("Classical", "Verify 1 KiB (Ed25519)", lambda: qc.ed25519_verify(ed_pk, msg_1k, ed_sig))

    # 8. Post-Quantum Digital Signatures: ML-DSA-65
    dpk, dsk = dsa.keygen()
    sig = dsa.sign(dsk, msg_1k)
    add("ML-DSA-65", "Sign 1 KiB (ML-DSA-65)", lambda: dsa.sign(dsk, msg_1k))
    add("ML-DSA-65", "Verify 1 KiB (ML-DSA-65)", lambda: dsa.verify(dpk, msg_1k, sig))

    return pd.DataFrame(rows)


def measure_sizes() -> pd.DataFrame:
    """Sizes in bytes, taken from real generated objects."""
    ident = qc.generate_identity("sizes")
    pub = ident.public()
    msg = b"x"
    overhead = {m: len(qc.encrypt(m, pub, b"")) for m in qc.MODES}
    _, f_c = qc.establish("classical", pub)
    _, f_p = qc.establish("pqc", pub)
    _, f_h = qc.establish("hybrid", pub)
    sig_pqc = qc.sign(ident, msg)
    sig_classical = qc.ed25519_sign(ident, msg)

    rows = [
        # Public Keys
        ("Classical", "Public key", len(ident.x_pub)),
        ("Classical", "Ed25519 Public key", len(ident.ed_pub)),
        ("ML-KEM-768", "Public key", len(ident.kem_pk)),
        ("Hybrid", "Public key", len(ident.x_pub) + len(ident.kem_pk)),
        ("ML-DSA-65", "Public key", len(ident.dsa_pk)),

        # Private Keys
        ("Classical", "Private key (X25519)", len(ident.x_sk.private_bytes_raw())),
        ("Classical", "Private key (Ed25519)", len(ident.ed_sk.private_bytes_raw()) if ident.ed_sk else 32),
        ("ML-KEM-768", "Private key", len(ident.kem_sk)),
        ("ML-DSA-65", "Private key", len(ident.dsa_sk)),

        # Ciphertexts & Transmitted Data
        ("Classical", "Key-exchange data sent (ciphertext)", sum(map(len, f_c.values()))),
        ("ML-KEM-768", "Key-exchange data sent (ciphertext)", sum(map(len, f_p.values()))),
        ("Hybrid", "Key-exchange data sent (ciphertext)", sum(map(len, f_h.values()))),

        # Signatures
        ("Classical", "Signature (Ed25519)", len(sig_classical)),
        ("ML-DSA-65", "Signature", len(sig_pqc)),

        # Container Overheads
        ("Classical", "Container overhead (empty plaintext)", overhead["classical"]),
        ("ML-KEM-768", "Container overhead (empty plaintext)", overhead["pqc"]),
        ("Hybrid", "Container overhead (empty plaintext)", overhead["hybrid"]),
    ]
    return pd.DataFrame(rows, columns=["group", "metric", "bytes"])
