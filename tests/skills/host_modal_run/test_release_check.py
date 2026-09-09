from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".skills/host-modal-run/scripts/release_check.py"
SPEC = importlib.util.spec_from_file_location("modal_release_check", SCRIPT)
release_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(release_check)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "release"
    (root / "synaptic-tuner").mkdir(parents=True)
    return root


class Runner:
    def __init__(self, *, dirty=False, wrong_pin=False, wrong_top=None, fail_stage=None, timeout_stage=None):
        self.calls = []
        self.dirty = dirty
        self.wrong_pin = wrong_pin
        self.wrong_top = wrong_top
        self.fail_stage = fail_stage
        self.timeout_stage = timeout_stage

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command[0] == "git":
            if "status" in command:
                return SimpleNamespace(returncode=0, stdout=" M source" if self.dirty else "")
            if "ls-tree" in command:
                return SimpleNamespace(returncode=0, stdout="160000 commit " + "a" * 40 + "\tsynaptic-tuner\n")
            if "--show-toplevel" in command:
                is_engine = Path(command[2]).name == "synaptic-tuner"
                wrong = self.wrong_top == ("engine" if is_engine else "host")
                top = str(Path(command[2]).parent) if wrong else command[2]
                return SimpleNamespace(returncode=0, stdout=top + "\n")
            return SimpleNamespace(returncode=0, stdout=("b" if self.wrong_pin else "a") * 40 + "\n")
        stage = _stage(command)
        if stage == self.timeout_stage:
            raise subprocess.TimeoutExpired(command, 1)
        output = ""
        stderr = ""
        returncode = 1 if stage == self.fail_stage else 0
        if stage == "g5-offline":
            returncode = 1
            output = release_check._offline_g5_output(Path(command[2]).parents[3])
        return SimpleNamespace(returncode=returncode, stdout=output, stderr=stderr)


def _stage(command) -> str:
    text = " ".join(command)
    if "test_training_operator_status.py" in text:
        return "host"
    if "test_modal_provider.py" in text:
        return "host-supplemental"
    if "test_modal_native_login.py" in text:
        return "native"
    if "test_cold_bootstrap.py" in text:
        return "cold"
    if "test_modal_bundle.py" in text:
        return "engine"
    if "sync_skills.py" in text:
        return "mirrors"
    if "g2_native_host.py" in text:
        return "g2"
    if "g3_engine_lock_digests.py" in text:
        return "g3"
    if "g5_isolation_triple.py" in text:
        return "g5-offline"
    return "unknown"


def test_default_composes_exact_isolated_lanes_without_bootstrap(tmp_path, capsys) -> None:
    root = _root(tmp_path)
    runner = Runner()
    assert release_check.main(["--project-root", str(root)], runner=runner) == 0
    child_calls = runner.calls[6:]
    assert [_stage(command) for command, _kwargs in child_calls] == [
        "host", "host-supplemental", "native", "cold", "engine", "mirrors", "g2", "g3", "g5-offline",
    ]
    assert "--prepare-runtime" not in child_calls[6][0]
    engine_command = child_calls[4][0]
    assert len(release_check.ENGINE_TESTS) == 19
    assert all(str(root / "synaptic-tuner" / path) in engine_command for path in release_check.ENGINE_TESTS)
    assert all(str(root / path) in child_calls[0][0] for path in release_check.HOST_TESTS)
    assert all(
        str(root / path) in child_calls[1][0]
        for path in release_check.SUPPLEMENTAL_HOST_TESTS
    )
    assert str(root / "tests/skills/host_modal_run/test_release_check.py") in child_calls[2][0]
    assert "result=S1-S3-pass-S4-expected-refusal-not-full-G5" in capsys.readouterr().out


def test_prepare_runtime_is_explicit_and_only_reaches_g2(tmp_path) -> None:
    root = _root(tmp_path)
    runner = Runner()
    assert release_check.main(
        ["--project-root", str(root), "--prepare-runtime"], runner=runner
    ) == 0
    uses = [command for command, _kwargs in runner.calls if "--prepare-runtime" in command]
    assert len(uses) == 1
    assert _stage(uses[0]) == "g2"


def test_dirty_or_wrong_pin_refuses_before_any_lane(tmp_path) -> None:
    root = _root(tmp_path)
    for runner in (
        Runner(dirty=True), Runner(wrong_pin=True), Runner(wrong_top="host"),
        Runner(wrong_top="engine"),
    ):
        assert release_check.main(["--project-root", str(root)], runner=runner) == 2
        assert len(runner.calls) == 6


def test_failure_and_timeout_stop_without_next_lane(tmp_path, capsys) -> None:
    root = _root(tmp_path)
    for runner in (Runner(fail_stage="native"), Runner(timeout_stage="native")):
        assert release_check.main(["--project-root", str(root)], runner=runner) == 1
        assert [_stage(command) for command, _kwargs in runner.calls[6:]] == [
            "host", "host-supplemental", "native",
        ]
        assert "cold" not in capsys.readouterr().out


def test_every_child_has_closed_credential_free_environment(tmp_path) -> None:
    root = _root(tmp_path)
    runner = Runner()
    assert release_check.main(["--project-root", str(root)], runner=runner) == 0
    expected = {
        "PATH": "/usr/bin:/bin", "MODAL_IS_REMOTE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }
    assert all(kwargs["env"] == expected for _command, kwargs in runner.calls)
    assert all(
        kwargs["stdin"] is subprocess.DEVNULL for _command, kwargs in runner.calls
    )


def test_g5_cannot_be_misreported_as_full_or_partial_without_marker(tmp_path, capsys) -> None:
    root = _root(tmp_path)
    runner = Runner()
    original = runner.__call__

    def false_full(command, **kwargs):
        result = original(command, **kwargs)
        if _stage(command) == "g5-offline":
            return SimpleNamespace(returncode=0, stdout="G5 PASS\n")
        return result

    assert release_check.main(["--project-root", str(root)], runner=false_full) == 1
    assert "stage=g5-offline reason=truth" in capsys.readouterr().out


def test_admission_timeout_is_closed(tmp_path, capsys) -> None:
    root = _root(tmp_path)

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("git", 1)

    assert release_check.main(["--project-root", str(root)], runner=timeout) == 2
    assert capsys.readouterr().out == (
        "RELEASE_CHECK FAIL stage=admission reason=unavailable\n"
    )


def test_project_root_must_be_one_absolute_argument(tmp_path, capsys) -> None:
    root = _root(tmp_path)
    assert release_check.main(["--project-root", "relative"], runner=Runner()) == 2
    assert release_check.main(
        ["--project-root", str(root), "--project-root", str(root)], runner=Runner()
    ) == 2
    assert capsys.readouterr().out.count("stage=arguments reason=invalid") == 2


def test_g5_rejects_extra_failure_contradiction_and_trace() -> None:
    baseline = release_check._offline_g5_output(Path("/released"))
    clean = SimpleNamespace(returncode=1, stdout=baseline, stderr="")
    assert release_check._expected_offline_g5(clean, Path("/released"))
    mutations = (
        baseline.replace("FAIL S4", "PASS S4"),
        baseline.replace("FAIL S4", "FAIL S3 other  bad\nFAIL S4"),
        baseline + "FAIL existence-process  unexpected\n",
        baseline + "G5 FAIL  failing checks: ['S4 rotation-attested', 'other']\n",
        baseline + "Traceback: private diagnostic\n",
    )
    assert not any(
        release_check._expected_offline_g5(
            SimpleNamespace(returncode=1, stdout=value, stderr=""), Path("/released")
        )
        for value in mutations
    )
    assert not release_check._expected_offline_g5(
        SimpleNamespace(returncode=1, stdout=baseline, stderr="private diagnostic\n"),
        Path("/released"),
    )
