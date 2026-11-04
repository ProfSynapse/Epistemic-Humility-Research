import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

# Default to this immutable fixture; an explicit external contract remains supported.
import os
os.environ.setdefault("EHR_R2_CONTRACT_DIR",str(Path(__file__).resolve().parents[1]))
