import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import qs_crypto as qc
from services.file_service import protect_file, recover_file


@pytest.fixture
def identity():
    return qc.generate_identity("Vault")


@pytest.mark.parametrize("mode", ["classical", "pqc", "hybrid"])
def test_file_protect_and_recover(identity, mode):
    sample_content = b"Binary PDF or Executable file content simulation \x00\xff\xfe\x01" * 100
    filename = "document.pdf"

    blob = protect_file(sample_content, filename, mode, identity.public())
    assert blob.startswith(qc.MAGIC)

    recovered, header = recover_file(blob, identity, expected_mode=mode)
    assert recovered == sample_content
    assert header["filename"] == filename
    assert header["mode"] == mode


def test_tampered_file_rejected(identity):
    sample = b"Financial quarterly reports"
    blob = protect_file(sample, "reports.xlsx", "pqc", identity.public())

    # Tamper with file container
    bad_blob = bytearray(blob)
    bad_blob[-5] ^= 0x01

    with pytest.raises(qc.IntegrityError):
        recover_file(bytes(bad_blob), identity)


def test_empty_file_rejected(identity):
    with pytest.raises(ValueError, match="empty"):
        protect_file(b"", "empty.txt", "pqc", identity.public())


def test_wrong_recipient_file_rejected(identity):
    other = qc.generate_identity("Intruder")
    blob = protect_file(b"Encrypted secrets", "secret.txt", "hybrid", identity.public())

    with pytest.raises(qc.IntegrityError):
        recover_file(blob, other)

