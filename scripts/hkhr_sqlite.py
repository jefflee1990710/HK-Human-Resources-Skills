#!/usr/bin/env python3
"""Shared SQLite utilities for hkhr-skills scripts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "employees.db"
SCHEMA_FILES = [
    REPO_ROOT / "schema" / "employee.sql",
    REPO_ROOT / "schema" / "employee_ir56b.sql",
    REPO_ROOT / "schema" / "lifecycle.sql",
    REPO_ROOT / "schema" / "compliance.sql",
    REPO_ROOT / "schema" / "leave.sql",
]


def get_db_path() -> Path:
    override = os.environ.get("EMPLOYEE_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_all_schemas() -> None:
    conn = connect()
    try:
        for schema_file in SCHEMA_FILES:
            sql = schema_file.read_text(encoding="utf-8")
            conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(r) for r in rows if r is not None]


def parse_json_arg(json_text: str | None, json_file: str | None) -> dict[str, Any]:
    if json_text:
        return json.loads(json_text)
    if json_file:
        return json.loads(Path(json_file).read_text(encoding="utf-8"))
    return {}


def parse_bool(raw: Any, default: bool = False) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))
