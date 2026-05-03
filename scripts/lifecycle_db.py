#!/usr/bin/env python3
"""Structured onboarding/offboarding lifecycle CLI."""

from __future__ import annotations

import argparse
import sqlite3
from typing import Any

from hkhr_sqlite import apply_all_schemas, connect, now_utc_iso, out, parse_bool, parse_json_arg, row_to_dict

ALLOWED_PHASES = {"onboarding", "offboarding"}
ALLOWED_STATUS = {"pending", "done", "skipped", "na"}

DEFAULT_TEMPLATES = [
    ("onboarding", "contract_sign", "Contract signing", 10, 1),
    ("onboarding", "collect_documents", "Collect employee documents", 20, 1),
    ("onboarding", "create_accounts", "Create internal accounts", 30, 1),
    ("onboarding", "asset_handover", "Asset handover", 40, 1),
    ("onboarding", "orientation", "Orientation and policy briefing", 50, 1),
    ("offboarding", "resignation_ack", "Resignation acknowledgement", 10, 1),
    ("offboarding", "revoke_access", "Revoke IT/door access", 20, 1),
    ("offboarding", "asset_return", "Asset return and verification", 30, 1),
    ("offboarding", "final_payroll", "Final payroll and statutory settlement", 40, 1),
    ("offboarding", "exit_interview", "Exit interview", 50, 0),
]


def _normalize_phase(value: Any) -> str | None:
    if value is None:
        return None
    phase = str(value).strip().lower()
    if phase not in ALLOWED_PHASES:
        return None
    return phase


def _normalize_status(value: Any) -> str | None:
    if value is None:
        return None
    status = str(value).strip().lower()
    if status not in ALLOWED_STATUS:
        return None
    return status


def cmd_seed_default_templates(_: argparse.Namespace) -> int:
    conn = connect()
    try:
        for phase, task_code, title, sort_order, is_required in DEFAULT_TEMPLATES:
            conn.execute(
                """
                INSERT INTO lifecycle_template (phase, task_code, title, sort_order, is_required, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(phase, task_code) DO UPDATE SET
                  title = excluded.title,
                  sort_order = excluded.sort_order,
                  is_required = excluded.is_required,
                  updated_at = excluded.updated_at
                """,
                (phase, task_code, title, sort_order, is_required, now_utc_iso()),
            )
        conn.commit()
    finally:
        conn.close()
    out({"ok": True, "seeded": len(DEFAULT_TEMPLATES)})
    return 0


def cmd_template_upsert(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    phase = _normalize_phase(payload.get("phase") or ns.phase)
    task_code = payload.get("task_code") or ns.task_code
    title = payload.get("title") or ns.title
    if phase is None or not task_code or not title:
        out({"ok": False, "error": "phase, task_code, title are required"})
        return 1
    sort_order = payload.get("sort_order", ns.sort_order)
    is_required = parse_bool(payload.get("is_required", ns.is_required), True)
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO lifecycle_template (phase, task_code, title, sort_order, is_required, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(phase, task_code) DO UPDATE SET
              title = excluded.title,
              sort_order = excluded.sort_order,
              is_required = excluded.is_required,
              updated_at = excluded.updated_at
            """,
            (phase, str(task_code).strip(), str(title).strip(), int(sort_order), int(is_required), now_utc_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    out({"ok": True, "phase": phase, "task_code": task_code})
    return 0


def cmd_template_list(ns: argparse.Namespace) -> int:
    phase = _normalize_phase(ns.phase) if ns.phase else None
    conn = connect()
    try:
        if phase:
            cur = conn.execute(
                "SELECT * FROM lifecycle_template WHERE phase = ? ORDER BY phase, sort_order, task_code",
                (phase,),
            )
        else:
            cur = conn.execute("SELECT * FROM lifecycle_template ORDER BY phase, sort_order, task_code")
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "templates": rows})
    return 0


def cmd_template_delete(ns: argparse.Namespace) -> int:
    phase = _normalize_phase(ns.phase)
    if phase is None:
        out({"ok": False, "error": "invalid phase"})
        return 1
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM lifecycle_template WHERE phase = ? AND task_code = ?", (phase, ns.task_code))
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "template not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted": {"phase": phase, "task_code": ns.task_code}})
    return 0


def cmd_task_sync(ns: argparse.Namespace) -> int:
    phase = _normalize_phase(ns.phase)
    if phase is None:
        out({"ok": False, "error": "invalid phase"})
        return 1
    employee_no = ns.employee_no.strip()
    conn = connect()
    created = 0
    try:
        cur = conn.execute(
            "SELECT phase, task_code, title FROM lifecycle_template WHERE phase = ? ORDER BY sort_order, task_code",
            (phase,),
        )
        templates = cur.fetchall()
        for item in templates:
            cur = conn.execute(
                """
                INSERT INTO lifecycle_task_instance (employee_no, phase, task_code, title, status, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(employee_no, phase, task_code) DO NOTHING
                """,
                (employee_no, item["phase"], item["task_code"], item["title"], now_utc_iso()),
            )
            if cur.rowcount > 0:
                created += 1
        conn.commit()
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "employee_no": employee_no, "phase": phase, "created": created})
    return 0


def cmd_task_upsert(ns: argparse.Namespace) -> int:
    payload = parse_json_arg(ns.json, ns.json_file)
    employee_no = (payload.get("employee_no") or ns.employee_no or "").strip()
    phase = _normalize_phase(payload.get("phase") or ns.phase)
    task_code = payload.get("task_code") or ns.task_code
    title = payload.get("title") or ns.title
    if not employee_no or phase is None or not task_code or not title:
        out({"ok": False, "error": "employee_no, phase, task_code, title are required"})
        return 1
    status = _normalize_status(payload.get("status") or ns.status or "pending")
    if status is None:
        out({"ok": False, "error": "invalid status"})
        return 1
    due_date = payload.get("due_date") or ns.due_date
    notes = payload.get("notes") or ns.notes
    completed_at = payload.get("completed_at") or ns.completed_at
    if status == "done" and not completed_at:
        completed_at = now_utc_iso()

    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO lifecycle_task_instance (
              employee_no, phase, task_code, title, status, due_date, notes, completed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(employee_no, phase, task_code) DO UPDATE SET
              title = excluded.title,
              status = excluded.status,
              due_date = excluded.due_date,
              notes = excluded.notes,
              completed_at = excluded.completed_at,
              updated_at = excluded.updated_at
            """,
            (employee_no, phase, task_code, title, status, due_date, notes, completed_at, now_utc_iso()),
        )
        conn.commit()
        cur = conn.execute(
            "SELECT * FROM lifecycle_task_instance WHERE employee_no = ? AND phase = ? AND task_code = ?",
            (employee_no, phase, task_code),
        )
        row = row_to_dict(cur.fetchone())
    except sqlite3.IntegrityError as e:
        out({"ok": False, "error": str(e)})
        return 1
    finally:
        conn.close()
    out({"ok": True, "task": row})
    return 0


def cmd_task_set_status(ns: argparse.Namespace) -> int:
    status = _normalize_status(ns.status)
    phase = _normalize_phase(ns.phase)
    if status is None or phase is None:
        out({"ok": False, "error": "invalid phase or status"})
        return 1
    completed_at = now_utc_iso() if status == "done" else None
    conn = connect()
    try:
        cur = conn.execute(
            """
            UPDATE lifecycle_task_instance
            SET status = ?, completed_at = ?, notes = coalesce(?, notes), updated_at = ?
            WHERE employee_no = ? AND phase = ? AND task_code = ?
            """,
            (status, completed_at, ns.notes, now_utc_iso(), ns.employee_no, phase, ns.task_code),
        )
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "task not found"})
            return 1
        cur = conn.execute(
            "SELECT * FROM lifecycle_task_instance WHERE employee_no = ? AND phase = ? AND task_code = ?",
            (ns.employee_no, phase, ns.task_code),
        )
        row = row_to_dict(cur.fetchone())
    finally:
        conn.close()
    out({"ok": True, "task": row})
    return 0


def cmd_task_list(ns: argparse.Namespace) -> int:
    where = []
    params: list[Any] = []
    if ns.employee_no:
        where.append("employee_no = ?")
        params.append(ns.employee_no)
    if ns.phase:
        phase = _normalize_phase(ns.phase)
        if phase is None:
            out({"ok": False, "error": "invalid phase"})
            return 1
        where.append("phase = ?")
        params.append(phase)
    if ns.status:
        status = _normalize_status(ns.status)
        if status is None:
            out({"ok": False, "error": "invalid status"})
            return 1
        where.append("status = ?")
        params.append(status)
    query = "SELECT * FROM lifecycle_task_instance"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY employee_no, phase, id LIMIT ?"
    params.append(ns.limit)
    conn = connect()
    try:
        cur = conn.execute(query, tuple(params))
        rows = [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    out({"ok": True, "count": len(rows), "tasks": rows})
    return 0


def cmd_task_delete(ns: argparse.Namespace) -> int:
    phase = _normalize_phase(ns.phase)
    if phase is None:
        out({"ok": False, "error": "invalid phase"})
        return 1
    conn = connect()
    try:
        cur = conn.execute(
            "DELETE FROM lifecycle_task_instance WHERE employee_no = ? AND phase = ? AND task_code = ?",
            (ns.employee_no, phase, ns.task_code),
        )
        conn.commit()
        if cur.rowcount == 0:
            out({"ok": False, "error": "task not found"})
            return 1
    finally:
        conn.close()
    out({"ok": True, "deleted": {"employee_no": ns.employee_no, "phase": phase, "task_code": ns.task_code}})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Apply all schemas")
    sub.add_parser("seed-default-templates", help="Seed onboarding/offboarding templates")

    template_list = sub.add_parser("template-list", help="List templates")
    template_list.add_argument("--phase")

    template_upsert = sub.add_parser("template-upsert", help="Create/update template")
    template_upsert.add_argument("--json")
    template_upsert.add_argument("--json-file")
    template_upsert.add_argument("--phase")
    template_upsert.add_argument("--task-code")
    template_upsert.add_argument("--title")
    template_upsert.add_argument("--sort-order", type=int, default=0)
    template_upsert.add_argument("--is-required")

    template_delete = sub.add_parser("template-delete", help="Delete template")
    template_delete.add_argument("phase")
    template_delete.add_argument("task_code")

    task_sync = sub.add_parser("task-sync", help="Create missing instances from templates")
    task_sync.add_argument("employee_no")
    task_sync.add_argument("phase")

    task_upsert = sub.add_parser("task-upsert", help="Create/update one task instance")
    task_upsert.add_argument("--json")
    task_upsert.add_argument("--json-file")
    task_upsert.add_argument("--employee-no")
    task_upsert.add_argument("--phase")
    task_upsert.add_argument("--task-code")
    task_upsert.add_argument("--title")
    task_upsert.add_argument("--status")
    task_upsert.add_argument("--due-date")
    task_upsert.add_argument("--completed-at")
    task_upsert.add_argument("--notes")

    task_status = sub.add_parser("task-set-status", help="Set task status")
    task_status.add_argument("employee_no")
    task_status.add_argument("phase")
    task_status.add_argument("task_code")
    task_status.add_argument("status")
    task_status.add_argument("--notes")

    task_list = sub.add_parser("task-list", help="List task instances")
    task_list.add_argument("--employee-no")
    task_list.add_argument("--phase")
    task_list.add_argument("--status")
    task_list.add_argument("--limit", type=int, default=500)

    task_delete = sub.add_parser("task-delete", help="Delete task instance")
    task_delete.add_argument("employee_no")
    task_delete.add_argument("phase")
    task_delete.add_argument("task_code")
    return p


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    if ns.command == "init":
        apply_all_schemas()
        out({"ok": True, "message": "schema applied"})
        return 0
    if ns.command == "seed-default-templates":
        return cmd_seed_default_templates(ns)
    if ns.command == "template-list":
        return cmd_template_list(ns)
    if ns.command == "template-upsert":
        return cmd_template_upsert(ns)
    if ns.command == "template-delete":
        return cmd_template_delete(ns)
    if ns.command == "task-sync":
        return cmd_task_sync(ns)
    if ns.command == "task-upsert":
        return cmd_task_upsert(ns)
    if ns.command == "task-set-status":
        return cmd_task_set_status(ns)
    if ns.command == "task-list":
        return cmd_task_list(ns)
    if ns.command == "task-delete":
        return cmd_task_delete(ns)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
