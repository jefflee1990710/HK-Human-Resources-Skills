#!/usr/bin/env python3
from __future__ import annotations

import sys

from _leave_core import main


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "leave-type-delete", *sys.argv[1:]]
    raise SystemExit(main())
