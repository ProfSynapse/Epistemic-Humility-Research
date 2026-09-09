import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from synaptic_host import cli, training_operator


ROOT = Path(__file__).resolve().parents[2]


def test_original_eight_token_run_parser_is_unchanged() -> None:
    arguments = [
        "training", "run", "--provider", "modal", "--config",
        "project://training/smokes/modal-sft.json", "--destination",
        "provider-staging",
    ]
    assert cli._parse(arguments) == (
        "modal", "project://training/smokes/modal-sft.json", "provider-staging"
    )
    assert training_operator._parse(arguments) is None


def test_fresh_process_routes_operator_command_from_release_cwd(tmp_path: Path) -> None:
    candidate = str(ROOT)
    script = (
        "import runpy,sys;"
        f"sys.path.insert(0,{candidate!r});"
        "sys.argv=['synaptic_host','training','status','--run-id','bad'];"
        "runpy.run_module('synaptic_host',run_name='__main__')"
    )
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script], cwd=tmp_path,
        env=environment, text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout) == {
        "schema_version": "synaptic-training-operator-result/v1",
        "code": "COMMAND_INVALID", "run_id": None,
    }
    assert completed.stderr == ""


def test_import_and_provider_failures_emit_only_closed_result(tmp_path: Path, capsys) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    manifest = SimpleNamespace(project_id="project-one")
    run_id = "run-" + "a" * 32
    for target in ("_project_context", "_reconcile"):
        patches = [patch.object(
            training_operator, "_project_context",
            return_value=(manifest, context),
        )]
        if target == "_project_context":
            patches[0] = patch.object(
                training_operator, "_project_context",
                side_effect=RuntimeError("provider-secret-text"),
            )
        else:
            patches.extend((
                patch("synaptic_host.launcher.ensure_and_reexec", return_value=object()),
                patch.object(training_operator, "_reconcile",
                             side_effect=RuntimeError("provider-secret-text")),
            ))
        entered = [item.start() for item in patches]
        try:
            assert training_operator.main(
                ["training", "reconcile", "--run-id", run_id],
                project_root=tmp_path, engine_root=tmp_path,
            ) == 4
        finally:
            for item in reversed(patches):
                item.stop()
        captured = capsys.readouterr()
        assert "provider-secret-text" not in captured.out + captured.err
        assert captured.err == ""
        assert json.loads(captured.out)["code"] == "OPERATION_UNAVAILABLE"
