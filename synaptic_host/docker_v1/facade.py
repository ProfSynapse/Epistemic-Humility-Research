"""Closure-sealed leased Docker host product facade."""

from __future__ import annotations


def _install_facade():
    from dataclasses import dataclass
    from enum import Enum
    from threading import Condition, Lock, get_ident
    from weakref import ref as weak_ref

    from synaptic_host.bundle_io_v1.model import digest_v1
    from synaptic_host.docker_v1.capability_assembly import (
        DockerCapabilityCleanupFailureV1, DockerCapabilityCleanupResultV1,
        DockerCapabilityCleanupStatusV1,
        DockerCapabilityOwnershipHandoffV1,
    )
    from tuner.execution.coordinator_v1.model import WorkflowRecordV1
    from tuner.execution.foundation_v2.identities import EffectKind
    from tuner.execution.providers.docker_provider_v1.model import (
        AuthenticatedDockerCommandBindingV1, DockerCommandBindingV1,
        DockerEffectIdentityV1, PreparedDockerPlanV1,
        validated_profile_snapshot,
    )

    sealed_types = set()

    class _SealedType(type):
        def __setattr__(cls, name, value):
            if cls in sealed_types:
                raise TypeError("sealed Docker host type")
            type.__setattr__(cls, name, value)

        def __delattr__(cls, name):
            if cls in sealed_types:
                raise TypeError("sealed Docker host type")
            type.__delattr__(cls, name)

    class LifecycleState(str, Enum):
        OPEN = "OPEN"
        CLOSING = "CLOSING"
        CLOSED = "CLOSED"
        CLOSED_WITH_FAILURES = "CLOSED_WITH_FAILURES"

    class FacadeCloseCode(str, Enum):
        CLEANED = "CLEANED"
        CLEANUP_FAILED = "CLEANUP_FAILED"
        CLEANUP_INDETERMINATE = "CLEANUP_INDETERMINATE"
        ACTIVE_OPERATION_CLOSE_DEFERRED = "ACTIVE_OPERATION_CLOSE_DEFERRED"
        REENTRANT_CLOSE_IN_PROGRESS = "REENTRANT_CLOSE_IN_PROGRESS"

    @dataclass(frozen=True, slots=True)
    class FacadeCloseResult:
        code: FacadeCloseCode
        terminal: bool
        result_digest: str

        def __post_init__(self):
            terminal_codes = {FacadeCloseCode.CLEANED,
                              FacadeCloseCode.CLEANUP_FAILED,
                              FacadeCloseCode.CLEANUP_INDETERMINATE}
            body = {"code": self.code.value,
                    "schema": "synaptic-host-docker-facade-close-result/v1",
                    "terminal": self.terminal}
            if (type(self.code) is not FacadeCloseCode
                    or type(self.terminal) is not bool
                    or self.terminal != (self.code in terminal_codes)
                    or self.result_digest != digest_v1(body)):
                raise ValueError("invalid Docker host close result")

        def canonical_without_digest(self):
            return {"code": self.code.value,
                    "schema": "synaptic-host-docker-facade-close-result/v1",
                    "terminal": self.terminal}

    def make_close_result(code):
        terminal = code in {FacadeCloseCode.CLEANED,
                            FacadeCloseCode.CLEANUP_FAILED,
                            FacadeCloseCode.CLEANUP_INDETERMINATE}
        body = {"code": code.value,
                "schema": "synaptic-host-docker-facade-close-result/v1",
                "terminal": terminal}
        return FacadeCloseResult(code, terminal, digest_v1(body))

    cleaned_result = make_close_result(FacadeCloseCode.CLEANED)
    failed_result = make_close_result(FacadeCloseCode.CLEANUP_FAILED)
    indeterminate_result = make_close_result(
        FacadeCloseCode.CLEANUP_INDETERMINATE)
    deferred_result = make_close_result(
        FacadeCloseCode.ACTIVE_OPERATION_CLOSE_DEFERRED)
    reentrant_result = make_close_result(
        FacadeCloseCode.REENTRANT_CLOSE_IN_PROGRESS)

    class OperationCode(str, Enum):
        UNAVAILABLE = "DOCKER_HOST_OPERATION_UNAVAILABLE"
        OPERATION_FAILED = "DOCKER_HOST_OPERATION_FAILED"
        RESULT_INVALID = "DOCKER_HOST_OPERATION_RESULT_INVALID"

    class CloseErrorCode(str, Enum):
        UNAVAILABLE = "DOCKER_HOST_CLOSE_UNAVAILABLE"
        CLOSE_FAILED = "DOCKER_HOST_CLOSE_FAILED"

    class OperationError(RuntimeError, metaclass=_SealedType):
        __slots__ = ("code",)

        def __init__(self, code):
            RuntimeError.__init__(self)
            object.__setattr__(self, "code", code if type(code) is OperationCode
                               else OperationCode.OPERATION_FAILED)

        def __setattr__(self, _name, _value):
            raise AttributeError("immutable Docker host operation error")

        def __init_subclass__(cls, **_kwargs):
            raise TypeError("Docker host operation error is final")

    class CloseError(RuntimeError, metaclass=_SealedType):
        __slots__ = ("code",)

        def __init__(self, code):
            RuntimeError.__init__(self)
            object.__setattr__(self, "code", code if type(code) is CloseErrorCode
                               else CloseErrorCode.CLOSE_FAILED)

        def __setattr__(self, _name, _value):
            raise AttributeError("immutable Docker host close error")

        def __init_subclass__(cls, **_kwargs):
            raise TypeError("Docker host close error is final")

    def exact_error_code(error, error_type, code_type, fallback):
        if type(error) is not error_type:
            return fallback
        try:
            code = object.__getattribute__(error, "code")
        except BaseException:
            return fallback
        return code if type(code) is code_type else fallback

    def operation_failure(code):
        raise OperationError(code) from None

    def close_failure(code):
        raise CloseError(code) from None

    def total_operation(callback, fallback=OperationCode.OPERATION_FAILED):
        try:
            return True, callback()
        except BaseException as error:
            code = exact_error_code(error, OperationError, OperationCode,
                                    fallback)
        return False, code

    def total_close(callback, fallback=CloseErrorCode.CLOSE_FAILED):
        try:
            return True, callback()
        except BaseException as error:
            code = exact_error_code(error, CloseError, CloseErrorCode, fallback)
        return False, code

    def snapshot_workflow(value):
        try:
            if type(value) is not WorkflowRecordV1:
                raise ValueError
            rebuilt = WorkflowRecordV1(
                value.schema_version, value.run, value.plan_fingerprint,
                value.preflight_digest, value.provider,
                value.provider_context_digest, value.provider_descriptor_digest,
                value.phase, value.revision, value.preparation_digest,
                value.stage, value.submit, value.cancel,
                value.provider_stage_ref, value.provider_run_ref,
                value.bound_cancellation, value.pre_cancel_phase,
                tuple(list(value.run_observation_digests)),
                value.artifact_manifest, value.artifact_manifest_digest,
                tuple(list(value.verified_artifacts)),
                tuple(list(value.verification_receipts)),
                tuple(list(value.verification_receipt_digests)),
                tuple(list(value.diagnostic_codes)),
                tuple(list(value.provider_run_observations)))
            if rebuilt != value or rebuilt.record_digest != value.record_digest:
                raise ValueError
            return rebuilt
        except BaseException:
            operation_failure(OperationCode.RESULT_INVALID)

    def snapshot_binding(value, effect_value):
        try:
            if type(value) is not AuthenticatedDockerCommandBindingV1:
                raise ValueError
            content = value.content
            if type(content) is not DockerCommandBindingV1:
                raise ValueError
            profile = validated_profile_snapshot(content.plan.profile)
            plan = PreparedDockerPlanV1(
                profile, content.plan.project_ref, content.plan.run_id,
                content.plan.plan_fingerprint, content.plan.source_digest,
                content.plan.preparation_digest)
            identity = DockerEffectIdentityV1(
                content.identity.command_digest, content.identity.effect_id,
                content.identity.effect_kind, plan)
            rebuilt_content = DockerCommandBindingV1(
                identity, bytes(content.command_bytes),
                content.original_submit_command_bytes,
                content.cancel_container_ref, content.cancel_reason_digest,
                content.cancel_submit_labels, content.cancel_authorization_digest)
            rebuilt = AuthenticatedDockerCommandBindingV1(
                rebuilt_content, value.binding_digest, value.authority_ref,
                value.key_ref, value.tag)
            if (rebuilt != value
                    or rebuilt_content.binding_digest != value.binding_digest
                    or rebuilt_content.effect_kind != effect_value):
                raise ValueError
            return rebuilt
        except BaseException:
            operation_failure(OperationCode.RESULT_INVALID)

    def snapshot_cleanup(value):
        try:
            if type(value) is not DockerCapabilityCleanupResultV1:
                raise ValueError
            failures = tuple(DockerCapabilityCleanupFailureV1(
                item.slot, item.resource_kind, item.failure_class,
                item.local_io_code) for item in value.failures)
            rebuilt = DockerCapabilityCleanupResultV1(
                value.status, value.attempted_count, value.released_count,
                value.provisional_attempted_count, failures,
                value.result_digest)
            return rebuilt if rebuilt == value else None
        except BaseException:
            return None

    class _RuntimeState:
        __slots__ = ("state_id", "original_wrapper_ref", "original_anchor",
                     "start", "reconcile", "binding")

        def __init__(self, state_id, original_wrapper_ref, original_anchor,
                     start, reconcile, binding):
            self.state_id, self.start = state_id, start
            object.__setattr__(self, "original_wrapper_ref", original_wrapper_ref)
            object.__setattr__(self, "original_anchor", original_anchor)
            self.reconcile, self.binding = reconcile, binding

        def __setattr__(self, name, value):
            if name in {"original_wrapper_ref", "original_anchor"}:
                raise AttributeError
            object.__setattr__(self, name, value)

    class _LifecycleStateRecord:
        __slots__ = ("state_id", "original_wrapper_ref", "original_anchor",
                     "condition", "state", "active_total",
                     "active_by_thread", "close_owner", "terminal", "runtime",
                     "handoff", "handoff_pin")

        def __init__(self, state_id, original_wrapper_ref, original_anchor,
                     runtime, handoff):
            self.state_id, self.condition = state_id, Condition(Lock())
            object.__setattr__(self, "original_wrapper_ref", original_wrapper_ref)
            object.__setattr__(self, "original_anchor", original_anchor)
            self.state, self.active_total = LifecycleState.OPEN, 0
            self.active_by_thread, self.close_owner = {}, None
            self.terminal, self.runtime = None, runtime
            self.handoff = self.handoff_pin = handoff

        def __setattr__(self, name, value):
            if name in {"original_wrapper_ref", "original_anchor"}:
                raise AttributeError
            object.__setattr__(self, name, value)

    registry_lock = Lock()
    anchor_by_wrapper_id = {}
    state_id_by_wrapper_id = {}
    state_by_id = {}
    anchor_by_state_id = {}

    def exact_registry_match(wrapper, wrapper_id, reference, anchor,
                             state_id, record):
        wrapper_anchor = anchor_by_wrapper_id.get(wrapper_id)
        return (wrapper_anchor is not None
                and wrapper_anchor[0] is reference
                and wrapper_anchor[1] is anchor
                and state_id_by_wrapper_id.get(wrapper_id) is state_id
                and state_by_id.get(state_id) is record
                and record.state_id is state_id
                and record.original_wrapper_ref is reference
                and record.original_wrapper_ref() is wrapper
                and record.original_anchor is anchor
                and anchor_by_state_id.get(state_id) is anchor)

    def orphan_close(record):
        if type(record) is not _LifecycleStateRecord:
            return
        handoff = None
        try:
            with record.condition:
                if record.state in {LifecycleState.CLOSED,
                                    LifecycleState.CLOSED_WITH_FAILURES}:
                    return
                if record.active_total or record.close_owner is not None:
                    return
                if (type(record.handoff)
                        is not DockerCapabilityOwnershipHandoffV1
                        or record.handoff._is_handle_owning() is not True):
                    return
                record.state = LifecycleState.CLOSING
                record.close_owner = object()
                handoff = record.handoff
        except BaseException:
            return
        if handoff is not None:
            cleanup_claim(record, handoff)

    def register_wrapper(wrapper, record_builder):
        wrapper_id, state_id, anchor = id(wrapper), object(), object()
        reference_holder = []
        record = None

        def collected(reference):
            orphan = None
            with registry_lock:
                wrapper_anchor = anchor_by_wrapper_id.get(wrapper_id)
                if (wrapper_anchor is not None
                        and wrapper_anchor[0] is reference
                        and wrapper_anchor[1] is anchor
                        and state_id_by_wrapper_id.get(wrapper_id) is state_id
                        and state_by_id.get(state_id) is record
                        and record.state_id is state_id
                        and record.original_wrapper_ref is reference
                        and record.original_wrapper_ref() is None
                        and record.original_anchor is anchor
                        and anchor_by_state_id.get(state_id) is anchor):
                    anchor_by_wrapper_id.pop(wrapper_id, None)
                    state_id_by_wrapper_id.pop(wrapper_id, None)
                    state_by_id.pop(state_id, None)
                    anchor_by_state_id.pop(state_id, None)
                    orphan = record
            if orphan is not None:
                orphan_close(orphan)

        reference = weak_ref(wrapper, collected)
        reference_holder.append(reference)
        try:
            record = record_builder(state_id, reference, anchor)
            if (type(record) not in {_RuntimeState, _LifecycleStateRecord}
                    or record.state_id is not state_id
                    or record.original_wrapper_ref is not reference
                    or record.original_anchor is not anchor):
                raise ValueError
        except BaseException:
            operation_failure(OperationCode.UNAVAILABLE)
        installed_anchor = installed_wrapper_state = False
        installed_state = installed_state_anchor = False
        try:
            with registry_lock:
                if (wrapper_id in anchor_by_wrapper_id
                        or wrapper_id in state_id_by_wrapper_id
                        or state_id in state_by_id
                        or state_id in anchor_by_state_id):
                    raise ValueError
                anchor_by_wrapper_id[wrapper_id] = (reference, anchor)
                installed_anchor = True
                state_id_by_wrapper_id[wrapper_id] = state_id
                installed_wrapper_state = True
                state_by_id[state_id] = record
                installed_state = True
                anchor_by_state_id[state_id] = anchor
                installed_state_anchor = True
        except BaseException:
            installed_any = any((
                installed_anchor, installed_wrapper_state, installed_state,
                installed_state_anchor,
            ))
            with registry_lock:
                current_anchor = anchor_by_wrapper_id.get(wrapper_id)
                if (installed_anchor and current_anchor is not None
                        and current_anchor[0] is reference
                        and current_anchor[1] is anchor):
                    anchor_by_wrapper_id.pop(wrapper_id, None)
                if (installed_wrapper_state
                        and state_id_by_wrapper_id.get(wrapper_id) is state_id):
                    state_id_by_wrapper_id.pop(wrapper_id, None)
                if installed_state and state_by_id.get(state_id) is record:
                    state_by_id.pop(state_id, None)
                if (installed_state_anchor
                        and anchor_by_state_id.get(state_id) is anchor):
                    anchor_by_state_id.pop(state_id, None)
            if installed_any:
                orphan_close(record)
            operation_failure(OperationCode.UNAVAILABLE)

    def state_for(wrapper, expected_type, error_kind):
        wrapper_id = id(wrapper)
        with registry_lock:
            wrapper_anchor = anchor_by_wrapper_id.get(wrapper_id)
            state_id = state_id_by_wrapper_id.get(wrapper_id)
            record = state_by_id.get(state_id)
            if (wrapper_anchor is None or wrapper_anchor[0]() is not wrapper
                    or record is None or type(record) is not expected_type
                    or not exact_registry_match(
                        wrapper, wrapper_id, wrapper_anchor[0],
                        wrapper_anchor[1], state_id, record)):
                if error_kind == "close":
                    close_failure(CloseErrorCode.UNAVAILABLE)
                operation_failure(OperationCode.UNAVAILABLE)
            return record

    class PrivateRuntimeAdapter(metaclass=_SealedType):
        __slots__ = ("__weakref__",)

        def __init__(self, *, start, reconcile, binding):
            if not all(callable(value) for value in (start, reconcile, binding)):
                operation_failure(OperationCode.UNAVAILABLE)
            register_wrapper(self, lambda state_id, reference, anchor:
                _RuntimeState(state_id, reference, anchor,
                              start, reconcile, binding))

        def __init_subclass__(cls, **_kwargs):
            raise TypeError("Docker private runtime adapter is final")

    def attached(record, error_kind):
        try:
            handoff = record.handoff
            if (type(handoff) is not DockerCapabilityOwnershipHandoffV1
                    or handoff is not record.handoff_pin
                    or handoff._is_exact() is not True
                    or handoff._is_handle_owning() is not True):
                raise ValueError
            return handoff
        except BaseException:
            if error_kind == "close":
                close_failure(CloseErrorCode.UNAVAILABLE)
            operation_failure(OperationCode.UNAVAILABLE)

    def exact_handoff(record, error_kind):
        try:
            handoff = record.handoff
            if (type(handoff) is not DockerCapabilityOwnershipHandoffV1
                    or handoff is not record.handoff_pin
                    or handoff._is_exact() is not True):
                raise ValueError
            return handoff
        except BaseException:
            if error_kind == "close":
                close_failure(CloseErrorCode.UNAVAILABLE)
            operation_failure(OperationCode.UNAVAILABLE)

    def publish_terminal(record, result):
        terminal = result if type(result) is FacadeCloseResult else indeterminate_result
        with record.condition:
            record.terminal = terminal
            record.state = (LifecycleState.CLOSED
                            if terminal.code is FacadeCloseCode.CLEANED
                            else LifecycleState.CLOSED_WITH_FAILURES)
            record.close_owner = None
            record.condition.notify_all()

    def cleanup_claim(record, handoff):
        result = indeterminate_result
        try:
            cleanup = snapshot_cleanup(handoff.cleanup_owned())
            if cleanup is not None:
                if cleanup.status is DockerCapabilityCleanupStatusV1.CLEANED:
                    result = cleaned_result
                elif cleanup.status is DockerCapabilityCleanupStatusV1.CLEANUP_FAILED:
                    result = failed_result
        except BaseException:
            result = indeterminate_result
        finally:
            publish_terminal(record, result)

    def release_lease(record, thread_id):
        handoff = None
        with record.condition:
            depth = record.active_by_thread[thread_id] - 1
            record.active_total -= 1
            if depth:
                record.active_by_thread[thread_id] = depth
            else:
                del record.active_by_thread[thread_id]
            if (record.active_total == 0
                    and record.state is LifecycleState.CLOSING
                    and record.close_owner is None):
                record.close_owner = thread_id
                handoff = record.handoff
            elif record.active_total == 0:
                record.condition.notify_all()
        if handoff is not None:
            cleanup_claim(record, handoff)

    def invoke_runtime(runtime, verb, argument=None):
        callback = getattr(runtime, verb)
        return callback() if argument is None else callback(argument)

    def operation_impl(wrapper, verb, snapshot, argument=None):
        record = state_for(wrapper, _LifecycleStateRecord, "operation")
        attached(record, "operation")
        thread_id = get_ident()
        with record.condition:
            if record.state is not LifecycleState.OPEN:
                operation_failure(OperationCode.UNAVAILABLE)
            record.active_total += 1
            record.active_by_thread[thread_id] = (
                record.active_by_thread.get(thread_id, 0) + 1)
        release = release_lease
        try:
            ok, value = total_operation(
                lambda: invoke_runtime(record.runtime, verb, argument))
            if not ok:
                operation_failure(value)
            attached(record, "operation")
            ok, value = total_operation(lambda: snapshot(value))
            if not ok:
                operation_failure(value)
            return value
        finally:
            release(record, thread_id)

    def close_impl(wrapper):
        record = state_for(wrapper, _LifecycleStateRecord, "close")
        handoff = exact_handoff(record, "close")
        thread_id, claim = get_ident(), False
        with record.condition:
            if record.state in {LifecycleState.CLOSED,
                                LifecycleState.CLOSED_WITH_FAILURES}:
                return record.terminal
            if record.active_by_thread.get(thread_id, 0) > 0:
                if record.state is LifecycleState.OPEN:
                    record.state = LifecycleState.CLOSING
                return deferred_result
            if record.state is LifecycleState.OPEN:
                if handoff._is_handle_owning() is not True:
                    close_failure(CloseErrorCode.UNAVAILABLE)
                record.state = LifecycleState.CLOSING
            if record.close_owner == thread_id:
                return reentrant_result
            if record.active_total == 0 and record.close_owner is None:
                record.close_owner, claim = thread_id, True
            else:
                while record.state is LifecycleState.CLOSING:
                    record.condition.wait()
                return record.terminal
        if claim:
            cleanup_claim(record, handoff)
        with record.condition:
            return record.terminal

    def public_operation(callback):
        ok, value = total_operation(callback)
        if ok:
            return value
        operation_failure(value)

    def public_close(callback):
        ok, value = total_close(callback)
        if ok:
            return value
        close_failure(value)

    class HostFacade(metaclass=_SealedType):
        __slots__ = ("__weakref__",)

        def __init__(self, runtime, handoff):
            ok, runtime_state = total_operation(
                lambda: state_for(runtime, _RuntimeState, "operation"),
                OperationCode.UNAVAILABLE)
            if (not ok or type(handoff)
                    is not DockerCapabilityOwnershipHandoffV1):
                operation_failure(OperationCode.UNAVAILABLE)
            register_wrapper(self, lambda state_id, reference, anchor:
                _LifecycleStateRecord(state_id, reference, anchor,
                                      runtime_state, handoff))

        def start_run(self):
            return public_operation(
                lambda: operation_impl(self, "start", snapshot_workflow))

        def reconcile_run(self):
            return public_operation(
                lambda: operation_impl(self, "reconcile", snapshot_workflow))

        def effect_binding(self, effect_kind):
            if type(effect_kind) is not EffectKind:
                operation_failure(OperationCode.OPERATION_FAILED)
            effect_value = effect_kind.value
            return public_operation(lambda: operation_impl(
                self, "binding", lambda value: snapshot_binding(
                    value, effect_value), effect_value))

        @property
        def lifecycle_state(self):
            return public_close(lambda: self._lifecycle_state())

        def _lifecycle_state(self):
            record = state_for(self, _LifecycleStateRecord, "close")
            handoff = exact_handoff(record, "close")
            with record.condition:
                if (record.state is LifecycleState.OPEN
                        and handoff._is_handle_owning() is not True):
                    close_failure(CloseErrorCode.UNAVAILABLE)
                return record.state

        def close(self):
            return public_close(lambda: close_impl(self))

        def __repr__(self):
            return "DockerHostFacadeV1(<redacted>)"

        __str__ = __repr__

        def __reduce__(self):
            operation_failure(OperationCode.UNAVAILABLE)

        __copy__ = __reduce__

        def __deepcopy__(self, _memo):
            return self.__reduce__()

        def __init_subclass__(cls, **_kwargs):
            raise TypeError("Docker host facade is final")

    names = (
        (LifecycleState, "DockerHostFacadeLifecycleStateV1"),
        (FacadeCloseCode, "DockerHostFacadeCloseCodeV1"),
        (FacadeCloseResult, "DockerHostFacadeCloseResultV1"),
        (OperationCode, "DockerHostOperationCodeV1"),
        (CloseErrorCode, "DockerHostCloseErrorCodeV1"),
        (OperationError, "DockerHostOperationErrorV1"),
        (CloseError, "DockerHostCloseErrorV1"),
        (PrivateRuntimeAdapter, "DockerPrivateFacadeRuntimeAdapterV1"),
        (HostFacade, "DockerHostFacadeV1"),
    )
    for cls, name in names:
        cls.__name__, cls.__qualname__ = name, name
    sealed_types.update({OperationError, CloseError, PrivateRuntimeAdapter,
                         HostFacade})
    return tuple(cls for cls, _name in names)


(
    DockerHostFacadeLifecycleStateV1, DockerHostFacadeCloseCodeV1,
    DockerHostFacadeCloseResultV1, DockerHostOperationCodeV1,
    DockerHostCloseErrorCodeV1, DockerHostOperationErrorV1,
    DockerHostCloseErrorV1, DockerPrivateFacadeRuntimeAdapterV1,
    DockerHostFacadeV1,
) = _install_facade()
del _install_facade

__all__: tuple[str, ...] = ()
