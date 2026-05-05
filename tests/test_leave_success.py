from __future__ import annotations

from tests.utils import run_json_script


def test_leave_success_flow(initialized_db: dict[str, str], employee_factory) -> None:
    employee_factory(employee_no="E301", full_name="Ho Ka Wai", email="ho@example.com")

    seed_payload = run_json_script("seed_leave_types.py", env=initialized_db)
    assert seed_payload["ok"] is True
    assert seed_payload["seeded"] >= 1

    leave_payload = run_json_script(
        "upsert_leave_application.py",
        args=[
            "--application-no",
            "LA-301",
            "--employee-no",
            "E301",
            "--leave-type-no",
            "AL",
            "--from-date",
            "2026-05-10",
            "--to-date",
            "2026-05-10",
            "--from-section",
            "AM",
            "--to-section",
            "PM",
            "--status",
            "Pending",
        ],
        env=initialized_db,
    )
    assert leave_payload["ok"] is True
    assert leave_payload["application"]["application_no"] == "LA-301"

    get_payload = run_json_script("get_leave_application.py", args=["LA-301"], env=initialized_db)
    assert get_payload["ok"] is True
    assert get_payload["application"]["employee_no"] == "E301"

    list_payload = run_json_script("list_leave_applications.py", args=["--employee-no", "E301"], env=initialized_db)
    assert list_payload["ok"] is True
    assert list_payload["count"] >= 1

    compensation_payload = run_json_script(
        "upsert_compensation_leave.py",
        args=[
            "--application-no",
            "CLA-301",
            "--employee-no",
            "E301",
            "--from-date",
            "2026-06-01",
            "--to-date",
            "2026-06-01",
            "--from-section",
            "AM",
            "--to-section",
            "PM",
            "--compensation-from-date",
            "2026-05-15",
            "--compensation-to-date",
            "2026-05-15",
            "--compensation-from-section",
            "AM",
            "--compensation-to-section",
            "PM",
            "--status",
            "Pending",
        ],
        env=initialized_db,
    )
    assert compensation_payload["ok"] is True
    assert compensation_payload["com_leave_application"]["application_no"] == "CLA-301"

    compensation_list_payload = run_json_script(
        "list_compensation_leave.py",
        args=["--employee-no", "E301"],
        env=initialized_db,
    )
    assert compensation_list_payload["ok"] is True
    assert compensation_list_payload["count"] >= 1

