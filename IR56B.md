# IR56B profile, readiness, and Excel export (SQLite)

Use this module to track IR56B-related personal fields, check completeness, and export an Excel workbook for manual filing preparation.

## Data model

Source schema: `schema/employee_ir56b.sql`

This table extends `employee` 1:1 by `employee_no`.

- Tax identity: `hkid`, `passport_no`
- Address bundle: `address_1..3`, `address_area_code`, `contact_address_1..3`, `contact_area_code`
- Personal/tax context: `place_of_birth`, `marital_status`, spouse fields

## Script (profile + readiness)

`scripts/ir56b_db.py`

### Commands

- `upsert` (create/update extension row)
- `get <employee_no>` (merged employee + ir56b profile)
- `list`
- `readiness <employee_no>` (returns `ready` + `missing_fields`)
- `delete <employee_no>`

### Example

```bash
python scripts/ir56b_db.py init
python scripts/ir56b_db.py upsert \
  --employee-no E001 \
  --hkid A1234567 \
  --address-1 "Flat A, 10/F, Example Building" \
  --address-area-code HK
python scripts/ir56b_db.py readiness E001
```

## Script (Excel export)

`scripts/ir56b_export.py`

### Command

- `export-xlsx [--employee-no E001] [--output output/ir56b_fill_template.xlsx]`

Workbook sheets:

- `Current`: merged values for each employee
- `Missing`: employees with required gaps
- `Field guide`: simple field definitions

### Example

```bash
python scripts/ir56b_export.py export-xlsx --output output/ir56b_2026.xlsx
```

This tooling is operational guidance only. It is not tax or legal advice.
