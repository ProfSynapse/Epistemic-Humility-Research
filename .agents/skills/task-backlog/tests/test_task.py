"""Tests for the task-backlog lifecycle CLI (task.py), the TODO.md generator
(build_todo_index.py), and the commit gate (check_task_gate.py).

Everything runs against a temporary repo root (a synthetic mini-repo) so the
tests never touch the real backlog/ or experiments/ trees. Core functions take
an explicit root, so the CLI is driven via main(["--root", str(tmp), ...]),
mirroring .skills/experiments/tests/test_exp.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import build_todo_index as bti
import check_task_gate as gate
import task  # noqa: E402  (sys.path set by conftest)


def _run(root: Path, *args: str) -> int:
    return task.main(["--root", str(root), *args])


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    return tmp_path


def _only_task_id(root: Path, dirname: str) -> str:
    files = list((root / "backlog" / dirname).glob("task-*.md"))
    assert len(files) == 1, files
    return task.load_task(files[0])["id"]


def _base_fields(**overrides) -> dict:
    fields = {
        "id": "task-000001",
        "title": "Test task",
        "status": "todo",
        "assignee": [],
        "tier": "P",
        "priority": "medium",
        "experiment": "",
        "component": "",
        "depends_on": [],
        "files": [],
        "new_files": [],
        "blocker": "",
        "created_date": "2026-08-27",
        "updated_date": "2026-08-27",
    }
    fields.update(overrides)
    return fields


def _raw_task(root: Path, dirname: str, task_id: str, slug: str, fields: dict) -> Path:
    d = root / "backlog" / dirname
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{task_id}-{slug}.md"
    fm = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True, default_flow_style=False)
    body = "## Description\n\n\n## Acceptance Criteria\n- [ ]\n\n## Work Log\n"
    path.write_text(f"---\n{fm}---\n{body}", encoding="utf-8")
    return path


def _write_experiment(root: Path, slug: str, status: str) -> None:
    d = root / "experiments" / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "experiment.yaml").write_text(f"slug: {slug}\nstatus: {status}\n", encoding="utf-8")


# --- id minting ---------------------------------------------------------


def test_mint_id_format(repo: Path):
    assert _run(repo, "new", "My first task", "--tier", "P") == 0
    tid = _only_task_id(repo, "tasks")
    assert task.ID_RE.match(tid)


def test_mint_id_avoids_collisions(monkeypatch):
    calls = iter(["aaaaaa", "aaaaaa", "bbbbbb"])
    monkeypatch.setattr(task.secrets, "token_hex", lambda n: next(calls))
    existing = {"task-aaaaaa"}
    assert task.mint_id(existing) == "task-bbbbbb"


def test_new_ids_are_unique_across_many(repo: Path):
    for i in range(15):
        assert _run(repo, "new", f"Task {i}", "--tier", "P") == 0
    ids = [task.load_task(p)["id"] for p in (repo / "backlog" / "tasks").glob("*.md")]
    assert len(ids) == len(set(ids)) == 15


def test_slugify_truncates_and_strips():
    assert task.slugify("Hello, World!!!  Testing") == "hello-world-testing"
    assert len(task.slugify("x" * 100)) <= 40


# --- new: draft flag and rollback ---------------------------------------


def test_new_draft_flag_writes_to_drafts(repo: Path):
    assert _run(repo, "new", "A draft idea", "--tier", "L", "--draft") == 0
    tid = _only_task_id(repo, "drafts")
    t = task.find_task(repo, tid)
    assert t["status"] == "draft"
    assert t["_dir"] == "drafts"


def test_new_rolls_back_on_nonexistent_experiment(repo: Path):
    assert _run(repo, "new", "Bad exp binding", "--tier", "P", "--experiment", "nope") == 2
    assert not list((repo / "backlog" / "tasks").glob("*.md"))


def test_new_rolls_back_on_nonexistent_file(repo: Path):
    assert _run(repo, "new", "Bad file binding", "--tier", "P", "--file", "nope.py") == 2
    assert not list((repo / "backlog" / "tasks").glob("*.md"))


# --- schema rejection (validate) ----------------------------------------


def test_validate_rejects_bad_status(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(status="bogus"))
    assert _run(repo, "validate") == 1


def test_validate_rejects_bad_tier(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(tier="Q"))
    assert _run(repo, "validate") == 1


def test_validate_rejects_unknown_depends_on(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(depends_on=["task-ffffff"]))
    assert _run(repo, "validate") == 1


def test_validate_rejects_cycle(repo: Path):
    _raw_task(
        repo, "tasks", "task-0000a1", "a",
        _base_fields(id="task-0000a1", depends_on=["task-0000b2"]),
    )
    _raw_task(
        repo, "tasks", "task-0000b2", "b",
        _base_fields(id="task-0000b2", depends_on=["task-0000a1"]),
    )
    errors = task.validate_all(repo)
    assert any("cycle" in e for e in errors)
    assert _run(repo, "validate") == 1


def test_validate_rejects_nonexistent_experiment(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(experiment="does-not-exist"))
    assert _run(repo, "validate") == 1


def test_validate_rejects_nonexistent_file(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(files=["nope.py"]))
    assert _run(repo, "validate") == 1


def test_validate_accepts_well_formed_task(repo: Path):
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields())
    assert _run(repo, "validate") == 0


# --- lifecycle transitions ------------------------------------------------


def test_claim_sets_in_progress_and_assignee(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    assert _run(repo, "claim", tid, "--as", "@alice") == 0
    t = task.find_task(repo, tid)
    assert t["status"] == "in-progress"
    assert t["assignee"] == ["@alice"]


def test_claim_refuses_when_held_by_another(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    assert _run(repo, "claim", tid, "--as", "@alice") == 0
    assert _run(repo, "claim", tid, "--as", "@bob") == 2
    t = task.find_task(repo, tid)
    assert t["assignee"] == ["@alice"]  # unchanged


def test_claim_is_idempotent_for_same_assignee(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    assert _run(repo, "claim", tid, "--as", "@alice") == 0
    assert _run(repo, "claim", tid, "--as", "@alice") == 0


def test_release_unassigns(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@alice")
    assert _run(repo, "release", tid) == 0
    t = task.find_task(repo, tid)
    assert t["status"] == "todo"
    assert t["assignee"] == []


def test_review_transition(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    assert _run(repo, "review", tid) == 0
    assert task.find_task(repo, tid)["status"] == "in-review"


def test_done_moves_file_to_completed(repo: Path):
    _run(repo, "new", "Do the thing", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    assert _run(repo, "done", tid) == 0
    t = task.find_task(repo, tid)
    assert t["status"] == "done"
    assert t["_dir"] == "completed"
    assert not list((repo / "backlog" / "tasks").glob("*.md"))


def test_list_flags_blocked_task(repo: Path, capsys):
    _run(repo, "new", "Dependency", "--tier", "P")
    dep_id = _only_task_id(repo, "tasks")
    _run(repo, "new", "Dependent", "--tier", "P", "--depends-on", dep_id)
    capsys.readouterr()
    assert _run(repo, "list") == 0
    out = capsys.readouterr().out
    assert f"[blocked by: {dep_id}]" in out


# --- terminal-experiment rot-killer cross-check --------------------------


def test_validate_flags_open_task_against_terminal_experiment(repo: Path):
    _write_experiment(repo, "my-exp", "resolved")
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(experiment="my-exp", status="todo"))
    errors = task.validate_all(repo)
    assert any("terminal" in e for e in errors)
    assert _run(repo, "validate") == 1


def test_validate_passes_open_task_against_signed_experiment(repo: Path):
    _write_experiment(repo, "my-exp", "signed")
    _raw_task(repo, "tasks", "task-000001", "t", _base_fields(experiment="my-exp", status="todo"))
    assert _run(repo, "validate") == 0


def test_validate_passes_done_task_against_terminal_experiment(repo: Path):
    _write_experiment(repo, "my-exp", "resolved")
    _raw_task(
        repo, "completed", "task-000001", "t",
        _base_fields(experiment="my-exp", status="done"),
    )
    assert _run(repo, "validate") == 0


# --- TODO.md generator ----------------------------------------------------


def test_generator_idempotent(repo: Path):
    _run(repo, "new", "Task one", "--tier", "P", "--priority", "high")
    _run(repo, "new", "Task two", "--tier", "L", "--priority", "low")
    todo = repo / "TODO.md"
    todo.write_text("# TODO\n\nsome hand-written preamble\n", encoding="utf-8")
    assert bti.main(["--root", str(repo), "--write"]) == 0
    first = todo.read_text(encoding="utf-8")
    assert bti.main(["--root", str(repo), "--write"]) == 0
    second = todo.read_text(encoding="utf-8")
    assert first == second
    assert "some hand-written preamble" in first
    assert bti.main(["--root", str(repo), "--check"]) == 0


def test_generator_flags_stale_todo(repo: Path):
    _run(repo, "new", "Task one", "--tier", "P")
    todo = repo / "TODO.md"
    todo.write_text("# TODO\n\nstale\n", encoding="utf-8")
    assert bti.main(["--root", str(repo), "--check"]) == 1


def test_generator_sorts_by_priority_then_date(repo: Path):
    _run(repo, "new", "Low pri", "--tier", "P", "--priority", "low")
    _run(repo, "new", "High pri", "--tier", "P", "--priority", "high")
    block = bti.render_block(repo)
    assert block.index("High pri") < block.index("Low pri")


def test_generator_counts_done_tasks(repo: Path):
    _run(repo, "new", "Task one", "--tier", "P")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "done", tid)
    block = bti.render_block(repo)
    assert "Done: 1 task(s)" in block


# --- commit gate -----------------------------------------------------------


def test_gate_exempt_files_never_gated():
    assert gate.is_gated("backlog/tasks/x.md") is False
    assert gate.is_gated("TODO.md") is False
    assert gate.is_gated("docs/sessions/note.md") is False
    assert gate.is_gated("experiments/foo/AMENDMENT.md") is False
    assert gate.is_gated(".agents/skills/task-backlog/scripts/task.py") is False
    assert gate.is_gated(".claude/skills/task-backlog/SKILL.md") is False
    assert gate.is_gated(".claude/settings.json") is False
    assert gate.is_gated("synaptic-tuner") is False
    assert gate.is_gated("analysis/foo.json") is False


def test_gate_scope_matches_gated_prefixes():
    assert gate.is_gated("bin/task.py") is True
    assert gate.is_gated(".skills/task-backlog/scripts/task.py") is True
    assert gate.is_gated(".githooks/pre-commit") is True
    assert gate.is_gated(".claude/hooks/foo.sh") is True
    assert gate.is_gated("papers/paper-5/manuscript.md") is True
    assert gate.is_gated("docs/architecture/foo.md") is True


def test_gate_uncovered_file_fails(repo: Path):
    errors = gate.check(repo, ["bin/foo.py"], staged_mode=True)
    assert errors


def test_gate_covered_and_fresh_passes(repo: Path):
    _run(repo, "new", "Cover bin", "--tier", "P", "--new-file", "bin/foo.py")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@me")
    task_rel = str(Path(task.find_task(repo, tid)["_path"]).relative_to(repo))
    errors = gate.check(repo, ["bin/foo.py", task_rel], staged_mode=True)
    assert errors == []


def test_gate_covered_but_not_fresh_in_range_mode_fails(repo: Path):
    _run(repo, "new", "Cover bin", "--tier", "P", "--new-file", "bin/foo.py")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@me")  # sets updated_date = today
    errors = gate.check(repo, ["bin/foo.py"], staged_mode=False)
    assert errors  # --range mode ignores the "updated today" fallback


def test_gate_covered_via_updated_today_in_staged_mode(repo: Path):
    _run(repo, "new", "Cover bin", "--tier", "P", "--new-file", "bin/foo.py")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@me")  # sets updated_date = today
    errors = gate.check(repo, ["bin/foo.py"], staged_mode=True)
    assert errors == []


def test_gate_new_files_subtree_prefix_covers(repo: Path):
    _run(repo, "new", "Cover skill dir", "--tier", "P", "--new-file", ".skills/task-backlog/")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@me")
    task_rel = str(Path(task.find_task(repo, tid)["_path"]).relative_to(repo))
    errors = gate.check(
        repo, [".skills/task-backlog/scripts/task.py", task_rel], staged_mode=True
    )
    assert errors == []


def test_gate_component_prefix_covers(repo: Path):
    (repo / "papers").mkdir()
    _run(repo, "new", "Cover papers", "--tier", "P", "--component", "papers")
    tid = _only_task_id(repo, "tasks")
    _run(repo, "claim", tid, "--as", "@me")
    task_rel = str(Path(task.find_task(repo, tid)["_path"]).relative_to(repo))
    errors = gate.check(repo, ["papers/paper-1/x.md", task_rel], staged_mode=True)
    assert errors == []


def test_gate_env_escape_hatch(monkeypatch, repo: Path, capsys):
    monkeypatch.setenv("EHR_TASK_OK", "1")
    assert gate.main(["--root", str(repo), "--staged"]) == 0
    assert "skipped" in capsys.readouterr().out
