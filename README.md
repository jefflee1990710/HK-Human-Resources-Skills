# HKHR Skills

`hkhr-skills` is a SQLite-backed HR skill toolkit for Hong Kong-focused HR operations.  
It provides structured agent workflows, command-line scripts, and schema definitions for payroll-adjacent processing, employee management, lifecycle operations, compliance tracking, leave applications, and IR56B readiness/export.

## Features

- ADW payroll calculation from dynamic Excel workbooks (`ADW.md`, `scripts/calculate_adw_salary.py`)
- Employee master data management in SQLite (`EMPLOYEE.md`, `scripts/*_employee.py`)
- Structured onboarding/offboarding task tracking (`LIFECYCLE.md`, `scripts/*_lifecycle*.py`)
- Employment compliance date tracking (contract/work eligibility) (`COMPLIANCE.md`, `scripts/*_compliance.py`)
- IR56B profile extension, readiness checking, and Excel export (`IR56B.md`, `scripts/*_ir56b*.py`)
- Leave module with leave type catalog, leave application, and compensation leave application (`LEAVE.md`, `scripts/*_leave*.py`)
- Per-feature scripts with direct SQLite access and one-command schema initialization (`scripts/init_employee.py`)

## Project Structure

- `SKILL.md`: skill hub entry with module index
- `schema/*.sql`: SQLite schemas (employee, IR56B, lifecycle, compliance, leave)
- `scripts/*.py`: CLI entrypoints for each module
- `data/hrcore.db`: default SQLite database file (created on first init)

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

## How to Use

## Database path

- Default: `data/hrcore.db`
- Override with environment variable:

```bash
export EMPLOYEE_DB_PATH="/absolute/path/to/hrcore.db"
```

Note: this project does not auto-migrate legacy `data/employees.db`. To keep using legacy data, point `EMPLOYEE_DB_PATH` to that file explicitly.

## Common workflows

### Employee CRUD

```bash
python scripts/create_employee.py --employee-no E001 --full-name "Chan Tai Man" --email chan@example.com
python scripts/get_employee_by_no.py E001
python scripts/search_employee.py Chan
python scripts/update_employee.py --employee-no E001 --department HR
python scripts/delete_employee.py E001
```

### Onboarding / Offboarding checklist

```bash
python scripts/seed_lifecycle_templates.py
python scripts/sync_lifecycle_tasks.py E001 onboarding
python scripts/list_lifecycle_tasks.py --employee-no E001 --phase onboarding
python scripts/set_lifecycle_task_status.py E001 onboarding contract_sign done
```

### Employment compliance

```bash
python scripts/create_compliance.py \
  --employee-no E001 \
  --record-type contract \
  --title "Employment Contract 2026" \
  --start-date 2026-01-01 \
  --end-date 2026-12-31
python scripts/list_compliance.py --employee-no E001
```

### Leave module

```bash
python scripts/seed_leave_types.py
python scripts/upsert_leave_application.py \
  --application-no LA-1 \
  --employee-no E001 \
  --leave-type-no AL \
  --from-date 2026-05-10 \
  --to-date 2026-05-10 \
  --from-section AM \
  --to-section PM \
  --status Pending
python scripts/list_leave_applications.py --employee-no E001
```

### IR56B readiness and export

```bash
python scripts/upsert_ir56b_profile.py --employee-no E001 --hkid A1234567 --address-1 "Flat A" --address-area-code HK
python scripts/check_ir56b_readiness.py E001
python scripts/export_ir56b_xlsx.py --output output/ir56b_fill_template.xlsx
```

## Script migration map

If you previously used monolithic scripts, migrate to feature scripts:

- `employee_db.py create|get-by-no|get-by-email|search|update|delete|list` -> `create_employee.py|get_employee_by_no.py|get_employee_by_email.py|search_employee.py|update_employee.py|delete_employee.py|list_employee.py`
- `leave_db.py leave-type-*` -> `upsert_leave_type.py|get_leave_type.py|list_leave_types.py|delete_leave_type.py`
- `leave_db.py application-*` -> `upsert_leave_application.py|get_leave_application.py|list_leave_applications.py|delete_leave_application.py`
- `leave_db.py com-leave-*` -> `upsert_compensation_leave.py|get_compensation_leave.py|list_compensation_leave.py|delete_compensation_leave.py`
- `lifecycle_db.py template-*|task-*|seed-default-templates` -> `upsert_lifecycle_template.py|delete_lifecycle_template.py|list_lifecycle_templates.py|upsert_lifecycle_task.py|set_lifecycle_task_status.py|sync_lifecycle_tasks.py|list_lifecycle_tasks.py|delete_lifecycle_task.py|seed_lifecycle_templates.py`
- `compliance_db.py create|get|list|update|delete` -> `create_compliance.py|get_compliance.py|list_compliance.py|update_compliance.py|delete_compliance.py`
- `ir56b_db.py upsert|get|list|readiness|delete` -> `upsert_ir56b_profile.py|get_ir56b_profile.py|list_ir56b_profiles.py|check_ir56b_readiness.py|delete_ir56b_profile.py`
- `ir56b_export.py export-xlsx` -> `export_ir56b_xlsx.py`

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
