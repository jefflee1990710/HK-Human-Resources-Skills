#!/usr/bin/env python3
"""Employment compliance records CLI."""

from __future__ import annotations

import argparse
import sqlite3
from typing import Any

from hkhr_sqlite import apply_all_schemas, connect, now_utc_iso, out, parse_json_arg, row_to_dict

ALLOWED_RECORD_TYPES = {"contract", "work_eligibility", "other"}


def _normalize_record_type(raw: Any) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value not in ALLOWED_RECORD_TYPES:
        return None
    return value


def cmd_create(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    employee_no = payload.get("employee_no") or ns.employee_no
    title = payload.get("title") or ns.title
    record_type = _normalize_record_type(payload.get("record_type") or ns.record_type)
    if not employee_no or not title or record_type is None:
        out(
            {
                "ok": False,
                "error": "employee_no, title, record_type are required; record_type must be contract|work_eligibility|other",
            }
        )
        return 1

    fields = {
        "employee_no": str(employee_no).strip(),
        "record_type": record_type,
        "title": str(title).strip(),
        "start_date": payload.get("start_date") or ns.start_date,
        "end_date": payload.get("end_date") or ns.end_date,
        "reference_no": payload.get("reference_no") or ns.reference_no,
        "country": payload.get("country") or ns.country,
        "remarks": payload.get("remarks") or ns.remarks,
        "updated_at": now_utc_iso(),
    }

    conn = connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO employment_compliance (
              employee_no, record_type, title, start_date, end_date,
              reference_no, country, remarks, updated_at
            ) VALUES (
              :employee_no, :record_type, :title, :start_date, :end_date,
              :reference_no, :country, :remarks, :updated_at
            )
            """,
            fields,
        )
        conn.commit()
        created_id = cur.lastrowid
        cur = conn.execute("SELECT * FROM employment_compliance WHERE id = ?", (created_id,))
        record = row_to_dict(cur.fetchone())
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "record": record})
    return 0


def cmd_get(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM employment_compliance WHERE id = ?", (ns.id,))
        record = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "record": record})
    return 0


def cmd_list(ns: argparse.Namespace) -> int:
    where = []
    params: list[Any] = []
    if ns.employee_no:
        where.append("employee_no = ?")
        params.append(ns.employee_no)
    if ns.record_type:
        record_type = _normalize_record_type(ns.record_type)
        if record_type is None:
            out({"ok": False, "error": "invalid --record-type"})
            return 1
        where.append("record_type = ?")
        params.append(record_type)

    query = "SELECT * FROM employment_compliance"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY coalesce(end_date, ''), id LIMIT ?"
    params.append(ns.limit)

    conn = connect()
    try:
        cur = conn.execute(query, tuple(params))
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "records": rows})
    return 0


def cmd_update(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    updates: dict[str, Any] = {}
    for key in ("employee_no", "title", "start_date", "end_date", "reference_no", "country", "remarks"):
        if key in payload and payload[key] is not None:
            updates[key] = payload[key]
        else:
            value = getattr(ns, key)
            if value is not None:
                updates[key] = value

    record_type_val = payload.get("record_type") if "record_type" in payload else ns.record_type
    if record_type_val is not None:
        record_type = _normalize_record_type(record_type_val)
        if record_type is None:
            out({"ok": False, "error": "record_type must be contract|work_eligibility|other"})
            return 1
        updates["record_type"] = record_type

    if not updates:
        out({"ok": False, "error": "no fields to update"})
        return 1
    updates["updated_at"] = now_utc_iso()

    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    params = list(updates.values()) + [ns.id]
    conn = connect()
    try:
        cur = conn.execute(f"UPDATE employment_compliance SET {set_clause} WHERE id = ?", params)
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "id not found"})
            return 1
        cur = conn.execute("SELECT * FROM employment_compliance WHERE id = ?", (ns.id,))
        record = row_to_dict(cur.fetchone())
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "record": record})
    return 0


def cmd_delete(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM employment_compliance WHERE id = ?", (ns.id,))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "id not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_id": ns.id})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Apply all schemas")

    create = sub.add_parser("create", help="Create compliance record")
    create.add_argument("--json")
    create.add_argument("--json-file")
    create.add_argument("--employee-no")
    create.add_argument("--record-type")
    create.add_argument("--title")
    create.add_argument("--start-date")
    create.add_argument("--end-date")
    create.add_argument("--reference-no")
    create.add_argument("--country")
    create.add_argument("--remarks")

    get = sub.add_parser("get", help="Get by id")
    get.add_argument("id", type=int)

    listing = sub.add_parser("list", help="List records")
    listing.add_argument("--employee-no")
    listing.add_argument("--record-type")
    listing.add_argument("--limit", type=int, default=200)

    update = sub.add_parser("update", help="Update by id")
    update.add_argument("id", type=int)
    update.add_argument("--json")
    update.add_argument("--json-file")
    update.add_argument("--employee-no")
    update.add_argument("--record-type")
    update.add_argument("--title")
    update.add_argument("--start-date")
    update.add_argument("--end-date")
    update.add_argument("--reference-no")
    update.add_argument("--country")
    update.add_argument("--remarks")

    delete = sub.add_parser("delete", help="Delete by id")
    delete.add_argument("id", type=int)
    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    if ns.command == "init":
        apply_all_schemas()
        out({"ok": True, "message": "schema applied"})
        return 0
    if ns.command == "create":
        return cmd_create(ns)
    if ns.command == "get":
        return cmd_get(ns)
    if ns.command == "list":
        return cmd_list(ns)
    if ns.command == "update":
        return cmd_update(ns)
    if ns.command == "delete":
        return cmd_delete(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
