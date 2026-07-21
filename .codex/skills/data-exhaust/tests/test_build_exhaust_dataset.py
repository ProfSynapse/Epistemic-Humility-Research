"""Smoke tests for the aggregate-mode copy-everything fix.

Regression target: build_exhaust_dataset.py's aggregate mode used to copy
only a fixed 9-name allowlist one level deep under analysis-committed/<cell>/,
which silently dropped every other experiment family's artifact vocabulary
(flat top-level files, three-level nesting, non-JSON files, non-allowlisted
names). These tests build a synthetic experiment tree that reproduces both a
flat layout and a nested/celled layout plus a hard-excluded path, and assert:

  1. every non-excluded source file is copied byte-for-byte, at any depth;
  2. a file whose relative path matches a hard-exclusion pattern is skipped
     and recorded (not copied, not silently dropped either -- accounted for);
  3. a file whose CONTENT matches a hard-exclusion pattern aborts the whole
     build (SystemExit), even if its path is clean;
  4. verify_exhaust.py's completeness check independently re-walks the
     source tree and fails loudly if the staged output and the source
     disagree, and fails (not silently passes) if --experiment-dir is
     omitted entirely.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import build_exhaust_dataset
import verify_exhaust


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_experiment(root: Path, slug: str) -> Path:
    """A minimal experiments/<slug>/ dir: experiment.yaml + AMENDMENT.md,
    with no analysis-committed/ yet (callers populate that)."""
    exp_dir = root / slug
    exp_dir.mkdir(parents=True)
    (exp_dir / "experiment.yaml").write_text(
        f"slug: {slug}\nstatus: resolved\ninstrument:\n  pins: {{}}\n",
        encoding="utf-8",
    )
    (exp_dir / "AMENDMENT.md").write_text("# amendment\n", encoding="utf-8")
    return exp_dir


@pytest.fixture()
def mixed_layout_experiment(tmp_path: Path) -> Path:
    """Reproduces the two layout shapes that broke the old allowlist:
    a flat top-level file, a nested (celled) subdirectory, a deeper
    three-level nested subdirectory, a non-JSON file, and one file whose
    relative PATH matches the bridge_llama2_7b_chat hard exclusion."""
    exp_dir = _make_experiment(tmp_path, "mixed-layout-exp")
    committed = exp_dir / "analysis-committed"

    # Flat: a top-level file with a name the old 9-name allowlist never knew.
    (committed).mkdir(parents=True)
    (committed / "final_report.json").write_text('{"result": "ok"}\n', encoding="utf-8")

    # Nested/celled: one level, like the old allowlist expected.
    (committed / "cell_a").mkdir()
    (committed / "cell_a" / "dose_fit.json").write_text('{"dose": 1}\n', encoding="utf-8")

    # Deeper nesting + non-JSON file, like bb-base-propensity-fit-read.
    (committed / "phase1" / "sub").mkdir(parents=True)
    (committed / "phase1" / "sub" / "notes.md").write_text("# notes\n", encoding="utf-8")

    # A path-level hard exclusion: must be skipped, not copied, not aborting.
    (committed / "bridge_llama2_7b_chat").mkdir()
    (committed / "bridge_llama2_7b_chat" / "rows.json").write_text('{"x": 1}\n', encoding="utf-8")

    return exp_dir


def test_build_copies_everything_and_skips_hard_excluded_path(tmp_path: Path, mixed_layout_experiment: Path) -> None:
    out_dir = tmp_path / "out"
    rc = build_exhaust_dataset.main(
        ["--experiment-dir", str(mixed_layout_experiment), "--out-dir", str(out_dir)]
    )
    assert rc == 0

    provenance = json.loads((out_dir / "PROVENANCE.json").read_text(encoding="utf-8"))
    assert provenance["shape"] == "aggregate"

    # Every non-excluded source file made it into the staged output, at
    # whatever depth it lived, with a matching sha256.
    expected_relpaths = {
        "final_report.json",
        "cell_a/dose_fit.json",
        "phase1/sub/notes.md",
    }
    assert set(provenance["files"].keys()) == expected_relpaths
    for rel in expected_relpaths:
        staged = out_dir / rel
        assert staged.is_file(), f"{rel} missing from staged output"
        assert sha256_of(staged) == provenance["files"][rel]
        # Byte-for-byte, not re-serialized.
        assert staged.read_bytes() == (mixed_layout_experiment / "analysis-committed" / rel).read_bytes()

    # The hard-excluded path was skipped, not copied, and recorded with a reason.
    assert not (out_dir / "bridge_llama2_7b_chat").exists()
    excluded_paths = {e["path"] for e in provenance["excluded"]}
    assert "bridge_llama2_7b_chat/rows.json" in excluded_paths
    for entry in provenance["excluded"]:
        assert entry["reason"], f"excluded entry has no reason: {entry}"


def test_build_aborts_on_content_level_hard_exclusion(tmp_path: Path) -> None:
    exp_dir = _make_experiment(tmp_path, "content-hit-exp")
    committed = exp_dir / "analysis-committed" / "cell_a"
    committed.mkdir(parents=True)
    (committed / "oops.json").write_text('{"note": "trained on openmoss data"}\n', encoding="utf-8")

    out_dir = tmp_path / "out"
    with pytest.raises(SystemExit):
        build_exhaust_dataset.main(["--experiment-dir", str(exp_dir), "--out-dir", str(out_dir)])
    # Refusing to build means no partial output should be trusted; the
    # top-level PROVENANCE.json marker for a completed build must be absent.
    assert not (out_dir / "PROVENANCE.json").exists()


def test_verify_completeness_passes_on_complete_build(tmp_path: Path, mixed_layout_experiment: Path) -> None:
    out_dir = tmp_path / "out"
    assert build_exhaust_dataset.main(
        ["--experiment-dir", str(mixed_layout_experiment), "--out-dir", str(out_dir)]
    ) == 0

    rc = verify_exhaust.main(
        ["--dataset-dir", str(out_dir), "--experiment-dir", str(mixed_layout_experiment)]
    )
    assert rc == 0


def test_verify_completeness_fails_when_a_source_file_is_missing_from_staged_output(
    tmp_path: Path, mixed_layout_experiment: Path
) -> None:
    out_dir = tmp_path / "out"
    assert build_exhaust_dataset.main(
        ["--experiment-dir", str(mixed_layout_experiment), "--out-dir", str(out_dir)]
    ) == 0

    # Simulate exactly the historical defect: a file that exists in the
    # source tree is entirely absent from the staged output, with no
    # exclusion entry explaining why (as if the builder had silently
    # dropped it). Remove it from disk AND from PROVENANCE.json's files map.
    dropped_rel = "phase1/sub/notes.md"
    (out_dir / dropped_rel).unlink()
    provenance_path = out_dir / "PROVENANCE.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    del provenance["files"][dropped_rel]
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    rc = verify_exhaust.main(
        ["--dataset-dir", str(out_dir), "--experiment-dir", str(mixed_layout_experiment)]
    )
    assert rc != 0


def test_verify_completeness_fails_closed_without_experiment_dir(tmp_path: Path, mixed_layout_experiment: Path) -> None:
    out_dir = tmp_path / "out"
    assert build_exhaust_dataset.main(
        ["--experiment-dir", str(mixed_layout_experiment), "--out-dir", str(out_dir)]
    ) == 0

    # A complete, correctly built dataset must still FAIL verification if
    # --experiment-dir is omitted: completeness cannot be claimed without
    # actually checking it against the source tree.
    rc = verify_exhaust.main(["--dataset-dir", str(out_dir)])
    assert rc != 0


def test_row_level_mode_is_unaffected(tmp_path: Path) -> None:
    """Regression guard: row-level (license-gated) mode keeps its existing
    cell-based PROVENANCE.json shape and is untouched by the aggregate
    copy-everything fix."""
    exp_dir = _make_experiment(tmp_path, "rows-mode-exp")
    rows_dir = tmp_path / "rows_input"
    rows_dir.mkdir()
    (rows_dir / "llama32_3b_instruct.jsonl").write_text(
        json.dumps({"row_key": "triviaqa:1", "source": "triviaqa", "generation_text": "hi", "answer_value": "hi", "answered": True})
        + "\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    rc = build_exhaust_dataset.main(
        ["--experiment-dir", str(exp_dir), "--rows-dir", str(rows_dir), "--out-dir", str(out_dir)]
    )
    assert rc == 0
    provenance = json.loads((out_dir / "PROVENANCE.json").read_text(encoding="utf-8"))
    assert provenance["shape"] == "rows"
    assert "cells" in provenance
    assert "files" not in provenance  # aggregate-only field must not leak into rows shape

    # triviaqa is text-free-only in the real license-gates.md: text-bearing
    # fields must be stripped.
    rows_path = out_dir / "llama32_3b_instruct" / "rows.jsonl"
    row = json.loads(rows_path.read_text(encoding="utf-8").splitlines()[0])
    assert "generation_text" not in row
    assert "answer_value" not in row

    # verify_exhaust must PASS on a row-level build with no --experiment-dir
    # at all (the completeness check is aggregate-only and must no-op here).
    rc = verify_exhaust.main(["--dataset-dir", str(out_dir)])
    assert rc == 0
