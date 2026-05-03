# IR56B profile, readiness, and Excel export (SQLite)

Use this module to track IR56B-related personal fields, check completeness, and export an Excel workbook for manual filing preparation.

## Data model

Source schema: `schema/employee_ir56b.sql`

This table extends `employee` 1:1 by `employee_no`.

- Tax identity: `hkid`, `passport_no`
- Address bundle: `address_1..3`, `address_area_code`, `contact_address_1..3`, `contact_area_code`
- Personal/tax context: `place_of_birth`, `marital_status`, spouse fields

## Feature scripts (profile + readiness)

### Commands

- `init_ir56b.py`
- `upsert_ir56b_profile.py` (create/update extension row)
- `get_ir56b_profile.py <employee_no>` (merged employee + ir56b profile)
- `list_ir56b_profiles.py`
- `check_ir56b_readiness.py <employee_no>` (returns `ready` + `missing_fields`)
- `delete_ir56b_profile.py <employee_no>`

### Example

```bash
python scripts/init_ir56b.py
python scripts/upsert_ir56b_profile.py \
  --employee-no E001 \
  --hkid A1234567 \
  --address-1 "Flat A, 10/F, Example Building" \
  --address-area-code HK
python scripts/check_ir56b_readiness.py E001
```

## Feature scripts (Excel export)

### Command

- `init_ir56b_export.py`
- `export_ir56b_xlsx.py [--employee-no E001] [--output output/ir56b_fill_template.xlsx]`

Workbook sheets:

- `Current`: merged values for each employee
- `Missing`: employees with required gaps
- `Field guide`: simple field definitions

### Example

```bash
python scripts/export_ir56b_xlsx.py --output output/ir56b_2026.xlsx
```

This tooling is operational guidance only. It is not tax or legal advice.
