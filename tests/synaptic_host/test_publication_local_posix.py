from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from synaptic_host.local_artifact_destination import (
    build_local_artifact_destination_registration_v1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import RecoveryResultV1, RecoveryStatusV1
from synaptic_host.publication_composition import (
    PublicationConfigurationDocumentsV1,
    compose_host_publication_v1,
)
from synaptic_tuner.api.v1 import (
    ProjectContext,
    PublicationRequest,
    RunArtifactRequest,
    RunOutcome,
    RunsAPI,
    RunVerification,
    TrainingRunRef,
    TrainingRunState,
    VerifiedArtifact,
)


class _ArtifactStream:
    def __init__(self, run, artifact, maximum_bytes, payload):
        self.run = run
        self.artifact = artifact
        self.maximum_bytes = maximum_bytes
        self._payload = payload

    def iter_bytes(self):
        midpoint = max(1, len(self._payload) // 2)
        yield self._payload[:midpoint]
        if midpoint < len(self._payload):
            yield self._payload[midpoint:]


class _RunsOperations:
    def __init__(self, run: TrainingRunRef, payload: bytes) -> None:
        self.run = run
        self.payload = payload
        self.artifact = VerifiedArtifact(
            "model", hashlib.sha256(payload).hexdigest(), len(payload)
        )

    def show(self, run):
        assert run == self.run
        return RunOutcome(
            "synaptic-run-outcome/v1",
            run,
            TrainingRunState.SUCCEEDED,
            (self.artifact,),
        )

    def reverify(self, run):
        assert run == self.run
        return RunVerification(run, True, "2026-08-31T12:00:00Z")

    def artifacts(self, request: RunArtifactRequest):
        assert request.run == self.run
        assert request.role == self.artifact.role
        assert request.maximum_bytes >= self.artifact.size_bytes
        return _ArtifactStream(
            request.run, self.artifact, request.maximum_bytes, self.payload
        )


def _write_json(path: Path, value: object) -> Path:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return path.resolve()


def _environment(tmp_path: Path):
    project = tmp_path / "host-project"
    engine = project / "synaptic-tuner"
    data_root = project / ".synaptic" / "artifacts"
    control_root = project / ".synaptic" / "publication-control"
    spool_root = project / ".synaptic" / "publication-spool"
    state_root = project / ".synaptic" / "state"
    for path in (engine, data_root, control_root, spool_root, state_root):
        path.mkdir(parents=True)

    context = ProjectContext.host(
        engine_root=engine,
        project_root=project,
        state_root=state_root,
    )
    storage_path = _write_json(project / "storage.json", {
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {
                "access": "read_create",
                "location": "project://.synaptic/artifacts",
                "permit_ref": "permit-artifact-data",
                "root_ref": "artifact-data",
            },
            {
                "access": "read_create",
                "location": "project://.synaptic/publication-control",
                "permit_ref": "permit-artifact-control",
                "root_ref": "artifact-control",
            },
            {
                "access": "read_create",
                "location": "project://.synaptic/publication-spool",
                "permit_ref": "permit-artifact-spool",
                "root_ref": "artifact-spool",
            },
        ],
    })
    destination_path = _write_json(project / "artifacts.json", {
        "schema_version": "synaptic-host-artifact-destinations/v1",
        "destinations": [{
            "adapter_ref": "host.local/v1",
            "configuration": {
                "control_root_ref": "artifact-control",
                "data_root_ref": "artifact-data",
                "schema_version": "synaptic-local-artifact-destination/v1",
            },
            "destination_ref": "local-proof",
            "display_name": "Local proof",
            "policy": {
                "maximum_artifact_bytes": 1_048_576,
                "maximum_total_bytes": 1_048_576,
            },
            "schema_version": "synaptic-host-artifact-destination/v1",
        }],
    })
    run = TrainingRunRef("run-posix-proof", "project-posix-proof")
    payload = b"submodule-first-publication-proof"
    runs = RunsAPI(_RunsOperations(run, payload))

    def compose():
        return compose_host_publication_v1(
            context=context,
            runs=runs,
            configuration=PublicationConfigurationDocumentsV1.from_paths(
                destination_path=destination_path, storage_path=storage_path
            ),
            spool_root_ref="artifact-spool",
            clock=lambda: "2026-08-31T12:00:00Z",
            registration_builders=(
                build_local_artifact_destination_registration_v1,
            ),
        )

    return SimpleNamespace(
        compose=compose,
        context=context,
        control_root=control_root,
        data_root=data_root,
        destination_path=destination_path,
        payload=payload,
        run=run,
        spool_root=spool_root,
        state_root=state_root,
        storage_path=storage_path,
    )


@pytest.mark.skipif(os.name != "posix", reason="real Linux retained-dirfd publication")
def test_real_linux_publication_is_restart_safe_and_project_owned(tmp_path: Path):
    environment = _environment(tmp_path)
    compose = environment.compose
    run = environment.run
    payload = environment.payload
    data_root = environment.data_root
    spool_root = environment.spool_root
    state_root = environment.state_root

    facade = compose()
    page = facade.destinations()
    assert tuple(item.destination_ref for item in page.destinations) == ("local-proof",)
    result = facade.publish(PublicationRequest(run, "local-proof"))
    assert result.state.value == "verified"
    assert result.artifacts == (_RunsOperations(run, payload).artifact,)
    assert facade.verify(result.publication).verified is True
    assert facade.publications("local-proof").publications == (result,)
    facade.close()

    assert (state_root / "training.sqlite3").is_file()
    members = tuple(data_root.iterdir())
    assert len(members) == 1
    assert members[0].is_file()
    assert members[0].read_bytes() == payload
    assert tuple(spool_root.iterdir()) == ()

    reopened = compose()
    replay = reopened.publish(PublicationRequest(run, "local-proof"))
    assert replay == result
    assert reopened.verify(result.publication).verified is True
    assert tuple(data_root.iterdir()) == members
    reopened.close()
    assert tuple(spool_root.iterdir()) == ()


@pytest.mark.skipif(os.name != "posix", reason="real Linux retained-dirfd publication")
def test_post_durable_indeterminate_recovers_after_full_recomposition(
    tmp_path: Path, monkeypatch,
):
    environment = _environment(tmp_path)
    original_create_once = LocalFilesystemV1.create_once
    create_calls = []
    injected = False

    def durable_then_indeterminate(self, *args, **kwargs):
        nonlocal injected
        result = original_create_once(self, *args, **kwargs)
        create_calls.append(result.status)
        if not injected and result.status is RecoveryStatusV1.FOUND:
            injected = True
            return RecoveryResultV1(
                RecoveryStatusV1.INDETERMINATE, result.mutation_id
            )
        return result

    monkeypatch.setattr(
        LocalFilesystemV1, "create_once", durable_then_indeterminate
    )
    facade = environment.compose()
    ambiguous = facade.publish(
        PublicationRequest(environment.run, "local-proof")
    )
    assert ambiguous.state.value == "ambiguous"
    assert create_calls == [RecoveryStatusV1.FOUND]
    durable_members = tuple(environment.data_root.iterdir())
    assert len(durable_members) == 1
    assert durable_members[0].read_bytes() == environment.payload
    facade.close()
    assert tuple(environment.spool_root.iterdir()) == ()

    reopened = environment.compose()
    verification = reopened.verify(ambiguous.publication)
    assert verification.verified is True
    recovered = reopened.publications("local-proof").publications
    assert len(recovered) == 1
    assert recovered[0].state.value == "verified"
    assert recovered[0].publication == ambiguous.publication
    assert create_calls == [RecoveryStatusV1.FOUND]
    assert tuple(environment.data_root.iterdir()) == durable_members
    assert tuple(environment.spool_root.iterdir()) == ()
    reopened.close()


# --------------------------------------------------------------------------
# Residual R-6 -- directory substitution at the configured spool path.
#
# The architecture doc (section 11, R-6) leaves this open: "what happens when a
# different directory occupies the configured path at the next acquisition ...
# whether a substituted directory is rejected at re-acquisition is not settled
# by this closure, and should be answered before anyone relies on the re-open
# as a check rather than as a rebind."
#
# ANSWER, measured: SILENTLY REBOUND. Nothing compares the freshly stat'd
# directory identity against any previously recorded one, so a different
# directory at the configured path is accepted without complaint.
#
# A correction to the doc's premise, verified against the source. R-6 says the
# binding "is re-established on each admission acquisition, which re-opens by
# path (filesystem.py:754)". It does not. At 85b922fc, filesystem.py:754 is
#     lease = self._port.acquire_directory_admission(authority.data_directory)
# which passes the ALREADY-RETAINED RetainedDirectoryV1 handle. There is no
# re-open by path anywhere in acquire_single_root_admission. The only re-open
# by path is in retain_single_root_authority, once per authority, so the
# realistic substitution window is between two COMPOSITIONS -- a restart --
# which is what the first test below exercises.
#
# These two tests PIN CURRENT BEHAVIOUR. If a later change adds an identity
# check and turns one of them red, that is a fix, not a regression: update the
# test to assert the new refusal and close R-6.
# --------------------------------------------------------------------------


@pytest.mark.skipif(os.name != "posix", reason="real Linux retained-dirfd publication")
def test_r6_substituted_spool_directory_is_rebound_not_detected(tmp_path: Path):
    """A different directory at the configured spool path is accepted silently."""
    environment = _environment(tmp_path)
    spool_root = environment.spool_root

    facade = environment.compose()
    first = facade.publish(PublicationRequest(environment.run, "local-proof"))
    assert first.state.value == "verified"
    identity_before = os.stat(spool_root)
    facade.close()
    assert tuple(spool_root.iterdir()) == ()

    # Substitute: move the original aside and put a fresh empty directory at
    # the configured path. Same path, different inode.
    spool_root.rename(spool_root.parent / "publication-spool-displaced")
    spool_root.mkdir()
    identity_after = os.stat(spool_root)
    assert identity_before.st_ino != identity_after.st_ino, (
        "the substitution did not actually change the directory identity, so "
        "this test would pass without testing anything"
    )

    # The recomposition does not notice. No ROOT_CHANGED, no ADMISSION_INVALID.
    reopened = environment.compose()
    replay = reopened.publish(PublicationRequest(environment.run, "local-proof"))
    assert replay == first
    assert reopened.verify(first.publication).verified is True
    reopened.close()
    assert tuple(spool_root.iterdir()) == ()


@pytest.mark.skipif(os.name != "posix", reason="real Linux retained-dirfd publication")
def test_r6_admission_reacquisition_uses_the_retained_handle_not_the_path(
    tmp_path: Path,
):
    """The admission re-acquisition cannot see a substitution, by construction.

    This is the mechanism behind the answer above, asserted directly rather
    than argued: acquire_single_root_admission takes the retained directory
    handle, so releasing and re-acquiring an admission across a substitution
    returns a lease bound to the ORIGINAL directory. The retained handle
    follows the inode, not the name.
    """
    from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1

    port = PosixRetainedDirfdPortV1()
    spool_root = tmp_path / "spool"
    spool_root.mkdir()

    retained = port.retain_directory(spool_root)
    identity_before = retained.identity

    lease = port.acquire_directory_admission(retained)
    port.release_directory_admission(retained, lease)

    # Substitute while no admission is held -- the widest possible window.
    spool_root.rename(tmp_path / "spool-displaced")
    (tmp_path / "spool").mkdir()
    substituted = os.stat(tmp_path / "spool")
    assert substituted.st_ino != identity_before.inode

    # Re-acquisition succeeds and is still bound to the original directory.
    regained = port.acquire_directory_admission(retained)
    assert regained.root_node.node_digest == lease.root_node.node_digest
    port.release_directory_admission(retained, regained)
    port.close_directory(retained)
