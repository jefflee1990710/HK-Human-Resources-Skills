# HKHR Skills

`hkhr-skills` is a SQLite-backed HR skill toolkit for Hong Kong-focused HR operations.  
It provides structured agent workflows, command-line scripts, and schema definitions for payroll-adjacent processing, employee management, lifecycle operations, compliance tracking, leave applications, and IR56B readiness/export.

## Features

Details for each area live in the linked module docs; CLI scripts live under `scripts/`.

### Employee ([EMPLOYEE.md](EMPLOYEE.md))

- SQLite-backed employee master with a fixed schema (names, contact, department, job title, hire date, employment status, notes, and related fields).
- Create, fetch by employee number or email, substring search across key fields, partial update, hard delete, and capped list.
- Uniqueness on `employee_no` and on `email` when set.

### Lifecycle — onboarding / offboarding ([LIFECYCLE.md](LIFECYCLE.md))

- Reusable lifecycle templates per phase (`onboarding` / `offboarding`).
- Sync template tasks onto an employee, then track per-employee task instances with optional due dates and completion notes.
- Task statuses: `pending`, `done`, `skipped`, `na`.
- List templates and tasks, upsert or delete templates and task instances, set status from the CLI.

### Employment compliance ([COMPLIANCE.md](COMPLIANCE.md))

- Per-employee compliance records for contract, work eligibility, or other types.
- Store titled records with start/end dates plus optional reference number, country, and remarks.
- Create, get by id, list with filters, update, and delete.

### Leave ([LEAVE.md](LEAVE.md))

- Leave type catalog (code, name, unit, paid flags, requirements): seed defaults, upsert, get, list, delete.
- Leave applications with date range, AM/PM sections, status workflow (`Pending` / `Approved` / `Rejected` / `Cancelled`), and day or hour units.
- Compensation leave applications with their own upsert/get/list/delete flow and status set.
- Data model aligned with `hrsys_web_v2`-style leave structures for interoperability.

### IR56B ([IR56B.md](IR56B.md))

- One-to-one IR56B profile extension on each employee (HKID, passport, address blocks, contact address, place of birth, marital and spouse-related fields).
- Upsert, get merged profile, list profiles, delete extension row.
- Readiness check returning `ready` plus a `missing_fields` list for filing prep.
- Excel export workbook with `Current`, `Missing`, and `Field guide` sheets (optional filter by employee).

### ADW — payroll from Excel ([ADW.md](ADW.md))

- Average daily wage (ADW) style monthly payout from user Excel workbooks when layout and column names vary.
- Schema inference with mapping confidence, `mapping_report.json`, and `questions_for_user.txt` for low-confidence cases.
- Modes: report-only mapping, interactive confirmation, or manual `--mapping-json` overrides.
- Outputs include employee payout summary, line breakdown, per-employee ADW detail, and calculation warnings (CSV under a chosen output directory).

### Toolkit-wide

- One database file for all modules; `scripts/init_employee.py` applies every module schema idempotently (`CREATE IF NOT EXISTS`).
- Each feature script prints a single JSON object to stdout (`ok` / payload / `error`) for operators and agents.
- Default database file under the user profile: **macOS** (and Linux) `~/.hkhrcore/hrcore.db`; **Windows** `%USERPROFILE%\.hkhrcore\hrcore.db`. Override with `EMPLOYEE_DB_PATH` (see [Database path](#database-path)).

## Project Structure

- `SKILL.md`: skill hub entry with module index
- `schema/*.sql`: SQLite schemas (employee, IR56B, lifecycle, compliance, leave)
- `scripts/*.py`: CLI entrypoints for each module
- Default SQLite database: macOS/Linux `~/.hkhrcore/hrcore.db`; Windows `%USERPROFILE%\.hkhrcore\hrcore.db` (created on first init)

## Installation

### 1) Prerequisites

- Python 3.10+ (recommended)

### 2) Install dependencies

From project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Initialize database schema

```bash
python scripts/init_employee.py
```

This applies all module schemas into the same SQLite database.

## How to Use (AI-first)

This repository is designed as a **skill project for AI assistants** (for example Cursor Agent, Claude Code, or other coding/ops agents).

Recommended flow:

1. Ask your AI to classify your request into a module (`ADW`, `EMPLOYEE`, `LIFECYCLE`, `COMPLIANCE`, `LEAVE`, `IR56B`).
2. Ask the AI to run the related script(s) and return JSON output plus a human-readable summary.
3. For any write action, ask the AI to show the exact command before execution.
4. Keep sensitive HR data local whenever possible.

## Common AI Use Cases

- **Payroll support (`ADW`)**
  - **Feature details**
    - Reads dynamic Excel workbook structures and infers sheet/column mapping.
    - Calculates ADW-based payout outputs and produces warning files for review.
    - Supports report-first mode for mapping validation before payroll calculation.
  - **Use cases**
    - "Calculate monthly ADW payout for staff and explain warning rows."
    - "Generate payout summary CSVs for finance handoff."
    - "Review mapping confidence and fix columns before final run."

- **Employee operations (`EMPLOYEE`)**
  - **Feature details**
    - Creates, updates, searches, lists, and deletes employee records in SQLite.
    - Supports JSON-style script outputs for automation and downstream parsing.
    - Uses home-based DB path by default with optional env override.
  - **Use cases**
    - "Add a new employee profile and verify by employee number."
    - "Search by name/keyword and update department/contact info."
    - "Produce a quick employee list snapshot for internal review."

- **Onboarding/offboarding (`LIFECYCLE`)**
  - **Feature details**
    - Seeds default checklist templates for onboarding and offboarding phases.
    - Syncs template tasks to employee-specific task instances.
    - Tracks task status (`pending`, `done`, `skipped`, `na`) per employee.
  - **Use cases**
    - "Prepare onboarding tasks for a new joiner and track completion."
    - "Run offboarding checklist and mark IT access revocation as done."
    - "List pending lifecycle actions by employee and phase."

- **Compliance tracking (`COMPLIANCE`)**
  - **Feature details**
    - Stores employment compliance records (contract, work eligibility, other).
    - Supports lifecycle of records: create, list, get, update, delete.
    - Enables filtering by employee and record type for monitoring.
  - **Use cases**
    - "Create contract validity records and monitor renewal windows."
    - "Track work-eligibility date ranges for expiring documents."
    - "Update compliance remarks after legal/admin review."

- **Leave handling (`LEAVE`)**
  - **Feature details**
    - Seeds and manages leave type catalog (unit, paid ratio, policy flags).
    - Handles standard leave applications and compensation leave applications.
    - Supports application status workflows (`Pending`, `Approved`, etc.).
  - **Use cases**
    - "Seed leave types, submit leave request, and list employee leave history."
    - "Record compensation leave for overtime and track status."
    - "Review leave requests by employee and approval status."

- **IR56B preparation (`IR56B`)**
  - **Feature details**
    - Upserts IR56B profile extension fields linked to employee master records.
    - Checks profile readiness against required IR56B data fields.
    - Exports IR56B workbook templates for completion and submission prep.
  - **Use cases**
    - "Validate readiness for tax filing and identify missing fields."
    - "Export IR56B workbook for batch completion."
    - "Maintain up-to-date HKID/passport and address data for filing."

- **Data quality checks**
  - **Feature details**
    - Uses script outputs to detect missing required fields and invalid values.
    - Highlights inconsistent date ranges and status mismatches.
    - Provides machine-readable JSON for repeatable validation workflows.
  - **Use cases**
    - "Run pre-payroll checks to catch incomplete records."
    - "Audit IR56B readiness gaps across employees."
    - "Validate compliance and leave data before monthly reporting."

- **Operational Q&A and assistant guidance**
  - **Feature details**
    - Interprets script JSON outputs into human-readable summaries.
    - Recommends next commands based on previous command outcomes.
    - Supports troubleshooting flow with explicit command/error context.
  - **Use cases**
    - "Explain what this command result means and what to run next."
    - "Diagnose why a script failed and suggest the smallest safe fix."
    - "Generate a concise operational status update for HR ops."

## Database path

**Default file** (when `EMPLOYEE_DB_PATH` is not set):

- **macOS:** `~/.hkhrcore/hrcore.db` (same as `$HOME/.hkhrcore/hrcore.db`)
- **Windows:** `%USERPROFILE%\.hkhrcore\hrcore.db` (for example `C:\Users\YourName\.hkhrcore\hrcore.db`)

On **Linux**, the default matches macOS: `~/.hkhrcore/hrcore.db`.

**Override** on any OS: set the `EMPLOYEE_DB_PATH` environment variable to an absolute path of the SQLite file.

macOS or Linux (bash/zsh):

```bash
export EMPLOYEE_DB_PATH="/absolute/path/to/hrcore.db"
```

Windows Command Prompt:

```bat
set EMPLOYEE_DB_PATH=C:\absolute\path\to\hrcore.db
```

Windows PowerShell:

```powershell
$env:EMPLOYEE_DB_PATH = "C:\absolute\path\to\hrcore.db"
```

Note: this project does not auto-migrate legacy `data/employees.db`. To keep using legacy data, point `EMPLOYEE_DB_PATH` to that file explicitly.

## Output contract

All scripts print JSON to stdout:

- success: `{"ok": true, ...}`
- failure: `{"ok": false, "error": "..."}`

This format is designed for both human operators and AI agent automation.

## Sensitive Data Notice (Important)

HR data is highly sensitive and may include personal identifiers, compensation, contact details, and tax-related records.

- Prefer processing HR data with a **local LLM / on-device model** connected to your AI agent.
- Avoid sending employee records, IR56B information, or payroll-related files to external hosted LLM APIs unless explicitly approved by your organization.
- Restrict database/file permissions and follow your internal security and compliance policies.
- This toolkit provides operational support only; it is not legal, tax, or compliance advice.
