# SYSTEM (hkhr-skills)

This document is **system-only**: paths, environment, and small operator utilities. It does not describe HR domain workflows (see [SKILL.md](SKILL.md) and the module `*.md` files).

## SQLite database path

- **Default file:** `~/.hkhrcore/hrcore.db` on macOS/Linux; `%USERPROFILE%\.hkhrcore\hrcore.db` on Windows.
- **Override:** set `EMPLOYEE_DB_PATH` to an absolute or user-expanded path; all feature scripts use the same resolution.
- **Implementation:** `get_db_path()` in [`scripts/hkhr_sqlite.py`](scripts/hkhr_sqlite.py).

## Open database folder in the default file manager

**Purpose:** Reveal the directory that contains the active SQLite file so you can copy it, inspect permissions, or open it in a GUI database tool manually.

**Script:** [`scripts/open_db_folder.py`](scripts/open_db_folder.py)

**What it does:**

- Resolves the database path via `EMPLOYEE_DB_PATH` or the default above.
- Creates the parent directory tree if it does not exist (same parent as the DB file would use on first connect).
- Opens that parent folder in the OS default file manager:
  - **macOS:** `open`
  - **Windows:** `explorer`
  - **Linux and other Unix:** `xdg-open`

**Usage (from repo root):**

```bash
python scripts/open_db_folder.py
```

**Stdout (JSON):**

- Success: `{"ok": true, "db_path": "<resolved db file>", "opened_folder": "<parent directory>"}`
- Failure: `{"ok": false, "error": "<message>"}`

Exit code `0` on success, non-zero on failure—aligned with other `scripts/*.py` tools.

**Limitations:**

- Does not open the `.db` inside a SQLite app; it only opens the **folder**.
- SSH sessions, CI, or headless hosts may fail if no graphical file manager is available; errors are returned in JSON and stderr from the underlying command.
