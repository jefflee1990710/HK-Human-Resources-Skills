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

## Script

`scripts/leave_db.py`

All commands return JSON (`ok`, payload, `error`).

### Leave type commands

- `seed-default-types`
- `leave-type-upsert`
- `leave-type-get <leave_type_no>`
- `leave-type-list`
- `leave-type-delete <leave_type_no>`

### Leave application commands

- `application-upsert`
- `application-get <application_no>`
- `application-list [--employee-no E001] [--status Pending]`
- `application-delete <application_no>`

### Compensation leave commands

- `com-leave-upsert`
- `com-leave-get <application_no>`
- `com-leave-list [--employee-no E001] [--status Pending]`
- `com-leave-delete <application_no>`

### Example

```bash
python scripts/leave_db.py init
python scripts/leave_db.py seed-default-types

python scripts/leave_db.py application-upsert \
  --application-no LA-2026-001 \
  --employee-no E001 \
  --leave-type-no AL \
  --from-date 2026-05-10 \
  --to-date 2026-05-12 \
  --from-section AM \
  --to-section PM \
  --status Pending

python scripts/leave_db.py application-list --employee-no E001
```
