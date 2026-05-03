# Leave application module (SQLite)

This module mirrors leave structures from `hrsys_web_v2` models:

- `LeaveType` (`LeaveType.ts`)
- `LeaveApplication` (`Leave.ts`)
- `ComLeaveApplication` (`ComLeaveApplication.ts`)

## Data model

Source schema: `schema/leave.sql`

- `leave_type`: leave catalog (code, name, unit, paid flags, requirements)
- `leave_application`: normal leave requests
- `compensation_leave_application`: compensation leave requests

Enums:

- sections: `AM`, `PM`
- leave status: `Pending`, `Approved`, `Rejected`, `Cancelled`
- com-leave status: `Pending`, `Approved`, `Rejected`
- leave unit: `Day`, `Hour`

## Feature scripts (`scripts/`)

Use one script per feature. All commands return JSON (`ok`, payload, `error`).

### Leave type commands

- `seed_leave_types.py`
- `upsert_leave_type.py`
- `get_leave_type.py <leave_type_no>`
- `list_leave_types.py`
- `delete_leave_type.py <leave_type_no>`

### Leave application commands

- `upsert_leave_application.py`
- `get_leave_application.py <application_no>`
- `list_leave_applications.py [--employee-no E001] [--status Pending]`
- `delete_leave_application.py <application_no>`

### Compensation leave commands

- `upsert_compensation_leave.py`
- `get_compensation_leave.py <application_no>`
- `list_compensation_leave.py [--employee-no E001] [--status Pending]`
- `delete_compensation_leave.py <application_no>`

### Example

```bash
python scripts/init_leave.py
python scripts/seed_leave_types.py

python scripts/upsert_leave_application.py \
  --application-no LA-2026-001 \
  --employee-no E001 \
  --leave-type-no AL \
  --from-date 2026-05-10 \
  --to-date 2026-05-12 \
  --from-section AM \
  --to-section PM \
  --status Pending

python scripts/list_leave_applications.py --employee-no E001
```
