"""Serialise results to CSV / JSON bytes for download."""
from __future__ import annotations

import csv
import io
import json


def to_csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def to_json_bytes(payload) -> bytes:
    return json.dumps(payload, indent=2, default=str).encode("utf-8")
