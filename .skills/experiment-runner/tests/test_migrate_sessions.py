from __future__ import annotations

from pathlib import Path

import yaml

import migrate_sessions as ms


def _session_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "docs" / "sessions").mkdir(parents=True)
    (tmp_path / "library").mkdir()
    (tmp_path / "docs" / "sessions" / "0001 - test-session.md").write_text(
        "---\n"
        "schema_version: research-session/v1\n"
        "session_id: old-id\n"
        "title: Test Session\n"
        "status: active\n"
        "created_at: '2026-07-08T17:27:24Z'\n"
        "updated_at: '2026-07-08T17:27:24Z'\n"
        "question: q\n"
        "trajectory: {anchor: docs/research-trajectory.md}\n"
        "checkpoints: []\n"
        "---\n"
        "# Test Session\n",
        encoding="utf-8",
    )
    (tmp_path / "library" / "note.md").write_text(
        "See docs/sessions/0001 - test-session.md and docs/sessions/0001.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_session_migration_plan_rewrites_exact_refs_and_reports_shorthand(tmp_path: Path):
    root = _session_repo(tmp_path)
    records = ms.session_records(root)
    mapping = ms.path_map(records)
    rewrites = ms.planned_rewrites(root, mapping)
    shorthand = ms.shorthand_refs(root)

    assert mapping == {
        "docs/sessions/0001 - test-session.md":
        "docs/sessions/20260708T172724Z-test-session.md"
    }
    assert "library/note.md" in rewrites
    assert "library/note.md" in shorthand


def test_apply_session_migration_updates_frontmatter_and_exact_refs(tmp_path: Path):
    root = _session_repo(tmp_path)
    records = ms.session_records(root)
    mapping = ms.path_map(records)

    ms.apply_migration(root, records, mapping)

    new_path = root / "docs" / "sessions" / "20260708T172724Z-test-session.md"
    assert new_path.is_file()
    assert not (root / "docs" / "sessions" / "0001 - test-session.md").exists()
    data = yaml.safe_load(new_path.read_text(encoding="utf-8").split("---", 2)[1])
    assert data["session_id"] == "20260708T172724Z-test-session"
    assert data["legacy_session"]["id"] == "old-id"
    assert data["legacy_session"]["path"] == "docs/sessions/0001 - test-session.md"
    text = (root / "library" / "note.md").read_text(encoding="utf-8")
    assert "docs/sessions/20260708T172724Z-test-session.md" in text
    assert "docs/sessions/0001." in text
    assert (root / "docs" / "migration" / "session-path-map.json").is_file()
