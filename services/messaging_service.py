"""Secure multi-party messaging workflow service according to Section 4.5."""
from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import qs_crypto as qc
from models.messages import MessageEnvelope


class MessagingError(Exception):
    """Base error for messaging workflows."""


class DecryptionFailedError(MessagingError):
    """Raised when ciphertext authentication or decryption fails."""


class SignatureVerificationError(MessagingError):
    """Raised when envelope digital signature verification fails."""


def create_participant_identities() -> tuple[qc.Identity, qc.Identity]:
    """Generate distinct long-term identities for Alice (sender) and Bob (recipient)."""
    alice = qc.generate_identity("Alice (Sender)")
    bob = qc.generate_identity("Bob (Recipient)")
    return alice, bob


def send_secure_message(
    sender: qc.Identity,
    recipient_pub: qc.PublicBundle,
    recipient_name: str,
    plaintext: bytes,
    mode: str = "pqc",
    signature_algorithm: str = "ML-DSA-65",
) -> MessageEnvelope:
    """Execute complete sender workflow: key establishment, AEAD encryption, canonical signing."""
    # 1. Establish shared secret and get header key data
    aes_key, key_fields = qc.establish(mode, recipient_pub)

    # 2. Generate unique 96-bit nonce
    nonce = os.urandom(12)

    # 3. Encrypt payload with AES-256-GCM
    # Contextual AAD binds mode and participants
    aad = f"QSH-MSG|v1|{mode}|{sender.name}|{recipient_name}".encode("utf-8")
    ciphertext = AESGCM(aes_key).encrypt(nonce, plaintext, aad)

    encaps_ct = base64.b64encode(key_fields.get("mlkem_ct", b"")).decode("ascii")
    eph_pk = base64.b64encode(key_fields.get("x25519_eph", b"")).decode("ascii")

    envelope = MessageEnvelope(
        message_id=str(uuid.uuid4()),
        version=1,
        cryptographic_mode=mode,
        key_establishment_algorithm=qc.MODE_LABEL[mode],
        sender_identity=sender.name,
        recipient_identity=recipient_name,
        encapsulation_ciphertext=encaps_ct,
        ephemeral_public_key=eph_pk,
        encryption_algorithm="AES-256-GCM (NIST SP 800-38D)",
        nonce=base64.b64encode(nonce).decode("ascii"),
        ciphertext=base64.b64encode(ciphertext).decode("ascii"),
        signature_algorithm=signature_algorithm,
        signature="",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # 4. Sign canonical envelope representation
    if signature_algorithm == "ML-DSA-65":
        canon = envelope.canonical_bytes()
        sig_bytes = qc.sign(sender, canon)
        envelope.signature = base64.b64encode(sig_bytes).decode("ascii")
    elif signature_algorithm == "Ed25519":
        canon = envelope.canonical_bytes()
        sig_bytes = qc.ed25519_sign(sender, canon)
        envelope.signature = base64.b64encode(sig_bytes).decode("ascii")
    else:
        envelope.signature_algorithm = "none"
        envelope.signature = ""

    return envelope


def receive_secure_message(
    recipient: qc.Identity,
    sender_pub: qc.PublicBundle,
    envelope: MessageEnvelope,
    expected_mode: str | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Execute complete recipient workflow: signature verification, key recovery, AEAD decryption."""
    # 1. Verify digital signature if present
    sig_valid = False
    if envelope.signature_algorithm in ("ML-DSA-65", "Ed25519") and envelope.signature:
        sig_bytes = base64.b64decode(envelope.signature.encode("ascii"))
        canon = envelope.canonical_bytes()
        if envelope.signature_algorithm == "ML-DSA-65":
            sig_valid = qc.verify(sender_pub.dsa_pk, canon, sig_bytes)
        elif envelope.signature_algorithm == "Ed25519":
            sig_valid = qc.ed25519_verify(sender_pub.ed_pub, canon, sig_bytes)

        if not sig_valid:
            raise SignatureVerificationError(
                f"Invalid digital signature! Verification failed under {envelope.signature_algorithm}."
            )

    # 2. Check mode enforcement
    mode = envelope.cryptographic_mode
    if expected_mode is not None and expected_mode != mode:
        raise qc.ModeMismatchError(
            f"Envelope was encrypted with mode '{mode}', but receiver required '{expected_mode}'."
        )

    # 3. Recover AES key
    fields: dict[str, bytes] = {}
    if envelope.encapsulation_ciphertext:
        fields["mlkem_ct"] = base64.b64decode(envelope.encapsulation_ciphertext)
    if envelope.ephemeral_public_key:
        fields["x25519_eph"] = base64.b64decode(envelope.ephemeral_public_key)

    try:
        aes_key = qc.recover(mode, recipient, fields)
    except Exception as exc:
        raise DecryptionFailedError(f"Failed to recover shared secret: {exc}") from exc

    # 4. Decrypt with AES-256-GCM
    nonce = base64.b64decode(envelope.nonce)
    ciphertext = base64.b64decode(envelope.ciphertext)
    aad = f"QSH-MSG|v1|{mode}|{envelope.sender_identity}|{envelope.recipient_identity}".encode("utf-8")

    try:
        plaintext = AESGCM(aes_key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise DecryptionFailedError(
            "Authentication failed: ciphertext has been modified or corrupted in transit."
        ) from exc

    metadata = {
        "message_id": envelope.message_id,
        "mode": mode,
        "sender": envelope.sender_identity,
        "signature_valid": sig_valid,
        "signature_algorithm": envelope.signature_algorithm,
        "timestamp": envelope.timestamp,
    }
    return plaintext, metadata

