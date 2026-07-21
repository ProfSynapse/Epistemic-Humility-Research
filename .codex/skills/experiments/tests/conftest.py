"""Make the experiments skill scripts importable as top-level modules.

Adds the skill's scripts/ dir to sys.path so `import exp` resolves without a
package __init__.py (the skill dir is not a Python package).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
