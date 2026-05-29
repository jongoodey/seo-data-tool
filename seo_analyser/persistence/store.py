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
    create_engine, delete, desc, insert, select,
)

_metadata = MetaData()

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

    def add_run(self, endpoint: str, family: str, params: dict,
                cost: float, status: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(insert(runs).values(
                endpoint=endpoint, family=family, params=json.dumps(params, default=str),
                cost=cost, status=status, created_at=_dt.datetime.now(_dt.UTC),
            ))

    def recent_runs(self, limit: int = 20) -> list[RunRecord]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(runs).order_by(desc(runs.c.id)).limit(limit)
            ).mappings().all()
        return [
            RunRecord(r["endpoint"], r["family"], json.loads(r["params"] or "{}"),
                      r["cost"], r["status"], r["created_at"])
            for r in rows
        ]

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
        # SQLAlchemy expects postgresql://, Railway sometimes gives postgres://
        url = url.replace("postgres://", "postgresql://", 1)
        return create_engine(url, future=True)
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    return create_engine(f"sqlite:///{data_dir / 'seo_analyser.db'}", future=True)


@lru_cache(maxsize=1)
def default_store() -> Store:
    return Store(_build_engine())
