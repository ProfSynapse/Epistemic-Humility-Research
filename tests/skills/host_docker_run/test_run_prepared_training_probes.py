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

import ast
import importlib.util
import subprocess
import sys
import types
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


# --------------------------------------------------------------------------
# P8 (blocker B-9): the container user can write the real stage parent
#
# The probe runs one container. These tests replace the driver's `_run`, so no
# Docker is involved; what is under test is the argv the driver BUILDS, the
# cause tag it reports, and the filesystem it touches.
# --------------------------------------------------------------------------

_USER = "1000:1000"
_DISTRO = "Ubuntu-22.04"
_ROOT = "/mnt"
_IMAGE = "example.invalid/img@sha256:" + "ab" * 32


def _fake_docker(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """A `_run` replacement that records the argv it was handed."""
    calls: list[list[str]] = []

    def run(argv, *, timeout=300):
        calls.append(list(argv))
        return _completed(argv, returncode, stdout, stderr)

    run.calls = calls  # type: ignore[attr-defined]
    return run


def _windows_root(tmp_path: Path) -> Path:
    """A project root the driver will accept as a Windows drive path.

    `_wsl_path` requires `Path.drive` to be a drive letter, which a POSIX
    `tmp_path` never has. Only the RENDERING needs the drive, so the mkdir side
    of the probe is exercised against `tmp_path` in the tests that care about
    the filesystem, and the rendering is exercised separately.
    """
    return tmp_path


_P8_OK = (
    "uid=1000 gid=1000 groups=1000\n"
    "WRITABLE\n"
    "HOME=/ home-not-writable\n"
)


def _run_p8(monkeypatch, project_root: Path, fake, *, user: str = _USER) -> None:
    monkeypatch.setattr(driver, "_run", fake)
    monkeypatch.setattr(
        driver, "_mount_source",
        lambda path, *, distro, root, check: f"\\\\wsl.localhost\\{distro}\\rendered",
    )
    driver._check_p8_stage_writable_as_container_user(
        "docker.exe", "npipe://x", _IMAGE, project_root,
        distro=_DISTRO, root=_ROOT, container_user=user,
    )


def test_p8_passes_and_reports_the_effective_user_as_evidence(
    monkeypatch, project_root, capsys
):
    fake = _fake_docker(stdout=_P8_OK)
    _run_p8(monkeypatch, project_root, fake)
    out = capsys.readouterr().out
    assert "PASS P8-stage-writable-as-container-user" in out
    assert _USER in out
    # `id` is echoed so the effective user is evidence in the report, not an
    # assumption. Section 18.11.
    assert "uid=1000 gid=1000" in out


def test_p8_probes_the_real_stage_parent_and_removes_only_its_own_directory(
    monkeypatch, project_root
):
    """It must create the stage parent and leave it, taking only `p8-probe`.

    `_verify_artifact_topology` (`docker_staging.py:1446-1481`) requires the
    writable artifact directories to be EMPTY, and it runs on every cut (section
    18.18, B-10), so a probe that left a file inside a stage would break the run
    at the next cut.
    """
    stage_parent = project_root.joinpath(*driver._STAGE_PARENT_PARTS)
    survivor = stage_parent / "an-existing-stage"
    survivor.mkdir(parents=True)

    _run_p8(monkeypatch, project_root, _fake_docker(stdout=_P8_OK))

    assert stage_parent.is_dir(), "P8 must not remove the stage parent"
    assert survivor.is_dir(), "P8 must never touch an existing stage"
    assert not (stage_parent / driver._P8_PROBE_DIRECTORY).exists()


def test_p8_creates_the_stage_parent_and_says_so(monkeypatch, project_root, capsys):
    """The fidelity cost the ruling accepted must be printed, not silent.

    A --probe-only pass now writes durable state, which changes the line runs
    1-4 could report (section 18.11).
    """
    _run_p8(monkeypatch, project_root, _fake_docker(stdout=_P8_OK))
    out = capsys.readouterr().out
    assert "CREATED the stage parent" in out
    assert "no durable state was written" in out


def test_p8_does_not_claim_to_have_created_an_existing_stage_parent(
    monkeypatch, project_root, capsys
):
    project_root.joinpath(*driver._STAGE_PARENT_PARTS).mkdir(parents=True)
    _run_p8(monkeypatch, project_root, _fake_docker(stdout=_P8_OK))
    out = capsys.readouterr().out
    assert "CREATED the stage parent" not in out
    assert "already present" in out


def test_p8_uses_the_profile_user_and_the_composition_conventions(
    monkeypatch, project_root
):
    """The argv must carry the profile's user, `--entrypoint env`, and `--network none`.

    Section 17.10: the probes assert the same contract the composition uses.
    `destination=` matches the spelling at `control_private.py:410-411`.
    """
    fake = _fake_docker(stdout=_P8_OK)
    _run_p8(monkeypatch, project_root, fake)
    argv = fake.calls[0]  # type: ignore[attr-defined]
    assert argv[argv.index("--user") + 1] == _USER
    assert argv[argv.index("--entrypoint") + 1] == driver._CONTAINER_ENTRYPOINT
    assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
    assert argv[argv.index("--entrypoint") + 2] == _IMAGE
    mount = argv[argv.index("--mount") + 1]
    assert mount.endswith(",destination=/artifacts")
    assert "--pull" in argv and argv[argv.index("--pull") + 1] == "never"


def test_p8_failure_names_the_user_the_source_the_stderr_and_the_remedy(
    monkeypatch, project_root
):
    fake = _fake_docker(
        returncode=1, stderr="touch: cannot touch '/artifacts/.p8probe': Permission denied"
    )
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p8(monkeypatch, project_root, fake)
    message = str(caught.value)
    assert message.startswith("P8-stage-writable-as-container-user:")
    assert _USER in message
    assert "wsl.localhost" in message
    assert "Permission denied" in message
    # The remedy is what makes this a precondition rather than a symptom.
    assert "/proc/mounts" in message
    assert _DISTRO in message
    assert "docker_host.container_user" in message
    assert "B-9" in message


def test_p8_removes_its_probe_directory_even_when_the_container_fails(
    monkeypatch, project_root
):
    with pytest.raises(driver.CheckFailure):
        _run_p8(monkeypatch, project_root, _fake_docker(returncode=1))
    stage_parent = project_root.joinpath(*driver._STAGE_PARENT_PARTS)
    assert not (stage_parent / driver._P8_PROBE_DIRECTORY).exists()


def test_p8_home_not_writable_warns_and_does_not_fail(
    monkeypatch, project_root, capsys
):
    """B-9-R1 is a WARNING by ruling (section 18.10), and it fires on every pass.

    A numeric `--user` has no `/etc/passwd` entry, so HOME=/ and is unwritable;
    that was measured on the committed image. Failing on it would refuse a
    configuration that is legitimate for a workload that never writes there.
    """
    _run_p8(monkeypatch, project_root, _fake_docker(stdout=_P8_OK))
    out = capsys.readouterr().out
    assert "WARN P8-home" in out
    assert "B-9-R1" in out
    assert "PASS P8-stage-writable-as-container-user" in out


def test_p8_stays_quiet_about_home_when_home_is_writable(
    monkeypatch, project_root, capsys
):
    stdout = "uid=0 gid=0\nWRITABLE\nHOME=/root home-writable\n"
    _run_p8(monkeypatch, project_root, _fake_docker(stdout=stdout))
    out = capsys.readouterr().out
    assert "WARN P8-home" not in out


def test_p8_fails_when_the_container_exits_zero_without_writing(
    monkeypatch, project_root
):
    """Exit 0 is not enough: the `sh -c` chain can succeed while the touch did not."""
    stdout = "uid=1000 gid=1000\nHOME=/ home-not-writable\n"
    with pytest.raises(driver.CheckFailure) as caught:
        _run_p8(monkeypatch, project_root, _fake_docker(returncode=0, stdout=stdout))
    assert str(caught.value).startswith("P8-stage-writable-as-container-user:")


# --------------------------------------------------------------------------
# Reading `docker_host.container_user` from the committed profile
# --------------------------------------------------------------------------

def test_container_user_is_read_from_the_profile():
    profile = {"docker_host": {"wsl_distro": _DISTRO, "container_user": _USER}}
    assert driver._read_container_user(profile) == _USER


def test_missing_container_user_names_the_unlanded_host_change_not_a_keyerror(
    project_root
):
    """The field and this driver land in different commits.

    Until the Host change lands, a run must say WHICH change is missing rather
    than raising `KeyError`. Same shape P5 uses for blocker B-1.
    """
    with pytest.raises(driver.CheckFailure) as caught:
        driver._read_container_user({"docker_host": {"wsl_distro": _DISTRO}})
    message = str(caught.value)
    assert message.startswith("P8-container-user-missing:")
    assert "B-9" in message
    assert "released checkout" in message


def test_a_name_form_container_user_is_refused_with_the_reason():
    """A name resolves against the IMAGE's /etc/passwd and cannot express a mount identity."""
    with pytest.raises(driver.CheckFailure) as caught:
        driver._read_container_user(
            {"docker_host": {"container_user": "unsloth:runtimeusers"}}
        )
    message = str(caught.value)
    assert message.startswith("P8-container-user-shape:")
    assert "/etc/passwd" in message


# --------------------------------------------------------------------------
# A2 must follow the composition, not the image's old default (section 18.12)
# --------------------------------------------------------------------------

def test_a2_passes_the_profile_user_rather_than_the_image_default(
    monkeypatch, project_root
):
    """The hard-coded `unsloth:runtimeusers` becomes a FALSE BLOCKER after B-9.

    It was faithful only while the composition passed no `--user`. Once it emits
    one, a hard-coded name fails a run the composition would have completed.
    """
    fake = _fake_docker(stdout="WRITABLE\n")
    monkeypatch.setattr(driver, "_run", fake)
    monkeypatch.setattr(
        driver, "_mount_source",
        lambda path, *, distro, root, check: "\\\\wsl.localhost\\rendered",
    )
    driver._assert_a2_artifacts_writable(
        "docker.exe", "npipe://x", _IMAGE, project_root,
        distro=_DISTRO, root=_ROOT, container_user=_USER,
    )
    argv = fake.calls[0]  # type: ignore[attr-defined]
    assert argv[argv.index("--user") + 1] == _USER
    assert "unsloth:runtimeusers" not in argv


def test_no_literal_container_user_survives_in_executable_code():
    """The old name may be EXPLAINED in prose but never PASSED to docker.

    Checked over the AST rather than the file text, because the A2 docstring
    records why the hard-coded value was wrong and that history is worth
    keeping. Docstrings are excluded; every other string constant is not.
    """
    tree = ast.parse(_DRIVER.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            docstrings.add(id(body[0].value))
    literals = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]
    assert "unsloth:runtimeusers" not in literals


# --------------------------------------------------------------------------
# Cause tags: a fault inside a probe must report THAT probe's name
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "check",
    ["B1-bind-probe", "A2-artifacts-writable", "P8-stage-writable-as-container-user"],
)
def test_wsl_path_reports_the_callers_cause_tag(check):
    """Three probes render a mount source through `_wsl_path`.

    A shared literal tag would make a fault inside one probe report another
    probe's name, which is the wrong-cause defect P7 split its own tags to
    avoid.
    """
    with pytest.raises(driver.CheckFailure) as caught:
        driver._wsl_path(Path("/not/a/windows/path"), _ROOT, check=check)
    assert str(caught.value).startswith(check + ":")


# --------------------------------------------------------------------------
# B-10 evidence (section 19.14): read-only observation around every cut
# --------------------------------------------------------------------------

def _make_stage(project_root: Path, name: str) -> Path:
    """A stage with the five directories `_create_artifact_topology` builds."""
    root = project_root.joinpath(*driver._STAGE_PARENT_PARTS) / name / "artifacts"
    for child in ("artifacts", "cache", "state", "tmp", "tracking"):
        (root / child).mkdir(parents=True)
    return root


def test_b10_evidence_reports_a_non_empty_state_before_the_cut(
    project_root, capsys
):
    root = _make_stage(project_root, "stagekey1")
    (root / "state" / "written-by-the-trainer").write_text("x", encoding="utf-8")

    driver._report_b10_evidence_before_cut(project_root, 2)

    line = capsys.readouterr().out.strip()
    assert line.startswith("B10-EVIDENCE cut=2 ")
    assert "state_nonempty=true" in line
    # The other three are reported too: the verifier fails on ANY of them, so
    # evidence about `state` alone could mislead.
    assert "artifacts_nonempty=false" in line
    assert "tmp_nonempty=false" in line
    assert "tracking_nonempty=false" in line
    assert "stagekey1" in line


def test_b10_evidence_says_none_when_no_stage_exists_yet(project_root, capsys):
    """Normal before staging; it must not read as an empty `state`."""
    driver._report_b10_evidence_before_cut(project_root, 1)
    line = capsys.readouterr().out.strip()
    assert "stage=NONE" in line
    assert "state_nonempty=unknown" in line
    assert "state_nonempty=false" not in line


def test_b10_evidence_does_not_mistake_the_p8_probe_directory_for_a_stage(
    project_root, capsys
):
    """`p8-probe` is this driver's own directory and the run never writes there.

    Counting it as a stage would report emptiness for a directory that cannot
    carry the evidence.
    """
    stage_parent = project_root.joinpath(*driver._STAGE_PARENT_PARTS)
    (stage_parent / driver._P8_PROBE_DIRECTORY / "artifacts").mkdir(parents=True)
    _make_stage(project_root, "stagekey1")

    driver._report_b10_evidence_before_cut(project_root, 2)

    out = capsys.readouterr().out
    assert driver._P8_PROBE_DIRECTORY not in out
    assert "stagekey1" in out
    assert out.count("B10-EVIDENCE") == 1


def test_b10_evidence_after_the_cut_carries_the_result_code(capsys):
    driver._report_b10_evidence_after_cut(
        2, 2, {"code": "START_UNAVAILABLE", "status": "unavailable"}
    )
    line = capsys.readouterr().out.strip()
    assert line.startswith("B10-EVIDENCE cut=2 ")
    assert "result=START_UNAVAILABLE" in line
    assert "status=unavailable" in line


def test_the_cut_loop_records_evidence_before_and_after_every_cut():
    """Both halves must bracket the cut, or the reading cannot be made."""
    source = _DRIVER.read_text(encoding="utf-8")
    loop = source.index("for cut in range(1, args.max_cuts + 1):")
    before = source.index("_report_b10_evidence_before_cut(project_root, cut)", loop)
    call = source.index("_one_cut(python_executable, project_root, args)", before)
    after = source.index("_report_b10_evidence_after_cut(", call)
    assert before < call < after


def test_p8_runs_after_the_bind_probe_and_before_the_first_assertion():
    """Order is ruled: P1..P7 -> B1 -> P8 -> A1..A4 (section 18.11).

    P8 cannot precede B1, because it needs a bind already proven to resolve or a
    mount-source fault would surface as a permission message.
    """
    source = _DRIVER.read_text(encoding="utf-8")
    p7 = source.index("_check_p7_branch_is_publishable(project_root)")
    bind = source.index("_probe_bind_source(", p7)
    p8 = source.index("_check_p8_stage_writable_as_container_user(", bind)
    a1 = source.index("_assert_a1_gpu(", p8)
    assert p7 < bind < p8 < a1


# --------------------------------------------------------------------------
# D1: a cut's stderr channel (section 20.14, blocker B-11)
#
# Section 20.11 rules that the Host surfaces an activation cause as ONE stderr
# line and adds no `cause` field, because the result model is fixed
# (`_failure` builds a positional V2 result; `test_cli.py:468` pins field
# presence per code). That ruling is only viable because the driver already
# prints stderr with the `stderr| ` prefix and still parses the result from the
# LAST stdout line -- and until now that behaviour was unpinned: the suite
# exercised stderr only on the P8 failure path, never for a cut. D1 converts the
# assumption an entire ruling rests on into a test.
#
# `_one_cut` calls `subprocess.run` directly rather than the driver's `_run`, so
# these cannot reuse the `_fake_docker`/`_run` harness above. The shim is
# installed on the DRIVER's `subprocess` reference rather than on the real
# module, so nothing outside the driver sees a replaced `run`.
# --------------------------------------------------------------------------

# The exact shape section 20.11 specifies, for run 5's failure. Frame identity
# only: no exception text, no absolute path, no value.
_CAUSE_LINE = (
    "synaptic-host: START_UNAVAILABLE ValueError "
    "at synaptic_host/security.py:373 in _win_validate_acl"
)

# Written as a literal rather than through `json.dumps` so the fixture's last
# line is byte-exact and does not depend on a serializer's key order.
_RESULT_LINE = '{"code": "START_UNAVAILABLE", "status": "unavailable", "run_id": null}'


class _CutArgs:
    """The four attributes `_one_cut` reads off the parsed namespace."""

    provider = "docker"
    config = "configs/training/tiny.json"
    destination = "runs/tiny"
    cut_timeout_seconds = 60


def _fake_cut(monkeypatch, *, stdout: str, stderr: str, returncode: int = 2):
    """Replace only what `_one_cut` reaches for: `run` and `list2cmdline`."""

    def run(argv, **kwargs):
        return subprocess.CompletedProcess(argv, returncode, stdout, stderr)

    monkeypatch.setattr(
        driver,
        "subprocess",
        types.SimpleNamespace(run=run, list2cmdline=subprocess.list2cmdline),
    )


def test_d1_a_cut_prints_the_stderr_cause_and_still_parses_the_last_stdout_line(
    monkeypatch, project_root, capsys
):
    """The operator sees the cause AND the result still parses (section 20.11).

    The fixture puts a NON-JSON preamble line ahead of the result line on
    stdout, so "parses the last line" is load-bearing here rather than trivially
    true: a driver that parsed the first line would return an empty result and
    this test would fail.
    """
    _fake_cut(
        monkeypatch,
        stdout="Host chatter that is not JSON\n" + _RESULT_LINE + "\n",
        stderr=_CAUSE_LINE + "\n",
    )

    exit_code, result = driver._one_cut("python.exe", project_root, _CutArgs())

    out = capsys.readouterr().out
    # Verbatim, prefix included: this is the text test-host quotes from a run.
    assert f"    stderr| {_CAUSE_LINE}" in out
    assert out.count(_CAUSE_LINE) == 1
    # stdout is untouched by the cause, so the result JSON still parses.
    assert exit_code == 2
    assert result == {
        "code": "START_UNAVAILABLE",
        "status": "unavailable",
        "run_id": None,
    }


def test_d1_the_cause_survives_when_it_is_not_the_only_stderr_line(
    monkeypatch, project_root, capsys
):
    """Every stderr line is printed, not just the first.

    Section 20.11 promises the operator sees the cause. `synaptic_host` writes
    nothing to stderr today, but the interpreter and any library beneath it can,
    so the cause is not guaranteed to arrive first or alone. A driver that
    printed only one line could drop it and every other test would stay green.
    """
    _fake_cut(
        monkeypatch,
        stdout=_RESULT_LINE + "\n",
        stderr="a warning from somewhere beneath the Host\n" + _CAUSE_LINE + "\n",
    )

    exit_code, result = driver._one_cut("python.exe", project_root, _CutArgs())

    out = capsys.readouterr().out
    assert f"    stderr| {_CAUSE_LINE}" in out
    assert "    stderr| a warning from somewhere beneath the Host" in out
    assert exit_code == 2
    assert result["code"] == "START_UNAVAILABLE"


# --------------------------------------------------------------------------
# P9: the locked project inputs (section 21.13, blocker B-12)
#
# B-12: the prepared path archived the WHOLE superproject at the locked commit,
# 412,794,880 bytes against a 256 MiB bound, so staging refused before any
# container existed. Section 21.4 rules that staging stages only the two
# descriptors `source_lock.inputs` records. P9 reports what that set costs
# BEFORE a run is issued.
#
# P9 REPORTS AND NEVER GATES (21.13: the Host owns the refusal, admission is
# the gate), so the central test here is the negative one: a total far over the
# bound must still return normally. A probe that quietly grew a gate would
# refuse runs the Host would have accepted.
#
# The probe derives the pair itself, because the lock is built during admission
# and there is no pre-run artifact to read. Section 21.4's addendum at 070995cc
# names quiet divergence as the failure worth engineering against, so the line
# must say it is the DRIVER's derivation and name the commit and both paths --
# that is what makes a disagreement with the Host's staged manifest visible
# rather than something a human has to infer.
# --------------------------------------------------------------------------

_CONFIG_REF = "project://training/smokes/docker-sft.json"
_CONFIG_REL = "training/smokes/docker-sft.json"
_DATASET_REL = "training/fixtures/modal-smoke.jsonl"
_COMMIT = "e00ab662aa11bb22cc33dd44ee55ff6677889900"


def _fake_git_inputs(*, config_size="1089", dataset_size="638",
                     config_body=None, rev_parse_rc=0, cat_file_rc=0):
    """Answer the three git reads P9 makes: rev-parse, cat-file -s, cat-file -p.

    Keyed on the subcommand at argv[3], the same shape `_fake_git` uses, because
    the driver always calls `git.exe -C <root> <subcommand> ...`.
    """
    if config_body is None:
        config_body = '{"dataset": {"ref": "project://' + _DATASET_REL + '"}}'

    def run(argv, *, timeout=300):
        assert argv[0] == "git.exe" and argv[1] == "-C", argv
        subcommand = argv[3]
        if subcommand == "rev-parse":
            if rev_parse_rc:
                return _completed(argv, rev_parse_rc, "", "fatal: not a git repository")
            return _completed(argv, 0, _COMMIT)
        if subcommand == "cat-file":
            if cat_file_rc:
                return _completed(argv, cat_file_rc, "", "fatal: path does not exist")
            spec = argv[-1]
            if argv[4] == "-s":
                return _completed(argv, 0, config_size if _CONFIG_REL in spec else dataset_size)
            return _completed(argv, 0, config_body)
        raise AssertionError(f"unexpected git subcommand: {argv}")

    return run


def _run_p9(monkeypatch, project_root: Path, fake) -> None:
    monkeypatch.setattr(driver, "_run", fake)
    driver._check_p9_locked_project_inputs(project_root, _CONFIG_REF)


def test_p9_reports_both_locked_inputs_and_their_total(
    monkeypatch, project_root, capsys
):
    _run_p9(monkeypatch, project_root, _fake_git_inputs())

    out = capsys.readouterr().out
    assert "training-config" in out and _CONFIG_REL in out
    assert "training-dataset" in out and _DATASET_REL in out
    # The total is the SUM of the two descriptors, not either one alone.
    assert "bytes=1727" in out
    assert "count=2" in out
    assert "PASS P9-locked-project-inputs" in out


def test_p9_names_the_commit_and_says_the_derivation_is_the_drivers(
    monkeypatch, project_root, capsys
):
    """Section 21.4's addendum: quiet divergence is the failure to engineer against.

    The probe is a second derivation of a scope the Host owns. It cannot cause a
    wrong stage, but it can produce a wrong REPORT, so the line must carry
    enough to be checked against the staged source manifest by hand.
    """
    _run_p9(monkeypatch, project_root, _fake_git_inputs())

    out = capsys.readouterr().out
    assert _COMMIT in out
    assert "DRIVER" in out


def test_p9_does_not_gate_when_the_total_exceeds_the_host_bound(
    monkeypatch, project_root, capsys
):
    """THE test for 21.13. Over the bound it WARNs and returns; it never exits.

    The Host owns the refusal. A probe that grew a gate here would refuse runs
    admission would have accepted, and would do it from a copy of a constant
    whose meaning section 21.7 already moved once.
    """
    over = str(driver._MAX_PROJECT_ARCHIVE_BYTES + 1)
    fake = _fake_git_inputs(config_size=over, dataset_size="1")

    # Returns normally: no CheckFailure, no SystemExit, no exception at all.
    _run_p9(monkeypatch, project_root, fake)

    out = capsys.readouterr().out
    assert "WARN P9-locked-project-inputs" in out
    assert "PASS P9-locked-project-inputs" not in out
    # It must say WHO refuses and that this probe does not, so the operator does
    # not read the WARN as a stop the driver made.
    assert "admission" in out.lower()
    assert "does not gate" in out


def test_p9_skips_with_a_named_reason_when_git_is_unavailable(
    monkeypatch, project_root, capsys
):
    """A plausible wrong number is worse than no number for a reporting probe.

    Nothing downstream re-checks P9's arithmetic, so a total read at the wrong
    commit would travel into the run report unchallenged.
    """
    _run_p9(monkeypatch, project_root, _fake_git_inputs(rev_parse_rc=128))

    out = capsys.readouterr().out
    assert "SKIP P9-locked-project-inputs" in out
    assert "bytes=" not in out


def test_p9_reports_the_config_when_the_dataset_ref_cannot_be_resolved(
    monkeypatch, project_root, capsys
):
    """Partial knowledge is reported as partial, never completed by guessing."""
    fake = _fake_git_inputs(config_body='{"no_dataset_key": true}')
    _run_p9(monkeypatch, project_root, fake)

    out = capsys.readouterr().out
    assert "training-config" in out
    assert "unresolved" in out
    # No total, because a total over an incomplete set is a wrong number.
    assert "count=2" not in out


def test_p9_runs_after_p7_and_before_the_bind_probe():
    """Ordering: P9 reads the commit P7 has just proven is the published one."""
    source = _DRIVER.read_text(encoding="utf-8")
    p7 = source.index("_check_p7_branch_is_publishable(project_root)")
    p9 = source.index("_check_p9_locked_project_inputs(", p7)
    bind = source.index("_probe_bind_source(", p9)
    assert p7 < p9 < bind


def test_p9_bounds_are_restated_from_the_host_with_a_citation():
    """Restated, not imported; the citation is what an auditor follows.

    A skill script does not import synaptic_host. The cost of restating is that
    the copy can drift, so the comment must name the file and lines it mirrors.
    """
    source = _DRIVER.read_text(encoding="utf-8")
    assert driver._MAX_PROJECT_ARCHIVE_BYTES == 256 * 1024 * 1024
    assert driver._MAX_PROJECT_EXPANDED_BYTES == 512 * 1024 * 1024
    assert driver._MAX_PROJECT_ENTRIES == 20_000
    assert "docker_staging.py:45-47" in source


# --------------------------------------------------------------------------
# P10-daemon-alive (blocker B-13, section 22.7)
#
# `docker context inspect` is not a daemon check: with Docker Desktop stopped it
# exits 0 with stdout byte-identical to the running case (measurement #203). The
# explicit `--host ... version` probe is the only one that separates the two
# states, and P10 issues it under the composition's own four-key environment.
# --------------------------------------------------------------------------

_ENDPOINT = "npipe:////./pipe/dockerDesktopLinuxEngine"
_DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
_SERVER_VERSION = "29.3.1"


def _fake_version(*, returncode: int = 0, stdout: str = _SERVER_VERSION,
                  stderr: str = "", seen: dict | None = None):
    """A `_run` replacement answering the version probe and recording its call."""

    def run(argv, *, timeout=300, env=None):
        assert argv[0] == _DOCKER, argv
        assert argv[1:3] == ["--host", _ENDPOINT], argv
        assert argv[3] == "version", argv
        assert "--format" in argv and "{{.Server.Version}}" in argv, argv
        if seen is not None:
            seen["argv"] = argv
            seen["env"] = env
        return _completed(argv, returncode, stdout, stderr)

    return run


def _four_keys(monkeypatch, **overrides):
    """Put exactly the composition's four keys in the environment."""
    values = {"SystemRoot": r"C:\Windows", "TEMP": r"C:\Temp",
              "TMP": r"C:\Temp", "WINDIR": r"C:\Windows"}
    values.update(overrides)
    for key, value in values.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


def test_p10_passes_and_reports_the_server_version(monkeypatch, capsys):
    _four_keys(monkeypatch)
    monkeypatch.setattr(driver, "_run", _fake_version())

    driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    out = capsys.readouterr().out
    assert "PASS P10-daemon-alive" in out
    assert _SERVER_VERSION in out


def test_p10_fails_clean_when_the_probe_exits_non_zero(monkeypatch, capsys):
    """THE red case. Exit 1 is the stopped-engine shape measured in #203.

    It must raise a NAMED failure, not fall through to the rest of the sweep:
    every later precondition would then report its own unrelated symptom.
    """
    _four_keys(monkeypatch)
    monkeypatch.setattr(
        driver, "_run",
        _fake_version(returncode=1, stdout="",
                      stderr="error during connect: open //./pipe/... "
                             "The system cannot find the file specified."),
    )

    with pytest.raises(driver.CheckFailure) as raised:
        driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    message = str(raised.value)
    assert message.startswith("P10-daemon-unavailable")
    assert "exit 1" in message
    # The remedy, and the two commands that would lie to the operator here.
    assert "Docker Desktop" in message
    assert "context inspect" in message
    assert "desktop status" in message


def test_p10_runs_the_probe_under_exactly_the_compositions_four_keys(monkeypatch):
    """The environment IS the B-13 variable, so an inherited one is a weaker check.

    A probe run under the operator's own environment carries USERPROFILE and
    would pass in precisely the case the Host fails.
    """
    _four_keys(monkeypatch)
    monkeypatch.setenv("USERPROFILE", r"C:\Users\operator")
    seen: dict = {}
    monkeypatch.setattr(driver, "_run", _fake_version(seen=seen))

    driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    assert set(seen["env"]) == set(driver._COMPOSITION_ENVIRONMENT_KEYS)
    assert "USERPROFILE" not in seen["env"]


def test_p10_reports_key_names_and_never_key_values(monkeypatch, capsys):
    """No secrets in probe output. The key set is the fact; the values are not."""
    _four_keys(monkeypatch, TEMP=r"C:\Users\operator\AppData\Local\Temp")
    monkeypatch.setattr(driver, "_run", _fake_version())

    driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    out = capsys.readouterr().out
    for key in driver._COMPOSITION_ENVIRONMENT_KEYS:
        assert key in out
    assert r"C:\Users\operator\AppData\Local\Temp" not in out
    assert r"C:\Windows" not in out


def test_p10_names_the_missing_key_the_host_would_not_name(monkeypatch):
    """A separate tag because the remedy is the shell, not Docker.

    A missing key reaches the Host as a KeyError folded into
    `one absolute Windows Docker executable is required`
    (`docker_prepared_composition.py:145`), which sends the operator after the
    wrong thing entirely.
    """
    _four_keys(monkeypatch, WINDIR=None)

    def unreachable(argv, *, timeout=300, env=None):
        raise AssertionError("the probe must not run with an incomplete environment")

    monkeypatch.setattr(driver, "_run", unreachable)

    with pytest.raises(driver.CheckFailure) as raised:
        driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    message = str(raised.value)
    assert message.startswith("P10-environment-incomplete")
    assert "WINDIR" in message


def test_p10_does_not_gate_on_an_empty_version_with_a_zero_exit(monkeypatch, capsys):
    """The ruling makes a NON-ZERO exit the gate. Zero with no version is unmeasured.

    Refusing there would be the driver inventing a condition the Host's own
    liveness check does not have (`docker_prepared_composition.py:172-178`
    tests the outcome, not the payload).
    """
    _four_keys(monkeypatch)
    monkeypatch.setattr(driver, "_run", _fake_version(stdout=""))

    driver._check_p10_daemon_alive(_DOCKER, _ENDPOINT)

    out = capsys.readouterr().out
    assert "WARN P10-daemon-alive" in out
    assert "PASS P10-daemon-alive" not in out


def test_p10_runs_after_p2_and_before_every_other_precondition():
    """Ordering: a stopped engine costs one command, not a full sweep."""
    source = _DRIVER.read_text(encoding="utf-8")
    call = source.index("_check_p10_daemon_alive(args.docker, args.endpoint)")
    p2 = source.index("_check_p2_endpoint(args.docker", 0)
    p3 = source.index("_check_p3_drive_letter_root(project_root)", call)
    assert p2 < call < p3


def test_p10_key_set_is_restated_from_the_host_with_a_citation():
    """Restated, not imported; the driver has never taken the synaptic_host seam.

    The contract itself is enforced by `DockerCLIEnvironmentV1.__post_init__`
    (`docker_v1/model.py:1144`) and asserted by test E1, so this driver does not
    re-derive it. It only has to name where the copy came from.
    """
    source = _DRIVER.read_text(encoding="utf-8")
    assert driver._COMPOSITION_ENVIRONMENT_KEYS == (
        "SystemRoot", "TEMP", "TMP", "WINDIR",
    )
    assert "docker_prepared_composition.py:116" in source
    assert "model.py:1144" in source
