from __future__ import annotations

from pathlib import Path

import provenance_audit as pa


def test_provenance_audit_counts_library_references(tmp_path: Path):
    (tmp_path / "library" / "notes").mkdir(parents=True)
    (tmp_path / "experiment" / "protocol").mkdir(parents=True)
    (tmp_path / "docs" / "sessions").mkdir(parents=True)
    (tmp_path / "experiments" / "new-cell").mkdir(parents=True)

    (tmp_path / "experiment" / "protocol" / "AMENDMENT-A-old-cell.md").write_text(
        "---\namendment: A\nslug: old-cell\nstatus: resolved\n---\n# Amendment A\n",
        encoding="utf-8",
    )
    (tmp_path / "experiments" / "new-cell" / "experiment.yaml").write_text(
        "slug: new-cell\n"
        "title: New Cell\n"
        "type: eval\n"
        "status: draft\n"
        "registered: true\n"
        "created_at: '2026-07-08T17:27:24Z'\n"
        "question: ''\n",
        encoding="utf-8",
    )
    (tmp_path / "library" / "notes" / "linked-paper.md").write_text(
        "Uses experiment/protocol/AMENDMENT-A-old-cell.md and "
        "experiments/new-cell/AMENDMENT.md.\n",
        encoding="utf-8",
    )

    report = pa.audit(tmp_path)

    assert report["legacy_amendments"]["count"] == 1
    assert report["experiments"]["count"] == 1
    assert report["links"]["files_by_area"]["library"] == 1
    assert "library/notes/linked-paper.md" in report["links"]["by_file"]
    assert "experiment/protocol/AMENDMENT-A-old-cell.md" in report["links"]["legacy_links"]


def test_provenance_audit_detects_session_identity_debt(tmp_path: Path):
    session_dir = tmp_path / "docs" / "sessions"
    session_dir.mkdir(parents=True)
    for name in ("0001 - one.md", "0001 - two.md"):
        (session_dir / name).write_text(
            "---\n"
            "schema_version: research-session/v1\n"
            "session_id: '0001'\n"
            "title: Legacy\n"
            "status: active\n"
            "created_at: '2026-07-08T00:00:00Z'\n"
            "updated_at: '2026-07-08T00:00:00Z'\n"
            "question: q\n"
            "trajectory: {anchor: docs/research-trajectory.md}\n"
            "checkpoints: []\n"
            "---\n",
            encoding="utf-8",
        )

    sessions = pa.audit(tmp_path)["sessions"]

    assert "0001" in sessions["duplicate_sequence_numbers"]
    assert "0001" in sessions["duplicate_session_ids"]
    assert len(sessions["serial_only_session_ids"]) == 2
