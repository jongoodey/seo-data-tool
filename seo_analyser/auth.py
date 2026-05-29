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


# Accept the project's existing .env.local convention (user_name/password) as
# well as the DATAFORSEO_* names, so credentials load without reconfiguration.
_LOGIN_KEYS = ("DATAFORSEO_LOGIN", "user_name", "login")
_PASSWORD_KEYS = ("DATAFORSEO_PASSWORD", "password")


def _read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if not _ENV_FILE.exists():
        return values
    for raw in _ENV_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def from_env() -> Credentials:
    """Read credentials from environment or .env.local.

    Supports DATAFORSEO_LOGIN/DATAFORSEO_PASSWORD and the project's existing
    user_name/password convention.
    """
    file_values = _read_env_file()

    def _first(keys: tuple[str, ...]) -> str:
        for key in keys:
            val = os.environ.get(key) or file_values.get(key)
            if val:
                return val
        return ""

    return Credentials(login=_first(_LOGIN_KEYS), password=_first(_PASSWORD_KEYS))
