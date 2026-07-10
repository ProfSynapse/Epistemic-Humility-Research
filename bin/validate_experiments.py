#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    script = root / ".agents" / "skills" / "experiments" / "scripts" / "exp.py"
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), "validate", *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
