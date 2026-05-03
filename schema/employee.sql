-- Fixed Employee schema for hkhr-skills SQLite database.
-- Apply with: python scripts/employee_db.py init

CREATE TABLE IF NOT EXISTS employee (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_no           TEXT NOT NULL UNIQUE,
  full_name             TEXT NOT NULL,
  preferred_name        TEXT,
  email                 TEXT UNIQUE,
  work_mobile           TEXT,
  personal_mobile       TEXT,
  date_of_birth         TEXT,
  -- ISO8601 date (YYYY-MM-DD); optional
  nationality           TEXT,
  residential_address   TEXT,
  department            TEXT,
  job_title             TEXT,
  hire_date             TEXT,
  -- ISO8601 date (YYYY-MM-DD)
  employment_status     TEXT NOT NULL DEFAULT 'active'
    CHECK (employment_status IN ('active', 'on_leave', 'terminated', 'probation')),
  notes                 TEXT,
  created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_employee_email ON employee (email);
CREATE INDEX IF NOT EXISTS idx_employee_full_name ON employee (full_name);
CREATE INDEX IF NOT EXISTS idx_employee_status ON employee (employment_status);
