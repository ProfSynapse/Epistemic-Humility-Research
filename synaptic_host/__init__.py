"""Lazy host adapters that do not import the engine before CLI bootstrap."""

from importlib import import_module

_EXPORTS = {
    "ArtifactDestinationConfigV1": (".artifact_destinations", "ArtifactDestinationConfigV1"),
    "ArtifactDestinationDeclarationV1": (".artifact_destinations", "ArtifactDestinationDeclarationV1"),
    "ArtifactDestinationPolicyV1": (".artifact_destinations", "ArtifactDestinationPolicyV1"),
    "AuthenticatedVerifiedArtifactSourceV1": (".verified_artifact_source", "AuthenticatedVerifiedArtifactSourceV1"),
    "BoundedGrantProvider": (".security", "BoundedGrantProvider"),
    "DestinationAdapterRegistrationV1": (".artifact_destinations", "DestinationAdapterRegistrationV1"),
    "DestinationEvidenceIssuerV1": (".publication_authority", "DestinationEvidenceIssuerV1"),
    "ExplicitModalHostSession": (".modal_provider", "ExplicitModalHostSession"),
    "FileHmacAuthenticator": (".security", "FileHmacAuthenticator"),
    "ImmutableArtifactDestinationRegistryV1": (".artifact_destinations", "ImmutableArtifactDestinationRegistryV1"),
    "ModalHostConfigV1": (".modal_provider", "ModalHostConfigV1"),
    "ModalProviderStateV1": (".modal_resolver", "ModalProviderStateV1"),
    "ModalTrainingIntentV1": (".modal_resolver", "ModalTrainingIntentV1"),
    "ScopedGitRemoteReader": (".security", "ScopedGitRemoteReader"),
    "PublicationEvidenceVerifierV1": (".publication_authority", "PublicationEvidenceVerifierV1"),
    "SqlitePublicationStoreV1": (".publication_store", "SqlitePublicationStoreV1"),
    "SqliteTrainingRepository": (".sqlite_repository", "SqliteTrainingRepository"),
    "ModalTrainingResolverV1": (".modal_resolver", "ModalTrainingResolverV1"),
    "VerifiedSourceEvidenceIssuerV1": (".publication_authority", "VerifiedSourceEvidenceIssuerV1"),
    "create_publication_evidence_v1": (".publication_authority", "create_publication_evidence_v1"),
    "load_artifact_destination_config_v1": (".artifact_destinations", "load_artifact_destination_config_v1"),
}

__all__ = tuple(_EXPORTS)


def __getattr__(name: str):
    """Resolve public host adapters only when a caller requests one."""
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
