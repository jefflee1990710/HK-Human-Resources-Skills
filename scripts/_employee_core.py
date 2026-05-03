#!/usr/bin/env python3
"""SQLite employee database CLI for AI and operator use.

Commands mirror common operations: init, create, get-by-no, get-by-email,
search, update, delete, list.

Default DB path: ~/.hkhrcore/hrcore.db
Override: EMPLOYEE_DB_PATH=/path/to/hrcore.db
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

ALLOWED_STATUS = {"active", "on_leave", "terminated", "probation"}
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = Path.home() / ".hkhrcore" / "hrcore.db"
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


def out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_init(_: argparse.Namespace) -> int:
    path = get_db_path()
    apply_all_schemas()
    out({"ok": True, "database": str(path), "message": "schema applied"})
    return 0


def cmd_create(ns: argparse.Namespace) -> int:
    payload = _load_json_payload(ns)
    employee_no = payload.get("employee_no") or ns.employee_no
    full_name = payload.get("full_name") or ns.full_name
    if not employee_no or not full_name:
        out({"ok": False, "error": "employee_no and full_name are required"})
        return 1

    status = _normalize_status(payload.get("employment_status") or ns.employment_status)
    if status is None:
        out({"ok": False, "error": f"employment_status must be one of {sorted(ALLOWED_STATUS)}"})
        return 1

    fields = {
        "employee_no": str(employee_no).strip(),
        "full_name": str(full_name).strip(),
        "preferred_name": _opt_str(payload, ns, "preferred_name"),
        "email": _opt_str(payload, ns, "email"),
        "work_mobile": _opt_str(payload, ns, "work_mobile"),
        "personal_mobile": _opt_str(payload, ns, "personal_mobile"),
        "date_of_birth": _opt_str(payload, ns, "date_of_birth"),
        "nationality": _opt_str(payload, ns, "nationality"),
        "residential_address": _opt_str(payload, ns, "residential_address"),
        "department": _opt_str(payload, ns, "department"),
        "job_title": _opt_str(payload, ns, "job_title"),
        "hire_date": _opt_str(payload, ns, "hire_date"),
        "employment_status": status,
        "notes": _opt_str(payload, ns, "notes"),
    }

    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO employee (
              employee_no, full_name, preferred_name, email, work_mobile, personal_mobile,
              date_of_birth, nationality, residential_address, department, job_title,
              hire_date, employment_status, notes
            ) VALUES (
              :employee_no, :full_name, :preferred_name, :email, :work_mobile, :personal_mobile,
              :date_of_birth, :nationality, :residential_address, :department, :job_title,
              :hire_date, :employment_status, :notes
            )
            """,
            fields,
        )
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()

    employee = get_employee_by_id(new_id)
    out({"ok": True, "employee": employee})
    return 0


def _load_json_payload(ns: argparse.Namespace) -> dict[str, Any]:
    if ns.json:
        return json.loads(ns.json)
    if ns.json_file:
        return json.loads(Path(ns.json_file).read_text(encoding="utf-8"))
    return {}


def _opt_str(payload: dict, ns: argparse.Namespace, key: str) -> str | None:
    v = payload.get(key)
    if v is None and hasattr(ns, key):
        v = getattr(ns, key)
    if v is None or v == "":
        return None
    return str(v).strip()


def _normalize_status(raw: Any) -> str | None:
    v = raw if raw not in (None, "") else "active"
    s = str(v).strip().lower().replace(" ", "_")
    if s not in ALLOWED_STATUS:
        return None
    return s


def get_employee_by_id(row_id: int) -> dict[str, Any] | None:
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM employee WHERE id = ?", (row_id,))
        return row_to_dict(cur.fetchone())
    finally:
        conn.close()


def cmd_get_by_no(ns: argparse.Namespace) -> int:
    no = ns.employee_no.strip()
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM employee WHERE employee_no = ?", (no,))
        emp = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "employee": emp})
    return 0


def cmd_get_by_email(ns: argparse.Namespace) -> int:
    email = ns.email.strip().lower()
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM employee WHERE lower(email) = ?", (email,))
        emp = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "employee": emp})
    return 0


def cmd_search(ns: argparse.Namespace) -> int:
    q = f"%{ns.query.strip()}%"
    conn = connect()
    try:
        cur = conn.execute(
            """
            SELECT * FROM employee
            WHERE employee_no LIKE :q OR full_name LIKE :q OR ifnull(preferred_name,'') LIKE :q
               OR ifnull(email,'') LIKE :q OR ifnull(work_mobile,'') LIKE :q
               OR ifnull(personal_mobile,'') LIKE :q OR ifnull(department,'') LIKE :q
               OR ifnull(job_title,'') LIKE :q
            ORDER BY employee_no
            LIMIT :lim
            """,
            {"q": q, "lim": ns.limit},
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "employees": rows})
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT * FROM employee ORDER BY employee_no LIMIT ?",
            (ns.limit,),
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "employees": rows})
    return 0


def cmd_update(ns: argparse.Namespace) -> int:
    payload = _load_json_payload(ns)
    employee_no = payload.get("employee_no") or ns.employee_no
    if not employee_no:
        out({"ok": False, "error": "employee_no required to identify row"})
        return 1

    updates: dict[str, Any] = {}
    for key in (
        "full_name",
        "preferred_name",
        "email",
        "work_mobile",
        "personal_mobile",
        "date_of_birth",
        "nationality",
        "residential_address",
        "department",
        "job_title",
        "hire_date",
        "employment_status",
        "notes",
    ):
        if key in payload and payload[key] is not None:
            updates[key] = payload[key]
        elif hasattr(ns, key):
            val = getattr(ns, key)
            if val is not None:
                updates[key] = val

    if "employment_status" in updates:
        s = _normalize_status(updates["employment_status"])
        if s is None:
            out({"ok": False, "error": f"employment_status must be one of {sorted(ALLOWED_STATUS)}"})
            return 1
        updates["employment_status"] = s

    if not updates:
        out({"ok": False, "error": "no fields to update"})
        return 1

    updates["updated_at"] = now_utc_iso()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [str(employee_no).strip()]

    conn = connect()
    try:
        cur = conn.execute(
            f"UPDATE employee SET {set_clause} WHERE employee_no = ?",
            values[:],
        )
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "employee_no not found"})
            return 1
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()

    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM employee WHERE employee_no = ?", (str(employee_no).strip(),))
        emp = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "employee": emp})
    return 0


def cmd_delete(ns: argparse.Namespace) -> int:
    no = ns.employee_no.strip()
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM employee WHERE employee_no = ?", (no,))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "employee_no not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_employee_no": no})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create DB file and apply schema")

    pc = sub.add_parser("create", help="createEmployee — insert row")
    pc.add_argument("--json", dest="json", help="JSON object with fields")
    pc.add_argument("--json-file", dest="json_file", help="Path to JSON file")
    pc.add_argument("--employee-no", dest="employee_no")
    pc.add_argument("--full-name", dest="full_name")
    pc.add_argument("--preferred-name", dest="preferred_name")
    pc.add_argument("--email", dest="email")
    pc.add_argument("--work-mobile", dest="work_mobile")
    pc.add_argument("--personal-mobile", dest="personal_mobile")
    pc.add_argument("--date-of-birth", dest="date_of_birth")
    pc.add_argument("--nationality", dest="nationality")
    pc.add_argument("--residential-address", dest="residential_address")
    pc.add_argument("--department", dest="department")
    pc.add_argument("--job-title", dest="job_title")
    pc.add_argument("--hire-date", dest="hire_date")
    pc.add_argument(
        "--employment-status",
        dest="employment_status",
        default="active",
        help="active|on_leave|terminated|probation",
    )
    pc.add_argument("--notes", dest="notes")

    pg = sub.add_parser("get-by-no", help="getEmployeeByEmployeeNo")
    pg.add_argument("employee_no", type=str)

    pe = sub.add_parser("get-by-email", help="getEmployeeByEmail")
    pe.add_argument("email", type=str)

    ps = sub.add_parser("search", help="searchEmployee — substring match")
    ps.add_argument("query", type=str)
    ps.add_argument("--limit", type=int, default=200)

    pl = sub.add_parser("list", help="List employees (ordered by employee_no)")
    pl.add_argument("--limit", type=int, default=500)

    pu = sub.add_parser("update", help="updateEmployee — patch by employee_no")
    pu.add_argument("--json", dest="json", help="JSON object with fields to set")
    pu.add_argument("--json-file", dest="json_file")
    pu.add_argument("--employee-no", dest="employee_no", required=False)
    pu.add_argument("--full-name", dest="full_name")
    pu.add_argument("--preferred-name", dest="preferred_name")
    pu.add_argument("--email", dest="email")
    pu.add_argument("--work-mobile", dest="work_mobile")
    pu.add_argument("--personal-mobile", dest="personal_mobile")
    pu.add_argument("--date-of-birth", dest="date_of_birth")
    pu.add_argument("--nationality", dest="nationality")
    pu.add_argument("--residential-address", dest="residential_address")
    pu.add_argument("--department", dest="department")
    pu.add_argument("--job-title", dest="job_title")
    pu.add_argument("--hire-date", dest="hire_date")
    pu.add_argument("--employment-status", dest="employment_status")
    pu.add_argument("--notes", dest="notes")

    pd = sub.add_parser("delete", help="deleteEmployee")
    pd.add_argument("employee_no", type=str)

    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()

    if ns.command == "init":
        return cmd_init(ns)
    if ns.command == "create":
        return cmd_create(ns)
    if ns.command == "get-by-no":
        return cmd_get_by_no(ns)
    if ns.command == "get-by-email":
        return cmd_get_by_email(ns)
    if ns.command == "search":
        return cmd_search(ns)
    if ns.command == "list":
        return cmd_list(ns)
    if ns.command == "update":
        return cmd_update(ns)
    if ns.command == "delete":
        return cmd_delete(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON: {e}"}), file=sys.stderr)
        raise SystemExit(1)
