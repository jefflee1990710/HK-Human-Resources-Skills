# ADW Salary Calculator

## Purpose

Use this skill to calculate employee monthly payout with ADW (Average Daily Wage) logic from user-uploaded Excel files, even when workbook structure and column names vary.

## Inputs Expected

User may provide one workbook or multiple files containing:

- Attendance records
- Salary records (monthly/basic salary and wage components)
- Leave data (annual leave, sick leave, maternity/paternity, unpaid leave)
- Optional employee master data

Input formats are dynamic and not fixed.

## Workflow

Copy this checklist and keep it updated:

```markdown
Progress:
- [ ] Step 1: Collect files and target payroll month
- [ ] Step 2: Run schema inference and mapping check
- [ ] Step 3: Ask user to confirm uncertain mappings/missing data
- [ ] Step 4: Run ADW payroll calculation
- [ ] Step 5: Share payout summary + breakdown + warnings
```

### Step 1: Collect minimum context

Ask user for:

1. Target payroll month (`YYYY-MM`)
2. Workbook path(s)
3. Confirmation of any special policy (if different from defaults)

Default policy assumptions:

- ADW lookback window: previous 12 calendar months (or shorter if data unavailable)
- ADW denominator excludes unpaid/no-pay style days when provided
- Long sick leave, maternity, paternity are paid at 4/5 of ADW unless user says otherwise

### Step 2: Infer workbook schema

Run:

```bash
python scripts/calculate_adw_salary.py \
  --input "<excel_path>" \
  --month "YYYY-MM" \
  --report-only
```

This produces:

- `mapping_report.json`: inferred sheet/column mapping with confidence
- `questions_for_user.txt`: clarification prompts when fields are uncertain/missing

### Step 3: Confirm mappings with user

If mapping confidence is low, ask user to confirm and provide mapping overrides:

```bash
python scripts/calculate_adw_salary.py \
  --input "<excel_path>" \
  --month "YYYY-MM" \
  --interactive
```

or supply manual mapping:

```bash
python scripts/calculate_adw_salary.py \
  --input "<excel_path>" \
  --month "YYYY-MM" \
  --mapping-json "<mapping_json_path>"
```

### Step 4: Calculate payout

Run:

```bash
python scripts/calculate_adw_salary.py \
  --input "<excel_path>" \
  --month "YYYY-MM" \
  --output-dir "output"
```

### Step 5: Return results to user

Always return:

- Employee payout summary (`employee_payout_summary.csv`)
- Breakdown lines (`employee_payout_breakdown.csv`)
- ADW detail by employee (`employee_adw_details.csv`)
- Calculation warnings (`calculation_warnings.csv`)

Explain:

- Which mappings were inferred vs confirmed
- Which assumptions were used due to missing data
- Which columns are still missing and how that affects precision

## Script Interface

Primary script: `scripts/calculate_adw_salary.py`

Key flags:

- `--input`: Excel file path (`.xlsx`, `.xlsm`, `.xls`)
- `--month`: payroll month (`YYYY-MM`)
- `--output-dir`: output folder (default `./output`)
- `--mapping-json`: optional manual column mapping override
- `--interactive`: interactive mapping confirmation in terminal
- `--report-only`: infer schema and produce mapping report only

## Output Contract

The skill should always provide:

1. Total payout per employee
2. Component-level breakdown (base salary, leave pay, deductions)
3. ADW used and lookback coverage
4. Missing-data warnings and any assumptions

## Notes

- This tool gives HR/payroll operational calculations. It is not legal advice.
- If user policy differs from defaults, re-run with policy override options in script.
