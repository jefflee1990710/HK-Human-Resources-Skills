from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI

from tests.utils import run_json_script

SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"


def _gemini_api_key() -> str | None:
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise AssertionError("Gemini returned empty content.")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise AssertionError(f"Could not find JSON object in Gemini output:\n{text}")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Gemini output did not contain valid JSON:\n{text}") from exc

    if not isinstance(parsed, dict):
        raise AssertionError(f"Expected JSON object from Gemini, got: {type(parsed)}")
    return parsed


def _build_model(api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        google_api_key=api_key,
        temperature=0,
    )


@pytest.mark.live_gemini
def test_langchain_gemini_selects_employee_workflow_and_applies_skill(initialized_db: dict[str, str]) -> None:
    api_key = _gemini_api_key()
    if not api_key:
        pytest.skip("Set GOOGLE_API_KEY or GEMINI_API_KEY to run live Gemini tests.")

    model = _build_model(api_key)
    skill_excerpt = SKILL_PATH.read_text(encoding="utf-8")
    prompt = f"""
You are routing an HR request using the hkhr-skills module list.

Reference:
{skill_excerpt}

User request:
"Create employee E901 with full name Chan Tai Man and email chan901@example.com, then fetch by employee number."

Return strict JSON object only with this shape:
{{
  "module": "<ADW|EMPLOYEE|LIFECYCLE|COMPLIANCE|LEAVE|IR56B>",
  "recommended_scripts": ["script1.py", "script2.py"],
  "why": "<short reason>"
}}
"""
    response = model.invoke(prompt)
    route = _extract_json_object(response.content if isinstance(response.content, str) else str(response.content))

    assert route["module"] == "EMPLOYEE"
    scripts = [str(s) for s in route.get("recommended_scripts", [])]
    scripts_text = " ".join(scripts).lower()
    assert "employee" in scripts_text
    assert ("create" in scripts_text) or ("upsert" in scripts_text)
    assert ("get" in scripts_text) or ("fetch" in scripts_text)

    create_payload = run_json_script(
        "create_employee.py",
        args=[
            "--employee-no",
            "E901",
            "--full-name",
            "Chan Tai Man",
            "--email",
            "chan901@example.com",
            "--hire-date",
            "2026-01-01",
            "--date-of-birth",
            "1990-02-01",
        ],
        env=initialized_db,
    )
    assert create_payload["ok"] is True

    get_payload = run_json_script("get_employee_by_no.py", args=["E901"], env=initialized_db)
    assert get_payload["ok"] is True
    assert get_payload["employee"]["email"] == "chan901@example.com"


@pytest.mark.live_gemini
def test_langchain_gemini_selects_leave_workflow_and_applies_skill(
    initialized_db: dict[str, str], employee_factory
) -> None:
    api_key = _gemini_api_key()
    if not api_key:
        pytest.skip("Set GOOGLE_API_KEY or GEMINI_API_KEY to run live Gemini tests.")

    employee_factory(employee_no="E902", full_name="Lee Man Yi", email="lee902@example.com")

    model = _build_model(api_key)
    prompt = """
Route this request to one hkhr-skills module and suggest scripts.

Request:
"Seed leave types, submit leave application LA-902 for employee E902 using AL from 2026-05-10 AM to PM, then list leave applications for E902."

Return strict JSON object only:
{
  "module": "<ADW|EMPLOYEE|LIFECYCLE|COMPLIANCE|LEAVE|IR56B>",
  "recommended_scripts": ["script1.py", "script2.py"],
  "why": "<short reason>"
}
"""
    response = model.invoke(prompt)
    route = _extract_json_object(response.content if isinstance(response.content, str) else str(response.content))

    assert route["module"] == "LEAVE"
    scripts = [str(s) for s in route.get("recommended_scripts", [])]
    scripts_text = " ".join(scripts).lower()
    assert "leave" in scripts_text
    assert ("seed" in scripts_text) or ("type" in scripts_text)
    assert "application" in scripts_text

    seed_payload = run_json_script("seed_leave_types.py", env=initialized_db)
    assert seed_payload["ok"] is True

    upsert_payload = run_json_script(
        "upsert_leave_application.py",
        args=[
            "--application-no",
            "LA-902",
            "--employee-no",
            "E902",
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
    assert upsert_payload["ok"] is True

    list_payload = run_json_script("list_leave_applications.py", args=["--employee-no", "E902"], env=initialized_db)
    assert list_payload["ok"] is True
    assert list_payload["count"] >= 1

