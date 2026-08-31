from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

import synaptic_host.artifact_destinations as destination_module
from synaptic_host.artifact_destinations import (
    ArtifactDestinationConfigV1,
    ArtifactDestinationDeclarationV1,
    ArtifactDestinationPolicyV1,
    DestinationAdapterInstallationV1,
    DestinationAdapterRegistrationV1,
    ImmutableArtifactDestinationRegistryV1,
    ResolvedDestinationAdapterV1,
    load_artifact_destination_config_v1,
)
from synaptic_host.publication_authority import create_publication_evidence_v1
from synaptic_tuner.api.v1 import ProjectContext


ROOT = Path(__file__).resolve().parents[2]


class LocalAdapter:
    def __init__(self, configuration: bytes) -> None:
        self.configuration = configuration

    def publish_once(self, command, source, ownership):
        raise NotImplementedError

    def lookup(self, command, permit):
        raise NotImplementedError

    def iter_bytes(self, command, artifact, maximum_bytes):
        return iter(())


class HFAdapter(LocalAdapter):
    pass


class FutureAdapter(LocalAdapter):
    pass


def test_generic_installation_requires_exact_registration_and_cleanup_function():
    registration = _registrations()[0]

    def cleaned():
        return True

    installation = DestinationAdapterInstallationV1(registration, cleaned)
    assert installation.registration is registration
    assert installation.cleanup_owned() is True

    def failed():
        return False

    assert DestinationAdapterInstallationV1(
        registration, failed
    ).cleanup_owned() is False

    with pytest.raises(TypeError, match="exact adapter registration"):
        DestinationAdapterInstallationV1(object(), cleaned)

    class Cleanup:
        def run(self):
            return True

    with pytest.raises(TypeError, match="exact adapter cleanup function"):
        DestinationAdapterInstallationV1(registration, Cleanup().run)


def test_generic_installation_rejects_non_boolean_cleanup_result():
    def invalid():
        return 1

    installation = DestinationAdapterInstallationV1(_registrations()[0], invalid)
    with pytest.raises(TypeError, match="exact boolean"):
        installation.cleanup_owned()


class AttributeBombAdapter(LocalAdapter):
    def __init__(self, configuration: bytes, *, armed: bool) -> None:
        super().__init__(configuration)
        self.armed = armed

    def __getattribute__(self, name: str):
        if name in {"publish_once", "lookup", "iter_bytes"} and object.__getattribute__(self, "armed"):
            raise RuntimeError("SECRET-CALLBACK-ATTRIBUTE")
        return object.__getattribute__(self, name)


class HostileBindingComparison:
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("SECRET-BINDING-COMPARE")

    def __ne__(self, other: object) -> bool:
        raise RuntimeError("SECRET-BINDING-COMPARE")


class BindingMutatingAdapter(LocalAdapter):
    def __init__(self, configuration: bytes) -> None:
        super().__init__(configuration)
        self.result = None
        self.mutated = False

    def __getattribute__(self, name: str):
        if name in {"publish_once", "lookup", "iter_bytes"}:
            mutated = object.__getattribute__(self, "mutated")
            result = object.__getattribute__(self, "result")
            if not mutated and result is not None:
                object.__setattr__(self, "mutated", True)
                object.__setattr__(
                    result, "authority_bindings", HostileBindingComparison()
                )
        return object.__getattribute__(self, name)


def _resolved(adapter: object, configuration: bytes) -> ResolvedDestinationAdapterV1:
    return ResolvedDestinationAdapterV1(
        adapter, ((
            "test-root",
            hashlib.sha256(b"resolved-authority\0" + configuration).hexdigest(),
        ),)
    )


def local_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
    return _resolved(LocalAdapter(configuration), configuration)


def hf_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
    return _resolved(HFAdapter(configuration), configuration)


def future_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
    return _resolved(FutureAdapter(configuration), configuration)


def wrong_factory(configuration: bytes) -> object:
    return object()


def _context(tmp_path: Path) -> ProjectContext:
    return ProjectContext.host(
        engine_root=tmp_path / "engine",
        project_root=tmp_path,
        state_root=tmp_path / ".synaptic/state",
    )


def _destination(ref: str, adapter: str, schema: str, **configuration) -> dict:
    return {
        "schema_version": "synaptic-host-artifact-destination/v1",
        "destination_ref": ref,
        "display_name": ref,
        "adapter_ref": adapter,
        "configuration": {"schema_version": schema, **configuration},
        "policy": {
            "maximum_artifact_bytes": 1024,
            "maximum_total_bytes": 4096,
        },
    }


def _write(tmp_path: Path, destinations: list[dict]) -> Path:
    path = tmp_path / "destinations.json"
    path.write_text(json.dumps({
        "schema_version": "synaptic-host-artifact-destinations/v1",
        "destinations": destinations,
    }), encoding="utf-8")
    return path.resolve()


def _registrations() -> tuple[DestinationAdapterRegistrationV1, ...]:
    return (
        DestinationAdapterRegistrationV1(
            "future/v1", "future-destination/v1", FutureAdapter, future_factory
        ),
        DestinationAdapterRegistrationV1(
            "hf/v1", "hf-destination/v1", HFAdapter, hf_factory
        ),
        DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, local_factory
        ),
    )


def test_checked_in_destination_config_uses_closed_host_contract() -> None:
    config = load_artifact_destination_config_v1((ROOT / "training/artifacts.json").resolve())
    assert tuple(item.destination_ref for item in config.destinations) == ("local-default",)
    declaration = config.destinations[0]
    assert declaration.adapter_ref == "host.local/v1"
    assert declaration.configuration_schema_version == "synaptic-local-artifact-destination/v1"
    assert json.loads(declaration.configuration_bytes) == {
        "schema_version": "synaptic-local-artifact-destination/v1",
        "control_root_ref": "artifact-publication-control",
        "data_root_ref": "artifact-local-default",
    }
    assert b"project://" not in declaration.configuration_bytes
    assert b'"root"' not in declaration.configuration_bytes


def test_same_registry_resolves_local_hf_and_future_adapters(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("future", "future/v1", "future-destination/v1", endpoint_ref="future://target"),
        _destination("hf", "hf/v1", "hf-destination/v1", repository_ref="hf://org/model"),
        _destination("local", "local/v1", "local-destination/v1", root="project://artifacts"),
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config, registrations=_registrations(), issuer=issuer, verifier=verifier
    )
    descriptors, complete = registry.list(101)
    assert complete is True
    assert tuple(item.destination_ref for item in descriptors) == ("future", "hf", "local")
    assert type(registry.resolve("future")[1]) is FutureAdapter
    assert type(registry.resolve("hf")[1]) is HFAdapter
    assert type(registry.resolve("local")[1]) is LocalAdapter
    assert all(verifier.verify(
        "publication-destination/v1", item.payload, item.tag, item.key_ref
    ) for item in descriptors)


@pytest.mark.parametrize("secret_key", ["token", "api_key", "apiKey", "password", "nested_secret"])
def test_config_rejects_recursive_credentials_and_secrets(
    tmp_path: Path, secret_key: str,
) -> None:
    value = _destination("local", "local/v1", "local-destination/v1")
    value["configuration"]["nested"] = {secret_key: "must-not-appear"}
    with pytest.raises(ValueError, match="credentials and secrets"):
        load_artifact_destination_config_v1(_write(tmp_path, [value]))


def test_config_allows_benign_key_references(tmp_path: Path) -> None:
    value = _destination(
        "local", "local/v1", "local-destination/v1",
        key_ref="host-key-reference", monkey_ref="benign",
    )
    loaded = load_artifact_destination_config_v1(_write(tmp_path, [value]))
    assert b"key_ref" in loaded.destinations[0].configuration_bytes


@pytest.mark.parametrize(
    "raw",
    [
        '{"schema_version":"synaptic-host-artifact-destinations/v1","schema_version":"x","destinations":[]}',
        '{"schema_version":"synaptic-host-artifact-destinations/v1","destinations":[],"unknown":1}',
        '{"schema_version":"wrong","destinations":[]}',
    ],
)
def test_config_rejects_duplicate_unknown_or_wrong_schema(tmp_path: Path, raw: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        load_artifact_destination_config_v1(path.resolve())


def test_config_rejects_noncanonical_destination_order_and_duplicates(tmp_path: Path) -> None:
    a = _destination("a", "local/v1", "local-destination/v1")
    b = _destination("b", "local/v1", "local-destination/v1")
    with pytest.raises(ValueError, match="ascending"):
        load_artifact_destination_config_v1(_write(tmp_path, [b, a]))
    with pytest.raises(ValueError, match="ascending"):
        load_artifact_destination_config_v1(_write(tmp_path, [a, a]))


def test_configuration_or_policy_change_changes_descriptor_identity(tmp_path: Path) -> None:
    first = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1", root="project://a")
    ])).destinations[0]
    second = ArtifactDestinationDeclarationV1(
        first.destination_ref, first.display_name, first.adapter_ref,
        first.configuration_schema_version,
        first.configuration_bytes.replace(b"project://a", b"project://b"),
        ArtifactDestinationPolicyV1(2048, 4096),
    )
    assert first.configuration_digest != second.configuration_digest
    assert first.policy.policy_digest != second.policy.policy_digest


def test_resolved_capability_identity_is_bound_into_destination_descriptor(
    tmp_path: Path,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination(
            "local", "local/v1", "local-destination/v1",
            data_root_ref="artifact-local-default",
            control_root_ref="artifact-publication-control",
        )
    ]))

    def factory_a(configuration: bytes) -> ResolvedDestinationAdapterV1:
        return ResolvedDestinationAdapterV1(
            LocalAdapter(configuration), (("data-root", "a" * 64),)
        )

    def factory_b(configuration: bytes) -> ResolvedDestinationAdapterV1:
        return ResolvedDestinationAdapterV1(
            LocalAdapter(configuration), (("data-root", "b" * 64),)
        )

    authority = create_publication_evidence_v1(_context(tmp_path))
    registration_a = (DestinationAdapterRegistrationV1(
        "local/v1", "local-destination/v1", LocalAdapter, factory_a
    ),)
    registration_b = (DestinationAdapterRegistrationV1(
        "local/v1", "local-destination/v1", LocalAdapter, factory_b
    ),)
    first = ImmutableArtifactDestinationRegistryV1(
        config=config, registrations=registration_a,
        issuer=authority.destinations, verifier=authority.verifier,
    ).resolve("local")[0]
    second = ImmutableArtifactDestinationRegistryV1(
        config=config, registrations=registration_b,
        issuer=authority.destinations, verifier=authority.verifier,
    ).resolve("local")[0]
    assert first.configuration_digest != second.configuration_digest
    assert first.configuration_digest not in {"a" * 64, config.destinations[0].configuration_digest}
    assert second.configuration_digest not in {"b" * 64, config.destinations[0].configuration_digest}
    assert first.identity_digest != second.identity_digest


@pytest.mark.parametrize(
    "result",
    [object(), ResolvedDestinationAdapterV1(object(), (("data-root", "a" * 64),))],
)
def test_registry_rejects_unsealed_or_wrong_resolved_factory_binding(
    tmp_path: Path, result: object,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))

    def factory(configuration: bytes) -> object:
        return result

    authority = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises((TypeError, ValueError), match="invalid binding|invalid type|callback access"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", LocalAdapter, factory
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )


@pytest.mark.parametrize(
    "mutated",
    [
        (),
        (("", "a" * 64),),
        ((" spaced ", "a" * 64),),
        (("control\nrole", "a" * 64),),
        ((("x" * 257), "a" * 64),),
        (("data", "A" * 64),),
        (("data", "a" * 64), ("data", "b" * 64)),
        (("z", "a" * 64), ("a", "b" * 64)),
        [("data", "a" * 64)],
    ],
)
def test_factory_result_is_fully_reconstructed_after_hostile_mutation(
    tmp_path: Path, mutated: object,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))

    def factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        result = ResolvedDestinationAdapterV1(
            LocalAdapter(configuration), (("data", "a" * 64),)
        )
        object.__setattr__(result, "authority_bindings", mutated)
        return result

    authority = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises(ValueError, match="resolved destination adapter binding is invalid"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", LocalAdapter, factory
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )


def test_callback_attribute_failure_is_closed_at_discovery_and_resolution(
    tmp_path: Path,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    created: list[AttributeBombAdapter] = []

    def factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        adapter = AttributeBombAdapter(configuration, armed=False)
        created.append(adapter)
        return ResolvedDestinationAdapterV1(adapter, (("data", "a" * 64),))

    authority = create_publication_evidence_v1(_context(tmp_path))
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", AttributeBombAdapter, factory
        ),),
        issuer=authority.destinations, verifier=authority.verifier,
    )
    created[0].armed = True
    with pytest.raises(ValueError, match="^destination adapter callback access failed$") as caught:
        registry.resolve("local")
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "SECRET" not in str(caught.value)

    def armed_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        return ResolvedDestinationAdapterV1(
            AttributeBombAdapter(configuration, armed=True), (("data", "a" * 64),)
        )

    with pytest.raises(ValueError, match="^destination adapter callback access failed$") as caught:
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", AttributeBombAdapter,
                armed_factory,
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "SECRET" not in str(caught.value)


def test_post_callback_binding_reread_never_invokes_hostile_equality(
    tmp_path: Path,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))

    def factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        adapter = BindingMutatingAdapter(configuration)
        result = ResolvedDestinationAdapterV1(
            adapter, (("data", "a" * 64),)
        )
        adapter.result = result
        return result

    authority = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises(ValueError, match="^resolved destination adapter binding changed$") as caught:
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", BindingMutatingAdapter,
                factory,
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "SECRET-BINDING-COMPARE" not in str(caught.value)

def test_registry_rejects_missing_schema_or_wrong_factory_type(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    with pytest.raises(ValueError, match="missing or incompatible"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "other/v1", LocalAdapter, local_factory
            ),),
            issuer=issuer, verifier=verifier,
        )
    with pytest.raises(TypeError, match="invalid binding"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", LocalAdapter, wrong_factory
            ),),
            issuer=issuer, verifier=verifier,
        )


def test_registry_detects_adapter_callback_substitution(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    adapter = registry.resolve("local")[1]
    adapter.lookup = lambda command, permit: None
    with pytest.raises(ValueError, match="binding changed"):
        registry.resolve("local")


def test_registry_rejects_factory_time_policy_mutation(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))

    def mutating_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        object.__setattr__(config.destinations[0].policy, "maximum_artifact_bytes", 2048)
        return _resolved(LocalAdapter(configuration), configuration)

    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    with pytest.raises(ValueError, match="changed during adapter construction"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", LocalAdapter, mutating_factory
            ),),
            issuer=issuer,
            verifier=verifier,
        )


def test_registry_rejects_whole_binding_tuple_substitution(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    original = registry._bindings[0]
    evil = LocalAdapter(b'{"schema_version":"local-destination/v1"}')
    replacement = destination_module._BoundDestinationV1(
        original.declaration,
        original.descriptor,
        evil,
        LocalAdapter,
        original.resolved_configuration_digest,
        evil.publish_once,
        evil.lookup,
        evil.iter_bytes,
    )
    registry._bindings = (replacement,)
    with pytest.raises(ValueError, match="binding changed"):
        registry.resolve("local")


def test_registry_anchor_is_not_redefined_by_module_global_replacement(
    tmp_path: Path, monkeypatch,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    monkeypatch.setattr(destination_module, "_get_registry_pin", lambda owner: None)
    monkeypatch.setattr(
        destination_module, "_discover_adapter_callbacks",
        lambda adapter: (_ for _ in ()).throw(RuntimeError("SECRET-REPLACEMENT")),
    )
    assert registry.resolve("local")[0].destination_ref == "local"


def test_factory_exception_is_closed_without_secret_or_context(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))

    def broken_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        raise RuntimeError("SECRET-FACTORY-PAYLOAD")

    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    with pytest.raises(ValueError, match="^destination adapter construction failed$") as error:
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "local-destination/v1", LocalAdapter, broken_factory
            ),),
            issuer=issuer,
            verifier=verifier,
        )
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_config_parsing_has_no_adapter_factory_effect(tmp_path: Path) -> None:
    calls = []

    def counted_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        calls.append(configuration)
        return _resolved(LocalAdapter(configuration), configuration)

    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    assert calls == []
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, counted_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    assert len(calls) == 1


def test_registry_rejects_unknown_destination_and_invalid_limit(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "local-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "local-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    with pytest.raises(KeyError):
        registry.resolve("missing")
    with pytest.raises(ValueError):
        registry.list(0)
    assert registry.list(1)[1] is True


def test_direct_config_objects_remain_exact_and_immutable() -> None:
    policy = ArtifactDestinationPolicyV1(1, 2)
    with pytest.raises(ValueError):
        ArtifactDestinationConfigV1(())
    with pytest.raises(TypeError):
        DestinationAdapterRegistrationV1("a", "b", LocalAdapter, LocalAdapter)
    assert policy.policy_digest == policy.policy_digest
