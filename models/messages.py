"""Structured cryptographic message envelope according to Section 4.5 specifications."""
from __future__ import annotations

import base64
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class MessageEnvelope:
    """Canonical encrypted message envelope binding headers, ciphertexts, and signatures."""

    message_id: str
    version: int
    cryptographic_mode: str
    key_establishment_algorithm: str
    sender_identity: str
    recipient_identity: str
    encapsulation_ciphertext: str  # Base64
    ephemeral_public_key: str  # Base64 (if applicable)
    encryption_algorithm: str
    nonce: str  # Base64
    ciphertext: str  # Base64
    signature_algorithm: str  # "ML-DSA-65", "Ed25519", or "none"
    signature: str  # Base64
    timestamp: str

    def canonical_bytes(self) -> bytes:
        """Deterministic byte representation used for digital signature verification.
        
        Binds message identifier, mode, parties, timestamp, and encrypted payload.
        """
        payload = {
            "message_id": self.message_id,
            "version": self.version,
            "cryptographic_mode": self.cryptographic_mode,
            "key_establishment_algorithm": self.key_establishment_algorithm,
            "sender_identity": self.sender_identity,
            "recipient_identity": self.recipient_identity,
            "encapsulation_ciphertext": self.encapsulation_ciphertext,
            "ephemeral_public_key": self.ephemeral_public_key,
            "encryption_algorithm": self.encryption_algorithm,
            "nonce": self.nonce,
            "ciphertext": self.ciphertext,
            "timestamp": self.timestamp,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageEnvelope:
        return cls(
            message_id=str(data.get("message_id", str(uuid.uuid4()))),
            version=int(data.get("version", 1)),
            cryptographic_mode=str(data.get("cryptographic_mode", "pqc")),
            key_establishment_algorithm=str(data.get("key_establishment_algorithm", "")),
            sender_identity=str(data.get("sender_identity", "Anonymous")),
            recipient_identity=str(data.get("recipient_identity", "Recipient")),
            encapsulation_ciphertext=str(data.get("encapsulation_ciphertext", "")),
            ephemeral_public_key=str(data.get("ephemeral_public_key", "")),
            encryption_algorithm=str(data.get("encryption_algorithm", "AES-256-GCM")),
            nonce=str(data.get("nonce", "")),
            ciphertext=str(data.get("ciphertext", "")),
            signature_algorithm=str(data.get("signature_algorithm", "none")),
            signature=str(data.get("signature", "")),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )

    @classmethod
    def from_json(cls, json_str: str) -> MessageEnvelope:
        return cls.from_dict(json.loads(json_str))

