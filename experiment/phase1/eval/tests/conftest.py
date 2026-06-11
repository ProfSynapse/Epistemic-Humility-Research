"""experiment/phase1/eval/tests/conftest.py

Make the eval modules importable as top-level modules (scorers, stats, run_eval)
without requiring package __init__.py files in the parent experiment/ tree
(which is outside this workstream's S2 boundary). Adds the eval dir to sys.path.
"""

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
