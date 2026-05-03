#!/usr/bin/env python3
"""IR56B profile extension CLI and readiness checker."""

from __future__ import annotations

import argparse
import sqlite3
from typing import Any

from hkhr_sqlite import apply_all_schemas, connect, now_utc_iso, out, parse_json_arg, row_to_dict

IR56B_FIELDS = [
    "employee_no",
    "hkid",
    "passport_no",
    "place_of_birth",
    "marital_status",
    "address_1",
    "address_2",
    "address_3",
    "address_area_code",
    "contact_address_1",
    "contact_address_2",
    "contact_address_3",
    "contact_area_code",
    "spouse_name",
    "spouse_hkid",
    "spouse_passport_no",
    "notes",
]

READINESS_REQUIRED = [
    "employee_no",
    "full_name",
    "email",
    "hire_date",
    "employment_status",
    "date_of_birth",
    "hkid_or_passport",
    "address_1",
    "address_area_code",
]


def _coalesce_str(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text != "":
            return text
    return None


def _get_combined_profile(employee_no: str) -> dict[str, Any] | None:
    conn = connect()
    try:
        cur = conn.execute(
            """
            SELECT
              e.employee_no,
              e.full_name,
              e.email,
              e.hire_date,
              e.employment_status,
              e.date_of_birth,
              e.nationality,
              e.residential_address,
              r.hkid,
              r.passport_no,
              r.place_of_birth,
              r.marital_status,
              r.address_1,
              r.address_2,
              r.address_3,
              r.address_area_code,
              r.contact_address_1,
              r.contact_address_2,
              r.contact_address_3,
              r.contact_area_code,
              r.spouse_name,
              r.spouse_hkid,
              r.spouse_passport_no,
              r.notes
            FROM employee e
            LEFT JOIN employee_ir56b r ON r.employee_no = e.employee_no
            WHERE e.employee_no = ?
            """,
            (employee_no,),
        )
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    return row


def cmd_upsert(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    employee_no = _coalesce_str(payload.get("employee_no"), ns.employee_no)
    if employee_no is None:
        out({"ok": False, "error": "employee_no is required"})
        return 1
    fields = {k: payload.get(k) for k in IR56B_FIELDS if k != "employee_no"}
    for key in fields:
        if fields[key] is None and hasattr(ns, key):
            fields[key] = getattr(ns, key)
    fields["employee_no"] = employee_no
    fields["updated_at"] = now_utc_iso()

    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO employee_ir56b (
              employee_no, hkid, passport_no, place_of_birth, marital_status,
              address_1, address_2, address_3, address_area_code,
              contact_address_1, contact_address_2, contact_address_3, contact_area_code,
              spouse_name, spouse_hkid, spouse_passport_no, notes, updated_at
            ) VALUES (
              :employee_no, :hkid, :passport_no, :place_of_birth, :marital_status,
              :address_1, :address_2, :address_3, :address_area_code,
              :contact_address_1, :contact_address_2, :contact_address_3, :contact_area_code,
              :spouse_name, :spouse_hkid, :spouse_passport_no, :notes, :updated_at
            )
            ON CONFLICT(employee_no) DO UPDATE SET
              hkid = excluded.hkid,
              passport_no = excluded.passport_no,
              place_of_birth = excluded.place_of_birth,
              marital_status = excluded.marital_status,
              address_1 = excluded.address_1,
              address_2 = excluded.address_2,
              address_3 = excluded.address_3,
              address_area_code = excluded.address_area_code,
              contact_address_1 = excluded.contact_address_1,
              contact_address_2 = excluded.contact_address_2,
              contact_address_3 = excluded.contact_address_3,
              contact_area_code = excluded.contact_area_code,
              spouse_name = excluded.spouse_name,
              spouse_hkid = excluded.spouse_hkid,
              spouse_passport_no = excluded.spouse_passport_no,
              notes = excluded.notes,
              updated_at = excluded.updated_at
            """,
            fields,
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()

    profile = _get_combined_profile(employee_no)
    out({"ok": True, "profile": profile})
    return 0


def cmd_get(ns: argparse.Namespace) -> int:
    profile = _get_combined_profile(ns.employee_no)
    out({"ok": True, "profile": profile})
    return 0


def cmd_delete(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM employee_ir56b WHERE employee_no = ?", (ns.employee_no,))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "employee_no not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_employee_no": ns.employee_no})
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            """
            SELECT e.employee_no, e.full_name, e.email, e.hire_date, e.employment_status,
                   r.hkid, r.passport_no, r.address_1, r.address_area_code, r.updated_at
            FROM employee e
            LEFT JOIN employee_ir56b r ON r.employee_no = e.employee_no
            ORDER BY e.employee_no
            LIMIT ?
            """,
            (ns.limit,),
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "profiles": rows})
    return 0


def cmd_readiness(ns: argparse.Namespace) -> int:
    profile = _get_combined_profile(ns.employee_no)
    if profile is None:
        out({"ok": False, "error": "employee_no not found"})
        return 1

    missing: list[str] = []
    if not _coalesce_str(profile.get("employee_no")):
        missing.append("employee_no")
    if not _coalesce_str(profile.get("full_name")):
        missing.append("full_name")
    if not _coalesce_str(profile.get("email")):
        missing.append("email")
    if not _coalesce_str(profile.get("hire_date")):
        missing.append("hire_date")
    if not _coalesce_str(profile.get("employment_status")):
        missing.append("employment_status")
    if not _coalesce_str(profile.get("date_of_birth")):
        missing.append("date_of_birth")
    if not (_coalesce_str(profile.get("hkid")) or _coalesce_str(profile.get("passport_no"))):
        missing.append("hkid_or_passport")
    if not _coalesce_str(profile.get("address_1"), profile.get("residential_address")):
        missing.append("address_1")
    if not _coalesce_str(profile.get("address_area_code")):
        missing.append("address_area_code")

    out(
        {
            "ok": True,
            "employee_no": ns.employee_no,
            "ready": len(missing) == 0,
            "missing_fields": missing,
            "required_fields": READINESS_REQUIRED,
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Apply all schemas")

    upsert = sub.add_parser("upsert", help="Create/update employee IR56B extension")
    upsert.add_argument("--json")
    upsert.add_argument("--json-file")
    upsert.add_argument("--employee-no")
    for field in IR56B_FIELDS:
        if field != "employee_no":
            upsert.add_argument(f"--{field.replace('_', '-')}", dest=field)

    get = sub.add_parser("get", help="Get combined employee + IR56B profile")
    get.add_argument("employee_no")

    delete = sub.add_parser("delete", help="Delete IR56B extension by employee_no")
    delete.add_argument("employee_no")

    listing = sub.add_parser("list", help="List basic IR56B profiles")
    listing.add_argument("--limit", type=int, default=500)

    readiness = sub.add_parser("readiness", help="Check IR56B required fields")
    readiness.add_argument("employee_no")
    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    if ns.command == "init":
        apply_all_schemas()
        out({"ok": True, "message": "schema applied"})
        return 0
    if ns.command == "upsert":
        return cmd_upsert(ns)
    if ns.command == "get":
        return cmd_get(ns)
    if ns.command == "delete":
        return cmd_delete(ns)
    if ns.command == "list":
        return cmd_list(ns)
    if ns.command == "readiness":
        return cmd_readiness(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
