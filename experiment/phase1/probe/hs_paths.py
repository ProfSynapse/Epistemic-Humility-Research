#!/usr/bin/env python3
"""Shared repo-anchored path constants/helpers for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). Holds REPO_ROOT and the _rel
display helper so every harness module can render repo-relative paths without
re-deriving the root. NOTE: PROBE_DIR deliberately does NOT live here — it is the
test monkeypatch seam (`monkeypatch.setattr(hsp, "PROBE_DIR", ...)`), so it stays
a module-level attribute on the hidden_state_probe facade and every PROBE_DIR
reader stays physically in the facade so the patched value is observed at call
time (a copy imported into a helper module would not see the patch). REPO_ROOT is
never monkeypatched, so it is safe to centralize here.
"""

from __future__ import annotations

from pathlib import Path

# Repo root is four levels up (experiment/phase1/probe/hs_paths.py).
REPO_ROOT = Path(__file__).resolve().parents[3]


def _rel(path: Path) -> str:
    """Path relative to REPO_ROOT for display, or absolute if outside it."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
