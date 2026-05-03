# Employment compliance dates (SQLite)

Use this module to store and query contract and work-eligibility timelines per employee.

## Data model

Source schema: `schema/compliance.sql`

Table: `employment_compliance`

- `record_type`: `contract` | `work_eligibility` | `other`
- date fields: `start_date`, `end_date` (`YYYY-MM-DD`)
- supporting fields: `reference_no`, `country`, `remarks`

## Feature scripts (`scripts/`)

Use one script per feature. All commands return JSON (`ok`, payload, `error`).

### Commands

- `init_compliance.py`
- `create_compliance.py`
- `get_compliance.py <id>`
- `list_compliance.py [--employee-no E001] [--record-type contract]`
- `update_compliance.py <id>`
- `delete_compliance.py <id>`

### Example

```bash
python scripts/init_compliance.py
python scripts/create_compliance.py \
  --employee-no E001 \
  --record-type contract \
  --title "Employment Contract 2026" \
  --start-date 2026-01-01 \
  --end-date 2026-12-31 \
  --reference-no CT-2026-001
python scripts/list_compliance.py --employee-no E001
```
