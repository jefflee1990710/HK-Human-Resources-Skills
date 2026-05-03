# Employee management (SQLite)

Use this module to maintain a **fixed-schema** employee directory backed by **SQLite**, with CLI scripts that return **JSON** so an agent can query and update records safely.

## Database location

| Default path | Override |
|--------------|----------|
| `data/hrcore.db` (under repo root) | Set `EMPLOYEE_DB_PATH` to an absolute or user-expanded path |

Create the file and tables once:

```bash
python scripts/init_employee.py
```

`init` now applies **all SQLite module schemas** in this repo (`employee`, `employee_ir56b`, `lifecycle`, `compliance`, `leave`) into the same database file.

No automatic migration is performed from legacy `data/employees.db`. If you need old data, set `EMPLOYEE_DB_PATH` to that file.

## Schema (fixed)

Source of truth: [schema/employee.sql](schema/employee.sql)

Logical field map (columns match these names in JSON/CLI flags):

| Column | Type / notes |
|--------|----------------|
| `id` | Integer primary key (auto) |
| `employee_no` | **Unique.** Business employee number |
| `full_name` | Required display/legal name |
| `preferred_name` | Optional |
| `email` | Optional; unique if set |
| `work_mobile` | Optional |
| `personal_mobile` | Optional |
| `date_of_birth` | Optional `YYYY-MM-DD` |
| `nationality` | Optional |
| `residential_address` | Optional |
| `department` | Optional |
| `job_title` | Optional |
| `hire_date` | Optional `YYYY-MM-DD` |
| `employment_status` | `active` · `on_leave` · `terminated` · `probation` (default `active`) |
| `notes` | Optional free text |
| `created_at` | UTC ISO8601 (set by DB) |
| `updated_at` | UTC ISO8601 (set on create; refreshed on **update**) |

**Constraints:** `employee_no` and `email` must remain unique where not null.

## Feature scripts (`scripts/`)

Each feature uses one script and returns **one JSON object** to stdout (`ok`, payload or `error`).

### Setup

- `init_employee.py` — apply schema (idempotent `CREATE IF NOT EXISTS`).

### Operations (aliases for agent workflows)

| Intent | Script |
|--------|--------|
| **createEmployee** | `create_employee.py` |
| **getEmployeeByEmployeeNo** | `get_employee_by_no.py <employee_no>` |
| **getEmployeeByEmail** | `get_employee_by_email.py <email>` |
| **searchEmployee** | `search_employee.py <query>` — substring match across no, names, email, mobiles, department, title |
| **updateEmployee** | `update_employee.py` — patch fields for one `employee_no` |
| **deleteEmployee** | `delete_employee.py <employee_no>` — hard delete |
| **list** (helper) | `list_employee.py` — ordered by `employee_no`, cap with `--limit` |

### Examples

```bash
# Create (flags)
python scripts/create_employee.py \
  --employee-no E001 \
  --full-name "Chan Tai Man" \
  --email chan@example.com \
  --work-mobile "+852 9000 1111" \
  --personal-mobile "+852 6000 2222" \
  --department Engineering \
  --job-title "Software Engineer" \
  --hire-date 2024-01-15

# Create (JSON)
python scripts/create_employee.py --json '{"employee_no":"E002","full_name":"Lee Siu Ming","email":"lee@example.com"}'

# getEmployeeByEmployeeNo
python scripts/get_employee_by_no.py E001

# getEmployeeByEmail (case-insensitive)
python scripts/get_employee_by_email.py Chan@Example.COM

# searchEmployee
python scripts/search_employee.py "Chan" --limit 50

# updateEmployee
python scripts/update_employee.py --employee-no E001 --department HR --employment-status on_leave

# deleteEmployee
python scripts/delete_employee.py E002

# List
python scripts/list_employee.py --limit 100
```

### Response shape

- **Single row:** `{ "ok": true, "employee": { ... } }` or `"employee": null` if not found (lookups still `ok: true`; check null).
- **Search/list:** `{ "ok": true, "count": N, "employees": [ ... ] }`
- **Mutations:** `{ "ok": true, "employee": { ... } }` or `{ "ok": true, "deleted_employee_no": "E002" }`
- **Errors:** `{ "ok": false, "error": "message" }` (non-zero exit)

### Agent notes

- Run from repo root (or use absolute paths for `--json-file` and `EMPLOYEE_DB_PATH`).
- Prefer **`init` once per machine/path** before creates.
- Related modules in the same DB: [LIFECYCLE.md](LIFECYCLE.md), [COMPLIANCE.md](COMPLIANCE.md), [IR56B.md](IR56B.md), [LEAVE.md](LEAVE.md).
- Store personal data only where policy allows; this tooling is **not** legal or security advice.
