# Employee management (SQLite)

Use this module to maintain a **fixed-schema** employee directory backed by **SQLite**, with CLI scripts that return **JSON** so an agent can query and update records safely.

## Database location

| Default path | Override |
|--------------|----------|
| `data/employees.db` (under repo root) | Set `EMPLOYEE_DB_PATH` to an absolute or user-expanded path |

Create the file and tables once:

```bash
python scripts/employee_db.py init
```

`init` now applies **all SQLite module schemas** in this repo (`employee`, `employee_ir56b`, `lifecycle`, `compliance`, `leave`) into the same database file.

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

## Script: `scripts/employee_db.py`

Single entrypoint; every command prints **one JSON object** to stdout (`ok`, payload or `error`).

### Setup

- `init` — apply schema (idempotent `CREATE IF NOT EXISTS`).

### Operations (aliases for agent workflows)

| Intent | Command |
|--------|---------|
| **createEmployee** | `create` |
| **getEmployeeByEmployeeNo** | `get-by-no <employee_no>` |
| **getEmployeeByEmail** | `get-by-email <email>` |
| **searchEmployee** | `search <query>` — substring match across no, names, email, mobiles, department, title |
| **updateEmployee** | `update` — patch fields for one `employee_no` |
| **deleteEmployee** | `delete <employee_no>` — hard delete |
| **list** (helper) | `list` — ordered by `employee_no`, cap with `--limit` |

### Examples

```bash
# Create (flags)
python scripts/employee_db.py create \
  --employee-no E001 \
  --full-name "Chan Tai Man" \
  --email chan@example.com \
  --work-mobile "+852 9000 1111" \
  --personal-mobile "+852 6000 2222" \
  --department Engineering \
  --job-title "Software Engineer" \
  --hire-date 2024-01-15

# Create (JSON)
python scripts/employee_db.py create --json '{"employee_no":"E002","full_name":"Lee Siu Ming","email":"lee@example.com"}'

# getEmployeeByEmployeeNo
python scripts/employee_db.py get-by-no E001

# getEmployeeByEmail (case-insensitive)
python scripts/employee_db.py get-by-email Chan@Example.COM

# searchEmployee
python scripts/employee_db.py search "Chan" --limit 50

# updateEmployee
python scripts/employee_db.py update --employee-no E001 --department HR --employment-status on_leave

# deleteEmployee
python scripts/employee_db.py delete E002

# List
python scripts/employee_db.py list --limit 100
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
