"""Private host composition for one authenticated Modal training ingress."""

from __future__ import annotations

import hashlib
import importlib
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from synaptic_tuner.api.v1 import (
    CanonicalDocument,
    EffectState,
    EventCode,
    GitCliLocalSourceInspector,
    HostPorts,
    LifecyclePhase,
    LifecycleRecord,
    MessageCode,
    ProjectContext,
    SourceLock,
    VerificationStatus,
    validate_source_lock_provenance_v1,
)
from synaptic_tuner.api.v1.modal import (
    ModalDurablePreparationV1,
    ModalPreparedRunV1,
    ModalVerificationPolicyV1,
    compose_modal_source_finalizer,
    compose_modal_training_operations,
)
from tuner.project.manifest import load_project_manifest

from .cli import (
    TrainingRunCommandCodeV2,
    TrainingRunCommandResultV2,
    TrainingRunCommandStatusV2,
    TrainingRunIngressV1,
    _authenticate_training_run_ingress_v1,
)
from .modal_provider import (
    ExplicitModalHostSession,
    ModalProviderAuthorityV1,
    build_worker_authenticator,
)
from .modal_resolver import ModalTrainingIntentV1, ModalTrainingResolverV1
from .security import (
    BoundedGrantProvider,
    FileHmacAuthenticator,
    ScopedGitRemoteReader,
    utc_now,
)
from .sqlite_repository import SqliteTrainingRepository

_RESULT_SCHEMA = "synaptic-training-run-command-result/v2"


class _RejectingSecretProvider:
    __slots__ = ()

    def resolve(self, _reference: object) -> str:
        raise ValueError("runtime secret values are unavailable to host composition")


class _RejectingTrainingResolver:
    __slots__ = ()

    def resolve(self, *_args: object, **_kwargs: object) -> object:
        raise ValueError("seed training resolver is unavailable")


class EvidenceKeyRouterV1:
    """One long-lived object routing sign and verify to one of two keys by ref.

    Section 29.3 ruling (1), item 3.  `sign` and `verify` are real methods on
    this class, so each attribute access yields a bound method whose
    `(__self__, __func__)` pair is stable for the life of the instance.  The
    engine pins that pair at `providers/modal/training.py` and compares it with
    `is not` on every subsequent cut, so a `__getattr__` shim, a
    `functools.partial` rebuilt per access, or any per-call rebinding would fail
    the identity pin.  Do not convert these methods into either shape.

    Routing is exact-ref, never a prefix or a fallback: a ref that is neither
    the host ref nor the worker ref raises rather than defaulting to one of
    them, so a mis-declared ref can never be silently admitted under the wrong
    key.  The two-method shape satisfies the engine's `EvidenceAuthenticator`
    port, which is structural.

    The scheme is symmetric HMAC.  Holding a key to verify is holding a key to
    sign.  Separating the refs confines each channel to its own key; it does
    not make either channel's tags unforgeable by whoever holds that key.
    """

    __slots__ = ("_by_ref",)

    def __init__(
        self,
        *,
        host: FileHmacAuthenticator,
        worker: FileHmacAuthenticator,
    ) -> None:
        if type(host) is not FileHmacAuthenticator or type(worker) is not FileHmacAuthenticator:
            raise TypeError("both evidence authenticators must be exact FileHmacAuthenticator")
        if host.key_ref == worker.key_ref:
            raise ValueError("host and worker evidence key references must differ")
        if host.key_path == worker.key_path:
            raise ValueError("host and worker evidence keys must be distinct files")
        self._by_ref = {host.key_ref: host, worker.key_ref: worker}

    def _route(self, key_ref: str) -> FileHmacAuthenticator:
        if type(key_ref) is not str:
            raise TypeError("evidence key reference must be exact text")
        authenticator = self._by_ref.get(key_ref)
        if authenticator is None:
            raise ValueError("unroutable evidence key reference")
        return authenticator

    def sign(self, purpose: str, payload: bytes, key_ref: str) -> bytes:
        return self._route(key_ref).sign(purpose, payload, key_ref)

    def verify(self, purpose: str, payload: bytes, tag: bytes, key_ref: str) -> bool:
        return self._route(key_ref).verify(purpose, payload, tag, key_ref)


def _credential(value: object) -> str | None:
    if type(value) is not str:
        return None
    try:
        encoded = value.encode("utf-8")
        snapshot = encoded.decode("utf-8")
    except UnicodeError:
        return None
    if (
        not encoded
        or len(encoded) > 4096
        or any(unicodedata.category(character).startswith("C") for character in snapshot)
    ):
        return None
    return snapshot


def _identity(kind: str, project_ref: str, ingress_digest: str) -> str:
    digest = hashlib.sha256(
        f"synaptic-modal-{kind}/v2\0{project_ref}\0{ingress_digest}".encode("utf-8")
    ).hexdigest()[:32]
    return f"{kind}-{digest}"


def _fresh_capability(
    purpose: str, project_ref: str, run_id: str,
    factory: Callable[[int], bytes],
) -> str:
    raw = factory(32)
    if type(raw) is not bytes or len(raw) != 32:
        raise ValueError("capability source is unavailable")
    value = hashlib.sha256(
        b"synaptic-modal-training-capability/v1\0"
        + purpose.encode("ascii") + b"\0"
        + project_ref.encode("utf-8") + b"\0"
        + run_id.encode("utf-8") + b"\0" + raw
    ).hexdigest()
    return f"{purpose}-{value}"


def _timestamp(value: object) -> str:
    if type(value) is not str:
        raise ValueError("clock must return exact text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("clock must include a timezone")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _report_swallowed_cause(error: BaseException, code) -> None:
    """Name the cause of a failure this module answers with a result code.

    B-18 class, section 29.5(b).  Every `except BaseException` below used to
    leave the exception unbound, unchained and unlogged, so a run that cost
    money reached the operator as a bare diagnostic code that named nothing.
    The worst of them wraps roughly ninety lines of
    `execute_modal_training_run_v2` and answers all of it with one opaque
    `COMPOSITION_UNAVAILABLE`.

    Section 27.4's pattern re-raises with the original as `__cause__`.  That
    pattern cannot apply verbatim here: these handlers RETURN a
    `TrainingRunCommandResultV2` rather than raising, and a dataclass has no
    `__cause__`.  The operationally equivalent form on this lane is the
    already-shipped cause-line renderer, which is exactly what the fourth
    B-18 site does at `synaptic_host/__main__.py` in its `ensure_and_reexec`
    handler.  This is that same shape, named once and reused.

    The result contract does NOT widen.  The envelope the run driver parses
    is unchanged: same code, same status, same fields.  The cause goes to
    stderr on the mechanism 20.11 ruled and 24.4 already uses.

    The import is inside the function and the whole call is guarded, by that
    same convention: a diagnostic that can fail the path it diagnoses is
    worse than no diagnostic at all.  `report_cause_line_v1` renders only
    `code`, the exception's CLASS name and a frame; it never renders the
    exception's message, and a test pins that
    (`test_cause_line_carries_no_text_no_path_and_no_traceback`).  So this
    cannot leak a credential that reached an exception message.

    Scope, and the boundary is deliberate.  This is called from every
    `except BaseException` in this module whose arm reaches `_full_failure`
    or `_operation_result`, and from no others.  The two handlers that
    answer with a bare boolean -- `_ingress_is_current` and the source-lock
    currency check -- are excluded: neither stands between the operator and a
    first failure, and both are re-asked on a path that does report.  The
    thirteen remaining B-18-class sites outside this lane are follow-up
    #438, recorded rather than silently treated as done.
    """

    try:
        from .cause_line import report_cause_line_v1

        report_cause_line_v1(error, code)
    except BaseException:
        pass


def _full_failure(
    code: TrainingRunCommandCodeV2, baseline: tuple[object, ...],
) -> TrainingRunCommandResultV2:
    provider_ref, config_ref, destination_ref, input_digest, *_unused = baseline
    status = (
        TrainingRunCommandStatusV2.REJECTED
        if code is TrainingRunCommandCodeV2.PREFLIGHT_REJECTED
        else TrainingRunCommandStatusV2.UNAVAILABLE
    )
    return TrainingRunCommandResultV2(
        _RESULT_SCHEMA, status, code,
        provider_ref, config_ref, destination_ref, input_digest,
        None, None, None, None, None, None,
    )


def _internal_failure() -> TrainingRunCommandResultV2:
    return TrainingRunCommandResultV2(
        _RESULT_SCHEMA,
        TrainingRunCommandStatusV2.UNAVAILABLE,
        TrainingRunCommandCodeV2.INTERNAL_FAILURE,
        None, None, None, None, None, None, None, None, None, None,
    )


def _operation_result(
    code: TrainingRunCommandCodeV2,
    baseline: tuple[object, ...],
    *,
    project_ref: str,
    run_id: str,
    plan_fingerprint: str,
    effect_id: str,
    provider_job_ref: str | None = None,
    submitted_at: str | None = None,
) -> TrainingRunCommandResultV2:
    provider_ref, config_ref, destination_ref, input_digest, *_unused = baseline
    return TrainingRunCommandResultV2(
        _RESULT_SCHEMA,
        (
            TrainingRunCommandStatusV2.SUBMITTED
            if code is TrainingRunCommandCodeV2.SUBMITTED
            else TrainingRunCommandStatusV2.RECONCILE_REQUIRED
        ),
        code,
        provider_ref, config_ref, destination_ref, input_digest,
        project_ref, run_id, plan_fingerprint, effect_id,
        provider_job_ref, submitted_at,
    )


def _matching_effect(record: LifecycleRecord, effect_id: str):
    matches = tuple(
        effect for effect in record.effects
        if effect.identity.effect_id == effect_id
    )
    return matches[0] if len(matches) == 1 else None


def _found_at(record: LifecycleRecord, effect_id: str) -> str | None:
    matches = tuple(
        event.occurred_at for event in record.events
        if (
            event.code is EventCode.EFFECT_FOUND
            and event.effect is not None
            and event.effect.identity.effect_id == effect_id
        )
    )
    return matches[0] if len(matches) == 1 else None


def _prepared_prefix(record: LifecycleRecord) -> LifecycleRecord:
    events = tuple(record.events[:4])
    if len(events) != 4:
        raise ValueError("durable preparation is incomplete")
    return LifecycleRecord(
        record.run_id, record.project_ref, 4, LifecyclePhase.READY,
        VerificationStatus.NOT_READY, events[-1].occurred_at,
        MessageCode.READY, events, (), events[1].grant_binding,
    )


@dataclass(frozen=True, slots=True)
class _DurableFoundV1:
    project_ref: str
    run_id: str
    plan_fingerprint: str
    effect_id: str
    provider_job_ref: str
    submitted_at: str


def _provenance_projection(
    ingress: TrainingRunIngressV1,
    authority: ModalProviderAuthorityV1,
) -> dict[str, object]:
    return {
        "training_input_digest": ingress.input_digest,
        "training_contract_identity_digest": ingress.contract_identity_digest,
        "training_source_sha256": ingress.source_sha256,
        "training_ingress_digest": ingress.envelope_digest,
        "provider_policy_digest": authority.training.digest,
    }


def _durable_static_matches(
    preparation: ModalDurablePreparationV1,
    authority: ModalProviderAuthorityV1,
    ingress: TrainingRunIngressV1,
    project_context: ProjectContext,
) -> bool:
    try:
        if type(project_context) is not ProjectContext:
            return False
        state = authority.state
        policy = authority.training
        config = authority.config
        modal_context = preparation.context
        if (
            modal_context.profile != policy.profile_ref
            or modal_context.binding != state.binding
            or modal_context.deployment.selection != state.selection
            or modal_context.control_volume_id != state.control_volume_id
            or modal_context.artifact_volume_id != state.artifact_volume_id
            or modal_context.maximum_cost_minor_units
            != config.maximum_cost_minor_units
            or modal_context.currency != config.currency
        ):
            return False
        source = preparation.detached_execution_source()
        if source.run_id != preparation.operation.run_id:
            return False
        inspected = GitCliLocalSourceInspector().inspect(context=project_context)
        expected_lock = SourceLock(
            run_id=source.run_id,
            mode=inspected.mode,
            project_source=inspected.project_source,
            engine_source=inspected.engine_source,
            project={"id": preparation.operation.project_ref},
            configuration=_provenance_projection(ingress, authority),
            plugins=inspected.plugins,
            inputs=inspected.inputs,
            runtime=inspected.runtime,
            outputs=inspected.outputs,
            created_at=source.created_at,
        )
        validate_source_lock_provenance_v1(
            source, expected_lock, _provenance_projection(ingress, authority)
        )
        return True
    except BaseException:
        return False


def _classify_durable(
    *,
    repository: SqliteTrainingRepository,
    authority: ModalProviderAuthorityV1,
    ingress: TrainingRunIngressV1,
    context: object,
    baseline: tuple[object, ...],
    project_ref: str,
    run_id: str,
    effect_id: str,
) -> TrainingRunCommandResultV2 | _DurableFoundV1 | None:
    """Return None only when the durable run is exactly absent."""

    record = preparation = None
    try:
        record = repository.load(project_ref, run_id)
        preparation = repository.load_modal_preparation(project_ref, run_id)
    except BaseException as error:
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
        )
        return _full_failure(TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline)
    if record is None and preparation is None:
        return None
    if type(record) is not LifecycleRecord or type(preparation) is not ModalDurablePreparationV1:
        return _full_failure(TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline)
    try:
        record = LifecycleRecord.from_canonical_bytes(record.canonical_bytes)
        preparation = ModalDurablePreparationV1.from_canonical_bytes(
            preparation.canonical_bytes
        )
        ModalPreparedRunV1(_prepared_prefix(record), preparation)
        plan_fingerprint = preparation.public_plan_fingerprint
        if (
            record.project_ref != project_ref
            or record.run_id != run_id
            or preparation.operation.project_ref != project_ref
            or preparation.operation.run_id != run_id
            or preparation.operation.effect.effect_id != effect_id
        ):
            raise ValueError
        if preparation.public_plan_fingerprint != preparation.operation.plan_fingerprint:
            raise ValueError
        # Bundle/source structural failure is malformed durable state.  Static
        # policy/provenance drift is classified separately below.
        preparation.detached_execution_source()
        static_matches = _durable_static_matches(
            preparation, authority, ingress, context
        )
        effect = _matching_effect(record, effect_id)
        if not static_matches:
            provider_job_ref = (
                effect.provider_job_ref
                if effect is not None and effect.state is EffectState.FOUND
                else None
            )
            return _operation_result(
                TrainingRunCommandCodeV2.RECONCILE_REQUIRED, baseline,
                project_ref=project_ref, run_id=run_id,
                plan_fingerprint=plan_fingerprint, effect_id=effect_id,
                provider_job_ref=provider_job_ref,
            )
        if effect is None:
            return _operation_result(
                TrainingRunCommandCodeV2.RECONCILE_REQUIRED, baseline,
                project_ref=project_ref, run_id=run_id,
                plan_fingerprint=plan_fingerprint, effect_id=effect_id,
            )
        if preparation.operation.effect != effect.identity:
            raise ValueError
    except BaseException as error:
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
        )
        return _full_failure(
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline
        )
    if effect.state is EffectState.FOUND:
        provider_job_ref = effect.provider_job_ref
        submitted_at = _found_at(record, effect_id)
        if type(provider_job_ref) is not str or submitted_at is None:
            return _full_failure(
                TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline
            )
        return _DurableFoundV1(
            project_ref, run_id, plan_fingerprint, effect_id,
            provider_job_ref, submitted_at,
        )
    return _operation_result(
        TrainingRunCommandCodeV2.RECONCILE_REQUIRED, baseline,
        project_ref=project_ref, run_id=run_id,
        plan_fingerprint=plan_fingerprint, effect_id=effect_id,
    )


def _default_sdk_loader() -> object:
    return importlib.import_module("modal")


def _restore_durable_found(
    found: _DurableFoundV1,
    session: ExplicitModalHostSession,
    ingress: TrainingRunIngressV1,
    baseline: tuple[object, ...],
) -> TrainingRunCommandResultV2:
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    restore_failed = False
    restored_id = None
    try:
        restored = session.restore_function_call(found.provider_job_ref)
        restored_id = object.__getattribute__(restored, "object_id")
    except BaseException as error:
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.RECONCILE_REQUIRED
        )
        restore_failed = True
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    if restore_failed or restored_id != found.provider_job_ref:
        return _operation_result(
            TrainingRunCommandCodeV2.RECONCILE_REQUIRED, baseline,
            project_ref=found.project_ref, run_id=found.run_id,
            plan_fingerprint=found.plan_fingerprint, effect_id=found.effect_id,
            provider_job_ref=found.provider_job_ref,
        )
    return _operation_result(
        TrainingRunCommandCodeV2.SUBMITTED, baseline,
        project_ref=found.project_ref, run_id=found.run_id,
        plan_fingerprint=found.plan_fingerprint, effect_id=found.effect_id,
        provider_job_ref=found.provider_job_ref,
        submitted_at=found.submitted_at,
    )


def _classify_after_preflight_rejection(
    *,
    repository: SqliteTrainingRepository,
    session: ExplicitModalHostSession,
    authority: ModalProviderAuthorityV1,
    ingress: TrainingRunIngressV1,
    project_context: ProjectContext,
    baseline: tuple[object, ...],
    project_ref: str,
    run_id: str,
    effect_id: str,
) -> TrainingRunCommandResultV2:
    """Converge only to an already durable identical admission; never retry."""
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    durable = _classify_durable(
        repository=repository,
        authority=authority,
        ingress=ingress,
        context=project_context,
        baseline=baseline,
        project_ref=project_ref,
        run_id=run_id,
        effect_id=effect_id,
    )
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    if type(durable) is _DurableFoundV1:
        return _restore_durable_found(durable, session, ingress, baseline)
    if type(durable) is TrainingRunCommandResultV2:
        return durable
    return _full_failure(TrainingRunCommandCodeV2.PREFLIGHT_REJECTED, baseline)


def _ingress_is_current(
    ingress: TrainingRunIngressV1, baseline: tuple[object, ...]
) -> bool:
    try:
        return _authenticate_training_run_ingress_v1(ingress) == baseline
    except BaseException:
        return False


def execute_modal_training_run_v2(
    ingress: TrainingRunIngressV1,
    *,
    project_root: Path,
    engine_root: Path,
    token_id: str,
    token_secret: str,
    sdk_loader: Callable[[], object] = _default_sdk_loader,
    clock: Callable[[], str] = utc_now,
    capability_factory: Callable[[int], bytes] = secrets.token_bytes,
) -> TrainingRunCommandResultV2:
    """Compose and start one Modal run without exposing provider controls."""

    baseline = _authenticate_training_run_ingress_v1(ingress)
    if baseline is None:
        return _internal_failure()
    if baseline[0] != "modal":
        return _full_failure(TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE, baseline)
    exact_token_id = _credential(token_id)
    exact_token_secret = _credential(token_secret)
    if exact_token_id is None or exact_token_secret is None:
        return _full_failure(
            TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE, baseline
        )
    if not callable(sdk_loader) or not callable(clock) or not callable(capability_factory):
        return _full_failure(
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline
        )

    try:
        project = Path(project_root).resolve(strict=True)
        engine = Path(engine_root).resolve(strict=True)
        manifest = load_project_manifest(project / "synaptic.yaml")
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        if manifest.path.parent.resolve(strict=True) != project:
            raise ValueError
        context = manifest.create_context(engine_root=engine, invocation_cwd=project)
        authority = ModalProviderAuthorityV1.load(context)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        project_ref = manifest.project_id
        run_id = _identity("run", project_ref, ingress.envelope_digest)
        effect_id = _identity("effect", project_ref, ingress.envelope_digest)
        repository = SqliteTrainingRepository.from_context(context, clock=clock)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        durable = _classify_durable(
            repository=repository, authority=authority, ingress=ingress,
            context=context, baseline=baseline, project_ref=project_ref,
            run_id=run_id, effect_id=effect_id,
        )
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        if type(durable) is TrainingRunCommandResultV2:
            return durable

        # Exact absence and exact, statically validated FOUND are the only
        # durable states permitted to cross the provider-session boundary.
        sdk = sdk_loader()
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        session = ExplicitModalHostSession.from_credentials(
            sdk=sdk, config=authority.config,
            token_id=exact_token_id, token_secret=exact_token_secret,
        )
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        if type(durable) is _DurableFoundV1:
            return _restore_durable_found(durable, session, ingress, baseline)

        now = _timestamp(clock())
        now_value = datetime.fromisoformat(now.replace("Z", "+00:00"))
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        # R1 (section 29.3 ruling (1)).  Two keys, three refs, one facade.
        # `authenticator` is the HOST key: it signs and verifies the source and
        # deployment attestations and never leaves this machine.
        # `worker_authenticator` is the container-channel key: it is the only
        # key the provider puts in the runtime Secret and the only ref the
        # stage claim carries.  `key_router` is the single long-lived object
        # both are reached through; see EvidenceKeyRouterV1 for why it must
        # stay one object with real methods.
        authenticator = FileHmacAuthenticator.from_context(context)
        authenticator.initialize()
        worker_authenticator = build_worker_authenticator(context)
        worker_authenticator.initialize()
        key_router = EvidenceKeyRouterV1(
            host=authenticator, worker=worker_authenticator,
        )
        facade = session.facade(authority.state)
        grants = BoundedGrantProvider(
            maximum_cost_minor_units=authority.config.maximum_cost_minor_units,
            currency=authority.config.currency,
            clock=clock,
        )
        common = dict(
            lifecycle=repository,
            runs=repository,
            grants=grants,
            secrets=_RejectingSecretProvider(),
            evidence_replay=repository,
            # R1: the port receives the router, not either key directly, so
            # every engine sign and verify is dispatched by its explicit ref.
            authenticator=key_router,
            clock=clock,
            git_remote=ScopedGitRemoteReader(),
            modal_reads=facade,
        )
        seed_ports = HostPorts(
            **common, training_resolver=_RejectingTrainingResolver()
        )
        verification = ModalVerificationPolicyV1(
            audience_ref=f"{project_ref}/{run_id}",
            source_issuer_ref="host-git-verifier-v1",
            deployment_issuer_ref="host-modal-verifier-v1",
            # R1: the source and deployment attestations stay on the HOST key.
            # These two refs are what makes them unforgeable by the container.
            source_key_ref=authenticator.key_ref,
            deployment_key_ref=authenticator.key_ref,
            challenge_factory=lambda purpose: _fresh_capability(
                "challenge-" + purpose, project_ref, run_id, capability_factory
            ),
            evidence_ref_factory=lambda purpose: _fresh_capability(
                "evidence-" + purpose, project_ref, run_id, capability_factory
            ),
        )
        finalizer = compose_modal_source_finalizer(seed_ports, verification)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        # D3: constructed fully by keyword, zero positional arguments.  The
        # ref fields differ only by their names now, and this construction is
        # the one place the stage-claim ref is chosen, so a positional call
        # would let a ref move role without any diff naming the field.
        intent = ModalTrainingIntentV1(
            project_ref=project_ref,
            run_id=run_id,
            created_at=now,
            # R1: the stage claim rides the WORKER key.  This is the only ref
            # the container's channel carries, and it is not the ref the
            # source and deployment attestations above are verified under.
            key_ref=worker_authenticator.key_ref,
            quote_expires_at=(
                now_value + timedelta(minutes=5)
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            maximum_cost_minor_units=authority.config.maximum_cost_minor_units,
            currency=authority.config.currency,
            effect_id=effect_id,
            artifact_slot_ref=_identity("slot", project_ref, ingress.envelope_digest),
            invocation_nonce=_identity("nonce", project_ref, ingress.envelope_digest),
        )
        resolver = ModalTrainingResolverV1(
            training_input=ingress.training_input,
            input_type=type(ingress.training_input),
            input_digest=ingress.input_digest,
            contract_identity_digest=ingress.contract_identity_digest,
            ingress_digest=ingress.envelope_digest,
            source_sha256=ingress.source_sha256,
            provider_authority=authority,
            intent=intent,
            finalizer=finalizer,
        )
        ports = HostPorts(**common, training_resolver=resolver)
        operations = compose_modal_training_operations(
            context=context,
            host_ports=ports,
            provider_config=authority.state.profile,
        )
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
    except BaseException as error:
        # The ninety-line wrapper named in 29.5(b).  This is the handler that
        # turned an AttributeError inside the composition into a bare
        # COMPOSITION_UNAVAILABLE with no way to tell which of ninety lines
        # produced it.
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
        )
        return _full_failure(
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE, baseline
        )

    try:
        request = operations.load(
            CanonicalDocument.from_mapping(ingress.training_input.to_dict())
        )
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        resolved = operations.resolve(request)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        plan = operations.plan(resolved)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
        plan_fingerprint = plan.fingerprint
    except BaseException as error:
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE
        )
        return _full_failure(
            TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE, baseline
        )

    preflight_rejected = False
    try:
        preflight = operations.preflight(plan)
    except BaseException as error:
        # The code named here is this handler's own classification.  The arm
        # below may still converge to an already durable SUBMITTED, in which
        # case the cause line records what the preflight raised and the result
        # records what the run actually is.  Both are true.
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.PREFLIGHT_REJECTED
        )
        preflight_rejected = True
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    if not preflight_rejected and preflight.ready is not True:
        preflight_rejected = True
    if preflight_rejected:
        return _classify_after_preflight_rejection(
            repository=repository, session=session, authority=authority,
            ingress=ingress, project_context=context, baseline=baseline,
            project_ref=project_ref, run_id=run_id, effect_id=effect_id,
        )
    try:
        grant = grants.authorize(preflight.authorization)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
    except BaseException as error:
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE
        )
        return _full_failure(
            TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE, baseline
        )
    try:
        operations.start(plan, preflight, grant)
        if not _ingress_is_current(ingress, baseline):
            raise ValueError
    except BaseException as error:
        # As at the preflight handler: START_UNAVAILABLE is this handler's own
        # classification, and the durable classification below may still answer
        # with SUBMITTED or RECONCILE_REQUIRED.
        _report_swallowed_cause(
            error, TrainingRunCommandCodeV2.START_UNAVAILABLE
        )
        durable = _classify_durable(
            repository=repository, authority=authority, ingress=ingress,
            context=context, baseline=baseline, project_ref=project_ref,
            run_id=run_id, effect_id=effect_id,
        )
        if not _ingress_is_current(ingress, baseline):
            return _internal_failure()
        if type(durable) is _DurableFoundV1:
            return _restore_durable_found(durable, session, ingress, baseline)
        return durable or _full_failure(TrainingRunCommandCodeV2.START_UNAVAILABLE, baseline)
    durable = _classify_durable(
        repository=repository, authority=authority, ingress=ingress,
        context=context, baseline=baseline, project_ref=project_ref,
        run_id=run_id, effect_id=effect_id,
    )
    if not _ingress_is_current(ingress, baseline):
        return _internal_failure()
    if type(durable) is _DurableFoundV1:
        return _restore_durable_found(durable, session, ingress, baseline)
    return durable or _full_failure(TrainingRunCommandCodeV2.START_UNAVAILABLE, baseline)


__all__: list[str] = []
