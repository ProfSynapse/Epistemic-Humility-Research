"""Lazy host adapters that do not import the engine before CLI bootstrap."""

from importlib import import_module

_EXPORTS = {
    "BoundedGrantProvider": (".security", "BoundedGrantProvider"),
    "ExplicitModalHostSession": (".modal_provider", "ExplicitModalHostSession"),
    "FileHmacAuthenticator": (".security", "FileHmacAuthenticator"),
    "ModalHostConfigV1": (".modal_provider", "ModalHostConfigV1"),
    "ModalProviderStateV1": (".modal_resolver", "ModalProviderStateV1"),
    "ModalTrainingIntentV1": (".modal_resolver", "ModalTrainingIntentV1"),
    "ScopedGitRemoteReader": (".security", "ScopedGitRemoteReader"),
    "SqliteTrainingRepository": (".sqlite_repository", "SqliteTrainingRepository"),
    "ModalTrainingResolverV1": (".modal_resolver", "ModalTrainingResolverV1"),
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
