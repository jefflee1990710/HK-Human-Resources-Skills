from __future__ import annotations

from tests.utils import run_json_script


def test_lifecycle_success_flow(initialized_db: dict[str, str], employee_factory) -> None:
    employee_factory(employee_no="E101", full_name="Lee Ka Yan", email="lee@example.com")

    seed_payload = run_json_script("seed_lifecycle_templates.py", env=initialized_db)
    assert seed_payload["ok"] is True
    assert seed_payload["seeded"] >= 1

    sync_payload = run_json_script("sync_lifecycle_tasks.py", args=["E101", "onboarding"], env=initialized_db)
    assert sync_payload["ok"] is True
    assert sync_payload["created"] >= 1

    list_payload = run_json_script(
        "list_lifecycle_tasks.py",
        args=["--employee-no", "E101", "--phase", "onboarding"],
        env=initialized_db,
    )
    assert list_payload["ok"] is True
    assert list_payload["count"] >= 1

    status_payload = run_json_script(
        "set_lifecycle_task_status.py",
        args=["E101", "onboarding", "contract_sign", "done"],
        env=initialized_db,
    )
    assert status_payload["ok"] is True
    assert status_payload["task"]["status"] == "done"

