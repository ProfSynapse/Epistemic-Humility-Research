"""Restoration pins a descriptor, not its ephemeral bound wrapper."""

import functools
import inspect
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from synaptic_host.modal_provider import ExplicitModalHostSession


class FreshPartialDescriptor:
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        return functools.partial(self.function, owner)


class ModalRestoreDescriptorTests(unittest.TestCase):
    def make_session(self, callback):
        class FunctionCall:
            from_id = FreshPartialDescriptor(callback)

        sdk = SimpleNamespace(__version__="1.5.4", FunctionCall=FunctionCall)
        client = object()
        session = ExplicitModalHostSession(sdk=sdk, client=client, config=object(), binding=object())
        return session, sdk, client

    def test_fresh_bound_partial_restores_once(self):
        calls = []
        def restore(owner, reference, *, client):
            calls.append((owner, reference, client))
            return SimpleNamespace(object_id=reference)
        session, sdk, client = self.make_session(restore)
        self.assertIsNot(sdk.FunctionCall.from_id, sdk.FunctionCall.from_id)
        self.assertTrue(session._restore_callback_is_current())
        restored = session.restore_function_call("fc-test")
        self.assertEqual(restored.object_id, "fc-test")
        self.assertEqual(calls, [(sdk.FunctionCall, "fc-test", client)])

    def test_descriptor_replaced_before_call_refuses_without_invoking(self):
        calls = []
        def restore(*args, **kwargs):
            calls.append(True)
        session, sdk, _ = self.make_session(restore)
        sdk.FunctionCall.from_id = FreshPartialDescriptor(restore)
        with self.assertRaises(ValueError):
            session.restore_function_call("fc-test")
        self.assertEqual(calls, [])

    def test_descriptor_replaced_during_call_refuses(self):
        calls = []
        def restore(owner, reference, *, client):
            calls.append(True)
            owner.from_id = FreshPartialDescriptor(restore)
            return SimpleNamespace(object_id=reference)
        session, _, _ = self.make_session(restore)
        with self.assertRaises(ValueError):
            session.restore_function_call("fc-test")
        self.assertEqual(calls, [True])

    def test_class_replacement_refuses(self):
        session, sdk, _ = self.make_session(lambda *_args, **_kwargs: None)
        sdk.FunctionCall = type("Other", (), {"from_id": sdk.FunctionCall.from_id})
        self.assertFalse(session._restore_callback_is_current())

    def test_in_place_target_mutation_before_call_never_invokes(self):
        calls = []
        session, sdk, _ = self.make_session(lambda *_args, **_kwargs: None)
        def changed(*args, **kwargs):
            calls.append(True)
        inspect.getattr_static(sdk.FunctionCall, "from_id").function = changed
        with self.assertRaises(ValueError):
            session.restore_function_call("fc-test")
        self.assertEqual(calls, [])

    def test_in_place_target_mutation_during_call_refuses(self):
        calls = []
        def restore(owner, reference, *, client):
            calls.append(True)
            inspect.getattr_static(owner, "from_id").function = lambda *_args, **_kwargs: None
            return SimpleNamespace(object_id=reference)
        session, _, _ = self.make_session(restore)
        with self.assertRaises(ValueError):
            session.restore_function_call("fc-test")
        self.assertEqual(calls, [True])

    def test_pinned_sdk_descriptor_shape_without_client_or_config(self):
        with patch.dict(os.environ, {"MODAL_IS_REMOTE": "1"}):
            try:
                import modal
            except ImportError:
                self.skipTest("Modal SDK is not installed")
        if modal.__version__ != "1.5.4":
            self.skipTest("Exact pinned Modal SDK is required")
        self.assertIsNot(modal.FunctionCall.from_id, modal.FunctionCall.from_id)
        self.assertIs(inspect.getattr_static(modal.FunctionCall, "from_id"),
                      inspect.getattr_static(modal.FunctionCall, "from_id"))
        session = ExplicitModalHostSession(sdk=modal, client=object(), config=object(), binding=object())
        self.assertTrue(session._restore_callback_is_current())


if __name__ == "__main__":
    unittest.main()
