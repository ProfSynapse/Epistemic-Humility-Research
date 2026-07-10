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
