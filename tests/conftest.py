from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from .utils import REPO_ROOT, run_json_script


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def test_env(tmp_path: Path) -> dict[str, str]:
    db_path = tmp_path / "hrcore.db"
    env = os.environ.copy()
    env["EMPLOYEE_DB_PATH"] = str(db_path)
    return env


@pytest.fixture
def initialized_db(test_env: dict[str, str]) -> dict[str, str]:
    payload = run_json_script("init_employee.py", env=test_env)
    assert payload.get("ok") is True
    return test_env


@pytest.fixture
def employee_factory(initialized_db: dict[str, str]) -> Callable[..., dict[str, Any]]:
    def _create(**overrides: Any) -> dict[str, Any]:
        data = {
            "employee_no": "E001",
            "full_name": "Chan Tai Man",
            "email": "chan@example.com",
            "hire_date": "2026-01-01",
            "date_of_birth": "1990-05-20",
            "employment_status": "active",
            "residential_address": "Flat A, HK Island",
            "department": "HR",
            "job_title": "Officer",
        }
        data.update(overrides)

        args = []
        for key, value in data.items():
            if value is None:
                continue
            args.extend([f"--{key.replace('_', '-')}", str(value)])

        payload = run_json_script("create_employee.py", args=args, env=initialized_db)
        assert payload.get("ok") is True
        return payload

    return _create

