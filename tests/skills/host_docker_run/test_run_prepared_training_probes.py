"""Probe-set tests for the checked-in host-docker-run driver.

Covers precondition P7 (blocker B-6): the project checkout must sit on a branch
whose upstream is on `origin` and whose remote tip equals HEAD, because
publication closure resolves the source through `_verified_remote_source`
(`docker_training.py:242`, raising at `:212`) and reports only
RESOLUTION_UNAVAILABLE when it cannot.

The driver is a checked-in operator script under `.skills/`, not a package
module, so it is loaded by path. Every git read goes through the driver's own
`_run`, which these tests replace with a table-driven fake; no real `git.exe`,
no network and no Docker are involved.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# tests/skills/host_docker_run/<this file> -> three levels up is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DRIVER = _REPO_ROOT / ".skills" / "host-docker-run" / "scripts" / "run_prepared_training.py"


def _load_driver():
    """Import the driver by path, the way an operator runs it."""
    spec = importlib.util.spec_from_file_location("_host_docker_run_driver", _DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


driver = _load_driver()

_HEAD = "48375bc3aa11bb22cc33dd44ee55ff6677889900"
_OTHER = "0011223344556677889900aabbccddeeff001122"
_BRANCH = "feat/submodule-cloud-api-v1-host"


def _fake_git(*, branch: str, remote: str, ls_remote_sha: str | None,
              points_at: str = "", head_rc: int = 0, ls_remote_rc: int = 0):
    """Build a `_run` replacement that answers the driver's git reads.

    Keyed on the git subcommand, which is argv[3] because the driver always
    calls `git.exe -C <root> <subcommand> ...`. `remote` is the value of
    `branch.<name>.remote`, the same local-config key the engine inspector reads
    at `source_bundle.py:668-675`; empty means the key is unset.
    """

    def run(argv, *, timeout=300):
        assert argv[0] == "git.exe", argv
        assert argv[1] == "-C", argv
        subcommand = argv[3]
        if subcommand == "rev-parse":
            return _completed(argv, head_rc, "" if head_rc else _HEAD)
        if subcommand == "branch" and "--show-current" in argv:
            return _completed(argv, 0, branch)
        if subcommand == "branch" and "--points-at" in argv:
            return _completed(argv, 0, points_at)
        if subcommand == "config":
            # `git config --get` exits 1 with no output when the key is unset,
            # which is how an unset upstream reaches the driver.
            assert argv[-1].startswith("branch.") and argv[-1].endswith(".remote"), argv
            return _completed(argv, 0 if remote else 1, remote)
        if subcommand == "ls-remote":
            if ls_remote_rc:
                return _completed(argv, ls_remote_rc, "", "fatal: could not read from remote")
            body = "" if ls_remote_sha is None else f"{ls_remote_sha}\trefs/heads/{branch}"
            return _completed(argv, 0, body)
        raise AssertionError(f"unexpected git subcommand: {argv}")

    return run


def _completed(argv, returncode, stdout="", stderr=""):
    return subprocess.CompletedProcess(argv, returncode, stdout + "\n", stderr)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return tmp_path


def _run_p7(monkeypatch, project_root: Path, fake) -> None:
    monkeypatch.setattr(driver, "_run", fake)
    driver._check_p7_branch_is_publishable(project_root)


# --------------------------------------------------------------------------
# Pass case
# --------------------------------------------------------------------------

def test_p7_passes_on_a_branch_tracking_origin_at_head(monkeypatch, project_root, capsys):
    _run_p7(
        monkeypatch, project_root,
        _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=_HEAD),
    )
    out = capsys.readouterr().out
    assert "PASS P7-branch-publishable" in out
    assert _BRANCH in out
    assert _HEAD[:12] in out


# --------------------------------------------------------------------------
# P7-detached-head
# --------------------------------------------------------------------------

def test_p7_detached_head_is_refused_and_names_the_branch_to_check_out(
    monkeypatch, project_root
):
    fake = _fake_git(
        branch="", remote="origin", ls_remote_sha=_HEAD, points_at=_BRANCH,
    )
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-detached-head:")
    assert f"git checkout {_BRANCH}" in message


def test_p7_detached_head_with_no_local_branch_at_head_still_gives_a_remedy(
    monkeypatch, project_root
):
    fake = _fake_git(branch="", remote="origin", ls_remote_sha=_HEAD, points_at="")
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-detached-head:")
    assert "git checkout -b" in message
    assert _HEAD[:12] in message


# --------------------------------------------------------------------------
# P7-no-upstream
# --------------------------------------------------------------------------

def test_p7_branch_without_an_upstream_is_refused(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="", ls_remote_sha=_HEAD)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-no-upstream:")
    assert "has no upstream" in message
    assert f"git branch --set-upstream-to=origin/{_BRANCH}" in message


def test_p7_upstream_on_a_remote_other_than_origin_is_refused(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="fork", ls_remote_sha=_HEAD)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-no-upstream:")
    assert "'fork'" in message


# --------------------------------------------------------------------------
# P7-remote-mismatch
# --------------------------------------------------------------------------

def test_p7_remote_tip_behind_head_is_refused(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=_OTHER)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-remote-mismatch:")
    assert _OTHER[:12] in message
    assert _HEAD[:12] in message
    assert f"git push origin {_BRANCH}" in message


def test_p7_branch_absent_on_origin_is_refused(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=None)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-remote-mismatch:")
    assert "has no refs/heads/" in message


def test_p7_ls_remote_failure_is_refused_not_skipped(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=_HEAD, ls_remote_rc=128)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    assert str(caught.value).startswith("P7-origin-unreachable:")


# --------------------------------------------------------------------------
# P7-origin-unreachable: a TRANSPORT failure, not a branch-state failure
# --------------------------------------------------------------------------

def test_p7_unreachable_origin_says_check_the_network_not_push(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=_HEAD, ls_remote_rc=128)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P7-origin-unreachable:")
    assert "check network access to origin" in message
    # Naming the wrong remedy is the defect this tag exists to prevent.
    assert "git push" not in message


def test_p7_unreachable_is_distinct_from_a_branch_absent_on_origin(
    monkeypatch, project_root
):
    """Exit 0 with no refs line is a real absence, so it stays a mismatch.

    `git ls-remote origin refs/heads/<absent>` exits 0 and prints nothing. That is
    git successfully reporting that the branch is not there, which a push fixes.
    Only a non-zero exit means the transport itself failed.
    """
    absent = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=None)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, absent)
    assert str(caught.value).startswith("P7-remote-mismatch:")
    assert "git push origin" in str(caught.value)

    unreachable = _fake_git(
        branch=_BRANCH, remote="origin", ls_remote_sha=None, ls_remote_rc=128
    )
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, unreachable)
    assert str(caught.value).startswith("P7-origin-unreachable:")


# --------------------------------------------------------------------------
# git itself unavailable: P7 fails closed, unlike P6 which SKIPs
# --------------------------------------------------------------------------

def test_p7_fails_closed_when_git_cannot_read_head(monkeypatch, project_root):
    fake = _fake_git(branch=_BRANCH, remote="origin", ls_remote_sha=_HEAD, head_rc=128)
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p7(monkeypatch, project_root, fake)
    assert str(caught.value).startswith("P7-git-unavailable:")


# --------------------------------------------------------------------------
# P7 runs in the precondition block, before anything touches Docker
# --------------------------------------------------------------------------

def test_p7_is_wired_into_the_precondition_block_after_p6():
    source = _DRIVER.read_text(encoding="utf-8")
    p6 = source.index("_check_p6_config_is_committed(project_root, args.config)")
    p7 = source.index("_check_p7_branch_is_publishable(project_root)", p6)
    # Search forward from P7 so this finds the CALL in main(), not the earlier
    # `def _probe_bind_source(`.
    bind = source.index("_probe_bind_source(", p7)
    assert p6 < p7 < bind, "P7 must run after P6 and before the first Docker probe"
