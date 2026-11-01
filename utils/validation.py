"""Input validation, file limits, and parameter verification."""
from __future__ import annotations

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MiB sensible upper limit for demonstration


def validate_file_payload(data: bytes, filename: str) -> None:
    """Validate that an uploaded file is within allowable limits and non-empty."""
    if not data:
        raise ValueError("Uploaded file is empty.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File size ({len(data):,} bytes) exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES:,} bytes."
        )


def validate_mode(mode: str) -> str:
    """Verify that mode is one of the supported modes."""
    valid_modes = ("classical", "pqc", "hybrid")
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Supported modes: {valid_modes}")
    return mode

