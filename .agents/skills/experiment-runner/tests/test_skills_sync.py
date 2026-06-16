"""Drift-check gate: the three skill trees must agree with the canonical source.

`.skills/experiment-runner/` is the canonical source; `.claude/skills/` and
`.agents/skills/` are generated mirrors (architecture §7). This test invokes the
repo-root `sync_skills.py --check` and asserts exit 0, making "the trees agree" a
verifiable CI invariant — the closing of the no-sync-mechanism gap (§7.4).

The comparison inside sync_skills.py is sha256 over CRLF-normalized content, NOT
a (possibly rtk-proxied) `diff`, so this test is immune to the documented
false-`identical` banner (§7.1).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Walk up from this test (.skills|.claude|.agents)/skills/experiment-runner/tests/
# to the repo root that owns sync_skills.py. We don't hardcode the depth: search
# upward for the first ancestor containing sync_skills.py so the test works
# identically from whichever mirror it is invoked in.
def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "sync_skills.py").is_file():
            return parent
    raise FileNotFoundError("sync_skills.py not found in any ancestor directory")


REPO_ROOT = _find_repo_root()
SYNC_SCRIPT = REPO_ROOT / "sync_skills.py"


def test_sync_script_exists():
    """The canonical-sync driver must be present at the repo root."""
    assert SYNC_SCRIPT.is_file(), f"missing sync driver: {SYNC_SCRIPT}"


def test_skill_trees_in_sync():
    """`sync_skills.py --check` must exit 0 — no drift across the three trees.

    A non-zero exit means the canonical .skills/ source and a mirror have
    diverged; the fix is `python3 sync_skills.py --write` (never a hand-edit to a
    mirror). The drift report is surfaced in the assertion message.
    """
    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--check", "--skill", "experiment-runner"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        "experiment-runner skill trees have drifted from the canonical .skills/ "
        f"source (run `python3 sync_skills.py --write`):\n{result.stdout}{result.stderr}"
    )


def test_project_context_docs_in_sync():
    """Unscoped sync check also validates root AGENTS.md / CLAUDE.md context."""
    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT), "--check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        "project context docs or skill mirrors have drifted "
        f"(run `python3 sync_skills.py --write`):\n{result.stdout}{result.stderr}"
    )
