"""Data models for identities and key bundles."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import qs_crypto as qc


@dataclass
class IdentitySummary:
    """Public metadata representation of an identity."""

    name: str
    fingerprint: str
    x25519_pk_bytes: int
    ed25519_pk_bytes: int
    mlkem_pk_bytes: int
    mldsa_pk_bytes: int

    @classmethod
    def from_identity(cls, ident: qc.Identity) -> IdentitySummary:
        return cls(
            name=ident.name,
            fingerprint=ident.fingerprint(),
            x25519_pk_bytes=len(ident.x_pub),
            ed25519_pk_bytes=len(ident.ed_pub),
            mlkem_pk_bytes=len(ident.kem_pk),
            mldsa_pk_bytes=len(ident.dsa_pk),
        )

