#!/usr/bin/env python3
"""Open the folder containing the HKHR SQLite database in the system file manager."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

from hkhr_sqlite import get_db_path


def open_folder_in_file_manager(folder: Path) -> None:
    folder = folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(folder)], check=True)
    elif system == "Windows":
        subprocess.run(["explorer", str(folder)], check=True)
    else:
        subprocess.run(["xdg-open", str(folder)], check=True)


def main() -> int:
    try:
        db_path = get_db_path()
        folder = db_path.parent
        open_folder_in_file_manager(folder)
        payload = {
            "ok": True,
            "db_path": str(db_path.resolve()),
            "opened_folder": str(folder.resolve()),
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
