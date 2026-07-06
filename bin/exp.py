#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    script_dir = root / ".agents" / "skills" / "experiments" / "scripts"
    sys.path.insert(0, str(script_dir))
    runpy.run_path(str(script_dir / "exp.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
