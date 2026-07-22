"""Make the data-exhaust skill scripts importable as top-level modules.

Adds the skill's scripts/ dir to sys.path so `import build_exhaust_dataset`
and `import verify_exhaust` resolve without a package __init__.py (the skill
dir is not a Python package), matching the pattern already used by the
experiments skill's tests/conftest.py.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
