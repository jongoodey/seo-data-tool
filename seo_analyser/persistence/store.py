"""Durable run history + saved presets.

One SQLAlchemy code path serves both backends: Postgres when DATABASE_URL is set
(Railway), else a local SQLite file (durable across restarts, no infra). Params
are stored as JSON text for cross-database portability. A nullable `workspace`
column is present now so v2 client workspaces need no migration.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy import (
    Column, DateTime, Float, Integer, MetaData, String, Table, Text,
    create_engine, delete, desc, insert, inspect, select, text, update,
)

_metadata = MetaData()
# Don't persist responses larger than this (bytes) to keep the DB sane.
_MAX_RESPONSE_BYTES = 8_000_000

runs = Table(
    "runs", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("endpoint", String(255)),
    Column("family", String(64)),
    Column("params", Text),
    Column("cost", Float),
    Column("status", String(16)),
    Column("created_at", DateTime),
    Column("workspace", String(128), nullable=True),
    Column("response", Text, nullable=True),
)

presets = Table(
    "presets", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255)),
    Column("family", String(64)),
    Column("endpoint", String(255)),
    Column("params", Text),
    Column("created_at", DateTime),
    Column("workspace", String(128), nullable=True),
)


@dataclass
class RunRecord:
    endpoint: str
    family: str
    params: dict
    cost: float
    status: str
    created_at: _dt.datetime
    id: int = 0
    has_response: bool = False


@dataclass
class PresetRecord:
    name: str
    family: str
    endpoint: str
    params: dict


class Store:
    def __init__(self, engine):
        self.engine = engine
        _metadata.create_all(engine)
        self._ensure_response_column()

    def _ensure_response_column(self) -> None:
        """Add the response column to pre-existing tables (idempotent migration)."""
        cols = {c["name"] for c in inspect(self.engine).get_columns("runs")}
        if "response" not in cols:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE runs ADD COLUMN response TEXT"))

    def add_run(self, endpoint: str, family: str, params: dict,
                cost: float, status: str, response: dict | None = None) -> None:
        response_json = None
        if response is not None:
            blob = json.dumps(response, default=str)
            if len(blob) <= _MAX_RESPONSE_BYTES:
                response_json = blob
        with self.engine.begin() as conn:
            conn.execute(insert(runs).values(
                endpoint=endpoint, family=family, params=json.dumps(params, default=str),
                cost=cost, status=status, created_at=_dt.datetime.now(_dt.UTC),
                response=response_json,
            ))

    def update_run(self, run_id: int, *, cost: float, status: str,
                   response: dict | None) -> None:
        """Overwrite a run's outcome in place (used when a pending task completes)."""
        response_json = None
        if response is not None:
            blob = json.dumps(response, default=str)
            if len(blob) <= _MAX_RESPONSE_BYTES:
                response_json = blob
        with self.engine.begin() as conn:
            conn.execute(update(runs).where(runs.c.id == run_id).values(
                cost=cost, status=status, response=response_json,
            ))

    def recent_runs(self, limit: int = 20) -> list[RunRecord]:
        # Exclude the (large) response body from the list query.
        cols = [runs.c.id, runs.c.endpoint, runs.c.family, runs.c.params,
                runs.c.cost, runs.c.status, runs.c.created_at,
                (runs.c.response.isnot(None)).label("has_response")]
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(*cols).order_by(desc(runs.c.id)).limit(limit)
            ).mappings().all()
        return [
            RunRecord(r["endpoint"], r["family"], json.loads(r["params"] or "{}"),
                      r["cost"], r["status"], r["created_at"],
                      id=r["id"], has_response=bool(r["has_response"]))
            for r in rows
        ]

    def load_response(self, run_id: int) -> dict | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(runs.c.response).where(runs.c.id == run_id)
            ).scalar_one_or_none()
        return json.loads(row) if row else None

    def save_preset(self, name: str, family: str, endpoint: str, params: dict) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(presets).where(presets.c.name == name))
            conn.execute(insert(presets).values(
                name=name, family=family, endpoint=endpoint,
                params=json.dumps(params, default=str), created_at=_dt.datetime.now(_dt.UTC),
            ))

    def list_presets(self) -> list[PresetRecord]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(presets).order_by(presets.c.name)
            ).mappings().all()
        return [
            PresetRecord(r["name"], r["family"], r["endpoint"],
                         json.loads(r["params"] or "{}"))
            for r in rows
        ]

    def load_preset(self, name: str) -> PresetRecord | None:
        return next((p for p in self.list_presets() if p.name == name), None)

    def delete_preset(self, name: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(delete(presets).where(presets.c.name == name))


def _build_engine():
    url = os.environ.get("DATABASE_URL")
    if url:
        # Railway gives postgres:// or postgresql://; SQLAlchemy's bare
        # postgresql:// dialect means psycopg2, but we ship psycopg v3,
        # so the URL must name the +psycopg driver explicitly.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return create_engine(url, future=True)
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return create_engine(f"sqlite:///{data_dir / 'seo_analyser.db'}", future=True)


@lru_cache(maxsize=1)
def default_store() -> Store:
    return Store(_build_engine())
