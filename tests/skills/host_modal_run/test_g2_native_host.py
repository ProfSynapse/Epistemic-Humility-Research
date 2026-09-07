"""Native G2 protocol tests: no downloads, credentials or provider calls."""
import contextlib
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from synaptic_host import cli, launcher

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('native_g2_under_test', ROOT / '.skills/host-modal-run/scripts/g2_native_host.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class NativeGateTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.dirty = False
        self.pin_mismatch = False
        def git(command, **kwargs):
            if 'status' in command:
                return ' M tracked-file' if self.dirty else ''
            if 'ls-tree' in command:
                return '160000 commit ' + 'b' * 40 + '\tsynaptic-tuner'
            if str(kwargs['cwd']).endswith('synaptic-tuner'):
                return 'c' * 40 if self.pin_mismatch else 'b' * 40
            return 'a' * 40
        def start(patcher):
            value = patcher.start()
            self.addCleanup(patcher.stop)
            return value
        start(patch.object(gate.subprocess, 'check_output', side_effect=git))
        self.proof = start(patch.object(launcher, '_runtime_proof', return_value=({}, 'f' * 64)))
        self.build = start(patch.object(launcher, '_build_runtime'))
        start(patch.object(launcher, '_runtime_stamp', return_value='stamp'))
        self.read = start(patch.object(cli, '_read_committed_git_blob_v1'))
        self.child = start(patch.object(gate.subprocess, 'run', return_value=SimpleNamespace(
            returncode=0, stdout='G2 NATIVE CHILD PASS\n', stderr='')))

    def run_gate(self, *args):
        with contextlib.redirect_stdout(self.output):
            return gate.main(list(args))

    def test_existing_runtime_passes_with_credential_free_isolated_child(self):
        self.assertEqual(self.run_gate(), 0)
        self.build.assert_not_called()
        command = self.child.call_args.args[0]
        self.assertIn('-I', command)
        self.assertNotIn('docker', command)
        self.assertEqual(self.child.call_args.kwargs['env'], {'PATH': '/usr/bin:/bin', 'MODAL_IS_REMOTE': '1'})
        self.read.assert_called_once()
        self.assertEqual(self.proof.call_count, 2)

    def test_missing_runtime_without_prepare_refuses_before_child(self):
        self.proof.side_effect = RuntimeError('absent')
        self.assertEqual(self.run_gate(), 1)
        self.build.assert_not_called()
        self.child.assert_not_called()

    def test_explicit_prepare_builds_then_verifies(self):
        self.proof.side_effect = [RuntimeError('absent'), ({}, 'f' * 64)]
        self.assertEqual(self.run_gate('--prepare-runtime'), 0)
        self.build.assert_called_once()
        self.assertEqual(self.proof.call_count, 2)

    def test_dirty_source_refuses_before_runtime_or_bootstrap(self):
        self.dirty = True
        self.assertEqual(self.run_gate('--prepare-runtime'), 1)
        self.proof.assert_not_called()
        self.build.assert_not_called()

    def test_wrong_engine_pin_refuses_before_runtime(self):
        self.pin_mismatch = True
        self.assertEqual(self.run_gate(), 1)
        self.proof.assert_not_called()

    def test_bootstrap_and_child_failures_are_closed(self):
        self.proof.side_effect = RuntimeError('synthetic-private-text')
        self.build.side_effect = RuntimeError('synthetic-private-text')
        self.assertEqual(self.run_gate('--prepare-runtime'), 1)
        self.proof.side_effect = None
        self.child.return_value = SimpleNamespace(returncode=1, stdout='synthetic-private-text', stderr='synthetic-private-text')
        self.assertEqual(self.run_gate(), 1)
        self.assertNotIn('synthetic-private-text', self.output.getvalue())


if __name__ == '__main__':
    unittest.main()
