-- IR56B extension fields (1:1 with employee via employee_no).

CREATE TABLE IF NOT EXISTS employee_ir56b (
  employee_no             TEXT PRIMARY KEY,
  hkid                    TEXT,
  passport_no             TEXT,
  place_of_birth          TEXT,
  marital_status          TEXT,
  address_1               TEXT,
  address_2               TEXT,
  address_3               TEXT,
  address_area_code       TEXT,
  contact_address_1       TEXT,
  contact_address_2       TEXT,
  contact_address_3       TEXT,
  contact_area_code       TEXT,
  spouse_name             TEXT,
  spouse_hkid             TEXT,
  spouse_passport_no      TEXT,
  notes                   TEXT,
  created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
  FOREIGN KEY (employee_no) REFERENCES employee(employee_no) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_employee_ir56b_hkid ON employee_ir56b (hkid);
CREATE INDEX IF NOT EXISTS idx_employee_ir56b_passport_no ON employee_ir56b (passport_no);
