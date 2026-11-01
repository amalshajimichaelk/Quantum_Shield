"""Cryptographic engine service facade."""
from __future__ import annotations

import qs_crypto as qc
from models.identities import IdentitySummary


def create_identity(name: str) -> qc.Identity:
    """Generate a full cryptographic identity bundle."""
    return qc.generate_identity(name)


def get_identity_summary(ident: qc.Identity) -> IdentitySummary:
    """Extract public summary without exposing private keys."""
    return IdentitySummary.from_identity(ident)


def test_crypto_engine_health() -> list[tuple[str, bool, str]]:
    """Execute live self-test of cryptographic primitives."""
    ident = qc.generate_identity("health_check")
    pub = ident.public()
    out = []

    for m in qc.MODES:
        blob = qc.encrypt(m, pub, b"health_check")
        ok = qc.decrypt(ident, blob, m)[0] == b"health_check"
        out.append((f"{qc.MODE_LABEL[m]} Round-trip", ok, "Authenticated encryption verified"))

    # Ed25519
    ed_sig = qc.ed25519_sign(ident, b"ed_check")
    ed_ok = qc.ed25519_verify(ident.ed_pub, b"ed_check", ed_sig)
    out.append(("Ed25519 Classical Signature", ed_ok, f"{len(ed_sig)} B signature verified"))

    # ML-DSA-65
    dsa_sig = qc.sign(ident, b"dsa_check")
    dsa_ok = qc.verify(ident.dsa_pk, b"dsa_check", dsa_sig)
    out.append(("ML-DSA-65 Post-Quantum Signature", dsa_ok, f"{len(dsa_sig)} B signature verified"))

    return out

