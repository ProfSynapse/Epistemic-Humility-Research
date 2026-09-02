# Native-Windows Artifact Publication Closure — Preparation

Phase: PREPARE. Feature: close native-Windows artifact publication for the prepared
Docker activation path. Status: research complete, read-only. No application code,
test, or configuration was changed.

Worktree: `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean`
Branch `feat/submodule-cloud-api-v1-host-clean` at `85b922fc`.
Engine submodule `synaptic-tuner` gitlink `aec998ee`.

All paths below are relative to that worktree root unless shown absolute.

---

## 1. Executive summary

The blocker recorded in `.codex/pact/pause-state.md:37` is real but it is **two
independent gaps, not one**. Prior notes describe only the second.

**Gap A — publication is not wired into production at all.** The prepared Docker
activation path constructs its composition without a `publication` argument at
`synaptic_host/docker_training.py:846-848`, so the parameter takes its default
`None` at `synaptic_host/docker_prepared_composition.py:297`. The factory that
would build a real publication composition,
`compose_docker_publication_v1` (`synaptic_host/docker_publication.py:442`), has
**no non-test caller** anywhere in the Host tree. The only end-to-end wiring that
exists lives in a test, `tests/synaptic_host/test_publication_local_posix.py:146-156`.
Closing the POSIX-only backend alone would therefore still publish nothing.

**Gap B — the local default backend is hard-bound to a Linux-only port.**
`synaptic_host/publication_composition.py:433` unconditionally evaluates
`LocalFilesystemV1(PosixRetainedDirfdPortV1(), storage)`. There is no platform
branch on that line. `PosixRetainedDirfdPortV1.__init__` raises
`CAPABILITY_UNAVAILABLE` at `synaptic_host/local_io_v1/posix.py:107-108` whenever
`detect_posix_capability_v1()` is not available, and that detector returns
available only for `sys.platform.startswith("linux")`
(`synaptic_host/local_io_v1/posix.py:73`). On native Windows the composition dies
at line 433 before any destination adapter is built.

**The decision-relevant finding.** POSIX-ness is *not* confined to the port. Path
types are clean everywhere and permission semantics are clean everywhere outside
the concrete port, but the **commit-proof protocol is encoded in shared model
validation**: a publication is proven committed by observing a file's hard-link
count go 1 to 2 and back to 1 across two directory fsyncs. Those invariants sit in
`synaptic_host/local_io_v1/model.py:695-697, 748-750, 978, 1092-1096` and
independently in `synaptic_host/artifact_spool.py:115-120`. A Windows backend
cannot satisfy those types merely by supplying a different port implementation. It
must either reproduce hard-link semantics on NTFS or the shared commit evidence
must be redesigned. That choice is the architect's single load-bearing decision,
and it is the subject of section 8.

**Recommended minimal closure** (section 8, Option A): reproduce the existing
commit protocol on NTFS with a Windows port, leaving every shared invariant, the
signed evidence digest, and the whole POSIX path untouched; make line 433
platform-selected using the `os.name == "nt"` pattern already proven in
`synaptic_host/security.py`; and wire `compose_docker_publication_v1` into
`docker_training.py`. One genuine semantic gap survives that choice and needs an
explicit architectural ruling: directory-level durability, since Windows has no
equivalent of `os.fsync` on a directory descriptor.

---

## 2. Worktree verification

Read-only git checks, run with `git -c safe.directory=*`.

| Check | Result |
|---|---|
| HEAD | `85b922fc0f9e47efa151d9e23ace1e29fda0580f` |
| Branch | `feat/submodule-cloud-api-v1-host-clean` |
| Diff against released `5503c528` | 3 files, all under `.codex/pact/` |
| Engine gitlink | `160000 commit aec998ee8d6a2e58d86e19e8132bc59aa21ebd53` |

`git diff --stat 5503c528 85b922fc` touches only `.codex/pact/memory.md`,
`.codex/pact/pause-state.md`, and `.codex/pact/session.md`. Application code,
tests, and the engine gitlink are identical to the released revision. The clean
worktree is a faithful base for this work.

**CLAUDE.md note.** The dispatch said `CLAUDE.md` is gitignored and may not exist
here. It does exist in this worktree and is tracked by the Host repo. Nothing in
this task wrote to it or to any skill mirror.

---

## 3. The publication pipeline, end to end

### 3.1 Where publication is skipped

The activation surface is `DockerPreparedCompositionV1`. Its constructor accepts
publication as an optional dependency:

```
synaptic_host/docker_prepared_composition.py:295-297
    def __init__(
        self, *, repository: object, builder: DockerPreparedControlBuilderV1,
        clock: Callable[[], str], publication: object | None = None,
    ) -> None:
```

The production caller omits it entirely:

```
synaptic_host/docker_training.py:846-848
    composition = DockerPreparedCompositionV1(
        repository=repository, builder=builder, clock=clock,
    )
```

The value flows into the run service at `docker_prepared_composition.py:310`, and
the service records the expected type:

```
synaptic_host/docker_execution.py:988-992
        clock: Callable[[], str], publication: object | None,
    ) -> None:
        if publication is not None:
            from .docker_publication import DockerPublicationCompositionV1
            if type(publication) is not DockerPublicationCompositionV1:
```

So the parameter expects exactly `DockerPublicationCompositionV1`
(`synaptic_host/docker_publication.py:375`), which is factory-issued only through
`compose_docker_publication_v1` (`synaptic_host/docker_publication.py:442`). It
additionally requires the object to expose callable `publish` and `close`
(`docker_execution.py:1004-1008`).

### 3.2 The silent skip

The consequence is precise and quiet. `reconcile` reaches the terminal phase and
returns without publishing:

```
synaptic_host/docker_execution.py:1103-1111
    def reconcile(self, request: DockerPreparedRunRequestV1) -> DockerPreparedRunOutcomeV1:
        current = self._load(request)
        if current.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED:
            if self._publication is None:
                return DockerPreparedRunOutcomeV1.from_record(current)
            result = self._publication.publish(request=request, record=current)
```

A run therefore reaches `ARTIFACTS_VERIFIED`, reports success, and produces no
publication record. `DockerPreparedRunOutcomeV1.published`
(`docker_execution.py:256-258`) stays `False` because both `publication_id` and
`publication_state` remain unset. This is exactly the failure mode
`.codex/pact/memory.md:29` warns against for a real GPU acceptance smoke.

### 3.3 The composition chain when publication IS supplied

```
compose_docker_publication_v1                  docker_publication.py:442
  -> _verified_record / _validate_configuration_binding   :448-453
  -> RunsAPI(_DockerRunsOperationsV1(...))                :454-456
  -> compose_host_publication_v1(...)                     :457-464
       -> filesystem = LocalFilesystemV1(PosixRetainedDirfdPortV1(), storage)
                                                 publication_composition.py:433
       -> acquire_local_artifact_spool_v1(filesystem, ...)             :443-445
       -> each registration_builder(filesystem=, storage=, spool=, evidence=, ...) :447-456
       -> ImmutableArtifactDestinationRegistryV1(...)                  :468-473
       -> PublicationOperationsV1(...)                                 :480-487
```

`compose_docker_publication_v1` requires `context`, `repository`, `request`,
`clock`, `spool_root_ref`, and `registration_builders`
(`docker_publication.py:442-447`). None of those is currently assembled on the
production path, which is the concrete shape of Gap A.

The spool root exists in configuration as `artifact-publication-spool`
(`training/storage.json`), alongside `artifact-local-default` and
`artifact-publication-control`. The destination declaration `local-default` bound
to adapter `host.local/v1` exists in `training/artifacts.json`. Configuration is
therefore already complete; only the code wiring is absent.

### 3.4 Authority, store, and the gate

Three responsibilities, commonly conflated, are distinct here.

| Module | Role | Evidence |
|---|---|---|
| `publication_authority.py` | Authenticates evidence. HMAC issuer/verifier over `<state_root>/publication/evidence-hmac.key`. Records nothing, gates nothing. | `:1`, `:92`, `:154`, `:163`, `:571-608`, `:580-583` |
| `publication_store.py` | Durable persistence, ownership, leases. Table `publication_records_v1`. | `:1`, `:118`, `:162-185`, insert at `:229-242` from `claim` `:377-390` |
| Engine `PublicationOperationsV1` | The actual gate. Resolves through the registry, verifies the descriptor, then drives claim to transfer to complete. | `synaptic-tuner/tuner/execution/coordinator_v1/publication.py:2128`, `:2151-2165`, `:2493-2590` |

Summary: the authority authenticates, the store records, the coordinator gates.
All three are handed to the coordinator at `publication_composition.py:480-487`.

---

## 4. POSIX dependency inventory and classification

Full symbol-level evidence was gathered across `publication_composition.py`,
every module of `local_io_v1/`, `local_artifact_destination.py`,
`artifact_spool.py`, `verified_artifact_source.py`, and the publication-touched
parts of `security.py`. The classification below groups the findings; per-symbol
line references follow.

### 4.1 Category (a) AVAILABLE — works on Windows as written

- File-type bit predicates. Every mask in the shared model is `& 0o170000`, i.e.
  file type only, never permission bits: `local_io_v1/model.py:350-351, 468,
  655-657, 695-697, 748, 978, 1096`; `local_io_v1/filesystem.py:437-438, 1410,
  1415, 1559, 1564, 1596, 1601, 1625, 1630`.
- Path typing. Contracts use native `pathlib.Path`, never `PurePosixPath`:
  `local_io_v1/filesystem.py:301`; `local_io_v1/model.py:231, 241, 269, 278`;
  `local_io_v1/config.py:137-140`. `PurePosixPath` appears in this Host package
  only in the container-side modules `docker_execution_state.py:12`,
  `docker_model_inventory.py:10`, `docker_staging.py:18`.
- The relative-component policy is already Windows-hardened, rejecting backslash,
  colon, trailing dot or space, and the reserved device names:
  `local_io_v1/model.py:94-127` and `:58-60`.
- Flag degradation already present: `getattr(os, "O_BINARY", 0)` and
  `getattr(os, "O_NOFOLLOW", 0)` at `publication_composition.py:92-95`;
  the same pattern at `security.py:549-550, 618-620, 697-698`.
- Windows reparse-point awareness already present inside the publication
  composition itself: `publication_composition.py:50, 67, 72, 80`.
- `os.fsync` on a **file** descriptor: `local_io_v1/posix.py:553`.
- `verified_artifact_source.py` has zero POSIX dependencies; its imports at
  `:3-24` include no `os`, `stat`, or `pathlib`.

### 4.2 Category (b) NEEDS-PORT — a Windows implementation must be written

These are the mechanical primitives. They are numerous but individually
tractable, and the Windows equivalents are already demonstrated elsewhere in this
repo (section 5).

| Primitive | Evidence |
|---|---|
| `fcntl` import, absent on Windows | `local_io_v1/posix.py:39-42` |
| `os.supports_dir_fd`, `os.supports_follow_symlinks` capability gates | `local_io_v1/posix.py:81, 82, 89, 90` |
| `O_CLOEXEC / O_DIRECTORY / O_NOFOLLOW` required as ints | `local_io_v1/posix.py:86` |
| dirfd-relative open, the core primitive | `local_io_v1/posix.py:261, 288-291, 335, 346-351, 393-396, 604-607, 621, 640, 731-736` |
| dirfd retention of raw int descriptors | `local_io_v1/posix.py:209-229`, files at `:231-243` |
| `os.stat(..., dir_fd=, follow_symlinks=False)` | `local_io_v1/posix.py:258, 263, 325, 636, 655` |
| `os.fstat` on a directory fd | `local_io_v1/posix.py:193, 389, 397, 406, 464, 466` |
| `os.scandir(<int fd>)` | `local_io_v1/posix.py:166, 312, 680` |
| `os.mkdir(name, 0o700, dir_fd=)` and `os.open(..., 0o600)` | `local_io_v1/posix.py:510, 592, 349, 734` |
| `os.link(..., src_dir_fd=, dst_dir_fd=)` and `os.unlink(..., dir_fd=)` | `local_io_v1/posix.py:567-570, 749-755, 578, 760, 782` |
| `st_dev` / `st_ino` node identity | `local_io_v1/filesystem.py:417-430, 433-439`; `artifact_spool.py:103-112` |
| `LocalFileIdentityV1`, a POSIX `stat` record in shared signatures | `local_io_v1/model.py:308-333`; consumed at `artifact_spool.py:20, 133, 145, 318-327` |
| Port protocol named for POSIX, 22 methods | `local_io_v1/filesystem.py:300-331` |

### 4.3 Category (c) SEMANTIC-GAP — needs an architectural decision

These are the findings that make this more than a port swap.

**C1. Directory fsync has no Windows equivalent.**
`os.fsync(<directory fd>)` is the durability barrier between "bytes written" and
"name visible": `local_io_v1/posix.py:559, 600, 759, 762, 783`, surfaced through
the port as `fsync_directory` (`filesystem.py:322`) and called at
`filesystem.py:3034` and `:3057`. Python on Windows cannot open a directory as a
flushable handle, and `FlushFileBuffers` on a directory handle is not equivalent.
The repo already uses `FlushFileBuffers` for a file, at `security.py:468`, so the
file half is solved and only the directory half is open. **This is the one gap
with no in-repo precedent and it needs an explicit ruling.**

**C2. The commit proof is hard-link count, and it lives in shared code.**
The publish algorithm is create-exclusive, then link, then fsync the directory,
then unlink the temporary, then fsync again:
`local_io_v1/posix.py:749-762` and `filesystem.py:3031-3058`. Commitment is
*proven* by the link-count transition, and that proof is asserted in shared
validation, not in the port:

- `local_io_v1/model.py:695-697` — `BorrowedFileV1` rejects `nlink != 1`.
- `local_io_v1/model.py:748-750` — `BorrowedHardlinkPairV1` requires `nlink == 2`.
- `local_io_v1/model.py:978` — journal `LINKED` phase requires `nlink == 2`.
- `local_io_v1/model.py:1092-1096` — `stat_is_regular_single_v1` requires `nlink == 1`,
  with the in-code comment that POSIX file-type bits are stable.
- `artifact_spool.py:115-120` — the spool independently requires `nlink == 1`.

NTFS does support hard links, so this is reproducible rather than impossible, but
it is a constraint on the port, not a free translation.

**C3. Root anchoring assumes a single filesystem root.**
`local_io_v1/posix.py:252-255` asserts `parts[0] == "/"` and opens `/` before
descending component by component. Windows has no single root; every absolute path
begins at a drive or a UNC share.

**C4. Spool admission is Linux-only, not merely POSIX-only.**
`_require_linux_admission` (`filesystem.py:586-589`) gates
`retain_single_root_authority`, `release_single_root_authority`,
`acquire_single_root_admission`, and `release_single_root_admission`
(`filesystem.py:675, 718, 746, 822`), which `acquire_local_artifact_spool_v1`
calls at `artifact_spool.py:624-646`. The mechanism is a non-blocking
`fcntl.flock(LOCK_EX)` on a directory descriptor
(`local_io_v1/posix.py:401-405`), whose crash-release property is the point.
Windows has no directory advisory lock with the same crash-release semantics.

**C5. Case-fold collision detection assumes a case-sensitive namespace.**
`local_io_v1/posix.py:175-178` treats an NFC-casefold collision as evidence of a
hostile or changed root. On a case-insensitive NTFS volume that condition is
normal, so the anomaly criterion needs redefining.

**C6. POSIX stat fields are hashed into signed evidence.**
`local_artifact_destination.py:171-188` hashes `identity.canonical()`, i.e.
device, inode, mode, nlink, and timestamps, into `registry_digest`, which is then
sealed into the authenticated tombstone and lookup evidence at
`local_artifact_destination.py:416, 457-470`. The value crossing to the engine is
an opaque hex string, so the engine contract stays clean, but evidence produced by
two different platform backends would not be mutually reproducible.

### 4.4 Answer to the confinement question

My teachback recorded this as the item most likely to be wrong, and it was
partly wrong. The corrected finding:

| Component | POSIX in signatures or validation? | Evidence |
|---|---|---|
| `verified_artifact_source.py` | No | `:3-24` |
| `publication_store.py` | No (only `os.urandom` at `:93`) | grep clean |
| `publication_authority.py` | No | grep clean |
| `artifact_destinations.py` (the registry) | No (only `pathlib.Path` at `:8`) | `:8` |
| Engine publication contract | No | `coordinator_v1/publication.py:381-397` |
| `security.py` | No POSIX-only contract; already dual-implemented | `:19, :60, :533-546, :599, :680` |
| `local_artifact_destination.py` | Type-clean, but hashes POSIX identity into evidence | `:171-188, :416` |
| `artifact_spool.py` | **Yes** — identity type, `S_IFMT`, `nlink == 1` | `:20, :103-120, :318-327` |
| `local_io_v1/model.py` | **Yes** — `nlink` 1/2 invariants | `:695-697, :748-750, :978, :1092-1096` |
| `local_io_v1/filesystem.py` | **Yes** — port named POSIX, platform gates | `:300, :581-589` |

So: path types are clean, permission semantics are clean, the registry and the
engine boundary are clean. **Hard-link commit semantics and the POSIX stat-record
shape are the two real leaks, and both live in `local_io_v1/model.py` plus
`artifact_spool.py`.** This widens the closure beyond the port but does not
invalidate the registry-preserving approach.

---

## 5. The Windows port pattern that already exists

Two separate precedents exist. The architect should reuse both rather than invent.

### 5.1 The handle-relative pattern in `docker_staging.py`

This module already performs handle-relative, redirect-proof, rename-out-blocking
directory work on native Windows. It is destroy-only, but the primitives are the
ones publication needs.

- Native binding, `ctypes.WinDLL` over `kernel32` and `ntdll`, guarded on
  `os.name != "nt"`: `docker_staging.py:327, 329-330`.
- Anchor open by path, using `FILE_FLAG_BACKUP_SEMANTICS` (0x02000000, `:200`) to
  open a **directory** handle and `FILE_FLAG_OPEN_REPARSE_POINT` (0x00200000,
  `:201`) so the anchor itself is not traversed: `docker_staging.py:441-448`.
- Every descendant opened **relative to the parent handle** via `NtCreateFile`
  with `OBJECT_ATTRIBUTES.RootDirectory` set to the parent handle, a
  single-component name, and `OBJ_DONT_REPARSE`: `docker_staging.py:471-503`,
  specifically `RootDirectory` at `:473` and `Attributes` at `:475`. Options at
  `:486-490` type the open as directory or non-directory and add
  `FILE_OPEN_REPARSE_POINT`. This is the Windows analogue of `dir_fd`.
- Identity proof by `(VolumeSerialNumber, 128-bit FileId)` via
  `GetFileInformationByHandleEx(FILE_ID_INFO)`, rejecting any reparse attribute:
  `docker_staging.py:393, 414-415`.
- Canonical location proof via `GetFinalPathNameByHandleW`, requiring a `\\?\`
  prefix: `docker_staging.py:420`.
- Handle-relative deletion, never by path:
  `SetFileInformationByHandle(FILE_DISPOSITION_INFO_EX, FILE_DISPOSITION_DELETE)`
  at `docker_staging.py:811-816`, deepest-first, with a re-proof immediately
  before each mutation at `:802-804`.

**How rename-out is blocked.** By holding an open handle whose share mode omits
`FILE_SHARE_DELETE`. `_FILE_SHARE_ALL = 0x7` (`:192`) is used during promotion, when
the tree must stay renameable; `_FILE_SHARE_READ_WRITE = 0x3` (`:193`) is used for
every handle once cleanup is active, at `:444` for the parent and `:498` for each
child. Windows requires DELETE access to rename an object, and an existing handle
without `FILE_SHARE_DELETE` denies a later open requesting DELETE, so the rename
fails with `ERROR_SHARING_VIOLATION`. The transition into that state re-verifies
both identities and both locations before closing the permissive handles:
`docker_staging.py:623, 626-643, 651-657`. The behaviour is asserted by
`tests/synaptic_host/test_docker_staging.py:112-114` and `:145-147`, which expect
`winerror == 32`.

**Caveat the architect must not miss:** there is **no port interface here.**
`docker_staging.py` declares zero Protocols. The POSIX sibling is a single inline
`shutil.rmtree` branch at `:854-861`, and platform selection is an inline ternary
at `:1688-1691`. So this module supplies proven *primitives* with no seam.

### 5.2 The dual-implementation pattern in `security.py`

This is the stronger structural precedent, and it is the template I recommend for
line 433.

- `if os.name == "nt": from ctypes import wintypes` at `security.py:19-20`, and the
  full Win32 block opening at `:60`.
- Symmetric selection at each operation:
  `_create_private_directory` `:533-540`, `_validate_private_directory` `:544-546`,
  key creation `:599-607`, key read `:680`.
- The Windows implementations already exist: `_win_create_private_directory` `:272`,
  `_win_validate_directory` `:392`, `_win_read_private_key` `:414`,
  `_win_create_private_key` `:449`.
- Crucially, it already made the analogous semantic decision this task faces: POSIX
  permission bits are replaced by an SDDL DACL (`security.py:250-270`) validated
  ACE by ACE (`:340-390`), with an NTFS requirement check `_win_require_ntfs`
  (`:284-293`) and a tighter share mode of `FILE_SHARE_READ` only (`:68`, used at
  `:308`).

### 5.3 The injection seam that already exists

`LocalFilesystemV1.__init__` already accepts an arbitrary port and an overridable
platform string:

```
synaptic_host/local_io_v1/filesystem.py:476-485
    def __init__(self, port: PosixFilesystemPortV1 | None, permit_authenticator,
                 *, native_platform: str | None = None)
    ...
    self._platform = sys.platform if native_platform is None else native_platform
```

`capability()` at `:557-579` already reports a `platform_family` of `posix`,
`windows`, or `other`, and `detect_posix_capability_v1` at `posix.py:64-71`
already computes a `windows` family as a named outcome. The contract anticipates a
non-POSIX family. Only `publication_composition.py:433` fails to use the seam.

### 5.4 What the staging pattern does not cover

The publication closure needs all of the following, none of which the Windows
staging layer provides:

1. No atomic rename-over. Promotion is create-if-absent
   (`docker_staging.py:1775-1780`); there is no `MoveFileEx` with
   `MOVEFILE_REPLACE_EXISTING` and no `CreateHardLinkW` anywhere in the tree.
2. No durability. There is no `FlushFileBuffers` in `docker_staging.py` at all.
3. No crash-recovery journal. `_WindowsStageCleanupV1` holds two in-memory booleans
   (`:319-320`); nothing survives process death.
4. No content verification. The Windows layer proves identity but never hashes;
   its opens request only `FILE_READ_ATTRIBUTES | SYNCHRONIZE | FILE_LIST_DIRECTORY`
   (`:481-485`), so a `FILE_READ_DATA` read path must be added.
5. No write path. It can only open existing (`_OPEN_EXISTING` `:446`, `_FILE_OPEN`
   `:500`); there is no handle-relative exclusive create.
6. No admission or lease model equivalent to the POSIX `flock`.

---

## 6. The provider-neutral destination registry

### 6.1 Contract

There is no module-level singleton. Registration is a per-composition passed-object
flow in three layers.

| Layer | Type | Location |
|---|---|---|
| Adapter registration | `DestinationAdapterRegistrationV1` — `adapter_ref`, `configuration_schema_version`, `adapter_type`, `factory` | `artifact_destinations.py:197-208` |
| Installation wrapper | `DestinationAdapterInstallationV1` — registration plus terminal `cleanup` | `artifact_destinations.py:211-228` |
| Registry | `ImmutableArtifactDestinationRegistryV1(*, config, registrations, issuer, verifier)` | `artifact_destinations.py:493-500`, built once at `publication_composition.py:468-473` |

The extension point is the `registration_builders` parameter of
`compose_host_publication_v1` (`publication_composition.py:395-402`). Each builder
is called with a fixed keyword set at `:447-456` and must return an installation
(`:457-458`). The local builder matching that signature is
`build_local_artifact_destination_registration_v1`
(`local_artifact_destination.py:567-576`).

Destination identity is a plain ref string, not a URL scheme. There is no
`local://` anywhere. The configured destination is `local-default` bound to
adapter ref `host.local/v1` (`local_artifact_destination.py:50`) in
`training/artifacts.json`.

The typed contract an adapter must satisfy is the engine Protocol
`DestinationPublicationPortV1`
(`synaptic-tuner/tuner/execution/coordinator_v1/publication.py:812-820`), with
`publish_once`, `lookup`, and `iter_bytes`. It is never checked as a Protocol at
runtime; conformance is a duck-typed probe of exactly those three names at
`artifact_destinations.py:289-301`.

### 6.2 Why provider neutrality survives a Windows adapter

The admission path contains no provider name, no platform check, and no allowlist.

- Adapters are looked up purely by `adapter_ref` string, matched on schema version:
  `artifact_destinations.py:524-530`.
- The adapter is built by the registration's own factory: `:533-537`.
- The only type gate is identity against the registration's own declared type:
  `:544-545`.
- Structural constraints only: 1 to 100 declarations, unique ascending
  `destination_ref` (`:184-194`), unique ascending `adapter_ref` (`:509-511`), and
  a rejection of credential-shaped configuration keys (`:32-41`, `:87-93`).

The test suite already proves multi-adapter admission with fictional adapter refs
at `tests/synaptic_host/test_artifact_destinations.py:180-190`. So neither adding a
second adapter nor swapping the port beneath the existing one requires any change
to `artifact_destinations.py`.

### 6.3 The local default and its platform binding

`LocalArtifactDestinationV1` (`local_artifact_destination.py:191`) is the only
production adapter. Its declaration is selected by matching the CLI destination
value at `docker_training.py:597-610`, which explicitly rejects `provider-staging`
at `:608`. That selection is unconditional and carries no platform branch. The
POSIX binding is one layer down, at `publication_composition.py:433`.

Note that `LocalArtifactDestinationV1` requires the concrete filesystem type:
`type(filesystem) is not LocalFilesystemV1` at `local_artifact_destination.py:580`.
A Windows implementation that reuses this adapter must therefore go in as a
*port* beneath `LocalFilesystemV1`, not as a replacement filesystem class.

### 6.4 Other providers — factual status

- **Modal exists but is not a publication destination.** `modal_provider.py` and
  `modal_resolver.py` import nothing from `artifact_destinations`; Modal is a
  training execution provider. Its `destination_ref` is a training-ingress field
  constrained to the literal `provider-staging` (`cli.py:23, 90, 850`), which
  `docker_training.py:608` rejects for artifact publication.
- **HF Jobs and RunPod do not exist in this tree in any form** — not as code, stub,
  comment, or configuration entry. The pause-state roadmap anticipates them; the
  code does not yet.

Exactly one production `adapter_ref` literal exists today: `host.local/v1`.

### 6.5 Test coverage

Files under `tests/synaptic_host/` exercising publication, destinations,
`local_io_v1`, prepared composition, or staging:

```
tests/synaptic_host/test_artifact_destinations.py
tests/synaptic_host/test_artifact_spool.py
tests/synaptic_host/test_local_artifact_destination.py
tests/synaptic_host/test_publication_authority.py
tests/synaptic_host/test_publication_composition.py
tests/synaptic_host/test_publication_local_posix.py
tests/synaptic_host/test_publication_store.py
tests/synaptic_host/test_docker_publication.py
tests/synaptic_host/test_docker_prepared_composition.py
tests/synaptic_host/test_docker_staging.py
tests/synaptic_host/test_verified_artifact_source.py
tests/synaptic_host/local_io_v1/test_boundaries.py
tests/synaptic_host/local_io_v1/test_config.py
tests/synaptic_host/local_io_v1/test_filesystem.py
tests/synaptic_host/local_io_v1/test_posix_ext4.py
tests/synaptic_host/local_io_v1/test_posix_spool_admission.py
tests/synaptic_host/docker_v1/test_prepared.py
```

The filename `test_publication_local_posix.py` is itself evidence that the
POSIX-ness of the default backend is already treated as a variant rather than an
invariant.

---

## 7. Test baseline from a real run in this worktree

`python` and `python3` on PATH are intercepted by the rtk hook, which returned
`Pytest: No tests collected`. This is the recorded rtk gotcha
(`.codex/pact/memory.md:20`). Using the absolute interpreter path bypasses it.
Two environment prerequisites were supplied read-only; **nothing was installed and
no file was written**:

- `PYTHONPATH` must include the repo root and `synaptic-tuner/`, because
  `synaptic_tuner` is not pip-installed in the conda environment. Without it:
  `ModuleNotFoundError: No module named 'synaptic_tuner'` at
  `tests/synaptic_host/docker_v1/conftest.py:9`.
- `test_docker_staging.py` shells out to git at import time and hits the
  `safe.directory` guard on this Windows drive. Supplied via `GIT_CONFIG_*`
  environment variables, not by writing git config.

Exact command (measured on CPython 3.12.9; `python` must resolve to that conda environment's interpreter):

```
cd /mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean && \
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0='*' \
PYTHONPATH="/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean:/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean/synaptic-tuner" \
python -m pytest \
  tests/synaptic_host/test_artifact_destinations.py tests/synaptic_host/test_artifact_spool.py \
  tests/synaptic_host/test_local_artifact_destination.py tests/synaptic_host/test_publication_authority.py \
  tests/synaptic_host/test_publication_composition.py tests/synaptic_host/test_publication_local_posix.py \
  tests/synaptic_host/test_publication_store.py tests/synaptic_host/test_docker_publication.py \
  tests/synaptic_host/test_docker_prepared_composition.py tests/synaptic_host/test_docker_staging.py \
  tests/synaptic_host/test_verified_artifact_source.py tests/synaptic_host/local_io_v1/test_boundaries.py \
  tests/synaptic_host/local_io_v1/test_config.py tests/synaptic_host/local_io_v1/test_filesystem.py \
  tests/synaptic_host/local_io_v1/test_posix_ext4.py tests/synaptic_host/local_io_v1/test_posix_spool_admission.py \
  tests/synaptic_host/docker_v1/test_prepared.py -q -rs --tb=no
```

Environment: `platform linux -- Python 3.12.9, pytest-9.0.2, pluggy-1.5.0`,
rootdir `/mnt/f/Code/Toolset-Training`, configfile `pytest.ini`.

Verbatim summary line:

```
============ 12 failed, 400 passed, 11 skipped, 1 warning in 10.20s ============
```

**Every publication, destination, and local-IO test passed**, including the two
real end-to-end POSIX publication tests in `test_publication_local_posix.py`.

The 12 failures are pre-existing environment and platform artifacts of running a
Windows-targeted Host on Linux. They are not regressions and not in the registry
core:

| Count | Cause | Evidence |
|---|---|---|
| 4 | `ValueError: prepared Docker stage requires a Windows drive path` | `synaptic_host/docker_v1/prepared.py:47` |
| 3 | `ValueError: one absolute Windows Docker executable is required` | `docker_prepared_composition.py:124`, gate at `:93-97` requires `os_name == "nt"` |
| 5 | `ValueError: exact locked Git object is unavailable` | `docker_staging.py:1045`; submodule gitlink object not resolvable from this worktree |

Version note: installed pytest is 9.0.2 while the engine extra declares
`pytest>=8,<9`. UNVERIFIED whether that contributes to any failure; all failure
messages point at platform or git causes, not pytest API.

### 7.1 Platform-conditioned skips — directly relevant

Eight Windows-only tests skip on this Linux host, all in
`tests/synaptic_host/test_docker_staging.py` with
`skipif(os.name != "nt", reason="Windows cleanup policy")` at `:47, 72, 95, 129,
162, 196, 215, 251`. These are the Windows handle-semantics proofs, including the
two rename-out-blocking tests.

Three fixture-gated skips in `local_io_v1/test_posix_ext4.py` (`:53, 273, 369`)
require `--b42-ext4-root` from a canonical WSL ext4 checkout
(`local_io_v1/conftest.py:87`).

**The asymmetry that matters for TEST-phase planning:** the only end-to-end local
publication proofs, `test_publication_local_posix.py:173` and `:209`, are
themselves guarded by `skipif(os.name != "posix")`. On native Windows there is
currently **no equivalent test at all**. The same holds for
`test_artifact_spool.py:631` and the nine tests in
`local_io_v1/test_posix_spool_admission.py:24`, which is gated on Linux
specifically.

---

## 8. Success criteria for the acceptance smoke

Concrete, code-derived criteria the closure must satisfy.

**Five artifacts, exact roles, exact order.** The outcome type asserts both the
count and the role tuple:

```
synaptic_host/docker_execution.py:186-194
    (self.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED) != (len(self.verified_artifacts) == 5)
    ... tuple(item.role for item in self.verified_artifacts) != (
        "final_model", "tokenizer", "training_lineage",
        "training_metrics", "workload_record",
    )
```

The same tuple is enforced on the verification result at
`docker_execution.py:683-686`. Note that the smoke input
`training/smokes/docker-sft.json` declares only two `required_kinds`,
`final_model` and `training_lineage`; the five-role tuple is the Host-side
verification contract, not the training-input declaration. The architect should
confirm that distinction is intended.

**Verification precedes publication.** Publication is only reachable from phase
`ARTIFACTS_VERIFIED` (`docker_execution.py:1105`), and the invalid diagnostics are
a closed set: `ARTIFACT_INVENTORY_MISSING`, `ARTIFACT_INVENTORY_INVALID`,
`ARTIFACT_INTEGRITY_INVALID`, `ARTIFACT_SEMANTIC_INVALID`
(`docker_execution.py:691-695`).

**A publication record must exist.** `DockerPreparedRunOutcomeV1.published`
(`:256-258`) is true only when `publication_id` or `publication_state` is set, and
both are set only through `from_publication` (`:232-250`), which additionally
requires the result's run to equal the record's run and the result's
`destination_ref` to equal the expected one (`:240-243`). A smoke that ends with
`published == False` has not closed this task.

**Replay must not duplicate.** `DockerPublicationCompositionV1.publish`
(`docker_publication.py:381-409`) re-reads the durable record and the configuration
and refuses on any drift: it compares `request`, `record`, a freshly loaded
`fresh` record, the phase, the run ref, the destination ref, and the current
configuration, raising `"Docker publication composition differs from the run"` on
mismatch. The store side enforces uniqueness through
`publication_records_v1` with unique `publication_id` and `record_digest`
(`publication_store.py:162-185`) and compare-and-swap transitions (`:407`).

**Acceptance evidence should therefore be:** one prepared run reaching
`ARTIFACTS_VERIFIED` with exactly the five roles, a publication record written
with a `publication_id`, `published == True`, and an identical rerun producing no
second container and no second publication record.

---

## 9. Options for the architect

Three options, each with its trade-off in one sentence. All three assume Gap A
(wiring `compose_docker_publication_v1` into `docker_training.py`) is closed
regardless, since no option publishes anything without it.

### Option A — Windows port reproducing the existing commit protocol on NTFS (RECOMMENDED, minimal)

Implement a `WindowsRetainedHandlePortV1` satisfying the existing
`PosixFilesystemPortV1` Protocol (`filesystem.py:300-331`) using the `NtCreateFile`
handle-relative primitives already proven in `docker_staging.py:471-503`, plus
`CreateHardLinkW` to reproduce the link-then-unlink commit. Make
`publication_composition.py:433` platform-selected using the `os.name == "nt"`
pattern from `security.py:533-546`. Relax the two platform gates
`_require_posix` (`filesystem.py:581-584`) and `_require_linux_admission`
(`:586-589`) to admit a Windows family, and supply a Windows admission primitive
in place of `flock`.

**Trade-off:** it is the only option that leaves every shared invariant, the signed
`registry_digest` evidence, and all 400 currently-passing tests untouched, at the
cost of requiring NTFS and of demanding a real answer to the directory-durability
gap C1.

**Why it is minimal under the stated constraints:** it adds no Docker-specific
destination model, no downloader, no cache framework, no compatibility layer, no
database table, and no legacy composition fallback. It uses the injection seam the
code already provides and the platform-selection pattern the repo already proved.

### Option B — generalize the shared commit evidence

Replace the `nlink` 1-2-1 proof in `local_io_v1/model.py:695-697, 748-750, 978,
1092-1096` and `artifact_spool.py:115-120` with an abstract commit-proof type that
both a POSIX and a Windows backend can satisfy differently.

**Trade-off:** it is architecturally cleaner and removes the NTFS dependency, but
it edits the shared durability contract and the composition of signed evidence,
which puts the entire POSIX publication path and its passing tests at risk for a
gain that only matters if a non-hardlink backend is ever needed.

### Option C — a second registered local adapter for Windows

Register a second adapter, for example `host.local.windows/v1`, alongside
`host.local/v1`, with its own destination declaration and its own commit protocol.

**Trade-off:** the registry admits it with zero changes (proven by
`artifact_destinations.py:524-545` and the multi-adapter tests at
`test_artifact_destinations.py:180-190`), but it still requires changing line 433
because `LocalArtifactDestinationV1` demands the concrete `LocalFilesystemV1` type
(`local_artifact_destination.py:580`), and it leaves two divergent local
publication semantics to maintain and two evidence shapes to reconcile.

**Recommendation: Option A.** Option C buys nothing that A does not, because both
must change line 433, and C adds a second semantics to maintain. Option B is the
right long-term shape but is disproportionate to closing one platform.

---

## 10. Open questions for the architect

1. **Directory durability (gap C1) has no in-repo precedent and must be ruled on.**
   Either accept a documented weaker barrier on Windows, or design one, for example
   by flushing a volume handle. The POSIX path performs four durability points
   (`filesystem.py:3009, 3034, 3057` and the journal fsyncs at `posix.py:600, 745,
   759, 762, 783`); the Windows equivalent must state which of them it preserves.
2. **Spool admission (gap C4).** The single-writer guarantee is a crash-released
   `flock` on a directory descriptor. What is the Windows equivalent, and does the
   crash-release property survive? Note this is gated on Linux specifically, not
   POSIX generally, so even macOS is currently excluded.
3. **The five-role tuple versus the smoke's two `required_kinds`.** The Host asserts
   five roles (`docker_execution.py:186-194`) while `training/smokes/docker-sft.json`
   declares `final_model` and `training_lineage`. Confirm the smoke will actually
   produce all five before treating the smoke as the acceptance gate.

---

## 11. Notes and caveats

- **Secretary memory query — answered, zero coverage.** I queried the secretary for
  prior memories on the publication registry and authority, `local_io_v1` ports,
  Windows staging and cleanup, and prepared Docker activation with the
  five-artifact criteria. The secretary scanned all 183 rows read-only and found
  **no memories matching any of the four areas.** No memory ID is cited for any
  finding in this document; every claim above rests on live files read in this
  worktree. Two keyword near-hits on "activation" and "prepared" are
  neural-network and SFT-dataset subjects and were deliberately not pulled in.

  One **adjacent-only** lesson exists and is recorded here because it bears on the
  Windows port design, not on any finding above. Memory `7bca2b0a7cff`
  (2026-06-15): path resolvers should compare host-agnostic repo-relative POSIX
  suffixes to sidestep the `F:\` versus `/mnt/f` split, and should return a skip
  rather than a guess on an ambiguous match. This is relevant because production
  orchestration is Windows Host Python while WSL translates mount paths, so a
  Windows publication port will meet the same dual-view path problem. Treat it as
  adjacent guidance, not as evidence about publication.
- **`bin/search` first-rule.** The repo requires `bin/search` before grep. It was
  invoked first and did not return within 120 seconds in this clean worktree, most
  likely because no knowledge-graph index is warm here. All subsequent searching
  used scoped, file-targeted greps over modules named in the dispatch, under the
  sanctioned `EHR_SEARCH_OK=1` bypass. No exploratory fan-out search was performed.
- **CLAUDE.md.** It exists and is tracked in this worktree, contrary to the
  dispatch note. Nothing here wrote to it or to any skill mirror.
- **UNVERIFIED items.** Whether CPython on Windows populates `st_dev`, `st_ino`,
  and `st_nlink` well enough to construct a valid `LocalFileIdentityV1`; whether
  the pytest 9.0.2 versus `>=8,<9` mismatch affects any result; and all Windows
  runtime behaviour described in section 5, which is read from source and from
  skipped tests, since no Windows host was available in this WSL worktree.
- No Docker, GPU, network, paid, or git-write operation was performed.
