---
name: hkhr-skills
description: Hong Kong HR skill hub. Use for payroll, ADW and average daily wage, leave and
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
| Employee master data (SQLite, CRUD + search) | [EMPLOYEE.md](EMPLOYEE.md) — `schema/employee.sql`, `scripts/*_employee.py` |
| Structured onboarding and offboarding | [LIFECYCLE.md](LIFECYCLE.md) — `schema/lifecycle.sql`, `scripts/*_lifecycle*.py` |
| Employment compliance dates | [COMPLIANCE.md](COMPLIANCE.md) — `schema/compliance.sql`, `scripts/*_compliance.py` |
| IR56B profile and completeness export | [IR56B.md](IR56B.md) — `schema/employee_ir56b.sql`, `scripts/*_ir56b*.py` |
| Leave types and leave applications | [LEAVE.md](LEAVE.md) — `schema/leave.sql`, `scripts/*_leave*.py` |

Add new areas as separate markdown files and link them in the table above.

## How to use this hub

1. Match the user’s request to a module (e.g. HK ADW monthly payroll → [ADW.md](ADW.md); employee directory → [EMPLOYEE.md](EMPLOYEE.md); leave handling → [LEAVE.md](LEAVE.md)).
2. Follow that module’s workflow end-to-end; do not assume every HR question maps to ADW.
3. Prefer this repo’s stated defaults and output contracts in each module; call out when something is operational guidance rather than legal advice.

## SQLite database safety rule (required)

When a task reads or writes HR records in this repo, treat the database as **SQLite** and ensure it exists before any query.

1. Use a home-directory DB path (never repo-local `data/`):
   - macOS/Linux: `~/.hkhrcore/hrcore.db`
   - Windows: `%USERPROFILE%\\.hkhrcore\\hrcore.db`
2. If the DB file does not exist, initialize it with:
   - `python scripts/init_employee.py`
3. Use the feature scripts in `scripts/` (for example `scripts/create_employee.py`, `scripts/list_leave_applications.py`).
4. Before first DB access on a machine/path, initialize schemas:
   - `python scripts/init_employee.py`
5. Prefer feature scripts in `scripts/` for DB operations so each action is self-contained.
6. Do not assume tables already exist; if a query fails with `no such table`, initialize schemas and retry.
7. Default DB path is home-based (`~/.hkhrcore/hrcore.db` on macOS/Linux; `%USERPROFILE%\\.hkhrcore\\hrcore.db` on Windows), unless `EMPLOYEE_DB_PATH` overrides it.
8. No automatic migration is performed from legacy `data/employees.db`; use `EMPLOYEE_DB_PATH` if you must continue reading that file.
9. Do not require a `data/` folder in the current working directory; the default DB lives under the user home directory and is auto-created.

## Error visibility rule (required)

When any script command fails, show concrete diagnostics to the user (not only `[error]`).

1. Before running repo scripts, verify location:
   - `pwd`
   - `ls scripts`
2. Run commands from repo root and preserve stderr in output.
3. On failure, report:
   - exact command
   - current working directory
   - full stderr/traceback text
   - exit code
4. If first command fails, do not silently continue to unrelated file search; first explain the failure details and suggest the next fix (for example wrong `cwd`, missing script, missing table, permission issue).
