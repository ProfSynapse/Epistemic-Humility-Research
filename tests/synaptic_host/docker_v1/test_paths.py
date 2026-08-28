from dataclasses import replace
import traceback

import pytest

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.model import (
    MAX_WSL_COMPONENT_BYTES_V1,
    MAX_WSL_PATH_BYTES_V1,
    AuthenticatedDockerWSLRootMappingV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
    DockerWSLRootMappingV1,
)
from synaptic_host.docker_v1.paths import DockerWSLPathTranslatorV1


class Authority:
    authority_ref = "wsl-path-authority"
    key_ref = "wsl-path-key"

    def issue(self, content):
        tag = digest_v1({"authority": self.authority_ref,
                         "key": self.key_ref,
                         "mapping": content.mapping_digest})
        return AuthenticatedDockerWSLRootMappingV1(
            content, self.authority_ref, self.key_ref, tag
        )

    def authenticate(self, value):
        expected = self.issue(value.content)
        if value != expected:
            return None
        content = value.content
        return AuthenticatedDockerWSLRootMappingV1(
            DockerWSLRootMappingV1(
                content.mapping_ref, content.distro, content.purpose,
                content.posix_root, content.mapping_digest,
            ), value.authority_ref, value.key_ref, value.tag,
        )


class Registry:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def resolve(self, mapping_ref, expected_mapping_digest):
        self.calls.append((mapping_ref, expected_mapping_digest))
        return self.value


def _request(
    mapping, *, posix_path=None, purpose=None, mapping_ref=None,
    expected_mapping_digest=None, expected_distro=None,
):
    return DockerWSLPathRequestV1.build(
        mapping_ref=(mapping.mapping_ref if mapping_ref is None else mapping_ref),
        expected_mapping_digest=(
            mapping.mapping_digest
            if expected_mapping_digest is None else expected_mapping_digest
        ),
        expected_distro=(
            mapping.distro if expected_distro is None else expected_distro
        ),
        purpose=(mapping.purpose if purpose is None else purpose),
        posix_path=(mapping.posix_root if posix_path is None else posix_path),
    )


@pytest.fixture(params=(
    ("source-root", DockerWSLPathPurposeV1.SOURCE_READ, "/home/joseph/source"),
    ("artifact-root", DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/srv/synaptic/artifacts"),
))
def path_env(request):
    mapping_ref, purpose, root = request.param
    authority = Authority()
    mapping = DockerWSLRootMappingV1.build(
        mapping_ref, "Ubuntu-22.04", purpose, root
    )
    registry = Registry(authority.issue(mapping))
    return mapping, authority, registry, DockerWSLPathTranslatorV1(
        registry=registry, authority=authority
    )


def test_exact_wsl_path_translates_to_authenticated_unc(path_env):
    mapping, _, registry, translator = path_env
    posix = mapping.posix_root + "/private/member.json"
    result = translator.translate(_request(mapping, posix_path=posix))
    assert result.unc_path == (
        "\\\\wsl.localhost\\Ubuntu-22.04" + posix.replace("/", "\\")
    )
    assert result.mapping_digest == mapping.mapping_digest
    assert registry.calls == [(mapping.mapping_ref, mapping.mapping_digest)]


@pytest.mark.parametrize("path", (
    "relative/path", "/home/../escape", "/home/./x", "/home//x",
    "/home/x/", "/home\\x", "/home/\x00x", "/home/\x1fx",
    "/home/e\u0301", "/" + "x" * 241,
))
def test_noncanonical_and_unsafe_paths_reject_before_registry(path_env, path):
    mapping, _, registry, translator = path_env
    before = list(registry.calls)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping, posix_path=path))
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID
    assert registry.calls == before


def test_prefix_confusion_purpose_and_unregistered_roots_fail_closed(path_env):
    mapping, _, registry, translator = path_env
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(
            mapping, posix_path=mapping.posix_root + "-foreign/member"
        ))
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID
    wrong = (DockerWSLPathPurposeV1.ARTIFACT_WRITE
             if mapping.purpose is DockerWSLPathPurposeV1.SOURCE_READ
             else DockerWSLPathPurposeV1.SOURCE_READ)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping, purpose=wrong))
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID
    registry.value = None
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping, mapping_ref="unknown-root"))
    assert caught.value.code is DockerPlatformCodeV1.ROOT_UNREGISTERED


def test_registry_exception_is_causally_suppressed(path_env):
    mapping, authority, _, _ = path_env

    class HostileRegistry:
        def resolve(self, mapping_ref, expected_mapping_digest):
            raise RuntimeError("secret registry exception")

    translator = DockerWSLPathTranslatorV1(
        registry=HostileRegistry(), authority=authority
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping))
    assert caught.value.code is DockerPlatformCodeV1.ROOT_UNREGISTERED
    assert caught.value.__suppress_context__ is True
    assert "secret" not in "".join(traceback.format_exception(caught.value))


def test_cross_distro_relabel_and_alternate_signer_reject(path_env):
    mapping, authority, registry, translator = path_env
    relabeled = DockerWSLRootMappingV1.build(
        mapping.mapping_ref, "Other-Distro", mapping.purpose,
        mapping.posix_root,
    )
    registry.value = replace(authority.issue(relabeled), tag="f" * 64)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping))
    assert caught.value.code is DockerPlatformCodeV1.AUTHENTICATION_FAILED

    registry.value = replace(authority.issue(mapping), authority_ref="alternate")
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping))
    assert caught.value.code is DockerPlatformCodeV1.AUTHENTICATION_FAILED


def test_validly_signed_cross_distro_relabel_conflicts_with_frozen_identity(
    path_env,
):
    mapping, authority, registry, translator = path_env
    relabeled = DockerWSLRootMappingV1.build(
        mapping.mapping_ref, "Other-Distro", mapping.purpose,
        mapping.posix_root,
    )
    registry.value = authority.issue(relabeled)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(_request(mapping))
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID


@pytest.mark.parametrize("mapping_ref", ("bad\nref", "\u00e9", "a" * 257))
def test_mapping_ref_is_canonical_before_registry_effect(path_env, mapping_ref):
    mapping, _, registry, translator = path_env
    request = _request(mapping)
    object.__setattr__(request, "mapping_ref", mapping_ref)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        translator.translate(request)
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID
    assert registry.calls == []


def test_wsl_component_and_total_utf8_path_bounds_are_exact(path_env):
    mapping, authority, registry, _ = path_env
    component = "a" * MAX_WSL_COMPONENT_BYTES_V1
    bounded_mapping = DockerWSLRootMappingV1.build(
        mapping.mapping_ref, mapping.distro, mapping.purpose,
        "/" + component,
    )
    bounded_registry = Registry(authority.issue(bounded_mapping))
    bounded = DockerWSLPathTranslatorV1(
        registry=bounded_registry, authority=authority
    )
    assert (
        bounded.translate(_request(bounded_mapping)).posix_path
        == bounded_mapping.posix_root
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerWSLRootMappingV1.build(
            "too-long-component", mapping.distro, mapping.purpose,
            "/" + component + "a",
        )
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID

    maximum_components = "/" + "/".join(["a"] * 128)
    assert DockerWSLRootMappingV1.build(
        "maximum-components", mapping.distro, mapping.purpose,
        maximum_components,
    ).posix_root == maximum_components
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerWSLRootMappingV1.build(
            "over-maximum-components", mapping.distro, mapping.purpose,
            maximum_components + "/a",
        )
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID

    multibyte_component = "\u00e9" * (MAX_WSL_COMPONENT_BYTES_V1 // 2)
    assert len(multibyte_component.encode("utf-8")) == MAX_WSL_COMPONENT_BYTES_V1
    assert DockerWSLRootMappingV1.build(
        "multibyte-component", mapping.distro, mapping.purpose,
        "/" + multibyte_component,
    ).posix_root == "/" + multibyte_component
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerWSLRootMappingV1.build(
            "over-multibyte-component", mapping.distro, mapping.purpose,
            "/" + multibyte_component + "a",
        )
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID

    components = (["a" * MAX_WSL_COMPONENT_BYTES_V1] * 16) + ["b" * 239]
    maximum_path = "/" + "/".join(components)
    assert len(maximum_path.encode("utf-8")) == MAX_WSL_PATH_BYTES_V1
    maximum_mapping = DockerWSLRootMappingV1.build(
        "maximum-path", mapping.distro, mapping.purpose, maximum_path
    )
    assert maximum_mapping.posix_root == maximum_path
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerWSLRootMappingV1.build(
            "over-maximum-path", mapping.distro, mapping.purpose,
            maximum_path + "b",
        )
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID


def test_digests_are_deterministic_and_bind_distro_root_purpose():
    source = DockerWSLRootMappingV1.build(
        "root", "Ubuntu-22.04", DockerWSLPathPurposeV1.SOURCE_READ,
        "/home/source",
    )
    assert source == DockerWSLRootMappingV1.build(
        "root", "Ubuntu-22.04", DockerWSLPathPurposeV1.SOURCE_READ,
        "/home/source",
    )
    assert len({
        source.mapping_digest,
        DockerWSLRootMappingV1.build(
            "root", "Other", DockerWSLPathPurposeV1.SOURCE_READ,
            "/home/source").mapping_digest,
        DockerWSLRootMappingV1.build(
            "root", "Ubuntu-22.04", DockerWSLPathPurposeV1.ARTIFACT_WRITE,
            "/home/source").mapping_digest,
        DockerWSLRootMappingV1.build(
            "root", "Ubuntu-22.04", DockerWSLPathPurposeV1.SOURCE_READ,
            "/home/other").mapping_digest,
    }) == 4


def test_mapping_builder_rejects_untyped_purpose_without_raw_failure():
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerWSLRootMappingV1.build(
            "root", "Ubuntu-22.04", "SOURCE_READ", "/home/source"
        )
    assert caught.value.code is DockerPlatformCodeV1.PATH_INVALID
