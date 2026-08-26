"""Tests for the experiments lifecycle CLI (exp.py).

Everything runs against a temporary repo root so the tests never touch the real
experiments/ tree. Core functions take an explicit root, so the CLI is driven via
main(["--root", str(tmp), ...]).
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest
import yaml

import exp  # noqa: E402  (sys.path set by conftest)


def _run(root: Path, *args: str) -> int:
    return exp.main(["--root", str(root), *args])


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A minimal repo root with an empty experiments/ dir."""
    (tmp_path / exp.EXPERIMENTS_DIRNAME).mkdir()
    return tmp_path


def _manifest(root: Path, slug: str) -> dict:
    return yaml.safe_load(
        (exp.experiments_dir(root) / slug / exp.MANIFEST_NAME).read_text(encoding="utf-8")
    )


def _write_manifest(root: Path, slug: str, data: dict) -> None:
    (exp.experiments_dir(root) / slug / exp.MANIFEST_NAME).write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


# --- scaffold -> sign -> validate happy path ---------------------------------

def test_new_scaffolds_files(repo: Path):
    assert _run(repo, "new", "my-cell", "--type", "steer-cell") == 0
    d = exp.experiments_dir(repo) / "my-cell"
    assert (d / exp.MANIFEST_NAME).is_file()
    assert (d / "AMENDMENT.md").is_file()
    assert (d / "NOTEBOOK.md").is_file()
    assert (d / "cell.yaml").is_file()
    assert (d / "gates.yaml").is_file()
    assert (d / ".gitignore").is_file()
    m = _manifest(repo, "my-cell")
    assert m["slug"] == "my-cell"
    assert m["title"] == "my-cell"
    assert m["type"] == "steer-cell"
    assert m["status"] == "draft"
    assert m["registered"] is True
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", m["created_at"])


def test_new_can_derive_slug_from_title(repo: Path):
    assert _run(repo, "new", "--title", "Uncertainty Readout Transfer", "--type", "probe-fit") == 0
    d = exp.experiments_dir(repo) / "uncertainty-readout-transfer"
    assert d.is_dir()
    m = _manifest(repo, "uncertainty-readout-transfer")
    assert m["slug"] == "uncertainty-readout-transfer"
    assert m["title"] == "Uncertainty Readout Transfer"
    assert (d / "AMENDMENT.md").read_text(encoding="utf-8").startswith(
        "# Uncertainty Readout Transfer\n"
    )


def test_new_refuses_existing_slug(repo: Path):
    assert _run(repo, "new", "dup", "--type", "eval") == 0
    assert _run(repo, "new", "dup", "--type", "eval") == 2


def test_new_rejects_bad_slug(repo: Path):
    assert _run(repo, "new", "Bad_Slug", "--type", "eval") == 2


def _sign_ready(repo: Path, slug: str) -> Path:
    """Scaffold, add a config file, and fill prediction/falsifier so sign works."""
    _run(repo, "new", slug, "--type", "steer-cell")
    d = exp.experiments_dir(repo) / slug
    (d / "cell.yaml").write_text("surface:\n  seed: 1\narms: []\n", encoding="utf-8")
    m = _manifest(repo, slug)
    m["question"] = "Does X actuate Y?"
    m["prediction"] = "Small positive effect."
    m["falsifier"] = "No difference vs control."
    m["instrument"]["configs"] = ["cell.yaml"]
    _write_manifest(repo, slug, m)
    return d


def test_sign_pins_and_flips_status(repo: Path, capsys):
    _sign_ready(repo, "cell-a")
    assert _run(repo, "sign", "cell-a") == 0
    m = _manifest(repo, "cell-a")
    assert m["status"] == "signed"
    pins = m["instrument"]["pins"]
    assert "cell.yaml" in pins
    assert len(pins["cell.yaml"]) == 64
    # surface: block triggers the steer-cell reminder
    assert "expected_config_sha" in capsys.readouterr().out


def test_sign_refuses_without_prediction(repo: Path):
    _run(repo, "new", "cell-b", "--type", "eval")
    d = exp.experiments_dir(repo) / "cell-b"
    (d / "cfg.yaml").write_text("a: 1\n", encoding="utf-8")
    m = _manifest(repo, "cell-b")
    m["instrument"]["configs"] = ["cfg.yaml"]
    _write_manifest(repo, "cell-b", m)
    assert _run(repo, "sign", "cell-b") == 2  # missing prediction/falsifier


def test_signed_experiment_validates(repo: Path):
    _sign_ready(repo, "cell-c")
    _run(repo, "sign", "cell-c")
    assert _run(repo, "validate") == 0


# --- persistence declarations (kill-resume safety) ---------------------------

def test_sign_refuses_module_without_persistence_declaration(repo: Path):
    d = _sign_ready(repo, "cell-persist-missing")
    (d / "harness.py").write_text("# harness\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-missing")
    m["instrument"]["modules"] = ["harness.py"]
    _write_manifest(repo, "cell-persist-missing", m)
    assert _run(repo, "sign", "cell-persist-missing") == 2
    assert _manifest(repo, "cell-persist-missing")["status"] == "draft"


def test_sign_accepts_incremental_persistence_declaration(repo: Path):
    d = _sign_ready(repo, "cell-persist-incremental")
    (d / "harness.py").write_text("# harness\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-incremental")
    m["instrument"]["modules"] = ["harness.py"]
    m["instrument"]["persistence"] = {
        "harness.py": {
            "persistence": "incremental",
            "checkpoint_path": "experiments/cell-persist-incremental/analysis/runlog/harness.jsonl",
        }
    }
    _write_manifest(repo, "cell-persist-incremental", m)
    assert _run(repo, "sign", "cell-persist-incremental") == 0
    assert _manifest(repo, "cell-persist-incremental")["status"] == "signed"


def test_sign_accepts_short_run_persistence_declaration(repo: Path):
    d = _sign_ready(repo, "cell-persist-shortrun")
    (d / "pool_builder.py").write_text("# pool builder\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-shortrun")
    m["instrument"]["modules"] = ["pool_builder.py"]
    m["instrument"]["persistence"] = {
        "pool_builder.py": {
            "persistence": "short-run",
            "measured_smoke_wall_clock_s": 42.5,
        }
    }
    _write_manifest(repo, "cell-persist-shortrun", m)
    assert _run(repo, "sign", "cell-persist-shortrun") == 0


def test_sign_refuses_incremental_without_checkpoint_path(repo: Path):
    d = _sign_ready(repo, "cell-persist-badincremental")
    (d / "harness.py").write_text("# harness\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-badincremental")
    m["instrument"]["modules"] = ["harness.py"]
    m["instrument"]["persistence"] = {"harness.py": {"persistence": "incremental"}}
    _write_manifest(repo, "cell-persist-badincremental", m)
    assert _run(repo, "sign", "cell-persist-badincremental") == 2


def test_sign_refuses_short_run_without_numeric_wall_clock(repo: Path):
    d = _sign_ready(repo, "cell-persist-badshortrun")
    (d / "pool_builder.py").write_text("# pool builder\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-badshortrun")
    m["instrument"]["modules"] = ["pool_builder.py"]
    m["instrument"]["persistence"] = {
        "pool_builder.py": {"persistence": "short-run", "measured_smoke_wall_clock_s": "fast"}
    }
    _write_manifest(repo, "cell-persist-badshortrun", m)
    assert _run(repo, "sign", "cell-persist-badshortrun") == 2


def test_sign_ignores_persistence_when_no_modules(repo: Path):
    # Config-only instruments (no bespoke modules) have nothing to declare.
    _sign_ready(repo, "cell-persist-nomodules")
    assert _run(repo, "sign", "cell-persist-nomodules") == 0


def test_validate_warns_but_passes_on_draft_missing_persistence(repo: Path, capsys):
    # validate only ever warns about a missing persistence declaration, even
    # on a draft: the hard-enforcement point is sign, not validate. This
    # keeps validate from retroactively failing on a stale draft that was
    # never run through `exp sign` at all.
    _run(repo, "new", "cell-persist-draft", "--type", "eval")
    d = exp.experiments_dir(repo) / "cell-persist-draft"
    (d / "harness.py").write_text("# harness\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-draft")
    m["question"] = "q"
    m["instrument"]["modules"] = ["harness.py"]
    _write_manifest(repo, "cell-persist-draft", m)
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "warning" in capsys.readouterr().err


def test_validate_warns_but_passes_on_signed_missing_persistence(repo: Path, capsys):
    # A signed experiment that predates this requirement (or was hand-edited
    # to simulate a legacy record) must only warn, never fail validate --
    # this is the backward-compat split for the ~85 pre-existing experiments.
    d = _sign_ready(repo, "cell-persist-legacy")
    (d / "harness.py").write_text("# harness\n", encoding="utf-8")
    m = _manifest(repo, "cell-persist-legacy")
    m["instrument"]["modules"] = ["harness.py"]
    m["instrument"]["persistence"] = {
        "harness.py": {
            "persistence": "incremental",
            "checkpoint_path": "experiments/cell-persist-legacy/analysis/runlog/harness.jsonl",
        }
    }
    _write_manifest(repo, "cell-persist-legacy", m)
    _run(repo, "sign", "cell-persist-legacy")
    # Simulate a legacy record signed before the declaration existed: strip it
    # back out post-sign without going through repin (this mirrors a manifest
    # written before the field existed, not a real repin scenario).
    m2 = _manifest(repo, "cell-persist-legacy")
    m2["instrument"]["persistence"] = {}
    _write_manifest(repo, "cell-persist-legacy", m2)
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "warning" in capsys.readouterr().err


# --- structural text-capture guard -------------------------------------------

def test_new_scaffolds_text_capture_enabled_by_default(repo: Path):
    _run(repo, "new", "cell-tc-default", "--type", "eval")
    m = _manifest(repo, "cell-tc-default")
    assert m["text_capture"] == "enabled"
    m["question"] = "q"
    _write_manifest(repo, "cell-tc-default", m)
    assert _run(repo, "validate") == 0


def test_validate_errors_on_missing_text_capture_for_new_experiment(repo: Path):
    _run(repo, "new", "cell-tc-missing", "--type", "eval")
    m = _manifest(repo, "cell-tc-missing")
    m["question"] = "q"
    del m["text_capture"]
    _write_manifest(repo, "cell-tc-missing", m)
    assert _run(repo, "validate") == 1


def test_validate_errors_on_blank_text_capture(repo: Path):
    _run(repo, "new", "cell-tc-blank", "--type", "eval")
    m = _manifest(repo, "cell-tc-blank")
    m["question"] = "q"
    m["text_capture"] = "   "
    _write_manifest(repo, "cell-tc-blank", m)
    assert _run(repo, "validate") == 1


def test_validate_errors_on_invalid_text_capture_value(repo: Path):
    _run(repo, "new", "cell-tc-invalid", "--type", "eval")
    m = _manifest(repo, "cell-tc-invalid")
    m["question"] = "q"
    m["text_capture"] = "sometimes"
    _write_manifest(repo, "cell-tc-invalid", m)
    assert _run(repo, "validate") == 1


def test_validate_accepts_not_applicable_text_capture(repo: Path):
    _run(repo, "new", "cell-tc-na", "--type", "eval")
    m = _manifest(repo, "cell-tc-na")
    m["question"] = "q"
    m["text_capture"] = "not-applicable"
    _write_manifest(repo, "cell-tc-na", m)
    assert _run(repo, "validate") == 0


def test_validate_accepts_textless_reason_text_capture(repo: Path):
    _run(repo, "new", "cell-tc-textless", "--type", "eval")
    m = _manifest(repo, "cell-tc-textless")
    m["question"] = "q"
    m["text_capture"] = "textless: probe-fit pass produces no generation text"
    _write_manifest(repo, "cell-tc-textless", m)
    assert _run(repo, "validate") == 0


def test_validate_rejects_textless_with_empty_reason(repo: Path):
    _run(repo, "new", "cell-tc-textless-empty", "--type", "eval")
    m = _manifest(repo, "cell-tc-textless-empty")
    m["question"] = "q"
    m["text_capture"] = "textless:"
    _write_manifest(repo, "cell-tc-textless-empty", m)
    assert _run(repo, "validate") == 1


def test_validate_grandfathers_experiment_created_before_cutoff(repo: Path):
    # Pre-cutoff experiments never had to declare text_capture at all.
    _run(repo, "new", "cell-tc-legacy-dated", "--type", "eval")
    m = _manifest(repo, "cell-tc-legacy-dated")
    m["question"] = "q"
    m["created_at"] = "2026-01-01T00:00:00Z"
    del m["text_capture"]
    _write_manifest(repo, "cell-tc-legacy-dated", m)
    assert _run(repo, "validate") == 0


def test_validate_grandfathers_experiment_missing_created_at(repo: Path):
    # Experiments that predate the created_at field entirely (~16 in the
    # real registry) must never start failing validate retroactively.
    _run(repo, "new", "cell-tc-no-created-at", "--type", "eval")
    m = _manifest(repo, "cell-tc-no-created-at")
    m["question"] = "q"
    del m["created_at"]
    del m["text_capture"]
    _write_manifest(repo, "cell-tc-no-created-at", m)
    assert _run(repo, "validate") == 0


# --- stale AMENDMENT.md header vs machine status -----------------------------

def test_validate_warns_on_stale_draft_header_when_signed(repo: Path, capsys):
    # AMENDMENT.md's scaffolded header reads "Status: draft (not signed...)"
    # and `sign` never rewrites it -- so a signed experiment whose header
    # still says draft/not-signed must warn, matching the drift found and
    # fixed across 19 amendments 2026-08-11 (gemma-4-e4b-family-atlas's
    # 2026-07-20 header correction established the fix pattern).
    _sign_ready(repo, "cell-header-stale")
    _run(repo, "sign", "cell-header-stale")
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    err = capsys.readouterr().err
    assert "warning" in err
    assert "cell-header-stale" in err
    assert "draft" in err.lower()


def test_validate_silent_on_corrected_header_when_signed(repo: Path, capsys):
    # The corrected-header convention (state the true status on the header's
    # own Status line, then narrate the old draft language in later prose
    # for the audit trail) must not re-trigger the warning it exists to fix.
    d = _sign_ready(repo, "cell-header-fixed")
    _run(repo, "sign", "cell-header-fixed")
    (d / "AMENDMENT.md").write_text(
        "# cell-header-fixed\n\n"
        "Status: signed (machine state in `experiment.yaml`); not yet\n"
        "resolved. This header was stale boilerplate reading \"draft (not\n"
        "signed)\" until 2026-08-11; corrected to match the machine state,\n"
        "which was already `signed`.\n\n"
        "Keep this document the prose home for the experiment.\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "warning" not in capsys.readouterr().err


def test_validate_silent_on_draft_header_when_draft(repo: Path, capsys):
    # A genuine draft correctly has a draft header; never flag it -- the
    # check only fires at signed-or-later, mirroring
    # `_stale_gate_status_problems`.
    _run(repo, "new", "cell-header-draft", "--type", "eval")
    m = _manifest(repo, "cell-header-draft")
    m["question"] = "Does X actuate Y?"
    _write_manifest(repo, "cell-header-draft", m)
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "warning" not in capsys.readouterr().err


# --- unfilled Outcome vs terminal status -------------------------------------

def test_validate_warns_on_placeholder_outcome_when_resolved(repo: Path, capsys):
    # `resolve` flips the machine status but never writes the Outcome prose,
    # so a resolved cell whose `## Outcome` still reads "Filled at
    # resolve..." must warn -- the four-cell defect class backfilled
    # 2026-08-11.
    _sign_ready(repo, "cell-outcome-stale")
    _run(repo, "sign", "cell-outcome-stale")
    _run(repo, "resolve", "cell-outcome-stale", "--verdict", "Passed.")
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    err = capsys.readouterr().err
    assert "warning" in err
    assert "cell-outcome-stale" in err
    assert "Outcome" in err and "terminal" in err


def test_validate_silent_on_written_outcome_when_resolved(repo: Path, capsys):
    # A written Outcome (no placeholder text left in the section body)
    # satisfies the check; the corrected header keeps the sibling
    # header-drift check quiet too, so stderr is fully clean.
    d = _sign_ready(repo, "cell-outcome-ok")
    _run(repo, "sign", "cell-outcome-ok")
    _run(repo, "resolve", "cell-outcome-ok", "--verdict", "Passed.")
    (d / "AMENDMENT.md").write_text(
        "# cell-outcome-ok\n\n"
        "Status: resolved (machine state in `experiment.yaml`).\n\n"
        "## Outcome\n\n"
        "Passed. All gates green; verdict copied to the manifest.\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "warning" not in capsys.readouterr().err


def test_validate_silent_on_placeholder_outcome_when_signed(repo: Path, capsys):
    # Pre-terminal statuses correctly carry the scaffold placeholder; only
    # a terminal status creates the obligation to write the Outcome. (The
    # header-drift warning may fire here; assert only that no Outcome
    # warning does.)
    _sign_ready(repo, "cell-outcome-signed")
    _run(repo, "sign", "cell-outcome-signed")
    capsys.readouterr()
    assert _run(repo, "validate") == 0
    assert "Outcome" not in capsys.readouterr().err


# --- pin drift detection -----------------------------------------------------

def test_validate_detects_pin_drift(repo: Path):
    d = _sign_ready(repo, "cell-d")
    _run(repo, "sign", "cell-d")
    assert _run(repo, "validate") == 0
    # Mutate the pinned file -> validate must fail.
    (d / "cell.yaml").write_text("surface:\n  seed: 999\narms: []\n", encoding="utf-8")
    assert _run(repo, "validate") == 1


def test_validate_detects_missing_pinned_file(repo: Path):
    d = _sign_ready(repo, "cell-e")
    _run(repo, "sign", "cell-e")
    (d / "cell.yaml").unlink()
    assert _run(repo, "validate") == 1


# --- validate: empty, registered:false, kg, inputs ---------------------------

def test_validate_passes_on_empty_experiments(repo: Path):
    assert _run(repo, "validate") == 0


def test_validate_passes_with_no_experiments_dir(tmp_path: Path):
    # experiments/ absent entirely.
    assert _run(tmp_path, "validate") == 0


def test_validate_skips_claim_requirements_for_unregistered(repo: Path):
    _run(repo, "new", "example", "--type", "steer-cell")
    d = exp.experiments_dir(repo) / "example"
    (d / "cell.yaml").write_text("surface:\n  seed: 1\n", encoding="utf-8")
    m = _manifest(repo, "example")
    m["question"] = "Teaching artifact question."
    m["registered"] = False
    m["status"] = "signed"
    m["instrument"]["configs"] = ["cell.yaml"]
    # pin it so the signed-file check still passes, but leave prediction empty
    import hashlib
    m["instrument"]["pins"] = {
        "cell.yaml": hashlib.sha256((d / "cell.yaml").read_bytes()).hexdigest()
    }
    _write_manifest(repo, "example", m)
    # No prediction/falsifier, but registered:false so claim reqs are skipped.
    assert _run(repo, "validate") == 0


def test_validate_flags_missing_input_path(repo: Path):
    _run(repo, "new", "cell-in", "--type", "eval")
    m = _manifest(repo, "cell-in")
    m["question"] = "q"
    m["inputs"] = ["does/not/exist.csv"]
    _write_manifest(repo, "cell-in", m)
    assert _run(repo, "validate") == 1


def test_validate_tolerates_missing_gitignored_data_input(repo: Path):
    # An input under an experiment's gitignored data dir (analysis/) is
    # run-materialized: absent in a fresh worktree/clean clone is a warning, not
    # a commit-blocking error. See _is_untracked_data_input.
    _run(repo, "new", "cell-din", "--type", "eval")
    m = _manifest(repo, "cell-din")
    m["question"] = "q"
    m["inputs"] = ["experiments/cell-din/analysis/runlog/x.jsonl"]
    _write_manifest(repo, "cell-din", m)
    assert _run(repo, "validate") == 0


def test_validate_still_flags_missing_tracked_data_input(repo: Path):
    # analysis-committed/ is tracked, so a missing input there is still a hard
    # error (the relaxation is scoped to analysis/ and directions/ only).
    _run(repo, "new", "cell-dtracked", "--type", "eval")
    m = _manifest(repo, "cell-dtracked")
    m["question"] = "q"
    m["inputs"] = ["experiments/cell-dtracked/analysis-committed/ids.json"]
    _write_manifest(repo, "cell-dtracked", m)
    assert _run(repo, "validate") == 1


def test_validate_flags_unresolvable_kg_id(repo: Path):
    _run(repo, "new", "cell-kg", "--type", "eval")
    m = _manifest(repo, "cell-kg")
    m["question"] = "q"
    m["kg"] = ["nonexistent-node-id"]
    _write_manifest(repo, "cell-kg", m)
    assert _run(repo, "validate") == 1


def test_validate_resolves_kg_id_from_library(repo: Path):
    lib = repo / "library" / "notes"
    lib.mkdir(parents=True)
    (lib / "some-paper.md").write_text("---\nid: some-paper\n---\nbody\n", encoding="utf-8")
    _run(repo, "new", "cell-kg2", "--type", "eval")
    m = _manifest(repo, "cell-kg2")
    m["question"] = "q"
    m["kg"] = ["some-paper"]
    _write_manifest(repo, "cell-kg2", m)
    assert _run(repo, "validate") == 0


def test_validate_flags_slug_dir_mismatch(repo: Path):
    _run(repo, "new", "cell-s", "--type", "eval")
    m = _manifest(repo, "cell-s")
    m["question"] = "q"
    m["slug"] = "wrong"
    _write_manifest(repo, "cell-s", m)
    assert _run(repo, "validate") == 1


def test_validate_flags_dir_without_manifest(repo: Path):
    (exp.experiments_dir(repo) / "orphan").mkdir()
    assert _run(repo, "validate") == 1


# --- reserved common/ dir + teaching-artifact rendering ----------------------

def test_validate_exempts_common_dir(repo: Path):
    # experiments/common/ is the shared code home; it has no manifest and must
    # not be flagged as a missing-manifest experiment.
    common = exp.experiments_dir(repo) / "common"
    (common / "graders").mkdir(parents=True)
    (common / "graders" / "example_grader.py").write_text("# grader\n", encoding="utf-8")
    assert _run(repo, "validate") == 0
    # common/ is also excluded from the manifest scan / registry.
    assert all(slug != "common" for slug, _p, _d in exp.iter_manifests(repo))


def test_example_cell_style_manifest_validates(repo: Path):
    # A registered:false, draft, unsigned teaching artifact with configs but no
    # pins (the shape of experiments/example-cell/) must pass validate.
    _run(repo, "new", "example-cell", "--type", "steer-cell")
    d = exp.experiments_dir(repo) / "example-cell"
    (d / "cell.yaml").write_text("surface:\n  seed: 1\n", encoding="utf-8")
    (d / "gates.yaml").write_text("gates: []\n", encoding="utf-8")
    m = _manifest(repo, "example-cell")
    m["question"] = "Teaching artifact for the mechinterp-cells skill."
    m["registered"] = False
    m["instrument"]["configs"] = ["cell.yaml", "gates.yaml"]
    _write_manifest(repo, "example-cell", m)
    assert _run(repo, "validate") == 0


def test_registry_marks_registered_false_rows(repo: Path):
    _run(repo, "new", "teach", "--type", "steer-cell")
    m = _manifest(repo, "teach")
    m["question"] = "Example question."
    m["registered"] = False
    _write_manifest(repo, "teach", m)
    md = exp.render_registry_md(repo)
    # Row is present (complete inventory) and clearly marked.
    assert "teach" in md
    assert "teaching artifact:" in md


def test_registry_omits_common_dir(repo: Path):
    (exp.experiments_dir(repo) / "common" / "renders").mkdir(parents=True)
    _run(repo, "new", "real", "--type", "eval")
    m = _manifest(repo, "real")
    m["question"] = "A real one."
    _write_manifest(repo, "real", m)
    md = exp.render_registry_md(repo)
    assert "real" in md
    # common/ never appears as a registry row.
    assert "| common |" not in md


# --- resolve -----------------------------------------------------------------

def test_resolve_stamps_verdict_and_status(repo: Path, capsys):
    _sign_ready(repo, "cell-r")
    _run(repo, "sign", "cell-r")
    assert _run(repo, "resolve", "cell-r", "--verdict", "Passed all gates.") == 0
    m = _manifest(repo, "cell-r")
    assert m["status"] == "resolved"
    assert m["verdict"] == "Passed all gates."
    assert "kg-ingest" in capsys.readouterr().out


def test_resolve_null_result_status(repo: Path):
    _sign_ready(repo, "cell-n")
    _run(repo, "sign", "cell-n")
    assert _run(repo, "resolve", "cell-n", "--verdict", "No effect.",
                "--status", "null-result") == 0
    assert _manifest(repo, "cell-n")["status"] == "null-result"


# --- repin: signed-but-unlaunched instrument repair --------------------------

def _repin_file(d: Path, name: str, body: str) -> None:
    """Overwrite a pinned instrument file so its bytes (and hash) change."""
    (d / name).write_text(body, encoding="utf-8")


def test_repin_happy_path(repo: Path, capsys):
    d = _sign_ready(repo, "cell-rp")
    _run(repo, "sign", "cell-rp")
    old_pin = _manifest(repo, "cell-rp")["instrument"]["pins"]["cell.yaml"]
    # Simulate a build-environment fix to the pinned instrument.
    _repin_file(d, "cell.yaml", "surface:\n  seed: 1\narms: []\nfixed: true\n")
    assert _run(repo, "repin", "cell-rp", "cell.yaml", "--reason", "Modal image dep fix") == 0
    m = _manifest(repo, "cell-rp")
    new_pin = m["instrument"]["pins"]["cell.yaml"]
    assert new_pin != old_pin
    # Status stays signed; a real repair never flips the lifecycle.
    assert m["status"] == "signed"
    repins = m["instrument"]["repins"]
    assert len(repins) == 1
    entry = repins[0]
    assert entry["file"] == "cell.yaml"
    assert entry["old_sha256"] == old_pin
    assert entry["new_sha256"] == new_pin
    assert entry["reason"] == "Modal image dep fix"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", entry["date"])
    # The repinned manifest validates.
    assert _run(repo, "validate") == 0
    assert "repinned 1 file" in capsys.readouterr().out


def test_repin_is_append_only(repo: Path):
    d = _sign_ready(repo, "cell-rp-append")
    _run(repo, "sign", "cell-rp-append")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 2\narms: []\n")
    _run(repo, "repin", "cell-rp-append", "cell.yaml", "--reason", "first fix")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 3\narms: []\n")
    _run(repo, "repin", "cell-rp-append", "cell.yaml", "--reason", "second fix")
    repins = _manifest(repo, "cell-rp-append")["instrument"]["repins"]
    assert [e["reason"] for e in repins] == ["first fix", "second fix"]
    # Prior entry is preserved unedited; the last entry chains from it.
    assert repins[1]["old_sha256"] == repins[0]["new_sha256"]
    assert _run(repo, "validate") == 0


def test_repin_refuses_noop(repo: Path):
    _sign_ready(repo, "cell-rp-noop")
    _run(repo, "sign", "cell-rp-noop")
    # File unchanged since signing -> nothing to repin.
    assert _run(repo, "repin", "cell-rp-noop", "cell.yaml", "--reason", "no change") == 2
    assert "repins" not in _manifest(repo, "cell-rp-noop")["instrument"]


def test_repin_refuses_unrelated_drift(repo: Path):
    d = _sign_ready(repo, "cell-rp-drift")
    # Add a second pinned config so one can drift while the other is repinned.
    (d / "gates.yaml").write_text("gates: []\n", encoding="utf-8")
    m = _manifest(repo, "cell-rp-drift")
    m["instrument"]["configs"] = ["cell.yaml", "gates.yaml"]
    _write_manifest(repo, "cell-rp-drift", m)
    _run(repo, "sign", "cell-rp-drift")
    # Intentionally change the file we intend to repin AND let gates.yaml drift.
    _repin_file(d, "cell.yaml", "surface:\n  seed: 9\narms: []\n")
    (d / "gates.yaml").write_text("gates: [unrelated]\n", encoding="utf-8")
    assert _run(repo, "repin", "cell-rp-drift", "cell.yaml", "--reason", "fix cell") == 2
    # Refused: no pins updated, no repins recorded.
    m2 = _manifest(repo, "cell-rp-drift")
    assert "repins" not in m2["instrument"]


def test_repin_refuses_unpinned_file(repo: Path):
    d = _sign_ready(repo, "cell-rp-unpinned")
    _run(repo, "sign", "cell-rp-unpinned")
    (d / "extra.yaml").write_text("x: 1\n", encoding="utf-8")
    # extra.yaml exists and differs, but was never pinned.
    assert _run(repo, "repin", "cell-rp-unpinned", "extra.yaml", "--reason", "nope") == 2


def test_repin_refuses_empty_reason(repo: Path):
    d = _sign_ready(repo, "cell-rp-noreason")
    _run(repo, "sign", "cell-rp-noreason")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 5\narms: []\n")
    assert _run(repo, "repin", "cell-rp-noreason", "cell.yaml", "--reason", "  ") == 2


def test_repin_refuses_on_draft(repo: Path):
    d = _sign_ready(repo, "cell-rp-draft")  # sign-ready but NOT signed
    _repin_file(d, "cell.yaml", "surface:\n  seed: 7\narms: []\n")
    assert _run(repo, "repin", "cell-rp-draft", "cell.yaml", "--reason", "too early") == 2


def test_repin_refuses_on_resolved(repo: Path):
    d = _sign_ready(repo, "cell-rp-resolved")
    _run(repo, "sign", "cell-rp-resolved")
    _run(repo, "resolve", "cell-rp-resolved", "--verdict", "Done.")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 8\narms: []\n")
    assert _run(repo, "repin", "cell-rp-resolved", "cell.yaml", "--reason", "after the fact") == 2


def test_validate_accepts_correct_repin(repo: Path):
    d = _sign_ready(repo, "cell-rp-val")
    _run(repo, "sign", "cell-rp-val")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 42\narms: []\n")
    _run(repo, "repin", "cell-rp-val", "cell.yaml", "--reason", "instrument repair")
    assert _run(repo, "validate") == 0


def test_validate_rejects_stale_repin(repo: Path):
    d = _sign_ready(repo, "cell-rp-stale")
    _run(repo, "sign", "cell-rp-stale")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 43\narms: []\n")
    _run(repo, "repin", "cell-rp-stale", "cell.yaml", "--reason", "instrument repair")
    assert _run(repo, "validate") == 0
    # Tamper with the last repin's new_sha256 so it no longer matches the live pin.
    # The pin still matches the file on disk, so this isolates the repins/pins
    # consistency check from ordinary pin drift.
    m = _manifest(repo, "cell-rp-stale")
    m["instrument"]["repins"][-1]["new_sha256"] = "0" * 64
    _write_manifest(repo, "cell-rp-stale", m)
    assert _run(repo, "validate") == 1


def test_show_displays_repins(repo: Path, capsys):
    d = _sign_ready(repo, "cell-rp-show")
    _run(repo, "sign", "cell-rp-show")
    _repin_file(d, "cell.yaml", "surface:\n  seed: 11\narms: []\n")
    _run(repo, "repin", "cell-rp-show", "cell.yaml", "--reason", "dep conflict fix")
    capsys.readouterr()  # drop repin output
    assert _run(repo, "show", "cell-rp-show") == 0
    out = capsys.readouterr().out
    assert "repins" in out
    assert "dep conflict fix" in out


# --- regen determinism + staleness ------------------------------------------

def test_regen_writes_registry(repo: Path):
    _sign_ready(repo, "cell-reg")
    _run(repo, "sign", "cell-reg")
    assert _run(repo, "regen") == 0
    base = exp.experiments_dir(repo)
    assert (base / exp.REGISTRY_MD_NAME).is_file()
    assert (base / exp.REGISTRY_JSON_NAME).is_file()
    assert exp.GENERATED_HEADER in (base / exp.REGISTRY_MD_NAME).read_text()
    assert exp.GENERATED_HEADER in (base / exp.REGISTRY_JSON_NAME).read_text()


def test_regen_is_deterministic(repo: Path):
    _sign_ready(repo, "cell-det")
    _run(repo, "sign", "cell-det")
    md1 = exp.render_registry_md(repo)
    md2 = exp.render_registry_md(repo)
    js1 = exp.render_registry_json(repo)
    js2 = exp.render_registry_json(repo)
    assert md1 == md2
    assert js1 == js2


def test_regen_check_detects_staleness(repo: Path):
    _sign_ready(repo, "cell-stale")
    _run(repo, "sign", "cell-stale")
    _run(repo, "regen")
    assert _run(repo, "regen", "--check") == 0
    # Add another experiment without regenerating -> stale.
    _sign_ready(repo, "cell-stale2")
    assert _run(repo, "regen", "--check") == 1


def test_regen_check_stale_when_registry_absent(repo: Path):
    _sign_ready(repo, "cell-missing-reg")
    assert _run(repo, "regen", "--check") == 1


def test_regen_registry_sorted_by_slug(repo: Path):
    for slug in ("zeta", "alpha", "mu"):
        _run(repo, "new", slug, "--type", "eval")
        m = _manifest(repo, slug)
        m["question"] = f"q-{slug}"
        _write_manifest(repo, slug, m)
    md = exp.render_registry_md(repo)
    assert md.index("alpha") < md.index("mu") < md.index("zeta")
