from __future__ import annotations

from pathlib import Path

import yaml

import migrate_legacy_amendments as mig


def _legacy_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "experiment" / "protocol").mkdir(parents=True)
    (tmp_path / "library" / "notes").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiment" / "protocol" / "AMENDMENT-AN-selected-setpoint-regulator.md").write_text(
        "---\n"
        "amendment: AN\n"
        "slug: selected-setpoint-regulator\n"
        "question: Does the regulator work?\n"
        "predictions:\n"
        "  orchestrator:\n"
        "    call: PASS\n"
        "outcome: NULL result.\n"
        "---\n"
        "# Amendment AN - Selected-setpoint regulator\n\n"
        "Body.\n",
        encoding="utf-8",
    )
    for path in (
        tmp_path / "docs" / "note.md",
        tmp_path / "library" / "notes" / "paper.md",
    ):
        path.write_text(
            "See experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md.\n",
            encoding="utf-8",
        )
    return tmp_path


def test_legacy_migration_plan_maps_paths_and_rewrites_library(tmp_path: Path):
    root = _legacy_repo(tmp_path)
    records = mig.legacy_records(root)
    mapping = mig.path_map(records)
    rewrites = mig.planned_rewrites(root, mapping)

    assert mapping == {
        "experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md":
        "experiments/selected-setpoint-regulator/AMENDMENT.md"
    }
    assert "library/notes/paper.md" in rewrites


def test_apply_legacy_migration_creates_historical_experiment(tmp_path: Path):
    root = _legacy_repo(tmp_path)
    records = mig.legacy_records(root)
    mapping = mig.path_map(records)

    mig.validate_plan(root, records, apply=True)
    mig.apply_migration(root, records, mapping)

    exp_dir = root / "experiments" / "selected-setpoint-regulator"
    assert (exp_dir / "AMENDMENT.md").is_file()
    assert not (root / "experiment" / "protocol" / "AMENDMENT-AN-selected-setpoint-regulator.md").exists()
    manifest = yaml.safe_load((exp_dir / "experiment.yaml").read_text(encoding="utf-8"))
    assert manifest["type"] == "historical-amendment"
    assert manifest["status"] == "historical"
    assert manifest["legacy"]["label"] == "AN"
    assert manifest["legacy"]["path"] == "experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md"
    assert manifest["legacy"]["migrated_to"] == "experiments/selected-setpoint-regulator/AMENDMENT.md"
    assert "falsifier" in manifest["migration"]["needs_manual_review"]
    assert "experiments/selected-setpoint-regulator/AMENDMENT.md" in (
        root / "library" / "notes" / "paper.md"
    ).read_text(encoding="utf-8")
    assert (root / "docs" / "migration" / "experiment-path-map.json").is_file()
