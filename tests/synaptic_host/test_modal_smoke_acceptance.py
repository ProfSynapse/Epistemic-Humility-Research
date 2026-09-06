"""Acceptance predicate for the Modal smoke of the prepared path.

Scope and what a green here does NOT mean
=========================================
This module implements the RUN-ACCEPTANCE predicate of the Modal smoke
(`docs/plans/modal-smoke-prepared-path-plan.md`, "Test Phase") plus the
scenarios that are reachable without a live provider call.  Two label sets
collide in that plan and in section 29 of
`docs/architecture/prepared-path-alpine-diagnostic.md`, so every reference
here is qualified:

  RUN-ACCEPTANCE (this module)      G1 SEAM / G2 SUBMIT / G3 DURABLE /
                                    G4 OUTCOME, plus K5.
  PRE-SUBMIT (section 29.12)        a DIFFERENT G1-G6: fix shapes landed,
                                    submit container and PATH bound, B-19
                                    digest equality, R1 K1-K4, isolation
                                    triple, chained cause.  Those are
                                    devops-modal's gate scripts, not these
                                    tests.

`G2`, `G3` and `G4` cannot be observed without the one paid submit.  What is
implemented here for them is the PREDICATE FUNCTION the live run will be
judged by, exercised against recorded fixtures.  A green on those tests proves
the predicate is well-formed, total and correctly rejects the violating shape.
It does NOT mean the smoke passed, and it is not evidence about any real run.
Each such test says so in its own docstring.

Engine binding
==============
The worktree carries no pytest configuration, so pytest's rootdir resolves to
the PARENT repository, which also contains a `synaptic_tuner` package.  A run
that binds the parent's copy is silent: exit 0, a plausible count, the wrong
tree.  `test_bind1_*` verifies the binding in the two independent parts the
plan mandates -- CONTAINMENT via `find_spec` (which tree) and the GITLINK
(which commit) -- because neither implies the other.  The superseded naive
form, asserting `synaptic_tuner.__file__` starts with the engine root, fails
on exactly the case it exists to catch: a namespace package has
`__file__ is None`, so the read raises instead of reporting a wrong binding.

Ownership
=========
`tests/synaptic_host/test_modal_training.py` is another agent's file and is
not touched.  K5's two structural arms are already covered there by
`test_k5_router_satisfies_the_engine_port_and_the_identity_pin`; this module
deliberately does NOT duplicate them and covers instead the arm that test
cannot reach -- see `test_k5_composition_hands_one_long_lived_router`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from synaptic_host.cli import TrainingRunCommandCodeV2, TrainingRunIngressV1
import synaptic_host.cli as cli
import synaptic_host.modal_training as modal_training
from synaptic_tuner.api.v1.training_input_loader import (
    load_training_input_contract_v1,
)

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"
PINNED_ENGINE_GITLINK = "5db2809d0160b166a0d2b133b97368ddcfe426ce"

# Every code the composition entry point can refuse with.  A refusal is
# acceptable to G4 only if it NAMES one of these; an unnamed refusal is RED.
_NAMED_REFUSALS = frozenset(
    {
        "AUTHORIZATION_UNAVAILABLE",
        "BOOTSTRAP_UNAVAILABLE",
        "CAPABILITY_UNSUPPORTED",
        "COMMAND_INVALID",
        "COMPOSITION_UNAVAILABLE",
        "CONFIG_REF_INVALID",
        "CONFIG_UNAVAILABLE",
        "CREDENTIALS_UNAVAILABLE",
        "DESTINATION_INVALID",
        "INPUT_INVALID",
        "PREFLIGHT_REJECTED",
        "PROVIDER_INVALID",
        "PROVIDER_UNAVAILABLE",
        "RECONCILE_REQUIRED",
        "RESOLUTION_UNAVAILABLE",
    }
)

# G4 treats these two as RED when they arrive without a chained cause: they
# name the swallowing site rather than the defect (the B-18 shape).
_OPAQUE_REFUSALS = frozenset({"START_UNAVAILABLE", "INTERNAL_FAILURE"})


# --------------------------------------------------------------------------
# Fixture construction.  Patterned on the existing Modal suite; not copied.
# --------------------------------------------------------------------------


def _document() -> dict[str, object]:
    return {
        "schema_version": "synaptic-training-input/v1",
        "method": "sft",
        "model": {
            "ref": "unsloth/tiny-model",
            "revision": "main",
            "tokenizer_revision": "main",
        },
        "dataset": {"ref": "project://training/dataset.jsonl"},
        "hyperparameters": {
            "schema_version": "synaptic-sft-hyperparameters/v1",
            "batch_size": 1,
            "gradient_accumulation_steps": 1,
            "learning_rate": 0.0002,
            "duration": {"max_steps": 2, "num_epochs": None},
            "max_seq_length": 128,
            "seed": 7,
            "save_steps": 1,
            "save_total_limit": 1,
            "lora_rank": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.0,
            "lora_target_modules": ["q_proj", "v_proj"],
            "use_dora": False,
            "use_rslora": False,
            "init_lora_weights": True,
            "split_dataset": False,
        },
        "artifacts": {"required_kinds": ["final_model"], "retain_checkpoints": False},
    }


def _commit_project(project: Path) -> None:
    """Give the project a HEAD, because admission reads the COMMITTED blob."""

    identity = (
        "-c",
        "user.name=synaptic-test",
        "-c",
        "user.email=synaptic-test@example.invalid",
        "-c",
        "commit.gpgsign=false",
    )
    for arguments in (
        ("init", "--quiet", "--initial-branch", "main"),
        ("add", "--force", "--", "training"),
        (*identity, "commit", "--quiet", "-m", "committed training input"),
    ):
        subprocess.run(
            ("git", "-C", str(project), *arguments),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


# The ingress type makes provider and destination co-vary: cli.py refuses a
# modal ingress whose destination is not "provider-staging" AND refuses a
# docker ingress whose destination IS.  A helper that hard-codes one
# destination can therefore only ever mint one provider.
_DESTINATION_FOR = {"modal": "provider-staging", "docker": "local-default"}


def _issue(tmp_path: Path, provider: str = "modal"):
    """Mint one authenticated ingress for `provider`, plus its project root."""

    project = tmp_path / "project"
    training = project / "training"
    training.mkdir(parents=True)
    (training / "input.json").write_text(
        json.dumps(_document(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    (training / "dataset.jsonl").write_text("{}\n", encoding="utf-8")
    (project / "synaptic.yaml").write_text("schema_version: test\n", encoding="utf-8")
    _commit_project(project)

    source = (training / "input.json").read_bytes()
    bundle = load_training_input_contract_v1()
    training_input = bundle.parse_json(source.decode("utf-8"))
    input_digest = training_input.input_digest()
    source_sha256 = hashlib.sha256(source).hexdigest()
    contract_identity_digest = bundle.identity.identity_digest
    body = {
        "schema_version": "synaptic-training-run-ingress/v1",
        "provider_ref": provider,
        "config_ref": "project://training/input.json",
        "destination_ref": _DESTINATION_FOR[provider],
        "input_digest": input_digest,
        "source_sha256": source_sha256,
        "contract_identity_digest": contract_identity_digest,
    }
    canonical = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    envelope_digest = hashlib.sha256(
        b"synaptic-training-run-ingress/v1\0" + canonical
    ).hexdigest()
    cli._ENGINE_CONTRACT_CACHE = (ENGINE, None, {}, bundle)
    config_blob = cli._read_committed_git_blob_v1(
        project, "training/input.json", maximum_bytes=65536
    )
    ingress = cli._issue_training_run_ingress_v1(
        provider,
        "project://training/input.json",
        _DESTINATION_FOR[provider],
        training_input,
        input_digest,
        source_sha256,
        contract_identity_digest,
        envelope_digest,
        bundle,
        project_root=project.resolve(strict=True),
        engine_root=ENGINE,
        config_blob=config_blob,
    )
    return ingress, project


@pytest.fixture
def modal_ingress(tmp_path: Path):
    ingress, project = _issue(tmp_path, "modal")
    assert type(ingress) is TrainingRunIngressV1, (
        "fixture precondition: a modal ingress must authenticate; got "
        f"{getattr(ingress, 'code', ingress)!r}"
    )
    return ingress, project


class _RecordingLoader:
    """An SDK loader that records whether it was ever called.

    RF1's claim is not merely "it refuses" but "it refuses BEFORE any SDK
    load".  Only a loader that can report non-invocation can falsify that.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> object:
        self.calls += 1
        raise AssertionError("the SDK loader must not run on a refusing path")


def _compose(ingress, project: Path, **overrides):
    arguments = {
        "project_root": project,
        "engine_root": ENGINE,
        "token_id": "token-id-value",
        "token_secret": "token-secret-value",
    }
    arguments.update(overrides)
    return modal_training.execute_modal_training_run_v2(ingress, **arguments)


def _code_name(result) -> str | None:
    return getattr(getattr(result, "code", None), "name", None)


# --------------------------------------------------------------------------
# BIND1 -- the engine binding, in the two independent parts.
# --------------------------------------------------------------------------


def test_bind1_engine_binding_is_contained_and_pinned() -> None:
    """BIND1: containment proves WHICH TREE, the gitlink proves WHICH COMMIT.

    Falsifier: bind the parent repository's `synaptic_tuner` (which exists and
    imports cleanly) and containment fails while every test still collects; or
    move the submodule pin and the gitlink assertion fails while containment
    still holds.  Neither part implies the other, so both are asserted.
    """

    for name in ("synaptic_tuner", "synaptic_tuner.api.v1.publication"):
        spec = importlib.util.find_spec(name)
        assert spec is not None, f"{name} does not resolve at all"
        origin = spec.origin
        locations = list(spec.submodule_search_locations or [])
        if origin is not None and origin != "namespace":
            assert Path(origin).resolve().is_relative_to(ENGINE.resolve()), (
                f"{name} resolves to {origin}, outside the pinned engine"
            )
        else:
            # A namespace package has __file__ is None.  The naive
            # __file__.startswith check would RAISE here rather than report the
            # wrong binding, and an empty location list proves nothing at all.
            assert locations, f"{name} is a namespace package with no locations"
            for location in locations:
                assert Path(location).resolve().is_relative_to(ENGINE.resolve()), (
                    f"{name} searches {location}, outside the pinned engine"
                )

    listing = subprocess.run(
        ("git", "-C", str(ROOT), "ls-tree", "HEAD", "synaptic-tuner"),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert listing[0] == "160000", f"synaptic-tuner is not a gitlink: {listing!r}"
    assert listing[2] == PINNED_ENGINE_GITLINK, (
        f"engine gitlink {listing[2]} is not the pinned {PINNED_ENGINE_GITLINK}"
    )


# --------------------------------------------------------------------------
# G1 SEAM
# --------------------------------------------------------------------------


def test_g1_seam_sdk_absent_before_composition_and_present_after() -> None:
    """G1: both directions on `sys.modules`, in a CLEAN interpreter.

    Falsifier: a composition path that imports `modal` eagerly (at Host import
    time rather than through the injected loader) makes the BEFORE assertion
    fail; a loader that never reaches the real SDK makes the AFTER assertion
    fail.

    Why a subprocess.  `sys.modules` is process-global.  Measured: `modal` is
    absent at interpreter start and still absent after the whole Host package
    graph is imported, so the BEFORE half is satisfiable in isolation.  It is
    NOT guaranteed under the full suite, where any earlier test may have
    imported the SDK, and the tempting repair -- deleting the entry in a
    fixture -- would make this test assert its own fixture instead of the seam.
    A clean interpreter keeps the observation honest and independent of
    collection order.

    The two halves need different things from the lane.  BEFORE needs only the
    Host, so it is asserted on every lane and is the half that catches an eager
    import.  AFTER needs the SDK to be installed, and it is not on every lane
    (the Windows Host interpreter has no `modal`).  So AFTER is asserted only
    where the SDK is importable, and the test says so rather than skipping
    whole and reporting nothing.
    """

    program = textwrap.dedent(
        f"""
        import json, sys
        sys.path.insert(0, {str(ROOT)!r})
        sys.path.append({str(ENGINE)!r})
        report = {{"before_any_host_import": "modal" in sys.modules}}
        import synaptic_host.modal_training as modal_training
        report["before_loader"] = "modal" in sys.modules
        try:
            sdk = modal_training._default_sdk_loader()
        except ModuleNotFoundError:
            report["sdk_installed"] = False
        else:
            report["sdk_installed"] = True
            report["after_loader"] = "modal" in sys.modules
            report["loader_returned_the_module"] = sdk is sys.modules.get("modal")
        print(json.dumps(report))
        """
    )
    completed = subprocess.run(
        (sys.executable, "-c", program), capture_output=True, text=True
    )
    assert completed.returncode == 0, (
        f"clean-interpreter probe failed: {completed.stderr[-2000:]}"
    )
    report = json.loads(completed.stdout.strip().splitlines()[-1])

    # Asserted on every lane.
    assert report["before_any_host_import"] is False
    assert report["before_loader"] is False, (
        "the SDK was imported by the Host package graph, so the seam is not "
        "the only entry point"
    )

    if not report["sdk_installed"]:
        pytest.skip(
            "the AFTER direction is unmeasurable here: no `modal` is installed "
            "for this interpreter, so the loader cannot reach one.  The BEFORE "
            "direction above was asserted and passed."
        )
    assert report["after_loader"] is True, (
        "the default loader did not put `modal` in sys.modules"
    )
    assert report["loader_returned_the_module"] is True


def test_g1_seam_the_default_loader_is_the_single_sdk_entry_point() -> None:
    """G1 (companion): exactly one site in the Host imports the SDK.

    Falsifier: add a second `import modal` or `import_module("modal")` anywhere
    under `synaptic_host/` and this fails.  The both-direction observation
    above is only meaningful if the seam is the sole entry, and that is a
    property of the whole package, not of one call.
    """

    package = ROOT / "synaptic_host"
    entries: list[str] = []
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if 'import_module("modal")' in stripped or stripped in {
                "import modal",
                "import modal as modal",
            }:
                entries.append((path.relative_to(ROOT).parts, number, stripped))

    assert len(entries) == 1, f"expected exactly one SDK entry, found {entries}"
    # Compared as path PARTS, not as a string: a string prefix bakes in the
    # separator and fails on Windows for a reason that has nothing to do with
    # the seam.
    assert entries[0][0] == ("synaptic_host", "modal_training.py"), entries[0]


# --------------------------------------------------------------------------
# RF1-RF4 -- the refusal ladder.  These guards fire in SOURCE ORDER, so each
# test must reach the branch it names rather than trip an earlier one.
# --------------------------------------------------------------------------


def test_rf1_missing_credentials_refuses_before_any_sdk_load(modal_ingress) -> None:
    """RF1: CREDENTIALS_UNAVAILABLE, and the SDK loader never runs.

    Falsifier: move the credential guard below the `sdk_loader()` call and the
    recording loader raises, turning this red.  Asserting the code alone would
    NOT catch that reordering, which is why invocation is counted.
    """

    ingress, project = modal_ingress
    loader = _RecordingLoader()
    result = _compose(ingress, project, token_id="", sdk_loader=loader)

    assert _code_name(result) == "CREDENTIALS_UNAVAILABLE"
    assert loader.calls == 0, "the SDK was loaded on a credential-refusing path"


def test_rf2_a_non_modal_baseline_refuses_provider_unavailable(tmp_path: Path) -> None:
    """RF2: an authenticated NON-modal ingress refuses PROVIDER_UNAVAILABLE.

    Falsifier: drop the `baseline[0] != "modal"` guard and composition would
    proceed into Modal machinery on a docker ingress.  The ingress is issued
    for real rather than mutated, because mutating `provider_ref` after issue
    breaks authentication and would refuse INTERNAL_FAILURE from an EARLIER
    guard -- a green for the wrong reason.
    """

    ingress, project = _issue(tmp_path, "docker")
    if type(ingress) is not TrainingRunIngressV1:
        pytest.skip(
            "this lane cannot issue a docker ingress: "
            f"{getattr(ingress, 'code', ingress)!r}"
        )
    loader = _RecordingLoader()
    result = _compose(ingress, project, sdk_loader=loader)

    assert _code_name(result) == "PROVIDER_UNAVAILABLE"
    assert loader.calls == 0


@pytest.mark.parametrize("knob", ["sdk_loader", "clock", "capability_factory"])
def test_rf3_a_non_callable_collaborator_refuses_composition(
    modal_ingress, knob: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RF3: each of the three injected collaborators is checked BY THE GUARD.

    Two things are asserted, and the second is the one that carries the test.
    COMPOSITION_UNAVAILABLE is produced at four separate sites in this module:
    the explicit guard before the try, and three `except BaseException`
    handlers that swallow and report.  So the code alone cannot say WHICH site
    refused.  Measured: narrowing the guard to `sdk_loader` alone leaves the
    other two arms passing on the code assertion, because a non-callable clock
    then raises inside the try and the handler returns the same code.  That is
    a green for the wrong reason.

    The discriminator is `_report_swallowed_cause`, which every handler calls
    and the guard never does.  Falsifier: narrow the guard to any subset of
    the three and the excluded arms reach a handler, the reporter fires, and
    those arms go red.
    """

    ingress, project = modal_ingress
    swallowed: list[str] = []
    monkeypatch.setattr(
        modal_training,
        "_report_swallowed_cause",
        lambda error, code: swallowed.append(type(error).__name__),
    )

    result = _compose(ingress, project, **{knob: object()})

    assert _code_name(result) == "COMPOSITION_UNAVAILABLE"
    assert swallowed == [], (
        f"a non-callable {knob} reached a swallowing handler ({swallowed}), so "
        "the guard before the try did not cover it"
    )


def _binding(sdk_version: str):
    """One ModalClientBinding, built positionally as the engine declares it.

    The field order is (account_ref, workspace_ref, environment_ref,
    client_ref, sdk_version); only the last is varied here.
    """

    from synaptic_tuner.api.v1.modal import ModalClientBinding

    return ModalClientBinding("acct", "workspace", "main", "client", sdk_version)


def _facade_arguments(sdk: object) -> dict[str, object]:
    """Every collaborator the facade needs, all valid, so only the version varies."""

    return {
        "sdk": sdk,
        "client": object(),
        "scope_observer": lambda _client: ("acct", "workspace", "main", "client"),
        "deployment_observer": lambda **_kwargs: None,
        "volume_names": {"volume-a": "name-a"},
    }


def test_rf4_the_facade_refuses_a_binding_carrying_the_wrong_version() -> None:
    """RF4 arm one: the BINDING's recorded version is checked at construction.

    Falsifier: delete the `binding.sdk_version != EXACT_MODAL_SDK_VERSION`
    comparison and a binding minted against an older SDK would be accepted, so
    the mismatch would travel to a paid submit before being noticed.

    This arm needs no SDK at all, so it is the half that runs on every lane.
    """

    from tuner.execution.providers.modal.facade import (
        EXACT_MODAL_SDK_VERSION,
        ExplicitModal154ReadFacade,
        ModalFacadeError,
    )

    wrong = "1.5.1" if EXACT_MODAL_SDK_VERSION != "1.5.1" else "1.5.0"
    stub_sdk = type("StubSdk", (), {"__version__": EXACT_MODAL_SDK_VERSION})()

    with pytest.raises(ModalFacadeError) as caught:
        ExplicitModal154ReadFacade(_binding(wrong), **_facade_arguments(stub_sdk))
    assert "modal_sdk_version_mismatch" in str(caught.value)


def test_rf4_the_facade_refuses_the_installed_sdk_when_its_version_differs() -> None:
    """RF4 arm two: the SDK OBJECT's own version is checked separately.

    Arm one alone is the false negative this arm exists to prevent: a binding
    minted correctly can still be handed an SDK of a different version, and
    only the second comparison catches that.  Falsifier: delete the
    `getattr(sdk, "__version__", None)` comparison and this goes green with a
    binding that says 1.5.4 and an SDK that is not.

    This arm is driven by the REAL installed SDK, so the refusal comes from the
    genuine article rather than from a stub.  The accepting arm -- pinned SDK
    present, facade constructed -- needs the submit container and is NOT
    exercised here.
    """

    from tuner.execution.providers.modal.facade import (
        EXACT_MODAL_SDK_VERSION,
        ExplicitModal154ReadFacade,
        ModalFacadeError,
    )

    modal_sdk = pytest.importorskip("modal")
    installed = getattr(modal_sdk, "__version__", None)
    if installed == EXACT_MODAL_SDK_VERSION:
        pytest.skip(
            f"this lane has the pinned SDK {installed}, so the refusing arm is "
            "unreachable here; the accepting arm needs the submit container"
        )

    with pytest.raises(ModalFacadeError) as caught:
        ExplicitModal154ReadFacade(
            _binding(EXACT_MODAL_SDK_VERSION), **_facade_arguments(modal_sdk)
        )
    assert "modal_sdk_version_mismatch" in str(caught.value)


# --------------------------------------------------------------------------
# E4 / G4 OUTCOME -- every refusal names its code.
# --------------------------------------------------------------------------


def g4_outcome_is_decided(code_name: str | None, *, has_chained_cause: bool) -> bool:
    """G4 OUTCOME predicate.

    DECIDED when the outcome is SUBMITTED, or a refusal that NAMES its code.
    The two opaque codes are acceptable only when a chained cause accompanies
    them; unaccompanied they name the swallowing site rather than the defect,
    which is the B-18 shape this gate exists to refuse.

    NOT THE SMOKE: this is the function the live run will be judged by.
    """

    if code_name is None:
        return False
    if code_name == "SUBMITTED":
        return True
    if code_name in _NAMED_REFUSALS:
        return True
    if code_name in _OPAQUE_REFUSALS:
        return has_chained_cause
    return False


def test_g4_predicate_accepts_named_refusals_and_refuses_opaque_ones() -> None:
    """G4: the predicate's own truth table.

    NOT THE SMOKE -- this exercises the predicate against recorded shapes, and
    proves nothing about any real run.  Falsifier: let the predicate return
    True for an unaccompanied START_UNAVAILABLE and the third case reddens.
    """

    assert g4_outcome_is_decided("SUBMITTED", has_chained_cause=False) is True
    assert g4_outcome_is_decided("PROVIDER_UNAVAILABLE", has_chained_cause=False) is True
    assert g4_outcome_is_decided("START_UNAVAILABLE", has_chained_cause=False) is False
    assert g4_outcome_is_decided("START_UNAVAILABLE", has_chained_cause=True) is True
    assert g4_outcome_is_decided("INTERNAL_FAILURE", has_chained_cause=False) is False
    assert g4_outcome_is_decided(None, has_chained_cause=True) is False
    assert g4_outcome_is_decided("NOT_A_CODE", has_chained_cause=True) is False


def test_e4_every_reachable_refusal_on_this_path_names_its_code(
    modal_ingress, tmp_path: Path
) -> None:
    """E4: sweep the reachable refusals; each one names a code G4 accepts.

    Falsifier: a refusal arm that returns a result whose `code` is None, or an
    unaccompanied opaque code, fails here.  The sweep is over ARMS actually
    driven, not over the enum, so it cannot pass by listing names.
    """

    ingress, project = modal_ingress
    observed: dict[str, str | None] = {}

    observed["missing-credentials"] = _code_name(
        _compose(ingress, project, token_id="")
    )
    observed["non-callable-loader"] = _code_name(
        _compose(ingress, project, sdk_loader=object())
    )
    observed["non-callable-clock"] = _code_name(
        _compose(ingress, project, clock=object())
    )

    assert observed, "the sweep drove no refusal at all"
    members = {member.name for member in TrainingRunCommandCodeV2}
    for arm, code_name in observed.items():
        assert code_name is not None, f"{arm} refused without naming a code"
        assert code_name in members, (
            f"{arm} refused with {code_name}, which is not a declared code"
        )
        assert g4_outcome_is_decided(code_name, has_chained_cause=False), (
            f"{arm} refused with the opaque code {code_name}"
        )
    # The predicate's accepting set must be a subset of the real enum, or a
    # typo in _NAMED_REFUSALS would silently widen what G4 accepts.
    assert _NAMED_REFUSALS <= members, sorted(_NAMED_REFUSALS - members)
    assert _OPAQUE_REFUSALS <= members, sorted(_OPAQUE_REFUSALS - members)


# --------------------------------------------------------------------------
# X2 -- the fake-versus-real control, varying ONLY sdk_loader.
# --------------------------------------------------------------------------


def test_x2_the_seam_is_the_only_difference_between_the_two_arms(
    modal_ingress,
) -> None:
    """X2: identical inputs, one knob varied, and the divergence is the seam.

    A naive "both arms produce the same failing set" assertion would be wrong
    HERE and green for the wrong reason: on this lane the arms diverge BY
    CONSTRUCTION, because the real loader reaches an SDK whose version the
    facade refuses while the fake arm does not.  So the control asserts the
    stronger, checkable thing: both arms travel the same refusal ladder up to
    the seam, and the only observable difference is attributable to the loader.

    Falsifier: make the two arms differ on a guard BEFORE the seam -- for
    instance by having composition read the loader earlier -- and the shared
    prefix assertions fail.
    """

    ingress, project = modal_ingress

    def fake_loader() -> object:
        raise AssertionError("the fake loader must not be reached on these arms")

    real_loader = modal_training._default_sdk_loader

    # Every arm below refuses BEFORE the seam, so the loader identity must not
    # change the outcome.  That is the control: same code, same reason, both.
    for description, overrides in (
        ("missing-credentials", {"token_id": ""}),
        ("non-callable-clock", {"clock": object()}),
    ):
        fake_result = _code_name(_compose(ingress, project, sdk_loader=fake_loader, **overrides))
        real_result = _code_name(_compose(ingress, project, sdk_loader=real_loader, **overrides))
        assert fake_result == real_result, (
            f"{description}: the arms diverged before the seam "
            f"(fake={fake_result}, real={real_result})"
        )
        assert fake_result is not None


# --------------------------------------------------------------------------
# K5 -- the arm the existing structural test cannot reach.
# --------------------------------------------------------------------------


def test_k5_composition_hands_one_long_lived_router() -> None:
    """K5 (composition arm): the CODE CONDITION, not the structural gate.

    `test_modal_training.py::test_k5_router_satisfies_the_engine_port_and_the_
    identity_pin` already proves the router CLASS satisfies the runtime
    checkable port and pins `(__self__, __func__)` across two reads.  That is
    a property of an object built in a test.  It does not show that the
    production path hands the engine ONE long-lived object rather than
    rebuilding a router per consumer, which is the CODE CONDITION section 29
    derived when it corrected itself about the port.

    This test reads the composition source and asserts the router is
    constructed exactly once and then passed by name.  Falsifier: construct a
    second `EvidenceKeyRouterV1` anywhere in the entry point, or inline the
    construction into a consumer's argument list, and the count changes.
    """

    source = (ROOT / "synaptic_host" / "modal_training.py").read_text(
        encoding="utf-8"
    )
    start = source.index("def execute_modal_training_run_v2")
    body = source[start:]
    constructions = body.count("EvidenceKeyRouterV1(")

    assert constructions == 1, (
        "the composition entry point builds the evidence router "
        f"{constructions} times; the CODE CONDITION requires exactly one "
        "long-lived object"
    )
    assert "key_router = EvidenceKeyRouterV1(" in body, (
        "the router is not bound to a name, so it cannot be passed as one "
        "long-lived object"
    )


# --------------------------------------------------------------------------
# G3 DURABLE -- the predicate, against recorded rows.
# --------------------------------------------------------------------------


def g3_durable_rows_are_exact(
    *,
    lifecycle_rows: list[tuple[str, str]],
    preparation_rows: list[tuple[str, str]],
    effect_ids: list[str],
    replay_audiences: list[str],
    project_ref: str,
    run_id: str,
) -> bool:
    """G3 DURABLE predicate: exactly one row per (project_ref, run_id).

    NOT THE SMOKE: exercised against recorded fixtures only.
    """

    key = (project_ref, run_id)
    if lifecycle_rows.count(key) != 1 or len(lifecycle_rows) != 1:
        return False
    if preparation_rows.count(key) != 1 or len(preparation_rows) != 1:
        return False
    if len(effect_ids) != len(set(effect_ids)):
        return False
    expected = f"{project_ref}/{run_id}"
    return bool(replay_audiences) and all(a == expected for a in replay_audiences)


def test_g3_predicate_rejects_each_violation_it_exists_to_catch() -> None:
    """G3: one accepting shape and one rejecting shape per clause.

    NOT THE SMOKE.  Falsifier: drop any clause from the predicate and the
    matching rejection case turns green, which is what makes each clause
    load-bearing rather than decorative.
    """

    good = dict(
        lifecycle_rows=[("proj", "run")],
        preparation_rows=[("proj", "run")],
        effect_ids=["effect-a"],
        replay_audiences=["proj/run"],
        project_ref="proj",
        run_id="run",
    )
    assert g3_durable_rows_are_exact(**good) is True

    assert g3_durable_rows_are_exact(
        **{**good, "lifecycle_rows": [("proj", "run"), ("proj", "run")]}
    ) is False
    assert g3_durable_rows_are_exact(
        **{**good, "preparation_rows": []}
    ) is False
    assert g3_durable_rows_are_exact(
        **{**good, "effect_ids": ["effect-a", "effect-a"]}
    ) is False
    assert g3_durable_rows_are_exact(
        **{**good, "replay_audiences": ["proj/other"]}
    ) is False
    assert g3_durable_rows_are_exact(**{**good, "replay_audiences": []}) is False


# --------------------------------------------------------------------------
# G2 SUBMIT -- the predicate, against recorded calls.
# --------------------------------------------------------------------------


def g2_submit_is_exactly_one_call(
    *,
    started_calls: list[str],
    function_name: str,
    expected_function_name: str,
    capabilities: list[bytes],
) -> bool:
    """G2 SUBMIT predicate: one call, deployment-identity naming, fresh capability.

    NOT THE SMOKE: exercised against recorded fixtures only.
    """

    if len(started_calls) != 1:
        return False
    if function_name != expected_function_name:
        return False
    if len(capabilities) != len(set(capabilities)):
        return False
    return all(len(c) == 32 for c in capabilities)


def test_g2_predicate_rejects_each_violation_it_exists_to_catch() -> None:
    """G2: one accepting shape and one rejecting shape per clause.

    NOT THE SMOKE.  Falsifier: relax the single-call clause and the retry case
    turns green, which is the exact defect G2 exists to catch (a second paid
    submit).
    """

    good = dict(
        started_calls=["call-1"],
        function_name="synaptic-train",
        expected_function_name="synaptic-train",
        capabilities=[b"\x01" * 32],
    )
    assert g2_submit_is_exactly_one_call(**good) is True

    assert g2_submit_is_exactly_one_call(
        **{**good, "started_calls": ["call-1", "call-2"]}
    ) is False
    assert g2_submit_is_exactly_one_call(**{**good, "started_calls": []}) is False
    assert g2_submit_is_exactly_one_call(
        **{**good, "function_name": "something-else"}
    ) is False
    assert g2_submit_is_exactly_one_call(
        **{**good, "capabilities": [b"\x01" * 32, b"\x01" * 32]}
    ) is False
    assert g2_submit_is_exactly_one_call(
        **{**good, "capabilities": [b"\x01" * 8]}
    ) is False


# --------------------------------------------------------------------------
# X1 -- shape sweep.  Never a value.
# --------------------------------------------------------------------------


def x1_shape_of(value: object) -> object:
    """Reduce a recorded structure to its SHAPE: types and keys, never values."""

    if isinstance(value, dict):
        return {key: x1_shape_of(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [x1_shape_of(item) for item in value]
    return type(value).__name__


def test_x1_the_shape_sweep_carries_no_values() -> None:
    """X1: the sweep reports structure and never leaks a value.

    Falsifier: let `x1_shape_of` fall through to `repr(value)` for scalars and
    the secret below appears in the rendered shape, turning this red.  A sweep
    that reported values would be a leak, which is why the assertion is on
    ABSENCE of the value rather than on presence of the key.
    """

    secret = "s3cr3t-value-that-must-never-appear"
    recorded = {
        "prepared_command": ["python", "-m", "trainer", secret],
        "staged_source": {"commit": secret, "members": [{"path": secret, "size": 1}]},
        "logs": [secret],
        "model_inventory": {"entries": [{"name": secret, "bytes": 2}]},
    }

    shape = x1_shape_of(recorded)
    rendered = json.dumps(shape, sort_keys=True)

    assert secret not in rendered, "the shape sweep leaked a value"
    assert shape["logs"] == ["str"]
    assert shape["staged_source"]["members"] == [{"path": "str", "size": "int"}]
    assert shape["prepared_command"] == ["str", "str", "str", "str"]
    # A non-JSON scalar must reduce to its type name, not to its repr.
    assert x1_shape_of({"capability": b"\x01" * 32}) == {"capability": "bytes"}
