import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import qs_crypto as qc


def test_ed25519_roundtrip():
    sk, pk = qc.ed25519_keygen()
    assert len(pk) == 32
    msg = b"Transaction authorization: $50,000 to Bob"
    sig = qc.ed25519_sign(sk, msg)
    assert len(sig) == 64
    assert qc.ed25519_verify(pk, msg, sig) is True


def test_ed25519_tamper_detection():
    sk, pk = qc.ed25519_keygen()
    msg = b"Signed payload"
    sig = qc.ed25519_sign(sk, msg)

    # Modified message
    assert qc.ed25519_verify(pk, b"Signed payloae", sig) is False

    # Modified signature
    bad_sig = bytearray(sig)
    bad_sig[10] ^= 0x01
    assert qc.ed25519_verify(pk, msg, bytes(bad_sig)) is False

    # Wrong public key
    _, other_pk = qc.ed25519_keygen()
    assert qc.ed25519_verify(other_pk, msg, sig) is False

    # Truncated signature / invalid length
    assert qc.ed25519_verify(pk, msg, sig[:30]) is False


def test_identity_ed25519_integration():
    ident = qc.generate_identity("Alice")
    assert ident.ed_sk is not None
    assert len(ident.ed_pub) == 32

    msg = b"Alice authorized document"
    sig = qc.ed25519_sign(ident, msg)
    assert len(sig) == 64
    assert qc.ed25519_verify(ident.ed_pub, msg, sig) is True


def test_classical_vs_pqc_signature_sizes():
    ident = qc.generate_identity("Signer")
    msg = b"Payload for comparison"

    sig_classical = qc.ed25519_sign(ident, msg)
    sig_pqc = qc.sign(ident, msg)

    assert len(ident.ed_pub) == 32
    assert len(sig_classical) == 64

    assert len(ident.dsa_pk) == 1952
    assert len(sig_pqc) == 3309

    # PQC signatures and keys are substantially larger than Ed25519
    assert len(sig_pqc) > 50 * len(sig_classical)
    assert len(ident.dsa_pk) > 60 * len(ident.ed_pub)


def test_keystore_with_ed25519():
    alice = qc.generate_identity("Alice")
    pw = "passphrase-for-keystore-123"
    ks = qc.export_keystore(alice, pw)
    restored = qc.import_keystore(ks, pw)

    assert restored.ed_pub == alice.ed_pub
    assert restored.ed_sk is not None

    msg = b"Signed by restored identity"
    sig = qc.ed25519_sign(restored, msg)
    assert qc.ed25519_verify(alice.ed_pub, msg, sig) is True

