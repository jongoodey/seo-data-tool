"""Credential handling. Reads .env.local for local dev; the UI may override."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env.local"


@dataclass
class Credentials:
    login: str
    password: str

    @property
    def is_complete(self) -> bool:
        return bool(self.login and self.password)


def from_env() -> Credentials:
    """Best-effort read of DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD from env or .env.local."""
    login = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")
    if (not login or not password) and _ENV_FILE.exists():
        for raw in _ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key == "DATAFORSEO_LOGIN" and not login:
                login = val
            elif key == "DATAFORSEO_PASSWORD" and not password:
                password = val
    return Credentials(login=login, password=password)
