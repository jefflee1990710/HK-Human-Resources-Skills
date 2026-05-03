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

## Feature scripts (`scripts/`)

Use one script per feature. All commands return JSON (`ok`, payload, `error`).

### Core commands

- `init_lifecycle.py`
- `seed_lifecycle_templates.py`
- `list_lifecycle_templates.py [--phase onboarding|offboarding]`
- `upsert_lifecycle_template.py --phase ... --task-code ... --title ...`
- `delete_lifecycle_template.py <phase> <task_code>`
- `sync_lifecycle_tasks.py <employee_no> <phase>` (copy missing template tasks to employee)
- `upsert_lifecycle_task.py ...` (create/update one task instance)
- `set_lifecycle_task_status.py <employee_no> <phase> <task_code> <status>`
- `list_lifecycle_tasks.py [--employee-no E001 --phase onboarding --status pending]`
- `delete_lifecycle_task.py <employee_no> <phase> <task_code>`

### Example

```bash
python scripts/init_lifecycle.py
python scripts/seed_lifecycle_templates.py
python scripts/sync_lifecycle_tasks.py E001 onboarding
python scripts/set_lifecycle_task_status.py E001 onboarding contract_sign done --notes "Signed on first day"
python scripts/list_lifecycle_tasks.py --employee-no E001 --phase onboarding
```
