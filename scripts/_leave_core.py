#!/usr/bin/env python3
"""Leave types and leave applications SQLite CLI."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

LEAVE_UNITS = {"Day", "Hour"}
SECTIONS = {"AM", "PM"}
LEAVE_STATUSES = {"Pending", "Approved", "Rejected", "Cancelled"}
COM_LEAVE_STATUSES = {"Pending", "Approved", "Rejected"}
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

DEFAULT_LEAVE_TYPES = [
    {
        "leave_type_no": "AL",
        "name": "Annual Leave",
        "description": "General annual leave",
        "leave_unit": "Day",
        "can_apply": True,
        "paid": True,
        "paid_ratio": 100,
        "allow_negative_balance": False,
        "reason_required": False,
        "attachment_required": False,
    },
    {
        "leave_type_no": "SL",
        "name": "Sick Leave",
        "description": "Medical sick leave",
        "leave_unit": "Day",
        "can_apply": True,
        "paid": True,
        "paid_ratio": 80,
        "allow_negative_balance": False,
        "reason_required": True,
        "attachment_required": True,
    },
]


def _enum(value: Any, allowed: set[str], name: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text not in allowed:
        return None
    return text


def _json_array(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    text = str(value).strip()
    if text == "":
        return None
    if text.startswith("["):
        return text
    return json.dumps([text], ensure_ascii=False)


def cmd_seed_default_types(_: argparse.Namespace) -> int:
    conn = connect()
    try:
        for item in DEFAULT_LEAVE_TYPES:
            conn.execute(
                """
                INSERT INTO leave_type (
                  leave_type_no, name, description, leave_unit, can_apply, paid, paid_ratio,
                  allow_negative_balance, reason_required, attachment_required, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(leave_type_no) DO UPDATE SET
                  name = excluded.name,
                  description = excluded.description,
                  leave_unit = excluded.leave_unit,
                  can_apply = excluded.can_apply,
                  paid = excluded.paid,
                  paid_ratio = excluded.paid_ratio,
                  allow_negative_balance = excluded.allow_negative_balance,
                  reason_required = excluded.reason_required,
                  attachment_required = excluded.attachment_required,
                  updated_at = excluded.updated_at
                """,
                (
                    item["leave_type_no"],
                    item["name"],
                    item["description"],
                    item["leave_unit"],
                    int(item["can_apply"]),
                    int(item["paid"]),
                    item["paid_ratio"],
                    int(item["allow_negative_balance"]),
                    int(item["reason_required"]),
                    int(item["attachment_required"]),
                    now_utc_iso(),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    out({"ok": True, "seeded": len(DEFAULT_LEAVE_TYPES)})
    return 0


def cmd_leave_type_upsert(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    leave_type_no = payload.get("leave_type_no") or ns.leave_type_no
    name = payload.get("name") or ns.name
    description = payload.get("description") or ns.description
    leave_unit = _enum(payload.get("leave_unit") or ns.leave_unit, LEAVE_UNITS, "leave_unit")
    if not leave_type_no or not name or not description or leave_unit is None:
        out({"ok": False, "error": "leave_type_no, name, description, leave_unit(Day|Hour) are required"})
        return 1
    fields = {
        "leave_type_no": str(leave_type_no).strip(),
        "name": str(name).strip(),
        "description": str(description).strip(),
        "leave_unit": leave_unit,
        "color": payload.get("color") or ns.color,
        "can_apply": int(parse_bool(payload.get("can_apply", ns.can_apply), True)),
        "paid": int(parse_bool(payload.get("paid", ns.paid), False)),
        "paid_ratio": payload.get("paid_ratio", ns.paid_ratio),
        "enable_paid_function": payload.get("enable_paid_function", ns.enable_paid_function),
        "paid_function": payload.get("paid_function") or ns.paid_function,
        "allow_negative_balance": int(parse_bool(payload.get("allow_negative_balance", ns.allow_negative_balance), False)),
        "reason_required": int(parse_bool(payload.get("reason_required", ns.reason_required), False)),
        "attachment_required": int(parse_bool(payload.get("attachment_required", ns.attachment_required), False)),
        "updated_at": now_utc_iso(),
    }
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO leave_type (
              leave_type_no, name, description, leave_unit, color, can_apply, paid, paid_ratio,
              enable_paid_function, paid_function, allow_negative_balance, reason_required,
              attachment_required, updated_at
            ) VALUES (
              :leave_type_no, :name, :description, :leave_unit, :color, :can_apply, :paid, :paid_ratio,
              :enable_paid_function, :paid_function, :allow_negative_balance, :reason_required,
              :attachment_required, :updated_at
            )
            ON CONFLICT(leave_type_no) DO UPDATE SET
              name = excluded.name,
              description = excluded.description,
              leave_unit = excluded.leave_unit,
              color = excluded.color,
              can_apply = excluded.can_apply,
              paid = excluded.paid,
              paid_ratio = excluded.paid_ratio,
              enable_paid_function = excluded.enable_paid_function,
              paid_function = excluded.paid_function,
              allow_negative_balance = excluded.allow_negative_balance,
              reason_required = excluded.reason_required,
              attachment_required = excluded.attachment_required,
              updated_at = excluded.updated_at
            """,
            fields,
        )
        conn.commit()
        cur = conn.execute("SELECT * FROM leave_type WHERE leave_type_no = ?", (fields["leave_type_no"],))
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "leave_type": row})
    return 0


def cmd_leave_type_get(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM leave_type WHERE leave_type_no = ?", (ns.leave_type_no,))
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "leave_type": row})
    return 0


def cmd_leave_type_list(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM leave_type ORDER BY leave_type_no LIMIT ?", (ns.limit,))
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "leave_types": rows})
    return 0


def cmd_leave_type_delete(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM leave_type WHERE leave_type_no = ?", (ns.leave_type_no,))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "leave_type_no not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_leave_type_no": ns.leave_type_no})
    return 0


def _leave_application_payload(ns: argparse.Namespace) -> tuple[dict[str, Any] | None, str | None]:
    payload = parse_json_arg(ns.json, ns.json_file)
    fields = {
        "application_no": payload.get("application_no") or ns.application_no,
        "employee_no": payload.get("employee_no") or ns.employee_no,
        "leave_type_no": payload.get("leave_type_no") or ns.leave_type_no,
        "application_ts": payload.get("application_ts") or ns.application_ts or now_utc_iso(),
        "from_date": payload.get("from_date") or ns.from_date,
        "to_date": payload.get("to_date") or ns.to_date,
        "from_section": _enum(payload.get("from_section") or ns.from_section, SECTIONS, "from_section"),
        "to_section": _enum(payload.get("to_section") or ns.to_section, SECTIONS, "to_section"),
        "no_of_days": payload.get("no_of_days", ns.no_of_days),
        "reason": payload.get("reason") or ns.reason,
        "attachment_filenames": _json_array(payload.get("attachment_filenames", ns.attachment_filenames)),
        "next_approver": payload.get("next_approver") or ns.next_approver,
        "next_approve_level": payload.get("next_approve_level", ns.next_approve_level if ns.next_approve_level else 1),
        "total_approve_level": payload.get("total_approve_level", ns.total_approve_level if ns.total_approve_level else 1),
        "approved_ts": payload.get("approved_ts") or ns.approved_ts,
        "rejected_ts": payload.get("rejected_ts") or ns.rejected_ts,
        "cancelled_ts": payload.get("cancelled_ts") or ns.cancelled_ts,
        "status": _enum(payload.get("status") or ns.status, LEAVE_STATUSES, "status"),
        "updated_at": now_utc_iso(),
    }
    required = ("application_no", "employee_no", "leave_type_no", "from_date", "to_date", "from_section", "to_section", "status")
    for key in required:
        if not fields[key]:
            return None, f"missing required field: {key}"
    return fields, None


def cmd_application_upsert(ns: argparse.Namespace) -> int:
    fields, error = _leave_application_payload(ns)
    if error:
        out({"ok": False, "error": error})
        return 1
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO leave_application (
              application_no, employee_no, leave_type_no, application_ts, from_date, to_date,
              from_section, to_section, no_of_days, reason, attachment_filenames, next_approver,
              next_approve_level, total_approve_level, approved_ts, rejected_ts, cancelled_ts,
              status, updated_at
            ) VALUES (
              :application_no, :employee_no, :leave_type_no, :application_ts, :from_date, :to_date,
              :from_section, :to_section, :no_of_days, :reason, :attachment_filenames, :next_approver,
              :next_approve_level, :total_approve_level, :approved_ts, :rejected_ts, :cancelled_ts,
              :status, :updated_at
            )
            ON CONFLICT(application_no) DO UPDATE SET
              employee_no = excluded.employee_no,
              leave_type_no = excluded.leave_type_no,
              application_ts = excluded.application_ts,
              from_date = excluded.from_date,
              to_date = excluded.to_date,
              from_section = excluded.from_section,
              to_section = excluded.to_section,
              no_of_days = excluded.no_of_days,
              reason = excluded.reason,
              attachment_filenames = excluded.attachment_filenames,
              next_approver = excluded.next_approver,
              next_approve_level = excluded.next_approve_level,
              total_approve_level = excluded.total_approve_level,
              approved_ts = excluded.approved_ts,
              rejected_ts = excluded.rejected_ts,
              cancelled_ts = excluded.cancelled_ts,
              status = excluded.status,
              updated_at = excluded.updated_at
            """,
            fields,
        )
        conn.commit()
        cur = conn.execute("SELECT * FROM leave_application WHERE application_no = ?", (fields["application_no"],))
        row = row_to_dict(cur.fetchone())
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "application": row})
    return 0


def cmd_application_get(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM leave_application WHERE application_no = ?", (ns.application_no,))
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "application": row})
    return 0


def cmd_application_list(ns: argparse.Namespace) -> int:
    where = []
    params: list[Any] = []
    if ns.employee_no:
        where.append("employee_no = ?")
        params.append(ns.employee_no)
    if ns.status:
        status = _enum(ns.status, LEAVE_STATUSES, "status")
        if status is None:
            out({"ok": False, "error": "invalid status"})
            return 1
        where.append("status = ?")
        params.append(status)
    query = "SELECT * FROM leave_application"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY application_ts DESC LIMIT ?"
    params.append(ns.limit)
    conn = connect()
    try:
        cur = conn.execute(query, tuple(params))
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "applications": rows})
    return 0


def cmd_application_delete(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM leave_application WHERE application_no = ?", (ns.application_no,))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "application_no not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_application_no": ns.application_no})
    return 0


def _com_leave_payload(ns: argparse.Namespace) -> tuple[dict[str, Any] | None, str | None]:
    payload = parse_json_arg(ns.json, ns.json_file)
    fields = {
        "application_no": payload.get("application_no") or ns.application_no,
        "employee_no": payload.get("employee_no") or ns.employee_no,
        "application_ts": payload.get("application_ts") or ns.application_ts or now_utc_iso(),
        "from_date": payload.get("from_date") or ns.from_date,
        "to_date": payload.get("to_date") or ns.to_date,
        "from_section": _enum(payload.get("from_section") or ns.from_section, SECTIONS, "from_section"),
        "to_section": _enum(payload.get("to_section") or ns.to_section, SECTIONS, "to_section"),
        "compensation_from_date": payload.get("compensation_from_date") or ns.compensation_from_date,
        "compensation_to_date": payload.get("compensation_to_date") or ns.compensation_to_date,
        "compensation_from_section": _enum(
            payload.get("compensation_from_section") or ns.compensation_from_section, SECTIONS, "compensation_from_section"
        ),
        "compensation_to_section": _enum(
            payload.get("compensation_to_section") or ns.compensation_to_section, SECTIONS, "compensation_to_section"
        ),
        "reason": payload.get("reason") or ns.reason,
        "attachment_filenames": _json_array(payload.get("attachment_filenames", ns.attachment_filenames)),
        "next_approver": payload.get("next_approver") or ns.next_approver,
        "next_approve_level": payload.get("next_approve_level", ns.next_approve_level if ns.next_approve_level else 1),
        "total_approve_level": payload.get("total_approve_level", ns.total_approve_level if ns.total_approve_level else 1),
        "approved_ts": payload.get("approved_ts") or ns.approved_ts,
        "rejected_ts": payload.get("rejected_ts") or ns.rejected_ts,
        "status": _enum(payload.get("status") or ns.status, COM_LEAVE_STATUSES, "status"),
        "updated_at": now_utc_iso(),
    }
    required = (
        "application_no",
        "employee_no",
        "from_date",
        "to_date",
        "from_section",
        "to_section",
        "compensation_from_date",
        "compensation_to_date",
        "compensation_from_section",
        "compensation_to_section",
        "status",
    )
    for key in required:
        if not fields[key]:
            return None, f"missing required field: {key}"
    return fields, None


def cmd_com_leave_upsert(ns: argparse.Namespace) -> int:
    fields, error = _com_leave_payload(ns)
    if error:
        out({"ok": False, "error": error})
        return 1
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO compensation_leave_application (
              application_no, employee_no, application_ts, from_date, to_date, from_section, to_section,
              compensation_from_date, compensation_to_date, compensation_from_section, compensation_to_section,
              reason, attachment_filenames, next_approver, next_approve_level, total_approve_level,
              approved_ts, rejected_ts, status, updated_at
            ) VALUES (
              :application_no, :employee_no, :application_ts, :from_date, :to_date, :from_section, :to_section,
              :compensation_from_date, :compensation_to_date, :compensation_from_section, :compensation_to_section,
              :reason, :attachment_filenames, :next_approver, :next_approve_level, :total_approve_level,
              :approved_ts, :rejected_ts, :status, :updated_at
            )
            ON CONFLICT(application_no) DO UPDATE SET
              employee_no = excluded.employee_no,
              application_ts = excluded.application_ts,
              from_date = excluded.from_date,
              to_date = excluded.to_date,
              from_section = excluded.from_section,
              to_section = excluded.to_section,
              compensation_from_date = excluded.compensation_from_date,
              compensation_to_date = excluded.compensation_to_date,
              compensation_from_section = excluded.compensation_from_section,
              compensation_to_section = excluded.compensation_to_section,
              reason = excluded.reason,
              attachment_filenames = excluded.attachment_filenames,
              next_approver = excluded.next_approver,
              next_approve_level = excluded.next_approve_level,
              total_approve_level = excluded.total_approve_level,
              approved_ts = excluded.approved_ts,
              rejected_ts = excluded.rejected_ts,
              status = excluded.status,
              updated_at = excluded.updated_at
            """,
            fields,
        )
        conn.commit()
        cur = conn.execute(
            "SELECT * FROM compensation_leave_application WHERE application_no = ?",
            (fields["application_no"],),
        )
        row = row_to_dict(cur.fetchone())
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "com_leave_application": row})
    return 0


def cmd_com_leave_get(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            "SELECT * FROM compensation_leave_application WHERE application_no = ?",
            (ns.application_no,),
        )
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "com_leave_application": row})
    return 0


def cmd_com_leave_list(ns: argparse.Namespace) -> int:
    where = []
    params: list[Any] = []
    if ns.employee_no:
        where.append("employee_no = ?")
        params.append(ns.employee_no)
    if ns.status:
        status = _enum(ns.status, COM_LEAVE_STATUSES, "status")
        if status is None:
            out({"ok": False, "error": "invalid status"})
            return 1
        where.append("status = ?")
        params.append(status)
    query = "SELECT * FROM compensation_leave_application"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY application_ts DESC LIMIT ?"
    params.append(ns.limit)
    conn = connect()
    try:
        cur = conn.execute(query, tuple(params))
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "com_leave_applications": rows})
    return 0


def cmd_com_leave_delete(ns: argparse.Namespace) -> int:
    conn = connect()
    try:
        cur = conn.execute(
            "DELETE FROM compensation_leave_application WHERE application_no = ?",
            (ns.application_no,),
        )
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "application_no not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted_application_no": ns.application_no})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Apply all schemas")
    sub.add_parser("seed-default-types", help="Seed standard leave types")

    lt_upsert = sub.add_parser("leave-type-upsert", help="Create/update leave type")
    lt_upsert.add_argument("--json")
    lt_upsert.add_argument("--json-file")
    lt_upsert.add_argument("--leave-type-no")
    lt_upsert.add_argument("--name")
    lt_upsert.add_argument("--description")
    lt_upsert.add_argument("--leave-unit")
    lt_upsert.add_argument("--color")
    lt_upsert.add_argument("--can-apply")
    lt_upsert.add_argument("--paid")
    lt_upsert.add_argument("--paid-ratio", type=float)
    lt_upsert.add_argument("--enable-paid-function")
    lt_upsert.add_argument("--paid-function")
    lt_upsert.add_argument("--allow-negative-balance")
    lt_upsert.add_argument("--reason-required")
    lt_upsert.add_argument("--attachment-required")

    lt_get = sub.add_parser("leave-type-get", help="Get leave type")
    lt_get.add_argument("leave_type_no")
    lt_list = sub.add_parser("leave-type-list", help="List leave types")
    lt_list.add_argument("--limit", type=int, default=500)
    lt_del = sub.add_parser("leave-type-delete", help="Delete leave type")
    lt_del.add_argument("leave_type_no")

    app_upsert = sub.add_parser("application-upsert", help="Create/update leave application")
    app_upsert.add_argument("--json")
    app_upsert.add_argument("--json-file")
    app_upsert.add_argument("--application-no")
    app_upsert.add_argument("--employee-no")
    app_upsert.add_argument("--leave-type-no")
    app_upsert.add_argument("--application-ts")
    app_upsert.add_argument("--from-date")
    app_upsert.add_argument("--to-date")
    app_upsert.add_argument("--from-section")
    app_upsert.add_argument("--to-section")
    app_upsert.add_argument("--no-of-days", type=float)
    app_upsert.add_argument("--reason")
    app_upsert.add_argument("--attachment-filenames")
    app_upsert.add_argument("--next-approver")
    app_upsert.add_argument("--next-approve-level", type=int)
    app_upsert.add_argument("--total-approve-level", type=int)
    app_upsert.add_argument("--approved-ts")
    app_upsert.add_argument("--rejected-ts")
    app_upsert.add_argument("--cancelled-ts")
    app_upsert.add_argument("--status")

    app_get = sub.add_parser("application-get", help="Get leave application")
    app_get.add_argument("application_no")
    app_list = sub.add_parser("application-list", help="List leave applications")
    app_list.add_argument("--employee-no")
    app_list.add_argument("--status")
    app_list.add_argument("--limit", type=int, default=500)
    app_del = sub.add_parser("application-delete", help="Delete leave application")
    app_del.add_argument("application_no")

    com_upsert = sub.add_parser("com-leave-upsert", help="Create/update compensation leave application")
    com_upsert.add_argument("--json")
    com_upsert.add_argument("--json-file")
    com_upsert.add_argument("--application-no")
    com_upsert.add_argument("--employee-no")
    com_upsert.add_argument("--application-ts")
    com_upsert.add_argument("--from-date")
    com_upsert.add_argument("--to-date")
    com_upsert.add_argument("--from-section")
    com_upsert.add_argument("--to-section")
    com_upsert.add_argument("--compensation-from-date")
    com_upsert.add_argument("--compensation-to-date")
    com_upsert.add_argument("--compensation-from-section")
    com_upsert.add_argument("--compensation-to-section")
    com_upsert.add_argument("--reason")
    com_upsert.add_argument("--attachment-filenames")
    com_upsert.add_argument("--next-approver")
    com_upsert.add_argument("--next-approve-level", type=int)
    com_upsert.add_argument("--total-approve-level", type=int)
    com_upsert.add_argument("--approved-ts")
    com_upsert.add_argument("--rejected-ts")
    com_upsert.add_argument("--status")

    com_get = sub.add_parser("com-leave-get", help="Get compensation leave application")
    com_get.add_argument("application_no")
    com_list = sub.add_parser("com-leave-list", help="List compensation leave applications")
    com_list.add_argument("--employee-no")
    com_list.add_argument("--status")
    com_list.add_argument("--limit", type=int, default=500)
    com_del = sub.add_parser("com-leave-delete", help="Delete compensation leave application")
    com_del.add_argument("application_no")
    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    if ns.command == "init":
        apply_all_schemas()
        out({"ok": True, "message": "schema applied"})
        return 0
    if ns.command == "seed-default-types":
        return cmd_seed_default_types(ns)
    if ns.command == "leave-type-upsert":
        return cmd_leave_type_upsert(ns)
    if ns.command == "leave-type-get":
        return cmd_leave_type_get(ns)
    if ns.command == "leave-type-list":
        return cmd_leave_type_list(ns)
    if ns.command == "leave-type-delete":
        return cmd_leave_type_delete(ns)
    if ns.command == "application-upsert":
        return cmd_application_upsert(ns)
    if ns.command == "application-get":
        return cmd_application_get(ns)
    if ns.command == "application-list":
        return cmd_application_list(ns)
    if ns.command == "application-delete":
        return cmd_application_delete(ns)
    if ns.command == "com-leave-upsert":
        return cmd_com_leave_upsert(ns)
    if ns.command == "com-leave-get":
        return cmd_com_leave_get(ns)
    if ns.command == "com-leave-list":
        return cmd_com_leave_list(ns)
    if ns.command == "com-leave-delete":
        return cmd_com_leave_delete(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
