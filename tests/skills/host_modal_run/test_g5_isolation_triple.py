"""Credential-free gate regressions; all provider calls use strict fakes.

Run with unittest, including inside the submit image (no pytest install needed).
The optional real-SDK test binds signatures only; it invokes no SDK entry.
"""
from __future__ import annotations

import contextlib
import functools
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".skills/host-modal-run/scripts/g5_isolation_triple.py"
spec = importlib.util.spec_from_file_location("g5_gate_under_test", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

WORKER_SOURCE = '''
def build_modal_deployment():
    app = sdk.App(APP_NAME, include_source=False)
    @app.function(retries=0, restrict_modal_access=True,
                  single_use_containers=True, include_source=False)
    def run_sft_v1(command):
        pass
'''


class WorkerSafetyTests(unittest.TestCase):
    def test_exact_worker_passes_despite_formatting(self):
        self.assertEqual(gate.missing_safety_literals(WORKER_SOURCE), [])

    def test_relaxed_worker_is_not_hidden_by_app_or_comment(self):
        source = WORKER_SOURCE.replace("single_use_containers=True, include_source=False",
                                       "single_use_containers=True, include_source=True")
        source += "\n# include_source=False\n"
        self.assertIn("include_source=False", source)
        self.assertEqual(gate.missing_safety_literals(source), ["include_source=False"])

    def test_each_relaxed_setting_fails_with_decoy_literals(self):
        for literal in gate.STANDING_SAFETY_LITERALS:
            with self.subTest(literal=literal):
                name = literal.split("=", 1)[0]
                source = WORKER_SOURCE.replace(literal, name + "=None")
                source += "\n# " + " ".join(gate.STANDING_SAFETY_LITERALS)
                self.assertEqual(gate.missing_safety_literals(source), [literal])

    def test_missing_ambiguous_dynamic_or_wrong_scope_fails_closed(self):
        cases = ["not valid Python!", WORKER_SOURCE.replace("run_sft_v1", "other"),
                 WORKER_SOURCE.replace("build_modal_deployment", "other"),
                 WORKER_SOURCE + WORKER_SOURCE,
                 WORKER_SOURCE.replace("@app.function(", "@other.function("),
                 WORKER_SOURCE.replace("@app.function(", "@app.function(**options, "),
                 WORKER_SOURCE.replace("    @app.function", "    @extra\n    @app.function")]
        for source in cases:
            with self.subTest(source=source):
                self.assertEqual(gate.missing_safety_literals(source), list(gate.STANDING_SAFETY_LITERALS))

    def test_boolean_is_not_integer_zero(self):
        self.assertEqual(gate.missing_safety_literals(WORKER_SOURCE.replace("retries=0", "retries=False")),
                         ["retries=0"])


def configuration():
    return {
        "environment_name": "synaptic-smoke-v1",
        "volumes": {"control_name": "synaptic-training-control-smoke-v1",
                    "artifact_name": "synaptic-training-artifacts-smoke-v1"},
        "runtime_secret": {"name": "synaptic-training-runtime-smoke-v1",
                           "required_keys": list(gate.REQUIRED_SECRET_KEYS)},
    }


class GateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="g5-test-")
        self.addCleanup(self.directory.cleanup)
        self.config_path = Path(self.directory.name) / "modal.json"
        self.config = configuration()
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.output = io.StringIO()
        def start(patcher):
            value = patcher.start()
            self.addCleanup(patcher.stop)
            return value
        start(patch.dict(os.environ, {}, clear=True))
        start(patch.object(gate, "read_worker_blob", return_value=WORKER_SOURCE))
        self.import_sdk = start(patch.object(gate.importlib, "import_module"))
        self.client = object()
        self.calls = []
        self.fail_stage = None

        def handle(stage, name, kwargs):
            self.calls.append((stage, name, kwargs))
            def hydrate():
                self.calls.append(("hydrate", stage, {}))
                if self.fail_stage == stage:
                    raise RuntimeError("synthetic-private-error-text")
            return SimpleNamespace(hydrate=hydrate)

        def client_from_credentials(token_id, token_secret):
            self.assertEqual((token_id, token_secret), ("sentinel-id", "sentinel-secret"))
            self.calls.append(("client", None, {}))
            return self.client

        def environment_from_name(name, *, create_if_missing=False, client=None):
            return handle("environment", name, locals())

        def volume_from_name(name, *, environment_name=None, create_if_missing=False, client=None):
            stage = "control-volume" if name == self.config["volumes"]["control_name"] else "artifact-volume"
            return handle(stage, name, locals())

        def secret_from_name(name, *, environment_name=None, required_keys=(), client=None):
            return handle("secret", name, locals())

        self.sdk = SimpleNamespace(
            __version__="1.5.4",
            Client=SimpleNamespace(from_credentials=client_from_credentials),
            Environment=SimpleNamespace(from_name=environment_from_name),
            Volume=SimpleNamespace(from_name=volume_from_name),
            Secret=SimpleNamespace(from_name=secret_from_name),
        )
        self.import_sdk.return_value = self.sdk

    def credentials(self):
        os.environ.update(MODAL_TOKEN_ID="sentinel-id", MODAL_TOKEN_SECRET="sentinel-secret")

    def main(self, *args):
        with contextlib.redirect_stdout(self.output):
            return gate.main(["--config", str(self.config_path), "--repo-root", str(ROOT), *args])

    def lookup(self):
        with contextlib.redirect_stdout(self.output):
            return gate.lookup_only(self.config)

    def test_missing_and_blank_credentials_never_start_container(self):
        with patch.object(gate, "run_lookup_container") as launch:
            for value in (None, "", " "):
                with self.subTest(value=value):
                    self.credentials()
                    if value is None:
                        del os.environ["MODAL_TOKEN_SECRET"]
                    else:
                        os.environ["MODAL_TOKEN_SECRET"] = value
                    self.assertEqual(self.main("--check", "--submit-image", "local:test",
                                               "--rotation-recorded-at", "2026-09-07T00:00:00Z"), 1)
            launch.assert_not_called()
        self.assertNotIn("G5 PASS", self.output.getvalue())

    def test_offline_failure_prevents_container_even_with_credentials(self):
        self.credentials()
        with patch.object(gate, "run_lookup_container") as launch:
            self.assertEqual(self.main("--check", "--submit-image", "local:test"), 1)
            launch.assert_not_called()

    def test_relaxed_worker_prevents_live_container(self):
        self.credentials()
        source = WORKER_SOURCE.replace("single_use_containers=True, include_source=False",
                                       "single_use_containers=True, include_source=True")
        with patch.object(gate, "read_worker_blob", return_value=source), \
                patch.object(gate, "run_lookup_container") as launch:
            self.assertEqual(self.main("--check", "--submit-image", "local:test",
                                       "--rotation-recorded-at", "2026-09-07T00:00:00Z"), 1)
            launch.assert_not_called()
        self.assertIn("FAIL S3 standing-safety", self.output.getvalue())

    def test_overlap_prevents_provider_reads(self):
        self.credentials()
        self.config["environment_name"] = "main"
        self.assertEqual(self.lookup(), 1)
        self.import_sdk.assert_not_called()

    def test_lookup_missing_credentials_prevents_sdk_import(self):
        self.assertEqual(self.lookup(), 1)
        self.import_sdk.assert_not_called()

    def test_wrong_sdk_prevents_client_and_lookups(self):
        self.credentials()
        self.sdk.__version__ = "1.5.1"
        self.assertEqual(self.lookup(), 1)
        self.assertEqual(self.calls, [])
        self.assertIn("G5 LOOKUP FAIL sdk-version", self.output.getvalue())

    def test_sdk_import_error_does_not_disclose_text(self):
        self.credentials()
        self.import_sdk.side_effect = RuntimeError("synthetic-private-error-text")
        self.assertEqual(self.lookup(), 1)
        self.assertEqual(self.output.getvalue(), "G5 LOOKUP FAIL sdk-import\n")

    def test_exact_named_lookups_and_noncreating_arguments(self):
        self.credentials()
        self.assertEqual(self.lookup(), 0)
        entries = [(stage, name, kwargs) for stage, name, kwargs in self.calls
                   if stage not in ("client", "hydrate")]
        self.assertEqual([s for s, _, _ in entries],
                         ["environment", "control-volume", "artifact-volume", "secret"])
        self.assertEqual([n for _, n, _ in entries], [self.config["environment_name"],
                         self.config["volumes"]["control_name"],
                         self.config["volumes"]["artifact_name"], self.config["runtime_secret"]["name"]])
        for stage, _, kwargs in entries:
            self.assertIs(kwargs["client"], self.client)
            if stage != "environment":
                self.assertEqual(kwargs["environment_name"], self.config["environment_name"])
            if stage != "secret":
                self.assertIs(kwargs["create_if_missing"], False)
            else:
                self.assertNotIn("create_if_missing", kwargs)
                self.assertEqual(kwargs["required_keys"], list(gate.REQUIRED_SECRET_KEYS))
        self.assertEqual(sum(s == "hydrate" for s, _, _ in self.calls), 4)
        self.assertEqual(self.output.getvalue(), "G5 LOOKUP PASS\n")

    def test_each_failed_hydration_stops_later_lookups_and_hides_error(self):
        self.credentials()
        stages = ["environment", "control-volume", "artifact-volume", "secret"]
        for index, stage in enumerate(stages):
            with self.subTest(stage=stage):
                self.calls.clear()
                self.output.seek(0)
                self.output.truncate()
                self.fail_stage = stage
                self.assertEqual(self.lookup(), 1)
                self.assertEqual(sum(s == "hydrate" for s, _, _ in self.calls), index + 1)
                self.assertEqual(self.output.getvalue(), f"G5 LOOKUP FAIL {stage}\n")

    def test_container_argv_contains_only_credential_names_and_readonly_mounts(self):
        self.credentials()
        result = subprocess.CompletedProcess([], 0, "G5 LOOKUP PASS\n", "")
        with patch.object(gate.subprocess, "run", return_value=result) as run:
            with contextlib.redirect_stdout(self.output):
                self.assertTrue(gate.run_lookup_container(self.config_path, "local:test", "docker", "unix:///test"))
        command = run.call_args.args[0]
        self.assertNotIn("--rm", command)
        self.assertIn("--pull=never", command)
        self.assertEqual([command[i + 1] for i, arg in enumerate(command) if arg == "-e"],
                         ["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"])
        self.assertTrue(all(command[i + 1].endswith(":ro") for i, arg in enumerate(command) if arg == "-v"))
        self.assertIn("--lookup-only", command)
        for value in ("sentinel-id", "sentinel-secret"):
            self.assertNotIn(value, " ".join(command))

    def test_failed_or_malformed_container_output_never_passes_or_leaks(self):
        for code, out in ((1, "G5 LOOKUP PASS\n"), (0, ""),
                          (0, "synthetic-private-error-text"), (1, "G5 LOOKUP FAIL secret\n")):
            with self.subTest(code=code, out=out):
                result = subprocess.CompletedProcess([], code, out, "synthetic-private-error-text")
                with patch.object(gate.subprocess, "run", return_value=result):
                    with contextlib.redirect_stdout(self.output):
                        self.assertFalse(gate.run_lookup_container(self.config_path, "local:test", "docker", "unix:///test"))
        self.assertNotIn("synthetic-private-error-text", self.output.getvalue())

    def test_offline_success_does_not_start_lookup_or_claim_full_pass(self):
        with patch.object(gate, "run_lookup_container") as launch:
            self.assertEqual(self.main("--rotation-recorded-at", "2026-09-07T00:00:00Z"), 0)
            launch.assert_not_called()
        self.import_sdk.assert_not_called()
        self.assertNotIn("G5 PASS", self.output.getvalue())

    def test_live_gate_requires_positive_container_evidence(self):
        self.credentials()
        for outcome in (False, True):
            with self.subTest(outcome=outcome), patch.object(gate, "run_lookup_container", return_value=outcome) as launch:
                self.assertEqual(self.main("--check", "--submit-image", "local:test",
                                           "--rotation-recorded-at", "2026-09-07T00:00:00Z"), 0 if outcome else 1)
                launch.assert_called_once()


class InstalledSdkSignatures(unittest.TestCase):
    def test_pinned_sdk_accepts_lookup_shapes_without_calls(self):
        try:
            import modal
        except ImportError:
            self.skipTest("Modal not installed; run in the submit image for the pin check")
        if modal.__version__ != "1.5.4":
            self.skipTest("run in the submit image for the Modal 1.5.4 signature check")
        sentinel = object()
        # SDK 1.5.4 exposes a MethodWithAio descriptor as a partial. inspect
        # follows its wrapped signature, which still includes implicit cls.
        constructor = modal.Client.from_credentials
        self.assertIsInstance(constructor, functools.partial)
        self.assertEqual(constructor.args, (modal.Client,))
        inspect.signature(constructor.func).bind(*constructor.args, sentinel, sentinel)
        inspect.signature(modal.Environment.from_name).bind("target", create_if_missing=False, client=sentinel)
        inspect.signature(modal.Volume.from_name).bind("target", environment_name="env", create_if_missing=False, client=sentinel)
        signature = inspect.signature(modal.Secret.from_name)
        signature.bind("target", environment_name="env", required_keys=list(gate.REQUIRED_SECRET_KEYS), client=sentinel)
        with self.assertRaises(TypeError):
            signature.bind("target", environment_name="env", create_if_missing=False)


class BuildCommandTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix" and Path("/bin/bash").is_file(), "Bash gate wrapper runs on the Linux lane")
    def test_g2_runs_existing_image_and_retains_container(self):
        with tempfile.TemporaryDirectory(prefix="g2-command-") as directory:
            root = Path(directory)
            script = root / ".skills/host-modal-run/container/build.sh"
            script.parent.mkdir(parents=True)
            script.write_bytes((ROOT / ".skills/host-modal-run/container/build.sh").read_bytes())
            requirements = root / "synaptic-tuner/requirements"
            requirements.mkdir(parents=True)
            (requirements / "modal-launcher-v1.lock").write_text("fixture", encoding="utf-8")
            binaries = root / "bin"
            binaries.mkdir()
            git = binaries / "git"
            git.write_text('#!/bin/sh\ncase "$*" in\n*ls-tree*) echo "160000 commit pinned synaptic-tuner";;\n*) echo pinned;;\nesac\n', encoding="utf-8")
            docker = binaries / "docker"
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$GATE_ARGV_RECORD"\n', encoding="utf-8")
            git.chmod(0o700)
            docker.chmod(0o700)
            record = root / "argv.txt"
            completed = subprocess.run(["/bin/bash", str(script), "--g2", "--no-build"],
                env={"PATH": str(binaries) + ":/usr/bin:/bin", "DOCKER_BIN": str(docker),
                     "SUBMIT_IMAGE_TAG": "local:test", "GATE_ARGV_RECORD": str(record)},
                capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            argv = record.read_text(encoding="utf-8").splitlines()
            self.assertEqual(argv[0], "run")
            self.assertIn("--pull=never", argv)
            self.assertNotIn("--rm", argv)
            self.assertIn("local:test", argv)
            self.assertIn("/gates/g2_submit_container.py", argv)


if __name__ == "__main__":
    unittest.main()
