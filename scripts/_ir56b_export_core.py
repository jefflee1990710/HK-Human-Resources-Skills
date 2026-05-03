#!/usr/bin/env python3
"""Export IR56B readiness workbook for manual completion."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "hrcore.db"
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


def out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))

FIELD_GUIDE = [
    {"field": "employee_no", "description": "Internal employee number"},
    {"field": "full_name", "description": "Employee full legal name"},
    {"field": "email", "description": "Primary email"},
    {"field": "hire_date", "description": "Join date YYYY-MM-DD"},
    {"field": "employment_status", "description": "active/on_leave/terminated/probation"},
    {"field": "date_of_birth", "description": "Date of birth YYYY-MM-DD"},
    {"field": "hkid", "description": "HKID if available"},
    {"field": "passport_no", "description": "Passport number if no HKID"},
    {"field": "address_1", "description": "Residential address line 1"},
    {"field": "address_2", "description": "Residential address line 2"},
    {"field": "address_3", "description": "Residential address line 3"},
    {"field": "address_area_code", "description": "Area code for residential address"},
    {"field": "contact_address_1", "description": "Contact address line 1"},
    {"field": "contact_address_2", "description": "Contact address line 2"},
    {"field": "contact_address_3", "description": "Contact address line 3"},
    {"field": "contact_area_code", "description": "Area code for contact address"},
    {"field": "place_of_birth", "description": "Place of birth"},
    {"field": "marital_status", "description": "Single/Married/Widowed/Divorced"},
    {"field": "spouse_name", "description": "Spouse name for tax declaration"},
    {"field": "spouse_hkid", "description": "Spouse HKID"},
    {"field": "spouse_passport_no", "description": "Spouse passport number"},
]


def _fetch_rows(employee_no: str | None = None) -> tuple[list[dict], list[dict]]:
    conn = connect()
    try:
        params = []
        where = ""
        if employee_no:
            where = "WHERE e.employee_no = ?"
            params.append(employee_no)
        cur = conn.execute(
            f"""
            SELECT
              e.employee_no,
              e.full_name,
              e.email,
              e.hire_date,
              e.employment_status,
              e.date_of_birth,
              coalesce(r.hkid, '') AS hkid,
              coalesce(r.passport_no, '') AS passport_no,
              coalesce(nullif(r.address_1, ''), nullif(e.residential_address, ''), '') AS address_1,
              coalesce(r.address_2, '') AS address_2,
              coalesce(r.address_3, '') AS address_3,
              coalesce(r.address_area_code, '') AS address_area_code,
              coalesce(r.contact_address_1, '') AS contact_address_1,
              coalesce(r.contact_address_2, '') AS contact_address_2,
              coalesce(r.contact_address_3, '') AS contact_address_3,
              coalesce(r.contact_area_code, '') AS contact_area_code,
              coalesce(r.place_of_birth, '') AS place_of_birth,
              coalesce(r.marital_status, '') AS marital_status,
              coalesce(r.spouse_name, '') AS spouse_name,
              coalesce(r.spouse_hkid, '') AS spouse_hkid,
              coalesce(r.spouse_passport_no, '') AS spouse_passport_no
            FROM employee e
            LEFT JOIN employee_ir56b r ON r.employee_no = e.employee_no
            {where}
            ORDER BY e.employee_no
            """,
            tuple(params),
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    missing_rows: list[dict] = []
    for row in rows:
        missing = []
        if not row.get("full_name"):
            missing.append("full_name")
        if not row.get("email"):
            missing.append("email")
        if not row.get("hire_date"):
            missing.append("hire_date")
        if not row.get("date_of_birth"):
            missing.append("date_of_birth")
        if not (row.get("hkid") or row.get("passport_no")):
            missing.append("hkid_or_passport")
        if not row.get("address_1"):
            missing.append("address_1")
        if not row.get("address_area_code"):
            missing.append("address_area_code")
        if missing:
            missing_rows.append(
                {
                    "employee_no": row.get("employee_no"),
                    "full_name": row.get("full_name"),
                    "missing_fields": ", ".join(missing),
                }
            )

    return rows, missing_rows


def cmd_export(ns: argparse.Namespace) -> int:
    rows, missing_rows = _fetch_rows(ns.employee_no)
    output_path = Path(ns.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Current")
        pd.DataFrame(missing_rows).to_excel(writer, index=False, sheet_name="Missing")
        pd.DataFrame(FIELD_GUIDE).to_excel(writer, index=False, sheet_name="Field guide")

    out(
        {
            "ok": True,
            "output": str(output_path),
            "rows": len(rows),
            "rows_missing_fields": len(missing_rows),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Apply all schemas")
    export = sub.add_parser("export-xlsx", help="Export IR56B workbook")
    export.add_argument("--employee-no", help="Optional single employee export")
    export.add_argument(
        "--output",
        default="output/ir56b_fill_template.xlsx",
        help="Output xlsx path",
    )
    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    if ns.command == "init":
        apply_all_schemas()
        out({"ok": True, "message": "schema applied"})
        return 0
    if ns.command == "export-xlsx":
        return cmd_export(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
