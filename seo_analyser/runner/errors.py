"""Normalise SDK / network exceptions into a single app-level error type.

No Streamlit imports here — the UI layer catches RunError and decides how to
display it. This keeps the runner testable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunError(Exception):
    kind: str          # "auth" | "rate_limit" | "bad_request" | "server" | "network" | "empty"
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        return f"[{self.kind}] {self.message}"


def normalise(exc: Exception) -> RunError:
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    body = getattr(exc, "body", None) or str(exc)
    if isinstance(status, int):
        if status == 401 or status == 403:
            return RunError("auth", "Authentication failed — check your DataForSEO login/password.", status)
        if status == 429:
            return RunError("rate_limit", "Rate limited by DataForSEO — slow down and retry.", status)
        if 400 <= status < 500:
            return RunError("bad_request", f"Bad request: {body}", status)
        if status >= 500:
            return RunError("server", "DataForSEO server error — try again shortly.", status)
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return RunError("network", f"Network error: {exc}")
    return RunError("network", f"Unexpected error: {exc}")
