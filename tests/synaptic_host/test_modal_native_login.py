"""Credential-free tests for native Modal authentication and launcher routing."""

import contextlib
import io
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from synaptic_host import launcher, modal_credentials


class SavedLoginTests(unittest.TestCase):
    def test_exact_saved_pair_and_no_client_construction(self):
        calls = []
        def get(key, *, use_env):
            self.assertFalse(use_env)
            calls.append(key)
            return {"token_id": "test-id", "token_secret": "test-secret"}[key]
        sdk = SimpleNamespace(__version__="1.5.4")
        config = SimpleNamespace(config=SimpleNamespace(get=get))
        with patch.object(modal_credentials.importlib, "import_module", side_effect=[sdk, config]):
            self.assertEqual(modal_credentials.saved_modal_credentials(), ("test-id", "test-secret"))
        self.assertEqual(calls, ["token_id", "token_secret"])

    def test_wrong_sdk_never_reads_saved_config(self):
        with patch.object(modal_credentials.importlib, "import_module",
                          return_value=SimpleNamespace(__version__="1.5.1")) as load:
            self.assertIsNone(modal_credentials.saved_modal_credentials())
        load.assert_called_once_with("modal")

    def test_failures_are_closed(self):
        output = io.StringIO()
        with patch.object(modal_credentials.importlib, "import_module",
                          side_effect=RuntimeError("synthetic-private-text")):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                self.assertIsNone(modal_credentials.saved_modal_credentials())
        self.assertEqual(output.getvalue(), "")

    def test_incomplete_blank_control_or_oversized_pair_refuses(self):
        for value in (None, "", " ", "value\n", "value\x7f", "x" * 4097):
            with self.subTest(value=value):
                sdk = SimpleNamespace(__version__="1.5.4")
                config = SimpleNamespace(config=SimpleNamespace(get=lambda key, **_: "test-id" if key == "token_id" else value))
                with patch.object(modal_credentials.importlib, "import_module", side_effect=[sdk, config]):
                    self.assertIsNone(modal_credentials.saved_modal_credentials())


class CredentialSelectionTests(unittest.TestCase):
    def test_explicit_complete_pair_never_reads_saved_login(self):
        with patch.object(modal_credentials, "saved_modal_credentials") as saved:
            self.assertEqual(modal_credentials.select_modal_credentials(
                {"MODAL_TOKEN_ID": "test-id", "MODAL_TOKEN_SECRET": "test-secret"},
                allow_saved=True), ("test-id", "test-secret"))
            saved.assert_not_called()

    def test_deployment_partial_or_invalid_explicit_pair_never_falls_back(self):
        for values in ({"MODAL_TOKEN_ID": "test-id"}, {"MODAL_TOKEN_SECRET": "test-secret"},
                       {"MODAL_TOKEN_ID": ""}, {"MODAL_TOKEN_SECRET": " "},
                       {"MODAL_TOKEN_ID": "test-id", "MODAL_TOKEN_SECRET": "bad\n"},
                       {"MODAL_TOKEN_ID": "test-id", "MODAL_TOKEN_SECRET": "x" * 4097},
                       {"MODAL_TOKEN_ID": "test-id", "MODAL_TOKEN_SECRET": "\ud800"}):
            with self.subTest(values=values), patch.object(modal_credentials, "saved_modal_credentials") as saved:
                self.assertIsNone(modal_credentials.select_modal_credentials(values, allow_saved=True))
                saved.assert_not_called()

    def test_absent_pair_reads_saved_login_only_when_allowed(self):
        with patch.object(modal_credentials, "saved_modal_credentials", return_value=("test-id", "test-secret")) as saved:
            self.assertIsNone(modal_credentials.select_modal_credentials({}, allow_saved=False))
            saved.assert_not_called()
            self.assertEqual(modal_credentials.select_modal_credentials({}, allow_saved=True), ("test-id", "test-secret"))
            saved.assert_called_once_with()


class NativeLauncherTests(unittest.TestCase):
    def test_long_operator_path_is_not_inherited(self):
        with patch.dict(os.environ, {"PATH": "x" * 5000, "HF_TOKEN": "not-forwarded"}, clear=True):
            environment = launcher._launcher_environment()
        self.assertEqual(environment, {"PATH": "/usr/bin:/bin"})

    def parent_environment(self, values):
        with patch.dict(os.environ, values, clear=True), \
                patch.object(launcher, "_runtime_proof", return_value=({}, "f" * 64)), \
                patch.object(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            root = Path.cwd()
            launcher.ensure_and_reexec(project_root=root, engine_root=root,
                                      argv=[], ingress_digest="b" * 64,
                                      contract_identity_digest="e" * 64)
        return run.call_args.kwargs["env"]

    def test_saved_profile_is_selected_only_when_both_env_names_absent(self):
        environment = self.parent_environment({"MODAL_PROFILE": "selected-profile", "HOME": "/home/test"})
        self.assertEqual(environment[launcher._SAVED_PROFILE], "1")
        self.assertEqual(environment["MODAL_PROFILE"], "selected-profile")
        self.assertNotIn("MODAL_TOKEN_ID", environment)
        self.assertNotIn("MODAL_TOKEN_SECRET", environment)

    def test_explicit_partial_blank_or_complete_pair_never_falls_back(self):
        for values in ({"MODAL_TOKEN_ID": "id"}, {"MODAL_TOKEN_SECRET": ""},
                       {"MODAL_TOKEN_ID": "id", "MODAL_TOKEN_SECRET": "secret"}):
            with self.subTest(values=values):
                environment = self.parent_environment({**values, "MODAL_PROFILE": "must-not-fallback"})
                self.assertNotIn(launcher._SAVED_PROFILE, environment)
                self.assertNotIn("MODAL_PROFILE", environment)

    def test_saved_login_is_read_after_proof_and_before_authority(self):
        events = []
        root = Path.cwd()
        environment = {launcher._MARKER: "1", launcher._INGRESS_DIGEST: "b" * 64,
                       launcher._CONTRACT_IDENTITY_DIGEST: "e" * 64,
                       launcher._RUNTIME_PROOF_DIGEST: "f" * 64, launcher._SAVED_PROFILE: "1"}
        def proof(*_):
            events.append("proof")
            return {}, "f" * 64
        def login():
            events.append("login")
            return "test-id", "test-secret"
        def issue(**_):
            events.append("authority")
            self.assertEqual(os.environ["MODAL_TOKEN_ID"], "test-id")
            self.assertEqual(os.environ["MODAL_TOKEN_SECRET"], "test-secret")
            return "authority"
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(launcher, "_runtime_proof", side_effect=proof), \
                patch.object(launcher, "launcher_python", return_value=Path(launcher.sys.executable)), \
                patch.object(modal_credentials, "saved_modal_credentials", side_effect=login), \
                patch.object(launcher, "_issue_isolated_child_authority_v1", side_effect=issue):
            self.assertEqual(launcher.ensure_and_reexec(
                project_root=root, engine_root=root, argv=[], ingress_digest="b" * 64,
                contract_identity_digest="e" * 64), "authority")
        self.assertEqual(events, ["proof", "login", "authority"])

    def test_bad_runtime_proof_never_reads_saved_login(self):
        root = Path.cwd()
        environment = {launcher._MARKER: "1", launcher._INGRESS_DIGEST: "b" * 64,
                       launcher._CONTRACT_IDENTITY_DIGEST: "e" * 64,
                       launcher._RUNTIME_PROOF_DIGEST: "f" * 64, launcher._SAVED_PROFILE: "1"}
        with patch.dict(os.environ, environment, clear=True), \
                patch.object(launcher, "_runtime_proof", return_value=({}, "a" * 64)), \
                patch.object(modal_credentials, "saved_modal_credentials") as login:
            with self.assertRaises(RuntimeError):
                launcher.ensure_and_reexec(project_root=root, engine_root=root, argv=[],
                                          ingress_digest="b" * 64, contract_identity_digest="e" * 64)
            login.assert_not_called()


if __name__ == "__main__":
    unittest.main()
