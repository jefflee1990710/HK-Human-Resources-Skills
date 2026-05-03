-- Structured onboarding / offboarding checklist persistence.

CREATE TABLE IF NOT EXISTS lifecycle_template (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  phase                   TEXT NOT NULL
    CHECK (phase IN ('onboarding', 'offboarding')),
  task_code               TEXT NOT NULL,
  title                   TEXT NOT NULL,
  sort_order              INTEGER NOT NULL DEFAULT 0,
  is_required             INTEGER NOT NULL DEFAULT 1
    CHECK (is_required IN (0, 1)),
  created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  UNIQUE (phase, task_code)
);

CREATE TABLE IF NOT EXISTS lifecycle_task_instance (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_no             TEXT NOT NULL,
  phase                   TEXT NOT NULL
    CHECK (phase IN ('onboarding', 'offboarding')),
  task_code               TEXT NOT NULL,
  title                   TEXT NOT NULL,
  status                  TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'done', 'skipped', 'na')),
  due_date                TEXT,
  completed_at            TEXT,
  notes                   TEXT,
  created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  UNIQUE (employee_no, phase, task_code),
  FOREIGN KEY (employee_no) REFERENCES employee(employee_no) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_template_phase_order
  ON lifecycle_template (phase, sort_order, task_code);
CREATE INDEX IF NOT EXISTS idx_lifecycle_instance_employee_phase
  ON lifecycle_task_instance (employee_no, phase);
CREATE INDEX IF NOT EXISTS idx_lifecycle_instance_status
  ON lifecycle_task_instance (status);
