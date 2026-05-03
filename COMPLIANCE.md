# Employment compliance dates (SQLite)

Use this module to store and query contract and work-eligibility timelines per employee.

## Data model

Source schema: `schema/compliance.sql`

Table: `employment_compliance`

- `record_type`: `contract` | `work_eligibility` | `other`
- date fields: `start_date`, `end_date` (`YYYY-MM-DD`)
- supporting fields: `reference_no`, `country`, `remarks`

## Script

`scripts/compliance_db.py`

All commands return JSON (`ok`, payload, `error`).

### Commands

- `create`
- `get <id>`
- `list [--employee-no E001] [--record-type contract]`
- `update <id>`
- `delete <id>`

### Example

```bash
python scripts/compliance_db.py init
python scripts/compliance_db.py create \
  --employee-no E001 \
  --record-type contract \
  --title "Employment Contract 2026" \
  --start-date 2026-01-01 \
  --end-date 2026-12-31 \
  --reference-no CT-2026-001
python scripts/compliance_db.py list --employee-no E001
```
