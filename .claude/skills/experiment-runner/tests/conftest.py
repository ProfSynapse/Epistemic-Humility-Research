"""Make the experiment-runner scripts importable as top-level modules.

Adds the skill's scripts/ dir to sys.path so `import run_matrix` /
`import check_prereqs` resolve without package __init__.py files (the skill dir
is not a Python package and lives outside any workstream's S2 package tree).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
