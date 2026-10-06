#!/usr/bin/env python3
"""Pre-sign timing wrapper (lab-notebook tier) around the engine's
analyze_confidence.py: identical CLI and computation; it only wraps the
engine's `capture`, `run_probes` and `knowledge_block` with wall-clock timers
(printed as JSON lines) so a throwaway timing pass can be extrapolated phase by
phase. Engine code is imported, never edited. Run from the synaptic-tuner root
inside the pinned engine image, on synthetic (non-PopQA) rows only.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TUNER = Path.cwd()
for p in (TUNER / "Trainers/decision", TUNER):
    sys.path.insert(0, str(p))

import decision_core.confidence_analysis as ca  # noqa: E402

T0 = time.perf_counter()


def _timed(name, fn, size=None):
    def wrapper(*a, **k):
        t = time.perf_counter()
        out = fn(*a, **k)
        rec = {"phase": name, "s": round(time.perf_counter() - t, 2), "t_since_start": round(time.perf_counter() - T0, 1)}
        if size is not None:
            rec["n"] = size(a, k)
        print("TIMING " + json.dumps(rec), flush=True)
        return out
    return wrapper


ca.capture = _timed("capture", ca.capture, lambda a, k: len(a[1]))
ca.run_probes = _timed("run_probes", ca.run_probes, lambda a, k: int(len(a[1])))
ca.knowledge_block = _timed("knowledge_block", ca.knowledge_block)
ca.analyze = _timed("analyze_total", ca.analyze)

import analyze_confidence  # noqa: E402

if __name__ == "__main__":
    rc = analyze_confidence.main(sys.argv[1:])
    print("TIMING " + json.dumps({"phase": "main_total", "s": round(time.perf_counter() - T0, 1)}), flush=True)
    raise SystemExit(rc)
