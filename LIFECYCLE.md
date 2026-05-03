# Structured onboarding / offboarding (SQLite)

Use this module to track employee lifecycle tasks with reusable templates and per-employee task instances.

## Data model

Source schema: `schema/lifecycle.sql`

- `lifecycle_template`: phase-level template tasks (`onboarding` / `offboarding`)
- `lifecycle_task_instance`: employee task status, due dates, completion notes

Statuses:

- `pending`
- `done`
- `skipped`
- `na`

## Script

`scripts/lifecycle_db.py`

All commands return JSON (`ok`, payload, `error`).

### Core commands

- `seed-default-templates`
- `template-list [--phase onboarding|offboarding]`
- `template-upsert --phase ... --task-code ... --title ...`
- `template-delete <phase> <task_code>`
- `task-sync <employee_no> <phase>` (copy missing template tasks to employee)
- `task-upsert ...` (create/update one task instance)
- `task-set-status <employee_no> <phase> <task_code> <status>`
- `task-list [--employee-no E001 --phase onboarding --status pending]`
- `task-delete <employee_no> <phase> <task_code>`

### Example

```bash
python scripts/lifecycle_db.py init
python scripts/lifecycle_db.py seed-default-templates
python scripts/lifecycle_db.py task-sync E001 onboarding
python scripts/lifecycle_db.py task-set-status E001 onboarding contract_sign done --notes "Signed on first day"
python scripts/lifecycle_db.py task-list --employee-no E001 --phase onboarding
```
