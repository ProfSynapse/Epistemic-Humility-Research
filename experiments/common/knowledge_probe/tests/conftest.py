"""Test path setup for the migrated knowledge-probe/mechinterp layout."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
KNOWLEDGE_PROBE = ROOT / "experiments/common/knowledge_probe"
MECHINTERP = ROOT / "experiments/common/mechinterp"
COMMON_READOUTS = ROOT / "experiments/common/readouts"
DOUBT_REGULATED = ROOT / "experiments/doubt-regulated-caution"
SELFAWARE_CONTROLS = ROOT / "experiments/selfaware-latent-knowledge-controls"

for path in (
    KNOWLEDGE_PROBE,
    MECHINTERP,
    COMMON_READOUTS,
    DOUBT_REGULATED,
    SELFAWARE_CONTROLS,
    ROOT / "experiment/phase1/eval",
):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
