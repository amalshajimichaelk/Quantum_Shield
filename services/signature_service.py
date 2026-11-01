"""Digital signature management service for classical (Ed25519) and PQC (ML-DSA-65)."""
from __future__ import annotations

import qs_crypto as qc


def sign_data(ident: qc.Identity, data: bytes, algorithm: str = "ML-DSA-65") -> bytes:
    """Sign data using the selected digital signature scheme."""
    if algorithm == "ML-DSA-65":
        return qc.sign(ident, data)
    elif algorithm == "Ed25519":
        return qc.ed25519_sign(ident, data)
    else:
        raise ValueError(f"Unsupported signature algorithm: {algorithm}")


def verify_data(public_key: bytes, data: bytes, signature: bytes, algorithm: str = "ML-DSA-65") -> bool:
    """Verify digital signature with public key."""
    if algorithm == "ML-DSA-65":
        return qc.verify(public_key, data, signature)
    elif algorithm == "Ed25519":
        return qc.ed25519_verify(public_key, data, signature)
    else:
        raise ValueError(f"Unsupported signature algorithm: {algorithm}")

