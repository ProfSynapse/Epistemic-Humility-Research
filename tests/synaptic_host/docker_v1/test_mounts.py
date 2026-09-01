from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.foundation_v2.commands import build_submit_command
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCommandBindingV1,
    DockerEffectIdentityV1,
    DockerImageV1,
    DockerRuntimeV1,
    DockerWorkloadV1,
    labels_for,
)

from synaptic_host.bundle_io_v1.model import (
    BundleIOCodeV1,
    BundleIOErrorV1,
    digest_v1,
)
from synaptic_host.docker_v1.model import (
    DockerMountCodeV1,
    DockerMountErrorV1,
    DockerStageBundleBindingV1,
)
from synaptic_host.docker_v1.mounts import DockerSubmitMountResolverV1


def _resolver(env):
    return DockerSubmitMountResolverV1(
        command_catalog=env["catalog"],
        command_authority=env["command_authority"],
        stage_store=env["stage_store"],
        stage_record_authority=env["stage_authority"],
        declaration_authority=env["declaration_authority"],
        binding_authority=env["binding_authority"],
        source_seal_authority=env["seal_authority"],
        mapping_registry=env["mappings"],
        mapping_authority=env["mapping_authority"],
        bundle_verifier=env["verifier"],
    )


def _inputs(env):
    return {
        name: env[name]
        for name in (
            "labels", "image", "runtime", "workload",
            "source_ref", "artifact_ref",
        )
    }


def _install_relabeled_stage(env, *, effect_id=None, command_digest=None):
    record = env["stage_record"]
    identity = replace(
        record.effect_identity,
        effect_id=effect_id or record.effect_identity.effect_id,
        command_digest=command_digest or record.effect_identity.command_digest,
    )
    seal = env["seal_authority"].issue(replace(
        record.source_seal.content,
        effect_identity_digest=identity.digest,
    ))
    rebuilt = DockerStageBundleBindingV1.build(
        effect_identity=identity,
        source_seal_request_digest=record.source_seal_request_digest,
        source_ref=record.source_ref,
        source_digest=record.source_digest,
        authenticated_declaration=record.authenticated_declaration,
        bundle_command_digest=record.bundle_command_digest,
        authenticated_binding=record.authenticated_binding,
        source_seal=seal,
    )
    env["stage_store"].values[record.stage_effect_id] = (
        env["stage_authority"].issue(rebuilt)
    )


def test_exact_create_inputs_resolve_authenticated_logical_mounts(mount_env):
    resolved = _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert resolved.source_wsl_private_path.startswith(
        "/mnt/synaptic/source/.synaptic-bundle-"
    )
    assert resolved.artifact_wsl_root == "/mnt/synaptic/artifacts"
    assert resolved.source_read_only is True
    assert mount_env["catalog"].calls == [mount_env["labels"].command_digest]
    assert mount_env["mappings"].calls == [
        ("source", mount_env["source_ref"]),
        ("artifact", mount_env["artifact_ref"]),
    ]
    assert len(mount_env["verifier"].calls) == 1
    assert resolved.stage_record_digest == mount_env["stage_record"].record_digest


@pytest.mark.parametrize(
    "change",
    (
        {"source_ref": "other-source"},
        {"artifact_ref": "other-artifact"},
        {"image": DockerImageV1("other-image", "sha256:" + "a" * 64)},
        {"runtime": DockerRuntimeV1(
            3, 1_073_741_824, 3600,
            AcceleratorDeviceRequestV1("cpu", (), ()),
        )},
        {"workload": DockerWorkloadV1(("python", "other.py"), (), "1" * 64)},
        {"labels": "wrong-profile"},
    ),
)
def test_every_create_input_is_checked_before_stage_and_mapping_calls(
    mount_env, change
):
    values = _inputs(mount_env)
    if change.get("labels") == "wrong-profile":
        values["labels"] = replace(values["labels"], profile_ref="opaque/other")
    else:
        values.update(change)
    before_stage = mount_env["stage_store"].get_calls
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**values)
    assert caught.value.code is DockerMountCodeV1.COMMAND_INVALID
    assert mount_env["stage_store"].get_calls == before_stage
    assert mount_env["mappings"].calls == []
    assert mount_env["verifier"].calls == []


def test_catalog_lookup_is_keyed_only_by_labels_command_digest(mount_env):
    _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert mount_env["catalog"].calls == [mount_env["labels"].command_digest]


def test_command_binding_authentication_failure_is_zero_stage_call(mount_env):
    mount_env["catalog"].value = replace(
        mount_env["catalog"].value, tag="f" * 64
    )
    before_stage = mount_env["stage_store"].get_calls
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED
    assert mount_env["stage_store"].get_calls == before_stage
    assert mount_env["mappings"].calls == []


def test_authenticated_predecessor_scope_mismatch_is_zero_stage_store_call(
    mount_env
):
    command = mount_env["command"]
    predecessor = replace(command.stage_predecessor, namespace_ref="other-namespace")
    rebuilt_command = build_submit_command(
        command.preparation, "submit-effect", command.payload,
        command.executor, predecessor,
    )
    old_binding = mount_env["catalog"].value.content
    identity = DockerEffectIdentityV1(
        rebuilt_command.digest, rebuilt_command.operation.effect.effect_id,
        "submit", old_binding.plan,
    )
    binding = DockerCommandBindingV1(identity, rebuilt_command.canonical_bytes)
    mount_env["catalog"].value = mount_env["command_authority"].issue(binding)
    values = _inputs(mount_env)
    values["labels"] = labels_for(identity)
    before_stage = mount_env["stage_store"].get_calls
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**values)
    assert caught.value.code in {
        DockerMountCodeV1.AUTHENTICATION_FAILED,
        DockerMountCodeV1.STAGE_CONFLICT,
    }
    assert mount_env["stage_store"].get_calls == before_stage
    assert mount_env["mappings"].calls == []


def test_missing_or_throwing_stage_store_is_closed_before_mapping(mount_env):
    stage_store = mount_env["stage_store"]
    stage_store.values.clear()
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.STAGE_INDETERMINATE
    assert mount_env["mappings"].calls == []

    stage_store.fail_get = True
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.STAGE_INDETERMINATE
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("envelope", ("declaration", "binding", "seal"))
def test_stage_envelopes_are_reauthenticated_on_mount_resolution(
    mount_env, envelope
):
    record = mount_env["stage_record"]
    declaration = record.authenticated_declaration
    binding = record.authenticated_binding
    seal = record.source_seal
    if envelope == "declaration":
        declaration = replace(declaration, tag="f" * 64)
    elif envelope == "binding":
        binding = replace(binding, tag="f" * 64)
        seal = mount_env["seal_authority"].issue(replace(
            seal.content,
            stage_ref="bundle-" + binding.proof_digest,
            evidence_digest=binding.proof_digest,
        ))
    else:
        seal = replace(seal, tag="f" * 64)
    rebuilt = DockerStageBundleBindingV1.build(
        effect_identity=record.effect_identity,
        source_seal_request_digest=record.source_seal_request_digest,
        source_ref=record.source_ref,
        source_digest=record.source_digest,
        authenticated_declaration=declaration,
        bundle_command_digest=record.bundle_command_digest,
        authenticated_binding=binding,
        source_seal=seal,
    )
    mount_env["stage_store"].values[record.stage_effect_id] = (
        mount_env["stage_authority"].issue(rebuilt)
    )
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED
    assert mount_env["mappings"].calls == []
    assert mount_env["verifier"].calls == []


@pytest.mark.parametrize(
    "relabel",
    (
        {"effect_id": "relabeled-stage"},
        {"command_digest": "f" * 64},
    ),
)
def test_authenticated_outer_stage_identity_relabel_rejects_before_mapping(
    mount_env, relabel
):
    _install_relabeled_stage(mount_env, **relabel)
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.STAGE_CONFLICT
    assert mount_env["mappings"].calls == []
    assert mount_env["verifier"].calls == []


def test_source_and_artifact_mappings_are_independent_and_not_swappable(mount_env):
    mount_env["mappings"].source = mount_env["mappings"].artifact
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.MAPPING_CONFLICT
    assert mount_env["mappings"].calls == [
        ("source", mount_env["source_ref"])
    ]
    assert mount_env["verifier"].calls == []


def test_mapping_authentication_failure_is_zero_verification(mount_env):
    mapping = mount_env["mappings"].source
    mount_env["mappings"].source = replace(mapping, tag="f" * 64)
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED
    assert mount_env["verifier"].calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("destination_ref", "rebound-destination"),
        ("root_authority_digest", "f" * 64),
        ("access_digest", "e" * 64),
        ("verify_borrow", object()),
        ("verify_root", object()),
    ),
)
def test_mapping_access_mutation_during_authenticated_snapshot_fails_closed(
    mount_env, field, value
):
    authority = mount_env["mapping_authority"]
    original = authority.authenticate
    entered, resume = Event(), Event()
    captured = {}

    def blocked(presented):
        trusted = original(presented)
        if presented.content.purpose.value == "source_bundle":
            captured["trusted"] = trusted
            entered.set()
            assert resume.wait(2)
        return trusted

    authority.authenticate = blocked
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            _resolver(mount_env).resolve_create_mounts, **_inputs(mount_env)
        )
        assert entered.wait(2)
        access = captured["trusted"].content.verify_access
        object.__setattr__(access, field, value)
        resume.set()
        with pytest.raises(DockerMountErrorV1):
            future.result(timeout=3)
    assert mount_env["verifier"].calls == []


def _substitute_verification(value, field):
    substitutions = {
        "command_digest": "f" * 64,
        "destination_ref": "other-destination",
        "root_authority_digest": "e" * 64,
        "access_digest": "d" * 64,
        "binding_digest": "c" * 64,
        "private_name": value.private_name + "x",
        "manifest_digest": "b" * 64,
        "inventory_digest": "a" * 64,
        "logical_entries": (
            (
                "dataset/other.json", value.logical_entries[0][1],
                value.logical_entries[0][2], value.logical_entries[0][3],
            ),
        ),
        "read_only": False,
        "verification_digest": "9" * 64,
    }
    object.__setattr__(value, field, substitutions[field])
    if field != "verification_digest":
        object.__setattr__(
            value, "verification_digest",
            digest_v1(value.canonical_without_digest()),
        )
    return value


@pytest.mark.parametrize(
    "field",
    (
        "command_digest", "destination_ref", "root_authority_digest",
        "access_digest", "binding_digest", "private_name",
        "manifest_digest", "inventory_digest", "logical_entries",
        "read_only", "verification_digest",
    ),
)
def test_every_verification_field_substitution_is_rejected(mount_env, field):
    mount_env["verifier"].transform = (
        lambda value: _substitute_verification(value, field)
    )
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.VERIFICATION_CONFLICT


def test_verifier_conflict_and_uncertainty_are_closed(mount_env):
    mount_env["verifier"].raise_error = BundleIOErrorV1(BundleIOCodeV1.CONFLICT)
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.VERIFICATION_CONFLICT
    assert "secret" not in str(caught.value)

    mount_env["verifier"].raise_error = RuntimeError("secret verifier")
    with pytest.raises(DockerMountErrorV1) as caught:
        _resolver(mount_env).resolve_create_mounts(**_inputs(mount_env))
    assert caught.value.code is DockerMountCodeV1.VERIFICATION_INDETERMINATE
    assert "secret" not in str(caught.value)
