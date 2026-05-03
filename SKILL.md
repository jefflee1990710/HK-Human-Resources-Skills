---
name: hkhr-skills
description: >-
  Hong Kong HR skill hub. Use for payroll, ADW and average daily wage, leave and
  statutory entitlements, attendance-to-pay workflows, employee records (SQLite),
  onboarding/offboarding lifecycle, employment compliance timelines, IR56B
  readiness/export, HR spreadsheets, and related operational HR questions where
  this repo’s playbooks or scripts apply.
---

# Hong Kong HR skill hub

This project is a **central place for HR-related agent guidance**, not a single tool. Start here to find the right doc or script for the user’s task.

## Modules in this repo

| Topic | Doc / entry |
|--------|-------------|
| ADW payroll from Excel (mapping, payout, warnings) | [ADW.md](ADW.md) — uses `scripts/calculate_adw_salary.py` |
| Employee master data (SQLite, CRUD + search) | [EMPLOYEE.md](EMPLOYEE.md) — `schema/employee.sql`, `scripts/employee_db.py` |
| Structured onboarding and offboarding | [LIFECYCLE.md](LIFECYCLE.md) — `schema/lifecycle.sql`, `scripts/lifecycle_db.py` |
| Employment compliance dates | [COMPLIANCE.md](COMPLIANCE.md) — `schema/compliance.sql`, `scripts/compliance_db.py` |
| IR56B profile and completeness export | [IR56B.md](IR56B.md) — `schema/employee_ir56b.sql`, `scripts/ir56b_db.py`, `scripts/ir56b_export.py` |
| Leave types and leave applications | [LEAVE.md](LEAVE.md) — `schema/leave.sql`, `scripts/leave_db.py` |

Add new areas as separate markdown files and link them in the table above.

## How to use this hub

1. Match the user’s request to a module (e.g. HK ADW monthly payroll → [ADW.md](ADW.md); employee directory → [EMPLOYEE.md](EMPLOYEE.md); leave handling → [LEAVE.md](LEAVE.md)).
2. Follow that module’s workflow end-to-end; do not assume every HR question maps to ADW.
3. Prefer this repo’s stated defaults and output contracts in each module; call out when something is operational guidance rather than legal advice.

## SQLite database safety rule (required)

When a task reads or writes HR records in this repo, treat the database as **SQLite** and ensure it exists before any query.

1. If the DB file does not exist (default `data/hrcore.db`, or path from `EMPLOYEE_DB_PATH`), initialize it with:
   - `python scripts/employee_db.py init`
2. Use the SQLite-backed scripts in `scripts/` (for example `scripts/employee_db.py`).
3. Before first DB access on a machine/path, initialize schemas:
   - `python scripts/employee_db.py init`
4. If using Python directly, use `scripts.hkhr_sqlite.connect()` and apply schemas first via `scripts.hkhr_sqlite.apply_all_schemas()` when needed.
5. Do not assume tables already exist; if a query fails with `no such table`, initialize schemas and retry.
6. Default DB path is `data/hrcore.db` unless `EMPLOYEE_DB_PATH` overrides it.
7. No automatic migration is performed from legacy `data/employees.db`; use `EMPLOYEE_DB_PATH` if you must continue reading that file.
