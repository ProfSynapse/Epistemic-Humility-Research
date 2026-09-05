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
    artifact_destination_declaration_digest_v1,
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


# Placeholder values, not real references: section 28 governs the key NAMES a
# configuration may carry and inspects no value, so what these say is
# immaterial.  They match what the checked-in document uses so a reader
# comparing a fixture to `training/artifacts.json` sees the same shape.
_CONFIGURATION_DEFAULTS = {
    "control_root_ref": "artifact-publication-control",
    "data_root_ref": "artifact-local-default",
}


def _destination(ref: str, adapter: str, schema: str, **configuration) -> dict:
    """Build a destination document that the section 28 parse gate accepts.

    The gate is the EXACT key set for the schema version (28.3), so a fixture
    naming only the keys its own assertion cares about would now be refused for
    a reason unrelated to the property it pins.  The helper therefore fills in
    the rest of the mapped set; an explicit keyword still wins, and a schema
    version the table does not map is left exactly as the caller wrote it so
    the unmapped-version tests still see what they built.
    """

    body = {"schema_version": schema, **configuration}
    for key in destination_module._ALLOWED_CONFIGURATION_KEYS.get(schema, ()):
        if key != "schema_version":
            body.setdefault(key, _CONFIGURATION_DEFAULTS.get(key, f"placeholder-{key}"))
    return {
        "schema_version": "synaptic-host-artifact-destination/v1",
        "destination_ref": ref,
        "display_name": ref,
        "adapter_ref": adapter,
        "configuration": body,
        "policy": {
            "maximum_artifact_bytes": 1024,
            "maximum_total_bytes": 4096,
        },
    }


def _declaration(ref: str, adapter: str, schema: str, **configuration):
    """Build a declaration WITHOUT going through the parser.

    Section 28's allowed-key table is enforced by
    load_artifact_destination_config_v1 at parse time only.
    ArtifactDestinationDeclarationV1.__post_init__ binds the configuration's own
    schema_version to the declaration field and never consults the table, so a
    destination whose schema version the table does not map can still be
    constructed here.  This is what preserves the multi-adapter registry pin
    below: that pin is about adapter binding, not configuration shape.
    """
    body = {"schema_version": schema, **configuration}
    return ArtifactDestinationDeclarationV1(
        ref, ref, adapter, schema,
        destination_module._canonical(body),
        ArtifactDestinationPolicyV1(1024, 4096),
    )


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
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, local_factory
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


def test_destination_declaration_digest_is_canonical_and_complete() -> None:
    declaration = load_artifact_destination_config_v1(
        (ROOT / "training/artifacts.json").resolve()
    ).destinations[0]
    digest = artifact_destination_declaration_digest_v1(declaration)
    assert len(digest) == 64
    changed = ArtifactDestinationDeclarationV1(
        declaration.destination_ref, declaration.display_name + " changed",
        declaration.adapter_ref, declaration.configuration_schema_version,
        declaration.configuration_bytes, declaration.policy,
    )
    assert artifact_destination_declaration_digest_v1(changed) != digest


def test_same_registry_resolves_local_hf_and_future_adapters(tmp_path: Path) -> None:
    # Section 28 maps one configuration schema version, so this document cannot
    # be PARSED any more.  The pin is that ONE registry resolves three different
    # adapters, which is unrelated to the parse-time key table, so the three
    # declarations are constructed directly and every assertion below stands as
    # authored.
    config = ArtifactDestinationConfigV1((
        _declaration("future", "future/v1", "future-destination/v1", endpoint_ref="future://target"),
        _declaration("hf", "hf/v1", "hf-destination/v1", repository_ref="hf://org/model"),
        _declaration("local", "local/v1", "synaptic-local-artifact-destination/v1", control_root_ref="project://artifacts"),
    ))
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
    value = _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    value["configuration"]["nested"] = {secret_key: "must-not-appear"}
    with pytest.raises(ValueError, match="credentials and secrets"):
        load_artifact_destination_config_v1(_write(tmp_path, [value]))


# Was test_config_allows_benign_key_references, which pinned that key_ref and
# monkey_ref PARSE because the denylist did not match them.  Section 28 refutes
# that premise: a benign name outside the allowed set is refused like any other,
# so the test is INVERTED rather than deleted and keeps the same fixture.
@pytest.mark.parametrize("benign_key", ["key_ref", "monkey_ref"])
def test_benign_key_reference_outside_the_allowed_set_is_refused(
    tmp_path: Path, benign_key: str,
) -> None:
    value = _destination(
        "local", "local/v1", "synaptic-local-artifact-destination/v1",
        **{benign_key: "host-key-reference"},
    )
    constructed: list[object] = []
    original = destination_module.ArtifactDestinationDeclarationV1

    class _Spy(original):  # type: ignore[misc, valid-type]
        def __post_init__(self) -> None:
            constructed.append(self)
            super().__post_init__()

    destination_module.ArtifactDestinationDeclarationV1 = _Spy
    try:
        with pytest.raises(ValueError) as caught:
            load_artifact_destination_config_v1(_write(tmp_path, [value]))
    finally:
        destination_module.ArtifactDestinationDeclarationV1 = original
    message = str(caught.value)
    assert benign_key in message
    assert "host-key-reference" not in message
    assert constructed == []


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
    a = _destination("a", "local/v1", "synaptic-local-artifact-destination/v1")
    b = _destination("b", "local/v1", "synaptic-local-artifact-destination/v1")
    with pytest.raises(ValueError, match="ascending"):
        load_artifact_destination_config_v1(_write(tmp_path, [b, a]))
    with pytest.raises(ValueError, match="ascending"):
        load_artifact_destination_config_v1(_write(tmp_path, [a, a]))


def test_configuration_or_policy_change_changes_descriptor_identity(tmp_path: Path) -> None:
    first = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1", control_root_ref="project://a")
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
            "local", "local/v1", "synaptic-local-artifact-destination/v1",
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
        "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, factory_a
    ),)
    registration_b = (DestinationAdapterRegistrationV1(
        "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, factory_b
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
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))

    def factory(configuration: bytes) -> object:
        return result

    authority = create_publication_evidence_v1(_context(tmp_path))
    with pytest.raises((TypeError, ValueError), match="invalid binding|invalid type|callback access"):
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, factory
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
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
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
                "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, factory
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )


def test_callback_attribute_failure_is_closed_in_its_message_at_both_sites(
    tmp_path: Path,
) -> None:
    """The message never quotes the adapter's payload; B-18 restores the chain.

    Before section 27.4 site 3 this also asserted `__cause__ is None`.  The
    guarantee it was really protecting is the message, and that is unchanged and
    still asserted below: "SECRET" never appears in what the caller reads.  The
    originating AttributeError now reaches `__cause__` so a failed publish names
    which attribute refused, which is the whole of B-18.
    """
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
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
            "local/v1", "synaptic-local-artifact-destination/v1", AttributeBombAdapter, factory
        ),),
        issuer=authority.destinations, verifier=authority.verifier,
    )
    created[0].armed = True
    with pytest.raises(ValueError, match="^destination adapter callback access failed$") as caught:
        registry.resolve("local")
    assert str(caught.value.__cause__) == "SECRET-CALLBACK-ATTRIBUTE"
    assert "SECRET" not in str(caught.value)

    def armed_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        return ResolvedDestinationAdapterV1(
            AttributeBombAdapter(configuration, armed=True), (("data", "a" * 64),)
        )

    with pytest.raises(ValueError, match="^destination adapter callback access failed$") as caught:
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "synaptic-local-artifact-destination/v1", AttributeBombAdapter,
                armed_factory,
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )
    assert str(caught.value.__cause__) == "SECRET-CALLBACK-ATTRIBUTE"
    assert "SECRET" not in str(caught.value)


def test_post_callback_binding_reread_never_invokes_hostile_equality(
    tmp_path: Path,
) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
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
                "local/v1", "synaptic-local-artifact-destination/v1", BindingMutatingAdapter,
                factory,
            ),),
            issuer=authority.destinations, verifier=authority.verifier,
        )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "SECRET-BINDING-COMPARE" not in str(caught.value)

def test_registry_rejects_missing_schema_or_wrong_factory_type(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
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
                "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, wrong_factory
            ),),
            issuer=issuer, verifier=verifier,
        )


def test_registry_detects_adapter_callback_substitution(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    adapter = registry.resolve("local")[1]
    adapter.lookup = lambda command, permit: None
    with pytest.raises(ValueError, match="binding changed"):
        registry.resolve("local")


def test_registry_rejects_factory_time_policy_mutation(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
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
                "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, mutating_factory
            ),),
            issuer=issuer,
            verifier=verifier,
        )


def test_registry_rejects_whole_binding_tuple_substitution(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    original = registry._bindings[0]
    evil = LocalAdapter(b'{"schema_version":"synaptic-local-artifact-destination/v1"}')
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
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, local_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    monkeypatch.setattr(destination_module, "_get_registry_pin", lambda owner: None)
    monkeypatch.setattr(
        destination_module, "_discover_adapter_callbacks",
        lambda adapter: (_ for _ in ()).throw(RuntimeError("SECRET-REPLACEMENT")),
    )
    assert registry.resolve("local")[0].destination_ref == "local"


def test_factory_exception_is_closed_in_its_message_but_chains_its_cause(
    tmp_path: Path,
) -> None:
    """Section 27.4 site 5, from the registry rather than the helper.

    The payload must not reach the message and does not.  It does now reach
    `__cause__`, deliberately: a destination adapter factory that refuses is the
    ordinary failure here, and before B-18 its reason was discarded outright.
    """
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))

    def broken_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        raise RuntimeError("SECRET-FACTORY-PAYLOAD")

    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    with pytest.raises(ValueError, match="^destination adapter construction failed$") as error:
        ImmutableArtifactDestinationRegistryV1(
            config=config,
            registrations=(DestinationAdapterRegistrationV1(
                "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, broken_factory
            ),),
            issuer=issuer,
            verifier=verifier,
        )
    assert type(error.value.__cause__) is RuntimeError
    assert str(error.value.__cause__) == "SECRET-FACTORY-PAYLOAD"
    assert "SECRET" not in str(error.value)


def test_config_parsing_has_no_adapter_factory_effect(tmp_path: Path) -> None:
    calls = []

    def counted_factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        calls.append(configuration)
        return _resolved(LocalAdapter(configuration), configuration)

    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))
    assert calls == []
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, counted_factory
        ),),
        issuer=issuer, verifier=verifier,
    )
    assert len(calls) == 1


def test_registry_rejects_unknown_destination_and_invalid_limit(tmp_path: Path) -> None:
    config = load_artifact_destination_config_v1(_write(tmp_path, [
        _destination("local", "local/v1", "synaptic-local-artifact-destination/v1")
    ]))
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.destinations
    registry = ImmutableArtifactDestinationRegistryV1(
        config=config,
        registrations=(DestinationAdapterRegistrationV1(
            "local/v1", "synaptic-local-artifact-destination/v1", LocalAdapter, local_factory
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


def test_c3_adapter_construction_failure_carries_the_factory_exception() -> None:
    """C3 of section 27.7 (site 5).

    `_construct_adapter` defers its translation until after the try statement,
    where the handler's `as` binding is already gone, so before B-18 the
    factory's exception was dropped entirely.  A factory raising is the ordinary
    way a destination adapter fails, and its message is the only thing that says
    why.
    """
    failure = ValueError("factory refused this configuration")

    def refusing_factory(configuration: bytes):
        raise failure

    with pytest.raises(ValueError) as raised:
        destination_module._construct_adapter(
            refusing_factory, b"{}", "0" * 64,
        )
    assert str(raised.value) == "destination adapter construction failed"
    assert raised.value.__cause__ is failure


def test_c4_callback_probe_failure_carries_the_attribute_error() -> None:
    """C4 of section 27.7, site 3.

    An adapter whose attribute access raises (rather than merely being absent)
    is the case the handler covers; the raise that reports it sits outside the
    handler, so the original needs carrying out explicitly.
    """
    failure = AttributeError("adapter attribute access refused")

    class RefusingAdapter:
        def __getattr__(self, name):
            raise failure

    with pytest.raises(ValueError) as raised:
        destination_module._discover_adapter_callbacks(RefusingAdapter())
    assert str(raised.value) == "destination adapter callback access failed"
    assert raised.value.__cause__ is failure


def test_c4_resolved_binding_failure_carries_the_original() -> None:
    """C4 of section 27.7, site 4.

    The binding reconstruction raises a bare `ValueError` from inside its own
    try block for each malformed field, then reports a single generic message
    after the handler.  Chaining keeps the inner raise's position in the
    traceback, which is what distinguishes a bad digest from a bad role.
    """
    binding = ResolvedDestinationAdapterV1(LocalAdapter(b"{}"), (("role", "0" * 64),))
    object.__setattr__(binding, "authority_bindings", ("not-a-pair",))
    with pytest.raises(ValueError) as raised:
        destination_module._reconstruct_resolved_binding(binding)
    assert str(raised.value) == "resolved destination adapter binding is invalid"
    assert raised.value.__cause__ is not None
    assert type(raised.value.__cause__) is ValueError
    assert raised.value.__cause__ is not raised.value


# ---------------------------------------------------------------------------
# Section 28 (SEC-M1): a version-keyed allowed key set, enforced at parse time.
#
# 28.3 rules the invariant first: destination configuration is a REFERENCE
# channel and must not be a credential channel.  The key set is the mechanism.
# The depth-wide banned-name scan is RETAINED beside it, because a key set
# governs one level while that scan governs the whole tree to _MAX_DEPTH; S5
# is what proves retention rather than replacement.
# ---------------------------------------------------------------------------

# Security-review's positive control (#365, restated in 28.7 item 1).  Every
# one of these passes the shipped denylist and every one is outside the allowed
# set, which is what makes S1 red on the shipped tree without any mutation.
# Placeholder values only: no example here may carry a realistic-looking secret.
_CONTROL_CREDENTIAL_KEYS = (
    "authorization", "bearer", "passphrase", "pat", "signature", "session_key",
    "key", "auth", "sas", "connection_string", "private_pem", "hmac", "salt",
    "cookie",
)

# Deliberately NOT a key of the literal table.  S6 quantifies over the table by
# asserting a version outside it; a suite that only iterates the table's keys
# cannot distinguish a fail-closed parser from the permissive lookup 28.4 names
# as non-conforming.
_UNMAPPED_CONFIG_SCHEMA = "synaptic-cloud-artifact-destination/v99"

_CHECKED_IN_CONFIGURATION_DIGEST = (
    "09fc6bb3c3781db28939c19c257c174754e53405edad931da5f4f06c7702ae26"
)


def _mapped_configurations() -> dict[str, frozenset[str]]:
    return dict(destination_module._ALLOWED_CONFIGURATION_KEYS)


def _mapped_destination(schema: str, allowed: frozenset[str], **override) -> dict:
    """A declaration that carries exactly the allowed keys, plus any override."""

    configuration = {
        key: f"placeholder-{key.replace('_', '-')}"
        for key in sorted(allowed) if key != "schema_version"
    }
    configuration.update(override)
    return _destination("local", "host.local/v1", schema, **configuration)


@pytest.mark.parametrize("credential_key", _CONTROL_CREDENTIAL_KEYS)
def test_s1_configuration_key_outside_the_allowed_set_is_refused(
    tmp_path: Path, credential_key: str,
) -> None:
    """28.7 item 1, the positive control, quantified over the literal table.

    The loop is over the table rather than over one hardcoded version, so a
    second schema version added later is covered the day its entry lands.
    """

    mapped = _mapped_configurations()
    assert mapped, "the literal table must not be empty"
    for schema, allowed in mapped.items():
        assert credential_key not in allowed
        value = _mapped_destination(schema, allowed, **{credential_key: "placeholder"})
        with pytest.raises(ValueError) as raised:
            load_artifact_destination_config_v1(_write(tmp_path, [value]))
        message = str(raised.value)
        assert credential_key in message, (schema, message)
        assert "placeholder" not in message, message


def test_s2_allowed_key_set_is_one_source_shared_with_the_adapter() -> None:
    """28.4: the adapter imports the constant, so the two can never drift.

    Identity, not equality: two equal literals in two modules is the duplication
    the ruling forbids, and only `is` refuses it.  The direction is forced --
    local_artifact_destination imports from artifact_destinations, so the
    reverse would cycle.
    """

    from synaptic_host import local_artifact_destination

    allowed = destination_module.LOCAL_DESTINATION_CONFIGURATION_KEYS
    assert allowed == frozenset({"schema_version", "control_root_ref", "data_root_ref"})
    assert local_artifact_destination.LOCAL_DESTINATION_CONFIGURATION_KEYS is allowed
    assert destination_module._ALLOWED_CONFIGURATION_KEYS[
        local_artifact_destination._CONFIG_SCHEMA
    ] is allowed


def test_s3_checked_in_destination_still_parses_with_an_unchanged_digest() -> None:
    """28.7 item 3, and 28.8's zero migration cost.

    A GREEN control before and after by construction: it asserts the change
    moved nothing.  The digest is pinned as a literal so that a change to the
    canonical bytes fails here rather than silently rebinding the record.
    """

    declaration = load_artifact_destination_config_v1(
        (ROOT / "training/artifacts.json").resolve()
    ).destinations[0]
    assert declaration.configuration_schema_version == "synaptic-local-artifact-destination/v1"
    assert json.loads(declaration.configuration_bytes) == {
        "schema_version": "synaptic-local-artifact-destination/v1",
        "control_root_ref": "artifact-publication-control",
        "data_root_ref": "artifact-local-default",
    }
    assert declaration.configuration_digest == _CHECKED_IN_CONFIGURATION_DIGEST


def test_s4_refused_configuration_constructs_no_declaration(
    tmp_path: Path, monkeypatch,
) -> None:
    """28.7 item 4: the refusal precedes the bytes.

    Moving the check earlier is worthless if only a later assertion proves it,
    so this pins the constructor itself.  `_canonical(config)` is an argument
    INSIDE that call, so constructing nothing is also canonicalizing nothing.
    """

    constructed = []
    real = destination_module.ArtifactDestinationDeclarationV1

    def spy(*args, **kwargs):
        constructed.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(destination_module, "ArtifactDestinationDeclarationV1", spy)
    for schema, allowed in _mapped_configurations().items():
        value = _mapped_destination(schema, allowed, authorization="placeholder")
        with pytest.raises(ValueError):
            load_artifact_destination_config_v1(_write(tmp_path, [value]))
    assert constructed == []


def test_s5_banned_name_nested_under_an_allowed_key_is_still_refused(
    tmp_path: Path,
) -> None:
    """28.7 item 5: the depth-wide scan was RETAINED, not replaced.

    The banned name sits under a key the allowlist permits, so the allowlist
    cannot be what refuses it; matching the denylist's own message is what
    discriminates the two.  A GREEN control before and after, which goes red
    under the one mutation that matters: deleting the scan at :85-93.
    """

    for schema, allowed in _mapped_configurations().items():
        holder = sorted(key for key in allowed if key != "schema_version")[0]
        value = _mapped_destination(schema, allowed, **{holder: {"api_key": "placeholder"}})
        with pytest.raises(ValueError, match="credentials and secrets"):
            load_artifact_destination_config_v1(_write(tmp_path, [value]))


def test_s6_unmapped_configuration_schema_version_is_refused_at_parse(
    tmp_path: Path, monkeypatch,
) -> None:
    """28.4 and 28.7 item 6 as amended (security-review #389).

    The quantifier is the point: the version asserted here is OUTSIDE the
    table, so the permissive shapes 28.4 names non-conforming -- `.get` with a
    None-only check, `.get` with a default, or falling through to the banned-
    name scan alone -- all fail this test.  Per 28.6's amendment the message
    WITHHOLDS the version, because a configuration_schema_version is itself a
    configuration value.
    """

    assert _UNMAPPED_CONFIG_SCHEMA not in _mapped_configurations()
    constructed = []
    real = destination_module.ArtifactDestinationDeclarationV1

    def spy(*args, **kwargs):
        constructed.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(destination_module, "ArtifactDestinationDeclarationV1", spy)
    value = _destination(
        "local", "host.local/v1", _UNMAPPED_CONFIG_SCHEMA,
        control_root_ref="artifact-publication-control",
        data_root_ref="artifact-local-default",
    )
    with pytest.raises(ValueError) as raised:
        load_artifact_destination_config_v1(_write(tmp_path, [value]))
    message = str(raised.value)
    assert _UNMAPPED_CONFIG_SCHEMA not in message, message
    assert "v99" not in message, message
    assert constructed == []


@pytest.mark.parametrize(
    "kept,gate",
    [("schema_version", "key_set"), ("data_root_ref", "version_read")],
)
def test_s7_proper_subset_of_the_allowed_keys_is_refused_at_parse(
    tmp_path: Path, kept: str, gate: str,
) -> None:
    """28.3: the parse gate is the EXACT key set, not containment.

    Containment accepts any proper subset, so a configuration that simply omits
    a required reference reaches the adapter as a differently-shaped object
    instead of as a refusal.  Both subsets the auditor reproduced are covered
    here, and they are refused by DIFFERENT gates -- which is why `gate` is a
    parameter and not a comment:

      * `schema_version` only reaches the key-set check, because the version
        read succeeds and every surviving key is inside the allowed set.  This
        is the containment hole; it is the arm that runs red before the fix.
      * `data_root_ref` only never reaches it: dropping `schema_version` makes
        the version read at the `_text` call refuse first.  That gate was
        already fail-closed, so this arm is a GREEN control on both trees, and
        it is recorded so a later reader does not mistake it for coverage of
        the key-set check.

    The invariant both arms share is what 28.3 and 28.6 actually require:
    refused at parse, no declaration constructed, no configuration VALUE and no
    version string in the message.
    """

    constructed: list[object] = []
    original = destination_module.ArtifactDestinationDeclarationV1

    # A SUBCLASS spy, not a function spy.  ArtifactDestinationConfigV1's
    # __post_init__ checks `type(item) is not ArtifactDestinationDeclarationV1`
    # against the module global, so patching that global with a function makes
    # the identity check fail for every item and the parse raises the
    # declarations-count message no matter what this test is probing.  On the
    # containment tree that produced a RED for the wrong reason.  A subclass
    # keeps the identity check true, so the only thing left to fail is the
    # property under test.
    class _Spy(original):  # type: ignore[misc, valid-type]
        def __post_init__(self) -> None:
            constructed.append(self)
            super().__post_init__()

    destination_module.ArtifactDestinationDeclarationV1 = _Spy
    try:
        mapped = _mapped_configurations()
        assert mapped, "the literal table must not be empty"
        for schema, allowed in mapped.items():
            assert kept in allowed, (schema, kept)
            value = _mapped_destination(schema, allowed)
            configuration = value["configuration"]
            dropped = sorted(key for key in configuration if key != kept)
            assert dropped, (schema, kept)
            for key in dropped:
                del configuration[key]
            assert set(configuration) == {kept}, (schema, configuration)

            with pytest.raises(ValueError) as raised:
                load_artifact_destination_config_v1(_write(tmp_path, [value]))
            message = str(raised.value)
            if gate == "key_set":
                for key in dropped:
                    assert key in message, (schema, kept, message)
            assert "placeholder" not in message, message
            assert schema not in message, message
    finally:
        destination_module.ArtifactDestinationDeclarationV1 = original
    assert constructed == []


def test_s8_configuration_wrong_in_both_directions_is_refused_as_an_extra_key(
    tmp_path: Path,
) -> None:
    """28.6 as amended: the dual-violation ordering, pinned.

    Every other section 28 fixture is wrong in exactly ONE direction -- S1 and
    the benign-key test add a key without removing one, S7 removes keys
    without adding one -- so none of them can see which of the two refusals
    runs first.  Swapping the unexpected block with the missing block leaves
    all of them green.  This fixture is wrong in BOTH directions at once,
    which is the only shape the ordering is visible from.

    The extra name is BENIGN.  `authorization` is outside all four banned sets
    at :32-41, which matters because `_configuration` runs its depth-wide scan
    before the version is read: a banned extra key is refused by the denylist
    and never reaches the exact-set gate this test exists to pin.

    The message must name the extra key, which is the reference-channel
    offender SEC-M1 exists for, and must NOT name the missing key, which is a
    completeness defect of a different class.  Per 28.6 neither a
    configuration value nor the version string may appear.
    """

    constructed: list[object] = []
    original = destination_module.ArtifactDestinationDeclarationV1

    # A SUBCLASS spy, not a function spy: ArtifactDestinationConfigV1's
    # __post_init__ checks `type(item) is not ArtifactDestinationDeclarationV1`
    # against the module global, so a function there reddens the parse for an
    # unrelated reason and hides what this test probes.
    class _Spy(original):  # type: ignore[misc, valid-type]
        def __post_init__(self) -> None:
            constructed.append(self)
            super().__post_init__()

    destination_module.ArtifactDestinationDeclarationV1 = _Spy
    try:
        mapped = _mapped_configurations()
        assert mapped, "the literal table must not be empty"
        for schema, allowed in mapped.items():
            removable = sorted(key for key in allowed if key != "schema_version")
            assert removable, (schema, allowed)
            missing = removable[0]

            value = _mapped_destination(schema, allowed, authorization="placeholder")
            configuration = value["configuration"]
            del configuration[missing]
            present = set(configuration)
            assert present - allowed == {"authorization"}, (schema, present)
            assert allowed - present == {missing}, (schema, present)

            with pytest.raises(ValueError) as raised:
                load_artifact_destination_config_v1(_write(tmp_path, [value]))
            message = str(raised.value)
            assert "authorization" in message, (schema, message)
            assert missing not in message, (schema, message)
            assert "placeholder" not in message, message
            assert schema not in message, message
    finally:
        destination_module.ArtifactDestinationDeclarationV1 = original
    assert constructed == []
