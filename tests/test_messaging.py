import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import qs_crypto as qc
from services.messaging_service import (
    create_participant_identities,
    send_secure_message,
    receive_secure_message,
    DecryptionFailedError,
    SignatureVerificationError,
)


@pytest.fixture
def participants():
    return create_participant_identities()


@pytest.mark.parametrize("mode", ["classical", "pqc", "hybrid"])
@pytest.mark.parametrize("sig_alg", ["ML-DSA-65", "Ed25519", "none"])
def test_send_and_receive_roundtrip(participants, mode, sig_alg):
    alice, bob = participants
    msg = b"Confidential memo: PQC migration scheduled for Q4."

    envelope = send_secure_message(
        sender=alice,
        recipient_pub=bob.public(),
        recipient_name=bob.name,
        plaintext=msg,
        mode=mode,
        signature_algorithm=sig_alg,
    )

    assert envelope.cryptographic_mode == mode
    assert envelope.signature_algorithm == sig_alg
    if sig_alg != "none":
        assert len(envelope.signature) > 0

    decrypted, meta = receive_secure_message(
        recipient=bob,
        sender_pub=alice.public(),
        envelope=envelope,
        expected_mode=mode,
    )

    assert decrypted == msg
    assert meta["sender"] == alice.name
    if sig_alg != "none":
        assert meta["signature_valid"] is True


def test_tampered_ciphertext_rejected(participants):
    alice, bob = participants
    msg = b"Top secret operational intelligence"

    envelope = send_secure_message(
        sender=alice,
        recipient_pub=bob.public(),
        recipient_name=bob.name,
        plaintext=msg,
        mode="pqc",
        signature_algorithm="ML-DSA-65",
    )

    # Flip one character in base64 ciphertext
    ct_chars = list(envelope.ciphertext)
    ct_chars[5] = "A" if ct_chars[5] != "A" else "B"
    envelope.ciphertext = "".join(ct_chars)

    # Note: modifying ciphertext affects both signature and AEAD authentication tag
    with pytest.raises((DecryptionFailedError, SignatureVerificationError)):
        receive_secure_message(bob, alice.public(), envelope)


def test_tampered_metadata_signature_rejected(participants):
    alice, bob = participants
    msg = b"Legal contract authorization"

    envelope = send_secure_message(
        sender=alice,
        recipient_pub=bob.public(),
        recipient_name=bob.name,
        plaintext=msg,
        mode="hybrid",
        signature_algorithm="ML-DSA-65",
    )

    # Tamper with recipient metadata
    envelope.recipient_identity = "Mallory"

    with pytest.raises(SignatureVerificationError):
        receive_secure_message(bob, alice.public(), envelope)


def test_mode_mismatch_rejected(participants):
    alice, bob = participants
    msg = b"Standard memo"

    envelope = send_secure_message(
        sender=alice,
        recipient_pub=bob.public(),
        recipient_name=bob.name,
        plaintext=msg,
        mode="classical",
        signature_algorithm="none",
    )

    with pytest.raises(qc.ModeMismatchError):
        receive_secure_message(bob, alice.public(), envelope, expected_mode="hybrid")

