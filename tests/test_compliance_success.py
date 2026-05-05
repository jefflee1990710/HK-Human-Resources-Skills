from __future__ import annotations

from tests.utils import run_json_script


def test_compliance_success_flow(initialized_db: dict[str, str], employee_factory) -> None:
    employee_factory(employee_no="E201", full_name="Wong Siu Ming", email="wong@example.com")

    create_payload = run_json_script(
        "create_compliance.py",
        args=[
            "--employee-no",
            "E201",
            "--record-type",
            "contract",
            "--title",
            "Employment Contract 2026",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-12-31",
            "--country",
            "HK",
        ],
        env=initialized_db,
    )
    assert create_payload["ok"] is True
    record_id = create_payload["record"]["id"]

    list_payload = run_json_script("list_compliance.py", args=["--employee-no", "E201"], env=initialized_db)
    assert list_payload["ok"] is True
    assert list_payload["count"] >= 1

    get_payload = run_json_script("get_compliance.py", args=[str(record_id)], env=initialized_db)
    assert get_payload["ok"] is True
    assert get_payload["record"]["title"] == "Employment Contract 2026"

    update_payload = run_json_script(
        "update_compliance.py",
        args=[str(record_id), "--title", "Employment Contract 2026 Revised", "--remarks", "Validated"],
        env=initialized_db,
    )
    assert update_payload["ok"] is True
    assert update_payload["record"]["title"] == "Employment Contract 2026 Revised"

    delete_payload = run_json_script("delete_compliance.py", args=[str(record_id)], env=initialized_db)
    assert delete_payload["ok"] is True
    assert delete_payload["deleted_id"] == record_id

