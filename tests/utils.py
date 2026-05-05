from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_script(
    script_name: str,
    args: list[str] | None = None,
    *,
    env: dict[str, str] | None = None,
    expect_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path), *(args or [])]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env or os.environ.copy(),
        capture_output=True,
        text=True,
    )
    if expect_success and proc.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(cmd)}\n"
            f"exit_code={proc.returncode}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc


def parse_json_output(output: str) -> dict[str, Any]:
    text = output.strip()
    if not text:
        raise AssertionError("Expected JSON output but stdout was empty.")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON output:\n{text}") from exc
    if not isinstance(parsed, dict):
        raise AssertionError(f"Expected JSON object output, got: {type(parsed)}")
    return parsed


def run_json_script(
    script_name: str,
    args: list[str] | None = None,
    *,
    env: dict[str, str] | None = None,
    expect_success: bool = True,
) -> dict[str, Any]:
    proc = run_script(script_name, args, env=env, expect_success=expect_success)
    return parse_json_output(proc.stdout)

