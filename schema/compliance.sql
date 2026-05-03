-- Employment compliance dates: contracts, work eligibility, and related records.

CREATE TABLE IF NOT EXISTS employment_compliance (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_no             TEXT NOT NULL,
  record_type             TEXT NOT NULL
    CHECK (record_type IN ('contract', 'work_eligibility', 'other')),
  title                   TEXT NOT NULL,
  start_date              TEXT,
  end_date                TEXT,
  reference_no            TEXT,
  country                 TEXT,
  remarks                 TEXT,
  created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  FOREIGN KEY (employee_no) REFERENCES employee(employee_no) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_compliance_employee_no
  ON employment_compliance (employee_no);
CREATE INDEX IF NOT EXISTS idx_compliance_record_type
  ON employment_compliance (record_type);
CREATE INDEX IF NOT EXISTS idx_compliance_end_date
  ON employment_compliance (end_date);
