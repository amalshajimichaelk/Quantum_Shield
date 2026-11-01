"""File encryption and protection service."""
from __future__ import annotations

import qs_crypto as qc
from utils.validation import validate_file_payload, validate_mode


def protect_file(
    data: bytes,
    filename: str,
    mode: str,
    recipient_pub: qc.PublicBundle,
) -> bytes:
    """Encrypt a file payload into an authenticated QuantumShield container."""
    validate_file_payload(data, filename)
    validate_mode(mode)
    return qc.encrypt(mode, recipient_pub, data, filename=filename)


def recover_file(
    blob: bytes,
    recipient_ident: qc.Identity,
    expected_mode: str | None = None,
) -> tuple[bytes, dict]:
    """Decrypt and verify an authenticated QuantumShield container."""
    if expected_mode:
        validate_mode(expected_mode)
    return qc.decrypt(recipient_ident, blob, expected_mode=expected_mode)

