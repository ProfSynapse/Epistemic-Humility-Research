"""Unit tests for the sync_skills.py drift-detection + prune mechanics (§7).

The sibling test_skills_sync.py asserts the LIVE trees are in sync (`--check`
exit 0 against the real .skills/.claude/.agents trees). That is the GREEN-NOW
invariant — but it cannot tell a working drift-check from a broken one that
always returns "in sync": a `check_skill` hard-wired to return `[]` would pass
it. This file closes that gap by exercising the FAILURE directions of the gate
against a synthetic three-tree layout, so the load-bearing behaviors are proven:

  * check_skill DETECTS content drift, missing-in-mirror, and extra-in-mirror.
  * check_skill is CRLF-agnostic (a CRLF-only delta is NOT drift) — the
    rtk-proxied-diff-proof property (§7.1).
  * write_skill propagates canonical -> both mirrors LF-normalized AND PRUNES
    stale mirror files (the exact-image guarantee, §7.4).

These are pure-function tests: sync_skills' module-level CANONICAL_ROOT /
MIRROR_ROOTS are monkeypatched onto a tmp_path tree, so nothing touches the real
skill trees. GPU-free, hermetic, no subprocess.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_sync_module():
    """Import the repo-root sync_skills.py as a module (it is not on sys.path).

    Walk up from this test (works identically from any of the three mirror trees)
    to the first ancestor owning bin/sync_skills.py, then load it by file path.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "bin" / "sync_skills.py"
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location("sync_skills", candidate)
            module = importlib.util.module_from_spec(spec)
            # Register before exec so dataclasses / future imports resolve cleanly.
            sys.modules.setdefault("sync_skills", module)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("bin/sync_skills.py not found in any ancestor directory")


sync_skills = _load_sync_module()
SKILL = "demo-skill"


@pytest.fixture()
def synthetic_trees(tmp_path: Path, monkeypatch):
    """A canonical tree + two mirrors under tmp_path, all initially in sync.

    Returns (canonical_dir, mirror_dirs). The module's CANONICAL_ROOT /
    MIRROR_ROOTS globals are repointed here so check_skill / write_skill operate
    on the synthetic layout, never the real trees.
    """
    canonical_root = tmp_path / ".skills"
    mirror_roots = (tmp_path / ".claude" / "skills", tmp_path / ".agents" / "skills")

    canonical_dir = canonical_root / SKILL
    (canonical_dir / "scripts").mkdir(parents=True)
    (canonical_dir / "SKILL.md").write_text("# demo\nline\n", encoding="utf-8")
    (canonical_dir / "scripts" / "run.py").write_text("print('hi')\n", encoding="utf-8")

    monkeypatch.setattr(sync_skills, "CANONICAL_ROOT", canonical_root)
    monkeypatch.setattr(sync_skills, "MIRROR_ROOTS", mirror_roots)

    # Seed both mirrors as exact images via the function under test.
    sync_skills.write_skill(SKILL)
    mirror_dirs = [root / SKILL for root in mirror_roots]
    assert sync_skills.check_skill(SKILL) == []  # precondition: in sync
    return canonical_dir, mirror_dirs


# --- write_skill: propagation + prune ----------------------------------------

def test_write_propagates_canonical_to_both_mirrors(synthetic_trees):
    canonical_dir, mirror_dirs = synthetic_trees
    for mirror in mirror_dirs:
        assert (mirror / "SKILL.md").read_text(encoding="utf-8") == "# demo\nline\n"
        assert (mirror / "scripts" / "run.py").read_text(encoding="utf-8") == "print('hi')\n"


def test_write_prunes_stale_mirror_file(synthetic_trees):
    """A file present in a mirror but not in canonical is REMOVED by --write.

    This is the exact-image guarantee (§7.4): mirrors are a mechanical image of
    canonical, never an accreting superset. Mission-named candidate gap.
    """
    canonical_dir, mirror_dirs = synthetic_trees
    stale = mirror_dirs[0] / "scripts" / "obsolete.py"
    stale.write_text("# left over from a deleted canonical file\n", encoding="utf-8")
    # Drift-check sees the extra file (proves the precondition for the prune).
    assert any("obsolete.py" in d for d in sync_skills.check_skill(SKILL))

    sync_skills.write_skill(SKILL)

    assert not stale.exists()  # pruned
    assert sync_skills.check_skill(SKILL) == []  # back in sync


def test_write_lf_normalizes_crlf_canonical_into_mirrors(synthetic_trees):
    """--write strips CRLF so a mirror never gains line endings canonical lacks."""
    canonical_dir, mirror_dirs = synthetic_trees
    (canonical_dir / "SKILL.md").write_bytes(b"# demo\r\nwindows\r\n")
    sync_skills.write_skill(SKILL)
    for mirror in mirror_dirs:
        assert (mirror / "SKILL.md").read_bytes() == b"# demo\nwindows\n"


# --- check_skill: the FAILURE directions of the gate -------------------------

def test_check_detects_content_drift(synthetic_trees):
    """A mirror file edited out of agreement is reported as content drift.

    The load-bearing gate behavior: without this, a hand-edited mirror ships
    silently. The sibling happy-path test cannot catch a check_skill that never
    reports drift; this one can.
    """
    canonical_dir, mirror_dirs = synthetic_trees
    (mirror_dirs[1] / "scripts" / "run.py").write_text(
        "print('TAMPERED')\n", encoding="utf-8")
    drift = sync_skills.check_skill(SKILL)
    assert any("run.py" in d and "content differs" in d for d in drift)


def test_check_detects_missing_in_mirror(synthetic_trees):
    canonical_dir, mirror_dirs = synthetic_trees
    (mirror_dirs[0] / "SKILL.md").unlink()
    drift = sync_skills.check_skill(SKILL)
    assert any("SKILL.md" in d and "absent in mirror" in d for d in drift)


def test_check_detects_extra_in_mirror(synthetic_trees):
    canonical_dir, mirror_dirs = synthetic_trees
    (mirror_dirs[0] / "scripts" / "extra.py").write_text("# extra\n", encoding="utf-8")
    drift = sync_skills.check_skill(SKILL)
    assert any("extra.py" in d and "absent in canonical" in d for d in drift)


def test_check_is_crlf_agnostic(synthetic_trees):
    """A CRLF-only difference is NOT drift (the rtk-diff-proof property, §7.1).

    Same content, different line endings => check_skill reports IN SYNC. This is
    why the gate hashes CRLF-normalized bytes rather than trusting a proxied diff.
    """
    canonical_dir, mirror_dirs = synthetic_trees
    # Rewrite one mirror file with CRLF but identical logical content.
    (mirror_dirs[0] / "SKILL.md").write_bytes(b"# demo\r\nline\r\n")
    assert sync_skills.check_skill(SKILL) == []  # CRLF-only => still in sync


def test_check_reports_mirror_missing_entirely(synthetic_trees, tmp_path):
    """If a whole mirror dir is gone, --check reports it (does not crash)."""
    canonical_dir, mirror_dirs = synthetic_trees
    import shutil
    shutil.rmtree(mirror_dirs[0])
    drift = sync_skills.check_skill(SKILL)
    assert any("mirror missing entirely" in d for d in drift)


# --- main() CLI exit-code gate (F1) ------------------------------------------
#
# The tests above prove check_skill / write_skill at the FUNCTION level. The thin
# main() wrapper turns a non-empty drift list into `return 1` + a printed DRIFT
# report (and the in-sync case into `return 0`). That wrapper was untested — the
# CI gate's FAILURE exit code was green-by-omission one level above check_skill.
# An inverted or wrong exit code in main() would pass CI silently even though
# check_skill correctly detects drift. These tests close that gap by driving the
# real argv entrypoint in-process.

def test_main_check_returns_1_and_reports_on_drift(synthetic_trees, capsys):
    """`main(['--check', ...])` exits 1 AND prints the DRIFT report when a mirror
    has diverged — the CI gate's fail direction (F1)."""
    canonical_dir, mirror_dirs = synthetic_trees
    (mirror_dirs[0] / "SKILL.md").write_text("# tampered\n", encoding="utf-8")
    rc = sync_skills.main(["--check", "--skill", SKILL])
    assert rc == 1
    out = capsys.readouterr().out
    assert "DRIFT" in out  # the report is surfaced, not swallowed


def test_main_check_returns_0_when_in_sync(synthetic_trees, capsys):
    """`main(['--check', ...])` exits 0 against the in-sync synthetic tree — the
    happy path at the CLI level (the sibling test_skills_sync.py covers exit-0
    against the LIVE trees via subprocess; this covers it in-process)."""
    rc = sync_skills.main(["--check", "--skill", SKILL])
    assert rc == 0


def test_main_write_then_check_clears_the_gate(synthetic_trees):
    """`main(['--write'])` after a drift re-images the mirrors, so the following
    `main(['--check'])` returns 0 — proves the write path clears the gate."""
    canonical_dir, mirror_dirs = synthetic_trees
    (mirror_dirs[0] / "scripts" / "stale.py").write_text("# stale\n", encoding="utf-8")
    assert sync_skills.main(["--check", "--skill", SKILL]) == 1  # drift present
    assert sync_skills.main(["--write", "--skill", SKILL]) == 0  # re-image
    assert sync_skills.main(["--check", "--skill", SKILL]) == 0  # back in sync


def test_project_context_check_detects_agent_claude_drift(tmp_path, monkeypatch):
    """Root AGENTS.md and CLAUDE.md must share one orchestrator section."""
    agents = tmp_path / "AGENTS.md"
    claude = tmp_path / "CLAUDE.md"
    agents.write_text(
        "prefix\n\n<!-- PROJECT_ORCHESTRATOR_START -->\n# Canonical\n<!-- PROJECT_ORCHESTRATOR_END -->\n",
        encoding="utf-8",
    )
    claude.write_text(
        "<!-- PROJECT_ORCHESTRATOR_START -->\n# Drifted\n<!-- PROJECT_ORCHESTRATOR_END -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sync_skills, "PROJECT_CONTEXT_DOCS", (agents, claude))
    monkeypatch.setattr(sync_skills, "PROJECT_CONTEXT_CANONICAL", agents)

    drift = sync_skills.check_project_context_docs()

    assert any("project orchestrator section differs" in item for item in drift)


def test_project_context_write_repairs_claude_from_agents(tmp_path, monkeypatch):
    """Unscoped --write can refresh CLAUDE.md from AGENTS.md without touching skills."""
    agents = tmp_path / "AGENTS.md"
    claude = tmp_path / "CLAUDE.md"
    canonical = (
        "<!-- PROJECT_ORCHESTRATOR_START -->\n"
        "# Canonical\n"
        "Use root project context only.\n"
        "<!-- PROJECT_ORCHESTRATOR_END -->\n"
    )
    agents.write_text("PACT block stays outside\n\n" + canonical, encoding="utf-8")
    claude.write_text("# Existing Claude notes\n", encoding="utf-8")
    monkeypatch.setattr(sync_skills, "PROJECT_CONTEXT_DOCS", (agents, claude))
    monkeypatch.setattr(sync_skills, "PROJECT_CONTEXT_CANONICAL", agents)

    assert sync_skills.write_project_context_docs() == 1

    assert sync_skills.check_project_context_docs() == []
    assert "PACT block stays outside" not in claude.read_text(encoding="utf-8")
    assert "# Existing Claude notes" in claude.read_text(encoding="utf-8")
