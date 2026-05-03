# HKHR Skills

`hkhr-skills` is a SQLite-backed HR skill toolkit for Hong Kong-focused HR operations.  
It provides structured agent workflows, command-line scripts, and schema definitions for payroll-adjacent processing, employee management, lifecycle operations, compliance tracking, leave applications, and IR56B readiness/export.

## Features

- ADW payroll calculation from dynamic Excel workbooks (`ADW.md`, `scripts/calculate_adw_salary.py`)
- Employee master data management in SQLite (`EMPLOYEE.md`, `scripts/employee_db.py`)
- Structured onboarding/offboarding task tracking (`LIFECYCLE.md`, `scripts/lifecycle_db.py`)
- Employment compliance date tracking (contract/work eligibility) (`COMPLIANCE.md`, `scripts/compliance_db.py`)
- IR56B profile extension, readiness checking, and Excel export (`IR56B.md`, `scripts/ir56b_db.py`, `scripts/ir56b_export.py`)
- Leave module with leave type catalog, leave application, and compensation leave application (`LEAVE.md`, `scripts/leave_db.py`)
- Shared SQLite helper with one-command schema initialization (`scripts/hkhr_sqlite.py`)

## Project Structure

- `SKILL.md`: skill hub entry with module index
- `schema/*.sql`: SQLite schemas (employee, IR56B, lifecycle, compliance, leave)
- `scripts/*.py`: CLI entrypoints for each module
- `data/employees.db`: default SQLite database file (created on first init)

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
python scripts/employee_db.py init
```

This applies all module schemas into the same SQLite database.

## How to Use

## Database path

- Default: `data/employees.db`
- Override with environment variable:

```bash
export EMPLOYEE_DB_PATH="/absolute/path/to/employees.db"
```

## Common workflows

### Employee CRUD

```bash
python scripts/employee_db.py create --employee-no E001 --full-name "Chan Tai Man" --email chan@example.com
python scripts/employee_db.py get-by-no E001
python scripts/employee_db.py search Chan
python scripts/employee_db.py update --employee-no E001 --department HR
python scripts/employee_db.py delete E001
```

### Onboarding / Offboarding checklist

```bash
python scripts/lifecycle_db.py seed-default-templates
python scripts/lifecycle_db.py task-sync E001 onboarding
python scripts/lifecycle_db.py task-list --employee-no E001 --phase onboarding
python scripts/lifecycle_db.py task-set-status E001 onboarding contract_sign done
```

### Employment compliance

```bash
python scripts/compliance_db.py create \
  --employee-no E001 \
  --record-type contract \
  --title "Employment Contract 2026" \
  --start-date 2026-01-01 \
  --end-date 2026-12-31
python scripts/compliance_db.py list --employee-no E001
```

### Leave module

```bash
python scripts/leave_db.py seed-default-types
python scripts/leave_db.py application-upsert \
  --application-no LA-1 \
  --employee-no E001 \
  --leave-type-no AL \
  --from-date 2026-05-10 \
  --to-date 2026-05-10 \
  --from-section AM \
  --to-section PM \
  --status Pending
python scripts/leave_db.py application-list --employee-no E001
```

### IR56B readiness and export

```bash
python scripts/ir56b_db.py upsert --employee-no E001 --hkid A1234567 --address-1 "Flat A" --address-area-code HK
python scripts/ir56b_db.py readiness E001
python scripts/ir56b_export.py export-xlsx --output output/ir56b_fill_template.xlsx
```

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
