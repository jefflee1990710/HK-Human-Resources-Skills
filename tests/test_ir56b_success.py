from __future__ import annotations

from pathlib import Path

from tests.utils import run_json_script


def test_ir56b_success_flow(initialized_db: dict[str, str], employee_factory, tmp_path: Path) -> None:
    employee_factory(
        employee_no="E401",
        full_name="Ng Chi Kit",
        email="ng@example.com",
        hire_date="2025-10-01",
        date_of_birth="1992-04-18",
        residential_address="Flat B, Kowloon",
    )

    upsert_payload = run_json_script(
        "upsert_ir56b_profile.py",
        args=[
            "--employee-no",
            "E401",
            "--hkid",
            "A1234567",
            "--address-1",
            "Flat B, Kowloon",
            "--address-area-code",
            "KLN",
        ],
        env=initialized_db,
    )
    assert upsert_payload["ok"] is True
    assert upsert_payload["profile"]["employee_no"] == "E401"

    readiness_payload = run_json_script("check_ir56b_readiness.py", args=["E401"], env=initialized_db)
    assert readiness_payload["ok"] is True
    assert readiness_payload["ready"] is True

    output_path = tmp_path / "ir56b_fill_template.xlsx"
    export_payload = run_json_script(
        "export_ir56b_xlsx.py",
        args=["--output", str(output_path)],
        env=initialized_db,
    )
    assert export_payload["ok"] is True
    assert output_path.exists()

