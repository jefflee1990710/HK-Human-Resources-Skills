from __future__ import annotations

from tests.utils import run_json_script


def test_employee_success_flow(initialized_db: dict[str, str]) -> None:
    create_payload = run_json_script(
        "create_employee.py",
        args=[
            "--employee-no",
            "E001",
            "--full-name",
            "Chan Tai Man",
            "--email",
            "chan@example.com",
            "--department",
            "HR",
            "--job-title",
            "Officer",
            "--hire-date",
            "2026-01-01",
            "--date-of-birth",
            "1990-05-20",
            "--employment-status",
            "active",
        ],
        env=initialized_db,
    )
    assert create_payload["ok"] is True
    assert create_payload["employee"]["employee_no"] == "E001"

    get_by_no_payload = run_json_script("get_employee_by_no.py", args=["E001"], env=initialized_db)
    assert get_by_no_payload["ok"] is True
    assert get_by_no_payload["employee"]["full_name"] == "Chan Tai Man"

    get_by_email_payload = run_json_script("get_employee_by_email.py", args=["chan@example.com"], env=initialized_db)
    assert get_by_email_payload["ok"] is True
    assert get_by_email_payload["employee"]["employee_no"] == "E001"

    search_payload = run_json_script("search_employee.py", args=["Chan"], env=initialized_db)
    assert search_payload["ok"] is True
    assert search_payload["count"] >= 1

    list_payload = run_json_script("list_employee.py", env=initialized_db)
    assert list_payload["ok"] is True
    assert list_payload["count"] >= 1

    update_payload = run_json_script(
        "update_employee.py",
        args=["--employee-no", "E001", "--department", "People Ops", "--work-mobile", "+85291234567"],
        env=initialized_db,
    )
    assert update_payload["ok"] is True
    assert update_payload["employee"]["department"] == "People Ops"

    delete_payload = run_json_script("delete_employee.py", args=["E001"], env=initialized_db)
    assert delete_payload["ok"] is True
    assert delete_payload["deleted_employee_no"] == "E001"

