from concurrent.futures import ThreadPoolExecutor
from copy import copy, deepcopy
import gc
import pickle
from threading import Event, Lock
from types import SimpleNamespace
import traceback
import weakref

import pytest

from synaptic_host.docker_v1.capability_assembly import (
    DockerCapabilityAssemblyCodeV1,
    DockerCapabilityAssemblyErrorV1,
    DockerCapabilityCleanupFailureClassV1,
    DockerCapabilityCleanupFailureV1,
    DockerCapabilityCleanupResultV1,
    DockerCapabilityOwnershipHandoffV1,
    DockerCapabilityResourceKindV1,
    DockerCapabilitySlotV1,
    DockerLiveCapabilityBuildV1,
)
from synaptic_host.docker_v1.facade import (
    DockerHostFacadeCloseCodeV1,
    DockerHostCloseErrorCodeV1,
    DockerHostCloseErrorV1,
    DockerHostOperationCodeV1,
    DockerHostOperationErrorV1,
    DockerHostFacadeLifecycleStateV1,
    DockerHostFacadeV1,
    DockerPrivateFacadeRuntimeAdapterV1,
)
from synaptic_tuner.api.v1.planning import (
    ProviderPlanContextV1,
    ProviderPlanRef,
    TrainingPlan,
    TrainingPlanBasisV1,
)
from synaptic_tuner.api.v1.providers import (
    ProviderCapabilities,
    ProviderDescriptor,
    ProviderRef,
)
from synaptic_tuner.api.v1.results import TrainingRunRef
from tuner.execution.coordinator_v1.model import WorkflowRecordV1
from tuner.execution.foundation_v2.identities import EffectKind


D = tuple(character * 64 for character in "123456789abcdef")


def _workflow():
    provider = ProviderRef("provider-a", "profile-a")
    run = TrainingRunRef("run-a", "project-a")
    descriptor = ProviderDescriptor(
        "synaptic-provider-descriptor/v1", "provider-a", "Provider A",
        "1.0.0", ProviderCapabilities(True, True, True, True, True, True),
    )
    basis = TrainingPlanBasisV1(
        "synaptic-training-plan-basis/v1", "request-a", run.project_ref,
        *D[:5],
    )
    context = ProviderPlanContextV1(
        "synaptic-provider-plan-context/v1", provider, basis.basis_digest,
        descriptor.descriptor_digest, D[5],
    )
    plan = TrainingPlan(
        "synaptic-training-plan/v2", basis,
        ProviderPlanRef(context.provider_context_digest),
    )
    return WorkflowRecordV1.planned(
        run=run, plan=plan, preflight_digest=D[6], context=context,
        provider=provider, descriptor=descriptor,
    )


class Runtime:
    def __init__(self, workflow, binding):
        self.workflow = workflow
        self.binding_value = binding
        self.start_hook = lambda: self.workflow
        self.reconcile_hook = lambda: self.workflow
        self.binding_hook = lambda _kind: self.binding_value
        self.calls = []

    def start(self):
        self.calls.append("start")
        return self.start_hook()

    def reconcile(self):
        self.calls.append("reconcile")
        return self.reconcile_hook()

    def binding(self, kind):
        self.calls.append(("binding", kind))
        return self.binding_hook(kind)


def _ownership(cleanup=None):
    class Ledger:
        def complete(self):
            return None

        def abort(self):
            if cleanup is None:
                return DockerCapabilityCleanupResultV1.build(0, 0, 0, ())
            try:
                cleanup(object())
            except BaseException:
                failure = DockerCapabilityCleanupFailureV1(
                    DockerCapabilitySlotV1.SOURCE_ROOT_AUTHORITY,
                    DockerCapabilityResourceKindV1.ROOT_AUTHORITY,
                    DockerCapabilityCleanupFailureClassV1.CLOSED,
                    None,
                )
                return DockerCapabilityCleanupResultV1.build(
                    1, 0, 0, (failure,)
                )
            return DockerCapabilityCleanupResultV1.build(1, 1, 0, ())

    live = DockerLiveCapabilityBuildV1(object(), Ledger())
    handoff = live.prepare_handoff()
    handoff.commit_handoff()
    return handoff


def _facade(workflow, binding, *, ownership=None, publish=True):
    runtime = Runtime(workflow, binding)
    adapter = DockerPrivateFacadeRuntimeAdapterV1(
        start=runtime.start, reconcile=runtime.reconcile,
        binding=runtime.binding,
    )
    if ownership is None:
        if publish:
            ownership = _ownership()
        else:
            class Ledger:
                def complete(self): return None
                def abort(self):
                    return DockerCapabilityCleanupResultV1.build(0, 0, 0, ())
            live = DockerLiveCapabilityBuildV1(object(), Ledger())
            ownership = live.prepare_handoff()
    facade = DockerHostFacadeV1(adapter, ownership)
    return facade, runtime, ownership, ownership


def test_product_surface_and_exact_reconstructed_results(mount_env):
    workflow = _workflow()
    binding = mount_env["catalog"].value
    facade, runtime, _cell, _ownership_value = _facade(workflow, binding)
    public = {
        name for name, value in vars(DockerHostFacadeV1).items()
        if not name.startswith("_") and (callable(value) or isinstance(value, property))
    }
    assert public == {
        "start_run", "reconcile_run", "effect_binding", "close",
        "lifecycle_state",
    }
    assert facade.start_run() == workflow
    assert facade.start_run() is not workflow
    assert facade.reconcile_run() == workflow
    returned = facade.effect_binding(EffectKind.SUBMIT)
    assert returned == binding and returned is not binding
    assert runtime.calls[-1] == ("binding", EffectKind.SUBMIT.value)


def test_unpublished_and_incomplete_attachment_never_operates(mount_env):
    facade, _runtime, handoff, ownership = _facade(
        _workflow(), mount_env["catalog"].value, publish=False
    )
    for operation in (
        facade.start_run, facade.reconcile_run,
        lambda: facade.effect_binding(EffectKind.SUBMIT), facade.close,
        lambda: facade.lifecycle_state,
    ):
        with pytest.raises((DockerHostOperationErrorV1, DockerHostCloseErrorV1)) as caught:
            operation()
        assert caught.value.code.value.endswith("UNAVAILABLE")
    ownership.commit_handoff()
    assert facade.start_run() == _workflow()
    with pytest.raises(DockerCapabilityAssemblyErrorV1) as caught:
        ownership.commit_handoff()
    assert caught.value.code is DockerCapabilityAssemblyCodeV1.BUILD_CLOSED


@pytest.mark.parametrize("operation", ("start", "reconcile", "binding"))
def test_runtime_wrong_result_or_exception_is_closed(mount_env, operation):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    if operation == "start":
        runtime.start_hook = lambda: object()
        call = facade.start_run
    elif operation == "reconcile":
        runtime.reconcile_hook = lambda: (_ for _ in ()).throw(
            RuntimeError("raw secret")
        )
        call = facade.reconcile_run
    else:
        runtime.binding_hook = lambda _kind: object()
        call = lambda: facade.effect_binding(EffectKind.SUBMIT)
    with pytest.raises(DockerHostOperationErrorV1) as caught:
        call()
    assert caught.value.code in {
        DockerHostOperationCodeV1.OPERATION_FAILED,
        DockerHostOperationCodeV1.RESULT_INVALID,
    }
    assert caught.value.__cause__ is None
    assert "raw secret" not in str(caught.value)


def test_mutated_exact_results_reject_under_lease(mount_env):
    workflow = _workflow()
    binding = mount_env["catalog"].value
    facade, runtime, _cell, _ownership_value = _facade(workflow, binding)
    object.__setattr__(workflow, "schema_version", "unsupported")
    with pytest.raises(DockerHostOperationErrorV1):
        facade.start_run()
    runtime.workflow = _workflow()
    object.__setattr__(binding, "tag", "bad")
    with pytest.raises(DockerHostOperationErrorV1):
        facade.effect_binding(EffectKind.SUBMIT)


def test_nested_open_operation_and_active_thread_close_defer(mount_env):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    observations = []

    def start():
        observations.append(facade.close())
        with pytest.raises(DockerHostOperationErrorV1):
            facade.reconcile_run()
        return runtime.workflow

    runtime.start_hook = start
    assert facade.start_run() == runtime.workflow
    assert observations[0].code is DockerHostFacadeCloseCodeV1.ACTIVE_OPERATION_CLOSE_DEFERRED
    assert observations[0].terminal is False
    assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSED


def test_final_outer_release_cleans_even_when_operation_raises(mount_env):
    calls = []

    def cleanup(_capability):
        calls.append("cleanup")

    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(cleanup),
    )

    def start():
        observation = facade.close()
        assert observation.code is DockerHostFacadeCloseCodeV1.ACTIVE_OPERATION_CLOSE_DEFERRED
        assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSING
        raise KeyboardInterrupt("raw operation failure")

    runtime.start_hook = start
    with pytest.raises(DockerHostOperationErrorV1):
        facade.start_run()
    assert calls == ["cleanup"]
    assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSED


def test_final_lease_removes_identity_before_cleanup_owner_reentry(mount_env):
    observations = []
    holder = {}

    def cleanup(_capability):
        observations.append(holder["facade"].close())

    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(cleanup),
    )
    holder["facade"] = facade

    def start():
        assert facade.close().code is DockerHostFacadeCloseCodeV1.ACTIVE_OPERATION_CLOSE_DEFERRED
        return runtime.workflow

    runtime.start_hook = start
    assert facade.start_run() == runtime.workflow
    assert observations[0].code is DockerHostFacadeCloseCodeV1.REENTRANT_CLOSE_IN_PROGRESS
    assert observations[0].terminal is False


def test_external_close_waits_active_and_rejects_new_nested_work(mount_env):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    entered = Event()
    release = Event()
    close_observations = []

    def start():
        entered.set()
        assert release.wait(2)
        close_observations.append(facade.close())
        with pytest.raises(DockerHostOperationErrorV1):
            facade.reconcile_run()
        return runtime.workflow

    runtime.start_hook = start
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(facade.start_run)
        assert entered.wait(2)
        closer = pool.submit(facade.close)
        for _ in range(1000):
            if facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSING:
                break
        assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSING
        release.set()
        assert active.result(timeout=2) == runtime.workflow
        result = closer.result(timeout=2)
    assert close_observations[0].code is DockerHostFacadeCloseCodeV1.ACTIVE_OPERATION_CLOSE_DEFERRED
    assert result.code is DockerHostFacadeCloseCodeV1.CLEANED


def test_concurrent_closers_converge_and_cleanup_once(mount_env):
    calls = 0
    lock = Lock()

    def cleanup(_capability):
        nonlocal calls
        with lock:
            calls += 1

    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(cleanup),
    )
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _index: facade.close(), range(32)))
    assert calls == 1
    assert all(value is results[0] for value in results)
    assert results[0].code is DockerHostFacadeCloseCodeV1.CLEANED
    assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSED


def test_close_owner_reentry_is_nonterminal_and_cleanup_runs_outside_lock(mount_env):
    observations = []
    holder = {}

    def cleanup(_capability):
        facade = holder["facade"]
        observations.append((facade.lifecycle_state, facade.close()))

    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(cleanup),
    )
    holder["facade"] = facade
    terminal = facade.close()
    state, reentrant = observations[0]
    assert state is DockerHostFacadeLifecycleStateV1.CLOSING
    assert reentrant.code is DockerHostFacadeCloseCodeV1.REENTRANT_CLOSE_IN_PROGRESS
    assert reentrant.terminal is False
    assert terminal.code is DockerHostFacadeCloseCodeV1.CLEANED


def test_cleanup_failure_and_indeterminate_are_terminal_and_never_retry(mount_env):
    calls = 0

    def fail(_capability):
        nonlocal calls
        calls += 1
        raise RuntimeError("raw cleanup secret")

    failed, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(fail),
    )
    first = failed.close()
    assert first.code is DockerHostFacadeCloseCodeV1.CLEANUP_FAILED
    assert failed.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSED_WITH_FAILURES
    assert failed.close() is first and calls == 1

    ownership = _ownership()
    ownership._controller_pin._ledger.abort = lambda: object()
    indeterminate, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value, ownership=ownership
    )
    result = indeterminate.close()
    assert result.code is DockerHostFacadeCloseCodeV1.CLEANUP_INDETERMINATE
    assert indeterminate.close() is result

    ownership = _ownership()
    ledger = ownership._controller_pin._ledger
    calls = []
    ledger.abort = lambda: (
        calls.append("abort"),
        (_ for _ in ()).throw(RuntimeError("raw ownership failure")),
    )[1]
    raised, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value, ownership=ownership
    )
    result = raised.close()
    assert result.code is DockerHostFacadeCloseCodeV1.CLEANUP_INDETERMINATE
    assert raised.close() is result and calls == ["abort"]


def test_facade_and_handoff_are_redacted_noncopyable_unpickleable(mount_env):
    facade, _runtime, handoff, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    assert repr(facade) == "DockerHostFacadeV1(<redacted>)"
    assert repr(handoff) == "DockerCapabilityOwnershipHandoffV1(<redacted>)"
    for operation in (copy, deepcopy, pickle.dumps):
        with pytest.raises(DockerHostOperationErrorV1):
            operation(facade)
    for operation in (copy, deepcopy, pickle.dumps):
        with pytest.raises(DockerCapabilityAssemblyErrorV1):
            operation(handoff)


def test_facade_rejects_subclasses_and_untyped_effect_kind(mount_env):
    with pytest.raises(TypeError):
        class Derived(DockerHostFacadeV1):
            pass
    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    with pytest.raises(DockerHostOperationErrorV1):
        facade.effect_binding("submit")
    with pytest.raises(DockerHostOperationErrorV1) as caught:
        facade.effect_binding(EffectKind.STAGE)
    assert caught.value.code is DockerHostOperationCodeV1.RESULT_INVALID


def test_prepared_handoff_blocks_facade_until_exact_single_commit(mount_env):
    runtime = Runtime(_workflow(), mount_env["catalog"].value)
    adapter = DockerPrivateFacadeRuntimeAdapterV1(
        start=runtime.start, reconcile=runtime.reconcile,
        binding=runtime.binding,
    )
    class Ledger:
        def complete(self): return None
        def abort(self):
            return DockerCapabilityCleanupResultV1.build(0, 0, 0, ())
    live = DockerLiveCapabilityBuildV1(object(), Ledger())
    handoff = live.prepare_handoff()
    facade = DockerHostFacadeV1(adapter, handoff)
    with pytest.raises(DockerHostOperationErrorV1):
        facade.start_run()

    def commit(_value):
        try:
            handoff.commit_handoff()
            return True
        except DockerCapabilityAssemblyErrorV1:
            return False

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(commit, range(32)))
    assert outcomes.count(True) == 1
    assert facade.start_run() == runtime.workflow


def test_closure_kernel_survives_module_rebinding_and_seals_methods(
    mount_env, monkeypatch,
):
    import synaptic_host.docker_v1.facade as facade_module

    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )

    def start():
        for name in (
            "DockerHostFacadeLifecycleStateV1", "DockerHostFacadeCloseCodeV1",
            "DockerHostFacadeCloseResultV1", "DockerHostOperationCodeV1",
            "DockerHostOperationErrorV1", "DockerHostCloseErrorV1",
            "DockerPrivateFacadeRuntimeAdapterV1",
            "DockerHostFacadeV1",
        ):
            monkeypatch.setattr(facade_module, name, object())
        with pytest.raises(TypeError):
            setattr(type(facade), "close", lambda _self: None)
        observation = facade.close()
        assert observation.code is DockerHostFacadeCloseCodeV1.ACTIVE_OPERATION_CLOSE_DEFERRED
        return runtime.workflow

    runtime.start_hook = start
    assert facade.start_run() == runtime.workflow
    assert facade.lifecycle_state is DockerHostFacadeLifecycleStateV1.CLOSED


def _facade_registries(facade):
    register = next(
        cell.cell_contents
        for cell in DockerHostFacadeV1.__init__.__closure__
        if callable(cell.cell_contents)
        and getattr(cell.cell_contents, "__name__", "") == "register_wrapper"
    )
    mappings = [
        cell.cell_contents for cell in register.__closure__
        if type(cell.cell_contents) is dict
    ]
    wrapper_id = id(facade)
    anchor_by_wrapper = next(
        value for value in mappings
        if wrapper_id in value and type(value[wrapper_id]) is tuple
    )
    state_id_by_wrapper = next(
        value for value in mappings
        if wrapper_id in value and type(value[wrapper_id]) is not tuple
    )
    state_id = state_id_by_wrapper[wrapper_id]
    state_by_id = next(
        value for value in mappings
        if state_id in value and hasattr(value[state_id], "state_id")
    )
    anchor_by_state = next(
        value for value in mappings
        if state_id in value and value is not state_by_id
    )
    return anchor_by_wrapper, state_id_by_wrapper, state_by_id, anchor_by_state


def test_weak_registry_collection_and_stale_token_callback_are_exact(mount_env):
    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    object_id = id(facade)
    anchors, wrapper_states, states, state_anchors = _facade_registries(facade)
    reference, anchor = anchors[object_id]
    state_id = wrapper_states[object_id]
    record = states[state_id]
    callback = reference.__callback__
    anchors[object_id] = (reference, object())
    callback(reference)
    assert object_id in anchors and state_id in states
    anchors[object_id] = (reference, anchor)
    facade_reference = weakref.ref(facade)
    del facade
    gc.collect()
    assert facade_reference() is None
    assert object_id not in anchors
    assert object_id not in wrapper_states
    assert state_id not in states
    assert state_id not in state_anchors


def test_closure_kernel_detects_raw_handoff_substitution_after_pin(mount_env):
    facade, _runtime, _handoff, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    assert facade.start_run() == _workflow()
    _anchors, wrapper_states, states, _state_anchors = _facade_registries(facade)
    record = states[wrapper_states[id(facade)]]
    object.__setattr__(record, "handoff", _ownership())
    with pytest.raises(DockerHostOperationErrorV1):
        facade.reconcile_run()


@pytest.mark.parametrize("verb", ("start", "reconcile", "binding"))
def test_each_operation_rematerializes_fresh_exact_error_without_secret_trace(
    mount_env, verb,
):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    injected = DockerHostOperationErrorV1(
        DockerHostOperationCodeV1.RESULT_INVALID
    )

    def fail(*_args):
        secret_local = "raw-secret-operation-trace"
        raise injected

    if verb == "start":
        runtime.start_hook = fail
        operation = facade.start_run
    elif verb == "reconcile":
        runtime.reconcile_hook = fail
        operation = facade.reconcile_run
    else:
        runtime.binding_hook = fail
        operation = lambda: facade.effect_binding(EffectKind.SUBMIT)
    with pytest.raises(DockerHostOperationErrorV1) as caught:
        operation()
    assert caught.value is not injected
    assert caught.value.code is DockerHostOperationCodeV1.RESULT_INVALID
    assert caught.value.args == ()
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    rendered = "".join(traceback.format_exception(caught.value))
    assert "raw-secret-operation-trace" not in rendered


def test_foreign_lookalike_and_malformed_error_are_generic(mount_env):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )

    class Lookalike(RuntimeError):
        @property
        def code(self):
            raise RuntimeError("raw-secret-code-property")

    runtime.start_hook = lambda: (_ for _ in ()).throw(Lookalike("secret"))
    with pytest.raises(DockerHostOperationErrorV1) as caught:
        facade.start_run()
    assert caught.value.code is DockerHostOperationCodeV1.OPERATION_FAILED
    assert caught.value.args == ()

    malformed = RuntimeError.__new__(DockerHostOperationErrorV1)
    RuntimeError.__init__(malformed)
    object.__setattr__(malformed, "code", object())
    runtime.start_hook = lambda: (_ for _ in ()).throw(malformed)
    with pytest.raises(DockerHostOperationErrorV1) as caught:
        facade.start_run()
    assert caught.value.code is DockerHostOperationCodeV1.OPERATION_FAILED

    with pytest.raises(TypeError):
        class Derived(DockerHostOperationErrorV1):
            pass
    with pytest.raises(TypeError):
        class DerivedClose(DockerHostCloseErrorV1):
            pass


@pytest.mark.parametrize(
    "attack", ("wrapper-anchor", "wrapper-state", "state-record", "state-anchor")
)
def test_each_missing_registry_mapping_fails_closed(mount_env, attack):
    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    anchors, wrapper_states, states, state_anchors = _facade_registries(facade)
    wrapper_id = id(facade)
    state_id = wrapper_states[wrapper_id]
    mapping, key = {
        "wrapper-anchor": (anchors, wrapper_id),
        "wrapper-state": (wrapper_states, wrapper_id),
        "state-record": (states, state_id),
        "state-anchor": (state_anchors, state_id),
    }[attack]
    retained = mapping.pop(key)
    try:
        with pytest.raises(DockerHostOperationErrorV1):
            facade.start_run()
        with pytest.raises(DockerHostCloseErrorV1) as caught:
            facade.close()
        assert caught.value.code is DockerHostCloseErrorCodeV1.UNAVAILABLE
        assert caught.value.args == ()
        with pytest.raises(DockerHostCloseErrorV1) as repeated:
            facade.close()
        with pytest.raises(DockerHostCloseErrorV1) as lifecycle:
            _state = facade.lifecycle_state
        assert repeated.value is not caught.value
        assert lifecycle.value is not repeated.value
        assert repeated.value.__cause__ is None
        assert repeated.value.__context__ is None
    finally:
        mapping[key] = retained


def test_record_transplant_and_wrapper_state_swap_fail_independently(mount_env):
    first, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    second, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    maps = _facade_registries(first)
    anchors, wrapper_states, states, state_anchors = maps
    first_id, second_id = id(first), id(second)
    first_state, second_state = wrapper_states[first_id], wrapper_states[second_id]
    first_record = states[first_state]
    states[first_state] = states[second_state]
    try:
        with pytest.raises(DockerHostOperationErrorV1):
            first.start_run()
    finally:
        states[first_state] = first_record
    wrapper_states[first_id] = second_state
    try:
        with pytest.raises(DockerHostOperationErrorV1):
            first.start_run()
    finally:
        wrapper_states[first_id] = first_state


def test_coordinated_facade_anchor_and_state_redirection_fails_origin_pin(
    mount_env,
):
    first, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    second, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    anchors, wrapper_states, _states, _state_anchors = _facade_registries(first)
    first_id, second_id = id(first), id(second)
    first_entry, first_state = anchors[first_id], wrapper_states[first_id]
    second_reference, second_anchor = anchors[second_id]
    anchors[first_id] = (first_entry[0], second_anchor)
    wrapper_states[first_id] = wrapper_states[second_id]
    try:
        with pytest.raises(DockerHostOperationErrorV1):
            first.start_run()
        with pytest.raises(DockerHostCloseErrorV1):
            first.close()
    finally:
        anchors[first_id] = first_entry
        wrapper_states[first_id] = first_state
    assert second_reference() is second


def test_coordinated_runtime_anchor_and_state_redirection_fails_origin_pin(
    mount_env,
):
    first_callbacks = Runtime(_workflow(), mount_env["catalog"].value)
    second_callbacks = Runtime(_workflow(), mount_env["catalog"].value)
    first_runtime = DockerPrivateFacadeRuntimeAdapterV1(
        start=first_callbacks.start, reconcile=first_callbacks.reconcile,
        binding=first_callbacks.binding,
    )
    second_runtime = DockerPrivateFacadeRuntimeAdapterV1(
        start=second_callbacks.start, reconcile=second_callbacks.reconcile,
        binding=second_callbacks.binding,
    )
    anchors, wrapper_states, _states, _state_anchors = _facade_registries(
        first_runtime
    )
    first_id, second_id = id(first_runtime), id(second_runtime)
    first_entry, first_state = anchors[first_id], wrapper_states[first_id]
    _second_reference, second_anchor = anchors[second_id]
    anchors[first_id] = (first_entry[0], second_anchor)
    wrapper_states[first_id] = wrapper_states[second_id]
    try:
        handoff = _ownership()
        with pytest.raises(DockerHostOperationErrorV1):
            DockerHostFacadeV1(first_runtime, handoff)
    finally:
        anchors[first_id] = first_entry
        wrapper_states[first_id] = first_state
    handoff = _ownership()
    facade = DockerHostFacadeV1(first_runtime, handoff)
    assert facade.start_run() == _workflow()


@pytest.mark.parametrize("field", ("original_wrapper_ref", "original_anchor"))
def test_record_origin_pin_mutation_and_equal_weakref_replacement_fail_closed(
    mount_env, field,
):
    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    _anchors, wrapper_states, states, _state_anchors = _facade_registries(facade)
    record = states[wrapper_states[id(facade)]]
    original = getattr(record, field)
    replacement = (
        weakref.ref(facade, lambda _reference: None)
        if field == "original_wrapper_ref" else object()
    )
    assert replacement is not original
    with pytest.raises(AttributeError):
        setattr(record, field, replacement)
    object.__setattr__(record, field, replacement)
    try:
        with pytest.raises(DockerHostOperationErrorV1):
            facade.start_run()
    finally:
        object.__setattr__(record, field, original)
    assert facade.start_run() == _workflow()


def test_registration_collision_rolls_back_nothing_and_never_double_cleans(mount_env):
    cleanup_calls = []
    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(lambda _capability: cleanup_calls.append("cleanup")),
    )
    anchors, wrapper_states, states, _state_anchors = _facade_registries(facade)
    state_id = wrapper_states[id(facade)]
    record = states[state_id]
    register = next(
        cell.cell_contents
        for cell in DockerHostFacadeV1.__init__.__closure__
        if callable(cell.cell_contents)
        and getattr(cell.cell_contents, "__name__", "") == "register_wrapper"
    )
    with pytest.raises(DockerHostOperationErrorV1):
        register(facade, lambda state_id, reference, anchor: type(record)(
            state_id, reference, anchor, record.runtime, record.handoff
        ))
    assert id(facade) in anchors and facade.start_run() == _workflow()
    assert facade.close().code is DockerHostFacadeCloseCodeV1.CLEANED
    assert cleanup_calls == ["cleanup"]


def test_nested_depths_and_repeated_final_release_external_close_races(mount_env):
    facade, runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value
    )
    runtime.reconcile_hook = lambda: (
        facade.effect_binding(EffectKind.SUBMIT), runtime.workflow
    )[1]
    runtime.start_hook = lambda: facade.reconcile_run()
    assert facade.start_run() == runtime.workflow
    assert facade.close().code is DockerHostFacadeCloseCodeV1.CLEANED

    for _iteration in range(20):
        calls = []
        entered, release = Event(), Event()
        raced, raced_runtime, _cell, _ownership_value = _facade(
            _workflow(), mount_env["catalog"].value,
            ownership=_ownership(
                lambda _capability: calls.append("cleanup")
            ),
        )

        def start():
            entered.set()
            assert release.wait(2)
            return raced_runtime.workflow

        raced_runtime.start_hook = start
        with ThreadPoolExecutor(max_workers=3) as pool:
            active = pool.submit(raced.start_run)
            assert entered.wait(2)
            closers = [pool.submit(raced.close) for _ in range(2)]
            release.set()
            assert active.result(timeout=2) == raced_runtime.workflow
            results = [value.result(timeout=2) for value in closers]
        assert calls == ["cleanup"]
        assert results[0] is results[1]


def test_orphan_wrapper_cleans_once_outside_registry_lock(mount_env):
    cleanup_calls = []
    created = []

    def cleanup(_capability):
        cleanup_calls.append("cleanup")
        nested, _runtime, _cell, _ownership_value = _facade(
            _workflow(), mount_env["catalog"].value
        )
        created.append(nested)

    facade, _runtime, _cell, _ownership_value = _facade(
        _workflow(), mount_env["catalog"].value,
        ownership=_ownership(cleanup),
    )
    reference = weakref.ref(facade)
    del facade
    gc.collect()
    assert reference() is None
    assert cleanup_calls == ["cleanup"]
    assert created[0].close().code is DockerHostFacadeCloseCodeV1.CLEANED
