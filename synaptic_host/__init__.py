"""Lazy host adapters that do not import the engine before CLI bootstrap."""

from importlib import import_module

_EXPORTS = {
    "LocalArtifactSpoolCleanupResultV1": (".artifact_spool", "LocalArtifactSpoolCleanupResultV1"),
    "LocalArtifactSpoolCleanupStatusV1": (".artifact_spool", "LocalArtifactSpoolCleanupStatusV1"),
    "LocalArtifactSpoolCodeV1": (".artifact_spool", "LocalArtifactSpoolCodeV1"),
    "LocalArtifactSpoolErrorV1": (".artifact_spool", "LocalArtifactSpoolErrorV1"),
    "LocalArtifactSpoolV1": (".artifact_spool", "LocalArtifactSpoolV1"),
    "HostPublicationFacadeV1": (".publication_composition", "HostPublicationFacadeV1"),
    "ArtifactDestinationConfigV1": (".artifact_destinations", "ArtifactDestinationConfigV1"),
    "ArtifactDestinationDeclarationV1": (".artifact_destinations", "ArtifactDestinationDeclarationV1"),
    "ArtifactDestinationPolicyV1": (".artifact_destinations", "ArtifactDestinationPolicyV1"),
    "DockerPublicationCompositionV1": (".docker_publication", "DockerPublicationCompositionV1"),
    "PublicationConfigurationDocumentsV1": (".publication_composition", "PublicationConfigurationDocumentsV1"),
    "AuthenticatedVerifiedArtifactSourceV1": (".verified_artifact_source", "AuthenticatedVerifiedArtifactSourceV1"),
    "BoundedGrantProvider": (".security", "BoundedGrantProvider"),
    "DestinationAdapterRegistrationV1": (".artifact_destinations", "DestinationAdapterRegistrationV1"),
    "DestinationAdapterInstallationV1": (".artifact_destinations", "DestinationAdapterInstallationV1"),
    "DestinationEvidenceIssuerV1": (".publication_authority", "DestinationEvidenceIssuerV1"),
    "DestinationInventoryEvidenceIssuerV1": (".publication_authority", "DestinationInventoryEvidenceIssuerV1"),
    "ExplicitModalHostSession": (".modal_provider", "ExplicitModalHostSession"),
    "FileHmacAuthenticator": (".security", "FileHmacAuthenticator"),
    "ImmutableArtifactDestinationRegistryV1": (".artifact_destinations", "ImmutableArtifactDestinationRegistryV1"),
    "ModalHostConfigV1": (".modal_provider", "ModalHostConfigV1"),
    "ModalProviderStateV1": (".modal_resolver", "ModalProviderStateV1"),
    "ModalTrainingIntentV1": (".modal_resolver", "ModalTrainingIntentV1"),
    "ScopedGitRemoteReader": (".security", "ScopedGitRemoteReader"),
    "PublicationEvidenceVerifierV1": (".publication_authority", "PublicationEvidenceVerifierV1"),
    "PublicationEvidenceAuthorityV1": (".publication_authority", "PublicationEvidenceAuthorityV1"),
    "PublicationLookupEvidenceIssuerV1": (".publication_authority", "PublicationLookupEvidenceIssuerV1"),
    "PublicationReceiptEvidenceIssuerV1": (".publication_authority", "PublicationReceiptEvidenceIssuerV1"),
    "PublicationTombstoneEvidenceIssuerV1": (".publication_authority", "PublicationTombstoneEvidenceIssuerV1"),
    "ResolvedDestinationAdapterV1": (".artifact_destinations", "ResolvedDestinationAdapterV1"),
    "SqlitePublicationStoreV1": (".publication_store", "SqlitePublicationStoreV1"),
    "SqliteTrainingRepository": (".sqlite_repository", "SqliteTrainingRepository"),
    "ModalTrainingResolverV1": (".modal_resolver", "ModalTrainingResolverV1"),
    "VerifiedSourceEvidenceIssuerV1": (".publication_authority", "VerifiedSourceEvidenceIssuerV1"),
    "create_publication_evidence_v1": (".publication_authority", "create_publication_evidence_v1"),
    "load_artifact_destination_config_v1": (".artifact_destinations", "load_artifact_destination_config_v1"),
    "acquire_local_artifact_spool_v1": (".artifact_spool", "acquire_local_artifact_spool_v1"),
    "compose_host_publication_v1": (".publication_composition", "compose_host_publication_v1"),
    "compose_docker_publication_v1": (".docker_publication", "compose_docker_publication_v1"),
    "artifact_destination_declaration_digest_v1": (".artifact_destinations", "artifact_destination_declaration_digest_v1"),
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
