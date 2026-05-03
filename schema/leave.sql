-- Leave type and leave applications aligned with hrsys_web_v2 leave models.

CREATE TABLE IF NOT EXISTS leave_type (
  leave_type_no            TEXT PRIMARY KEY,
  name                     TEXT NOT NULL,
  description              TEXT NOT NULL,
  leave_unit               TEXT NOT NULL
    CHECK (leave_unit IN ('Day', 'Hour')),
  color                    TEXT,
  can_apply                INTEGER NOT NULL DEFAULT 1
    CHECK (can_apply IN (0, 1)),
  paid                     INTEGER NOT NULL DEFAULT 0
    CHECK (paid IN (0, 1)),
  paid_ratio               REAL,
  enable_paid_function     INTEGER
    CHECK (enable_paid_function IN (0, 1) OR enable_paid_function IS NULL),
  paid_function            TEXT,
  allow_negative_balance   INTEGER NOT NULL DEFAULT 0
    CHECK (allow_negative_balance IN (0, 1)),
  reason_required          INTEGER NOT NULL DEFAULT 0
    CHECK (reason_required IN (0, 1)),
  attachment_required      INTEGER NOT NULL DEFAULT 0
    CHECK (attachment_required IN (0, 1)),
  created_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS leave_application (
  application_no           TEXT PRIMARY KEY,
  employee_no              TEXT NOT NULL,
  leave_type_no            TEXT NOT NULL,
  application_ts           TEXT NOT NULL,
  from_date                TEXT NOT NULL,
  to_date                  TEXT NOT NULL,
  from_section             TEXT NOT NULL
    CHECK (from_section IN ('AM', 'PM')),
  to_section               TEXT NOT NULL
    CHECK (to_section IN ('AM', 'PM')),
  no_of_days               REAL,
  reason                   TEXT,
  attachment_filenames     TEXT,
  next_approver            TEXT,
  next_approve_level       INTEGER NOT NULL DEFAULT 1,
  total_approve_level      INTEGER NOT NULL DEFAULT 1,
  approved_ts              TEXT,
  rejected_ts              TEXT,
  cancelled_ts             TEXT,
  status                   TEXT NOT NULL
    CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Cancelled')),
  created_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  FOREIGN KEY (employee_no) REFERENCES employee(employee_no) ON DELETE CASCADE,
  FOREIGN KEY (leave_type_no) REFERENCES leave_type(leave_type_no)
);

CREATE TABLE IF NOT EXISTS compensation_leave_application (
  application_no              TEXT PRIMARY KEY,
  employee_no                 TEXT NOT NULL,
  application_ts              TEXT NOT NULL,
  from_date                   TEXT NOT NULL,
  to_date                     TEXT NOT NULL,
  from_section                TEXT NOT NULL
    CHECK (from_section IN ('AM', 'PM')),
  to_section                  TEXT NOT NULL
    CHECK (to_section IN ('AM', 'PM')),
  compensation_from_date      TEXT NOT NULL,
  compensation_to_date        TEXT NOT NULL,
  compensation_from_section   TEXT NOT NULL
    CHECK (compensation_from_section IN ('AM', 'PM')),
  compensation_to_section     TEXT NOT NULL
    CHECK (compensation_to_section IN ('AM', 'PM')),
  reason                      TEXT,
  attachment_filenames        TEXT,
  next_approver               TEXT,
  next_approve_level          INTEGER NOT NULL DEFAULT 1,
  total_approve_level         INTEGER NOT NULL DEFAULT 1,
  approved_ts                 TEXT,
  rejected_ts                 TEXT,
  status                      TEXT NOT NULL
    CHECK (status IN ('Pending', 'Approved', 'Rejected')),
  created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  FOREIGN KEY (employee_no) REFERENCES employee(employee_no) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_leave_application_employee_no
  ON leave_application (employee_no);
CREATE INDEX IF NOT EXISTS idx_leave_application_status
  ON leave_application (status);
CREATE INDEX IF NOT EXISTS idx_leave_application_leave_type
  ON leave_application (leave_type_no);
CREATE INDEX IF NOT EXISTS idx_com_leave_employee_no
  ON compensation_leave_application (employee_no);
CREATE INDEX IF NOT EXISTS idx_com_leave_status
  ON compensation_leave_application (status);
