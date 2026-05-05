from __future__ import annotations

from pathlib import Path

import pandas as pd

from tests.utils import run_script


def test_adw_calculation_success(tmp_path: Path) -> None:
    workbook_path = tmp_path / "adw_input.xlsx"
    output_dir = tmp_path / "adw_output"

    salary_df = pd.DataFrame(
        [
            {
                "employee_id": "E501",
                "month": "2026-04",
                "base_salary": 20000,
                "allowance": 1000,
                "commission": 500,
                "bonus": 0,
                "deduction": 0,
            },
            {
                "employee_id": "E501",
                "month": "2026-05",
                "base_salary": 21000,
                "allowance": 1000,
                "commission": 800,
                "bonus": 0,
                "deduction": 0,
            },
        ]
    )
    leave_df = pd.DataFrame(
        [
            {
                "employee_id": "E501",
                "month": "2026-05",
                "annual_leave_days": 1,
                "sick_leave_days": 0,
                "unpaid_leave_days": 0,
            }
        ]
    )

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        salary_df.to_excel(writer, sheet_name="salary", index=False)
        leave_df.to_excel(writer, sheet_name="leave", index=False)

    proc = run_script(
        "calculate_adw_salary.py",
        args=[
            "--input",
            str(workbook_path),
            "--month",
            "2026-05",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert proc.returncode == 0
    assert (output_dir / "mapping_report.json").exists()
    assert (output_dir / "employee_payout_summary.csv").exists()
    assert (output_dir / "employee_payout_breakdown.csv").exists()
    assert (output_dir / "employee_adw_details.csv").exists()
    assert (output_dir / "calculation_warnings.csv").exists()

