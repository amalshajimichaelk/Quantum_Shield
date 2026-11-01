"""Binary and JSON serialization utilities."""
from __future__ import annotations

import base64
import json
from typing import Any


def b64_encode(data: bytes) -> str:
    """Encode bytes into standard Base64 string."""
    return base64.b64encode(data).decode("ascii")


def b64_decode(text: str) -> bytes:
    """Decode standard Base64 string to bytes."""
    return base64.b64decode(text.encode("ascii"), validate=True)


def safe_json_dumps(obj: Any) -> str:
    """Serialize object to sorted deterministic JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

