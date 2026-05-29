"""Encode/decode a request (endpoint + params) into a shareable URL token."""
from __future__ import annotations

import base64
import json

SHARE_KEY = "s"


def encode_share(family: str, endpoint: str, params: dict) -> str:
    blob = json.dumps({"f": family, "e": endpoint, "p": params}, default=str)
    return base64.urlsafe_b64encode(blob.encode("utf-8")).decode("ascii")


def decode_share(token: str) -> dict | None:
    """Return {family, endpoint, params} from a token, or None if invalid."""
    if not token:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or "f" not in data or "e" not in data:
        return None
    return {"family": data["f"], "endpoint": data["e"], "params": data.get("p", {})}
