# Native-Windows Artifact Publication Closure — Architecture

Phase: ARCHITECT. Feature: close native-Windows artifact publication for the
prepared Docker activation path. Status: decision-complete. No application code,
test, or configuration was changed by this phase.

Worktree: `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean`
Branch `feat/submodule-cloud-api-v1-host-clean` at `85b922fc`.
Engine submodule `synaptic-tuner` gitlink `aec998ee` — **not changed by this design.**

Upstream: `docs/preparation/native-windows-publication-closure.md` (PREPARE, task #8).

All paths below are relative to that worktree root unless shown absolute.

---


> **Citation baseline.** Every `file.py:N` citation in this document is against
> the host tree at commit `85b922fc`, the state this design was written from, and
> the engine submodule at `aec998ee`. CODE-phase edits shift these numbers: as of
> this revision `filesystem.py` and `docker_training.py` are both modified in the
> working tree, and `filesystem.py` line numbers past `_is_directory` run about
> nine lines higher there than they do here. Verify a citation with
> `git show 85b922fc:<path>`, not against the working tree. Checking against a
> live-edited file produces false mismatches that look like documentation errors.
> Three files are new in this commit and have no state at that baseline:
> `synaptic_host/local_io_v1/windows.py`,
> `tests/synaptic_host/local_io_v1/test_windows_port_contract.py` and
> `tests/synaptic_host/test_publication_local_windows.py`. Citations to them,
> including R-7's `windows.py:833` and `windows.py:628`, are against the working
> tree at commit time, and `git show 85b922fc:<path>` reports
> `Not a valid object name` for them by construction.

## 1. Executive summary

The closure is **Option A with one substituted primitive**. The preparer's shape is
correct and is adopted: a Windows handle-relative port beneath the existing
`LocalFilesystemV1`, platform selection at `publication_composition.py:433`, and
wiring `compose_docker_publication_v1` into `docker_training.py`. Three things
changed after verification.

**1. The commit primitive is not `CreateHardLinkW`.** The preparer recommended it.
`CreateHardLinkW` is path-based, and the entire port exists to be handle-relative,
so a path-based link would open a TOCTOU hole in the one operation the protocol
uses as its commit proof. The correct primitive is `NtSetInformationFile` with
`FileLinkInformationEx`, which takes a `RootDirectory` handle plus a
single-component name — the exact analogue of `os.link(..., dst_dir_fd=)`. See
ruling (c).

**2. The 128-bit file id needs no lossy reduction.** This was my pre-registered
most-likely-wrong item and it is **retired, disproved**. `LocalFileIdentityV1`
constrains its integer fields only by `type(value) is int and value >= 0`
(`local_io_v1/model.py:316-320`), and `canonical_bytes_v1` serialises through
`json.dumps` (`local_io_v1/model.py:161`), which renders arbitrary-precision
Python integers exactly. A 128-bit `FileId` therefore travels into
`registry_digest` losslessly. The residual on identity is confined to the
synthesised `mode`, not to the file id.

**3. Publication must be constructed lazily, not at line 846.** `reconcile` is a
one-cut-per-call state machine (`docker_execution.py:1103-1129`): from
`PROCESS_SUCCEEDED` it verifies artifacts, writes `ARTIFACTS_VERIFIED`, and
**returns without publishing**. Publication happens on the *next* call. Building
the publication eagerly at `docker_training.py:846` would acquire the spool
admission lease on every activation, including submits and observations that can
never publish. See ruling (e).

**The one genuine semantic gap survives and is ruled, not softened.** Windows has
no equivalent of `os.fsync` on a directory descriptor. `fsync_directory` must
never degrade to a silent no-op: that would leave every shared invariant passing
while destroying the crash-safety property the protocol exists to provide, and the
loss would be invisible until a real crash. The ruling is to probe the barrier at
port construction and **fail closed** with `CAPABILITY_UNAVAILABLE` if it is
unavailable. See ruling (a) and residual R-1.

**Nothing forbidden is required.** No Docker-specific destination model, no
downloader, no generic cache framework, no compatibility layer or shim, no new
database table, no legacy composition fallback. No blocker escalation is needed.

---

## 2. System context

```
   Windows Host Python (production)
  +---------------------------------------------------------------+
  |  _activate_docker_training_v1        docker_training.py:675    |
  |      |                                                          |
  |      +-- DockerPreparedCompositionV1        :846  (Gap A here)  |
  |      +-- compose_docker_publication_v1   docker_publication.py:442
  |               |                                                 |
  |               +-- compose_host_publication_v1                    |
  |                       publication_composition.py:395             |
  |                       |                                          |
  |                       +-- LocalFilesystemV1(<PORT>, storage) :433 (Gap B)
  |                       |        ^                                 |
  |                       |        +-- PosixRetainedDirfdPortV1  (Linux, unchanged)
  |                       |        +-- WindowsRetainedHandlePortV1 (NEW)
  |                       |                                          |
  |                       +-- acquire_local_artifact_spool_v1        |
  |                       +-- ImmutableArtifactDestinationRegistryV1 |
  |                       +-- PublicationOperationsV1  (engine, unchanged)
  +---------------------------------------------------------------+
              |                                    |
              v                                    v
      docker.exe over named pipe            NTFS volume
      (container: network-disabled,         (spool + control + data roots)
       credential-free — unchanged)
```

Boundaries this design does not cross:

- The engine submodule at `aec998ee`. Read for ruling (f); not modified.
- The container. Publication is entirely Host-side and post-verification. The
  container's network and credential surface is untouched.
- The POSIX path. `local_io_v1/posix.py` is not edited at all.

---

## 3. The two gaps, verified

### 3.1 Gap A — publication is unwired

`docker_training.py:846-848` constructs the composition with three keywords:

```
    composition = DockerPreparedCompositionV1(
        repository=repository, builder=builder, clock=clock,
    )
```

`publication` therefore takes its `None` default
(`docker_prepared_composition.py:297`), and `reconcile` returns early at
`docker_execution.py:1105-1107`. `DockerPreparedRunOutcomeV1.published`
(`docker_execution.py:256-258`) stays `False`.

Everything `compose_docker_publication_v1` needs is already in scope at that
point in `_activate_docker_training_v1`:

| Parameter | Source | Evidence |
|---|---|---|
| `context` | function parameter | `docker_training.py:677` |
| `repository` | local binding | `docker_training.py:817` |
| `request` | local binding | `docker_training.py:843-845` |
| `clock` | function parameter | `docker_training.py:678` |
| `spool_root_ref` | new module constant `"artifact-publication-spool"` | declared at `training/storage.json:35` |
| `registration_builders` | `(build_local_artifact_destination_registration_v1,)` | `local_artifact_destination.py:567-576` |

The publication configuration is **not** a new plumbing surface:
`_configuration_for_request` (`docker_publication.py:342-351`) reads
`artifacts.json` and `storage.json` out of the already-built prepared stage.
Gap A is a pure code-wiring change with zero configuration change.

### 3.2 Gap B — the port is Linux-bound

`publication_composition.py:433` reads:

```
        filesystem = LocalFilesystemV1(PosixRetainedDirfdPortV1(), storage)
```

`PosixRetainedDirfdPortV1.__init__` raises `CAPABILITY_UNAVAILABLE`
(`local_io_v1/posix.py:107-108`) unless `detect_posix_capability_v1` reports
available, which requires `platform_value.startswith("linux")`
(`local_io_v1/posix.py:73`). A second, independent gate exists in the coordinator:
`_POSIX_PLATFORMS = ("linux", "darwin", "freebsd", "openbsd", "netbsd")`
(`local_io_v1/filesystem.py:72`), consulted by `_require_posix`
(`:581-584`) and `_require_linux_admission` (`:586-589`). Both gates must widen.

---

## 4. Component architecture

### 4.1 What is new, what changes, what is untouched

| Component | Disposition |
|---|---|
| `WindowsRetainedHandlePortV1` | **NEW.** Satisfies `PosixFilesystemPortV1` in full (all 21 methods). |
| `detect_windows_capability_v1` | **NEW.** Mirrors `detect_posix_capability_v1`. Fails closed. |
| `publication_composition.py:433` | **MODIFIED.** Two-branch port factory. |
| `filesystem.py:72, 581-589` | **MODIFIED.** Platform membership + gate rename. |
| `docker_training.py` activation | **MODIFIED.** Lazy publication construction + close. |
| `local_io_v1/posix.py` | **UNTOUCHED.** |
| `local_io_v1/model.py` invariants | **UNTOUCHED.** All satisfied on NTFS. |
| `artifact_spool.py` | **UNTOUCHED.** `nlink == 1` is satisfied. |
| `artifact_destinations.py` registry | **UNTOUCHED.** Admission is by `adapter_ref` only. |
| `local_artifact_destination.py` | **UNTOUCHED.** Adapter reused as-is. |
| Engine `synaptic-tuner` | **UNTOUCHED.** |

The registry never learns that a platform exists. Admission is by `adapter_ref`
string with no platform check (`artifact_destinations.py:524-545`), and the sole
production adapter ref stays `host.local/v1`. Provider neutrality is preserved by
not touching the registry at all.

### 4.2 Why the port is the seam, and not a new filesystem class

`LocalArtifactDestinationV1`'s builder requires the concrete type:

```
    local_artifact_destination.py:579-580
        type(filesystem) is not LocalFilesystemV1
```

So a Windows implementation cannot be a sibling filesystem class. It must go in
*beneath* `LocalFilesystemV1` as a port. `LocalFilesystemV1.__init__` already
accepts an arbitrary port and an overridable platform string
(`filesystem.py:556-566`), and `capability()` already computes a `windows`
platform family (`:557-579`). The seam exists; only line 433 fails to use it.

---

## 5. Rulings

### (c) Hardlink commit proof on NTFS — REPRODUCIBLE

**Ruling: the `nlink` 1 → 2 → 1 proof is reproduced faithfully on NTFS. No shared
invariant changes. Option A stands; Option B is not needed.**

The protocol being reproduced is the create-commit sequence at
`filesystem.py:3009-3070`:

| Step | Call | Assertion afterwards |
|---|---|---|
| 1 | `fsync_file(opened)` `:3009` | size + sha256 re-verified by re-open `:3013-3020` |
| 2 | journal `FILE_DURABLE` `:3022-3031` | — |
| 3 | `link_at(parent, staging, final)` `:3033` | — |
| 4 | `fsync_directory(parent)` `:3034` | `_same_node`, `nlink == 2`, `changed_ns` monotonic `:3036-3043` |
| 5 | journal `LINKED` `:3045-3053` | `model.py:978` requires `nlink == 2` |
| 6 | `unlink_at(parent, staging)` `:3055` | — |
| 7 | `fsync_directory(parent)` `:3056` | `_is_regular_single` i.e. `nlink == 1`, `changed_ns` monotonic `:3057-3061` |
| 8 | journal `COMMITTED` `:3063-3070` | — |

**Primitive substitution.** Use `NtSetInformationFile` with
`FileLinkInformationEx` for step 3 and the existing
`FILE_DISPOSITION_INFO_EX` / `FILE_DISPOSITION_DELETE` pattern
(`docker_staging.py:811-816`) for step 6. Both are handle-relative:
`FILE_LINK_INFORMATION` carries a `RootDirectory` handle plus a single-component
name, matching `os.link(..., src_dir_fd=, dst_dir_fd=)` at `posix.py:749-755`.
**Do not use `CreateHardLinkW`**: it resolves a full path, which reintroduces the
exact redirect window the retained-handle design eliminates. This is a deliberate
departure from the preparer's section 9 wording and it is the safer primitive, not
merely a different one.

**`LocalFileIdentityV1` construction.** The type is a plain 7-integer record
(`model.py:308-333`). Field-by-field mapping:

| Field | Windows source | Faithful? |
|---|---|---|
| `nlink` | `FILE_STANDARD_INFO.NumberOfLinks` | Exact. This is the commit proof. |
| `device` | `FILE_ID_INFO.VolumeSerialNumber` (64-bit) | Exact. |
| `inode` | `FILE_ID_INFO.FileId` (128-bit) as a Python `int` | **Exact — no reduction.** |
| `size` | `FILE_STANDARD_INFO.EndOfFile` | Exact. |
| `changed_ns` | `FILE_BASIC_INFO.ChangeTime` | Exact, 100 ns granularity. |
| `modified_ns` | `FILE_BASIC_INFO.LastWriteTime` | Exact, 100 ns granularity. |
| `mode` | **Synthesised constant** | See below. |

On the file id: `__post_init__` (`model.py:316-320`) validates only
`type(value) is int and value >= 0`, with no bit-width bound, and
`canonical_bytes_v1` (`model.py:161`) serialises via `json.dumps`, which writes
Python big integers in full decimal. The 128-bit id reaches `registry_digest`
without loss. `docker_staging.py:393, 414-415` already reads `FILE_ID_INFO` in
this repo, so the primitive is proven here.

On timestamps: convert `FILETIME` (100 ns ticks since 1601) to nanoseconds since
the Unix epoch, clamped at zero so the non-negative constraint always holds. The
monotonicity assertions at `:3042` and `:3060` use strict `<`, so two operations
landing in the same 100 ns tick compare equal and pass. No residual here.

On `mode`: Windows has no POSIX mode. The port synthesises two fixed constants,
`stat.S_IFREG | 0o600` for files and `stat.S_IFDIR | 0o700` for directories.

An earlier draft of this section justified that by claiming every consumer in
shared code inspects only the file-type nibble `mode & 0o170000` and never the
permission bits. That claim is false. Two consumers compare the whole value, and
one of them was already cited in the list offered as proof of the opposite.
Corrected, the consumers split into two groups.

*Nibble-only*, tolerant of any permission bits: `model.py:350`,
`model.py:695-697` (`S_ISREG` / `S_ISLNK` on a borrow), `model.py:748`,
`model.py:978`, `model.py:1094-1096` (`stat_is_regular_single_v1`),
`filesystem.py:399-400` (`_is_directory`), `filesystem.py:403-404`
(`_is_regular_single`), `filesystem.py:407-414` (`_is_regular_pair`), and
`artifact_spool.py:103-112`, whose own `_same_node` reduces both sides through
`stat.S_IFMT`.

*Full-mode*, comparing the whole value: `filesystem.py:417-430` — the `_same_node`
belonging to this module, which carries `mode` as one member of a five-field
tuple — and `model.py:747`, `first_identity != second_identity`, which is full
dataclass equality. Both were mis-shelved in the earlier draft. `filesystem.py`'s
`_same_node` was listed as nibble-only, and the `model.py` citation pointed at
`748`, the nibble check that sits one line *below* the full-equality check at
`747`.

The ruling survives, but not for the reason first given. A fixed constant per file
type makes both sides of every full-mode comparison equal, so those comparisons
pass. They are not indifferent to the permission bits; they are satisfied by the
bits being identical on both sides. The real constraint is therefore stronger than
"constant nibble":

> The synthesised `mode` must be byte-identical for every stat of every file of
> the same type, and no Windows file attribute may leak into the permission bits.
> `FILE_ATTRIBUTE_READONLY` is the tempting one to map onto `0o400`. Do not.

Both full-mode comparisons are load-bearing, on two different paths. On the commit
path, `filesystem.py:3040` asserts `_same_node(final_linked, staging_linked)`. On
the recovery path, `recover_create` (`filesystem.py:3195`) compares
`staging_identity == evidence` (`:3259`) and `final_identity == staging_identity`
(`:3268`), where `evidence` is `latest.file_identity` (`:3253`) read back from the
durable journal via `snapshot_journal` on `root_authority.control_directory`
(`filesystem.py:3101-3108`).

The recovery path sets the outer bound on the constraint, and that bound is wider
than a single process. `recover_create` exists to run after a process died
mid-mutation, so it compares a `mode` written to disk by an **earlier** process
against one synthesised by the current one. The two constants are consequently a
durable part of the on-disk journal format, not an in-run convention. Changing
either value in a later build makes every journal record written by an older build
recover as `CONFLICT` where it should have been `INDETERMINATE`, silently turning
a resumable mutation into a failed one. Treat the constants as versioned: if they
ever have to change, that is a journal format change, not an edit to a literal.

Access control on Windows is carried by the SDDL DACL the repo already applies in
`security.py:250-270`, validated ACE by ACE at `:340-390`. The synthesised value
is also hashed into `registry_digest` through `identity.canonical()`
(`local_artifact_destination.py:171-188`), so it **must be a named module
constant, documented as part of the evidence contract, and never derived from an
ACL or an umask**. Deriving it would make both the digest and the recovery
comparison vary with directory permissions. Residual R-2.

**Cross-platform digest reproducibility is a non-issue.** `registry_digest` is a
within-run authenticated witness sealed into a lookup outcome or tombstone
(`local_artifact_destination.py:391-424, 452-480`). It is never compared against a
digest computed on another host. Two Linux hosts already disagree on `device` and
`inode`; so do two runs on one host after a file is recreated. Windows introduces
no new property. The preparer's gap C6 is closed as not-a-gap.

**NTFS is required.** `FILE_ID_INFO` and `FileLinkInformationEx` are not available
on FAT or exFAT. The port must verify the volume at the first retention of each
root, before any mutation through it, reusing the `_win_require_ntfs` pattern at
`security.py:284-293`, and raise `CAPABILITY_UNAVAILABLE` otherwise. Section 6.2
explains why this cannot be a construction-time check and why per-root is the
stronger placement.

### (a) Directory durability on Windows — FAIL CLOSED, DO NOT NO-OP

**Ruling: three of the four durability points are preserved exactly. The fourth,
directory-entry durability, is preserved as a probed barrier that fails closed at
port construction. `fsync_directory` must never become a silent no-op.**

The four durability points and their disposition:

| # | POSIX point | Evidence | Windows disposition |
|---|---|---|---|
| D1 | `fsync` of the artifact file | `filesystem.py:3009` via `posix.py:553` | **Preserved exactly.** `FlushFileBuffers(file_handle)`, already bound at `security.py:174-175` and used at `:469`. |
| D2 | `fsync` of the parent directory after link | `filesystem.py:3034` | Probed barrier. See below. |
| D3 | `fsync` of the parent directory after unlink | `filesystem.py:3056` | Probed barrier. See below. |
| D4 | journal `fsync` of record file then control directory | `posix.py:745, 759, 762, 783` | File half preserved exactly; directory half is the same probed barrier. |

D2, D3 and the directory half of D4 are the same operation: make a namespace
mutation durable. POSIX needs an explicit `fsync(dirfd)` because POSIX does not
guarantee a directory entry is durable once the file's data is synced. NTFS
records namespace mutations in `$LogFile` and recovers them as a unit, so the
ordering and atomicity properties the protocol depends on are provided by the
filesystem rather than by an explicit call.

That difference is a reason to be careful, not a licence to skip the call. The
design rule is:

1. `WindowsRetainedHandlePortV1.fsync_directory` issues a real barrier:
   `FlushFileBuffers` on the retained directory handle.
2. `detect_windows_capability_v1` **probes that barrier at port construction**, on
   a handle it opens for the purpose, and reports `UNAVAILABLE` if the call fails.
   `WindowsRetainedHandlePortV1.__init__` then raises
   `LocalIOErrorV1(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)`, exactly mirroring
   `posix.py:106-108`.
3. There is **no fallback branch that returns success without a barrier.** A
   silent no-op would satisfy every `nlink` and `changed_ns` assertion in
   `filesystem.py:3036-3061` while removing the crash-safety guarantee, and the
   loss would only surface after a real power failure. Fail loudly at startup
   instead of quietly at the worst moment.

**Residual R-1 (named, bounded).** If the directory-handle flush succeeds, the
Windows barrier still rests partly on the NTFS log rather than on a POSIX-style
synchronous directory `fsync`. The design does not claim these are bit-equivalent
guarantees. R-1 is the documented difference: *directory-entry durability on
Windows is NTFS-log-backed and is not independently proven by this closure.* The
TEST phase must not assert crash-durability on Windows; it asserts the barrier is
*called and succeeds*, which is what this design controls. Elevating R-1 requires
a power-loss rig, which is out of scope.

### (b) Spool admission on Windows — ASYMMETRIC SHARE MODE ON THE DIRECTORY HANDLE

**Ruling: replace the non-blocking `flock` with a second, asymmetrically shared
open of the spool data directory itself. Single-writer and crash-release are both
preserved, and no new namespace entry is created.**

The POSIX mechanism is a non-blocking `flock(LOCK_EX | LOCK_NB)` on a directory
descriptor (`posix.py:401-405`), mapping `EAGAIN`/`EWOULDBLOCK` to `ROOT_IN_USE`.
Two properties matter: exactly one writer, and automatic release when the holding
process dies.

The Windows analogue is share-mode exclusion. A second opener that the existing
handle's `ShareAccess` does not permit fails with `ERROR_SHARING_VIOLATION` (32) —
the same error the repo already asserts for rename-blocking at
`tests/synaptic_host/test_docker_staging.py:112-114` — which maps to
`ROOT_IN_USE`, matching the POSIX mapping exactly. Crash-release holds because
Windows closes every handle when a process terminates, so the exclusion is
released by the kernel, not by cleanup code. This is the same crash-release
property as `flock`, and it is mandatory rather than advisory, which is strictly
stronger.

**The admission target is the directory, not a file.**
`acquire_single_root_admission` passes `authority.data_directory` to the port
(`filesystem.py:753`), so `acquire_directory_admission` receives the spool data
root directory, exactly as the POSIX port locks the directory fd.

**A dedicated admission file is forbidden here, and this is load-bearing.** An
earlier shape for this ruling placed a lock file inside the spool root. That is
wrong: `LocalArtifactSpoolV1._startup_reclaim` (`artifact_spool.py:193-217`)
enumerates every entry in the spool root and **raises**
`LocalArtifactSpoolCodeV1.INVALID` for any name failing
`_FILENAME_RE = ^synaptic-spool-v1-[0-9a-f]{64}\.blob$` (`:29`, checked at
`:204-205`), and again for any entry failing `_valid_file` (`:209-210`). There is
no skip path. A lock file would either abort every startup or, if named to pass
the regex, be treated as a reclaimable artifact. Locking the directory handle adds
no entry, so `artifact_spool.py` needs **no change at all**.

**The constraint the access pair must satisfy.** The admission handle must be
opened so that (i) a second admission open is denied, and (ii) the port's own
subsequent directory opens still succeed. Concretely: the admission handle
requests a write-flavoured access the normal opens do not request, and shares only
the flavours the normal opens do request. The normal handle-relative opens in this
repo request `FILE_READ_ATTRIBUTES | SYNCHRONIZE | FILE_LIST_DIRECTORY` with
`_FILE_SHARE_READ_WRITE = 0x3` (`docker_staging.py:481-485, 193`), which gives the
coder both halves of the pair to satisfy.

Windows share-mode arithmetic is a runtime property and is **not** verified by
this design, which reads from source only. S4 must confirm the exact
`DesiredAccess` / `ShareAccess` pair on a real Windows host before the port is
considered complete. Residual R-4.

`RetainedDirectoryAdmissionV1` is constructed identically to the POSIX path
(`posix.py:409-415`): a `secrets.token_hex(16)` lease ref, the retained node
digest, the process id, and the process instance ref. No model change.

### (d) Platform selection at line 433 — TWO-BRANCH FACTORY, NOT A COMPATIBILITY LAYER

**Ruling: introduce a module-private factory in `publication_composition.py` that
selects the port on `os.name == "nt"`, mirroring `security.py:533-546`.**

```
def _local_filesystem_port_v1():
    if os.name == "nt":
        from .local_io_v1.windows import WindowsRetainedHandlePortV1
        return WindowsRetainedHandlePortV1()
    from .local_io_v1.posix import PosixRetainedDirfdPortV1
    return PosixRetainedDirfdPortV1()
```

Line 433 becomes `filesystem = LocalFilesystemV1(_local_filesystem_port_v1(), storage)`.

This is not a compatibility layer under the stated constraint. It adds no
re-export, no dual signature, no deprecated wrapper, and no degradation path:
each branch constructs the real port for its own platform, and neither branch can
serve the other. On an unsupported platform such as macOS the constructed port
raises `CAPABILITY_UNAVAILABLE`, which is the behaviour today. The pattern is the
one this repo already uses for `_create_private_directory` (`security.py:533-540`),
`_validate_private_directory` (`:544-546`), key creation (`:599-607`), and key
read (`:680`).

**Import discipline.** The import is inside the branch, so a Linux process never
imports the `ctypes.WinDLL` module and a Windows process never imports `fcntl`.
`docker_staging.py:327-330` already guards its `WinDLL` binding on `os.name != "nt"`.

### (e) Wiring `compose_docker_publication_v1` — LAZY, PHASE-GATED, CLOSED

**Ruling: construct the publication only when the loaded phase is already
`ARTIFACTS_VERIFIED`, and close it in a `finally`. `publication=None` stops being
the production default for the publish cut only.**

Three facts force this shape. Two of them were independently corroborated by
coder-wiring during CODE, and the corroboration is recorded here because it turns
the design's reasoning into an enforced constraint rather than a convention:
`compose_docker_publication_v1` refuses outright unless the loaded phase is already
`ARTIFACTS_VERIFIED` (`docker_publication.py:451` calls `_verified_record`, which
raises `ARTIFACTS_UNVERIFIED` at `:132-139`), and `DockerPreparedRunServiceV1`
rejects anything that is not exactly a `DockerPublicationCompositionV1`
(`docker_execution.py:990-993`). A lazy, phase-gated construction is therefore not
merely the tidy choice; an eager one raises, and a duck-typed stand-in is refused.

1. **`reconcile` is one cut per call.** From `PROCESS_SUCCEEDED` it verifies and
   writes `ARTIFACTS_VERIFIED`, then returns (`docker_execution.py:1112-1129`).
   It publishes only when the phase is *already* `ARTIFACTS_VERIFIED` on entry
   (`:1104-1110`). The publish cut is therefore always a separate call whose entry
   phase is known before the publication is needed.
2. **Nothing closes the publication for you.** `DockerPreparedCompositionV1` has
   no `close` and never calls one; `DockerPreparedRunServiceV1` only stores the
   object (`docker_execution.py:1014`). The publication owns a spool root
   authority, an admission lease, and a SQLite store, so the creating caller must
   release them.
3. **Eager construction would acquire the lease on every activation.** Submits and
   observations would take the spool admission they can never use, and would fail
   on a host where the spool root is not yet provisioned.

The activation path at `docker_training.py:846-871` becomes:

```
    admission = builder.prepare_admission(request)          # was composition.prepare_admission
    ... unchanged create / load ...
    current = repository.load_docker_run_mutation(run.project_ref, run.run_id)
    ...
    if current.phase in {CREATE_ADMITTED, CREATE_ATTEMPTED, CREATED}:
        outcome = DockerPreparedCompositionV1(
            repository=repository, builder=builder, clock=clock,
        ).submit(request)
    elif current.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED:
        publication = compose_docker_publication_v1(
            context=context, repository=repository, request=request, clock=clock,
            spool_root_ref=_PUBLICATION_SPOOL_ROOT_REF,
            registration_builders=(
                build_local_artifact_destination_registration_v1,
            ),
        )
        try:
            outcome = DockerPreparedCompositionV1(
                repository=repository, builder=builder, clock=clock,
                publication=publication,
            ).reconcile(request)
        finally:
            publication.close()
    else:
        outcome = DockerPreparedCompositionV1(
            repository=repository, builder=builder, clock=clock,
        ).reconcile(request)
```

`composition.prepare_admission` is a pure delegation to `self._builder`
(`docker_prepared_composition.py:313-314`), so calling the builder directly at
the admission step is behaviour-identical and removes the need for a composition
before the phase is known.

`_PUBLICATION_SPOOL_ROOT_REF = "artifact-publication-spool"` is a new module
constant in `docker_training.py`, matching `training/storage.json:35`. No
configuration file changes.

### (f) Five-role tuple versus the smoke's two `required_kinds` — NEITHER CHANGES

**Ruling: `training/smokes/docker-sft.json` does not change, and the Host
five-role assertion does not change. There is no conflict. The apparent conflict
is dead input.**

The Docker admission resolver **discards** the smoke's `required_kinds` and
substitutes the Host's own constant:

```
    docker_training.py:520-523
            artifact_policy=ArtifactPolicy(
                _ARTIFACT_ROLES,
                snapshot.training_input.artifacts.retain_checkpoints,
            ),
```

where `_ARTIFACT_ROLES` is the full five-tuple at `docker_training.py:47-50`. Only
`retain_checkpoints` is forwarded from the smoke input. The two-element array in
`training/smokes/docker-sft.json` never reaches the engine on the Docker path. The
Modal path does forward it (`modal_resolver.py:757-771`), which is why the field
exists and why removing it would be wrong.

From engine source, the SFT trainer writes all five roles unconditionally on a
successful run: `synaptic-tuner/Trainers/sft/runtime_v1.py:1420-1473` emits
`workload_record` (:1422), `training_lineage` (:1440), `training_metrics` (:1448),
`final_model` (:1456) and `tokenizer` (:1468) as straight-line calls with no
conditional branch, reached after `exit_code == 0` (:1407) and after the model and
tokenizer directories validate (:1415-1416).

The asserted **order** is a Host-side normalisation, not an engine guarantee. The
engine emits in pipeline order; `docker_execution.py:974-976` re-sorts
alphabetically by role, which yields exactly the tuple asserted at `:191-194` and
`:683-686`. This matters because a future engine reordering cannot break the Host
assertion.

**Residual R-3.** Emission is read from source; no container was run. Runtime
confirmation is deferred to the GPU smoke, and it is the **first** check in the
acceptance sequence in section 9 so the smoke fails fast on a missing role rather
than after training completes.

### (g) The WSL and POSIX path — UNCHANGED

**Ruling: `local_io_v1/posix.py` is not edited. `_POSIX_PLATFORMS` gains no
members. POSIX and WSL behaviour is byte-identical. Two tests in
`tests/synaptic_host/local_io_v1/test_filesystem.py` must be re-aimed because they
encode an invariant this closure deliberately retires; every other test in the
baseline keeps passing without modification.**

Two private methods change behaviour, so they are renamed to stop asserting the
opposite of what they enforce:

| Before | After | Change |
|---|---|---|
| `_require_posix` (`filesystem.py:581-584`), 9 call sites | `_require_retained_port` | Membership test widens from `_POSIX_PLATFORMS` to `_SUPPORTED_PLATFORMS = _POSIX_PLATFORMS + ("win32",)`. POSIX behaviour byte-identical. |
| `_require_linux_admission` (`:586-589`), 4 call sites at `:675, :718, :746, :822` | `_require_directory_admission` | Admits `linux` or `win32`. `darwin` and the BSDs stay excluded exactly as today. |

`capability()` at `:557-579` already derives `platform_family` from
`_POSIX_PLATFORMS` membership and already has a `windows` branch; widening
availability to include `win32` makes the reported family and feature set correct
for the new port without changing the POSIX result.

#### Which admission features `win32` may claim

Widening availability alone leaves `capability()` reporting `win32` as AVAILABLE
with only the three base features, because the four admission features are gated
on `startswith("linux")` at `filesystem.py:566-572`. Ruling (b) establishes that
two of those four hold on Windows, so the report would understate the port.

**Ruling: `win32` claims exactly two of the four —
`crash-released-admission` and `directory-inode-admission`. It claims neither
`exec-closed-admission` nor `nonblocking-directory-flock`.** Change the gate at
`:566` from a single `startswith("linux")` branch into two branches; `linux` keeps
all four and its reported set is byte-identical to today. Sorted totals become
seven features on Linux and five on Windows.

The split is not arbitrary. A feature string is a claim, and `features` is hashed
into the capability digest at `filesystem.py:573-579`, so an unearned entry is an
unearned piece of evidence — the same objection raised against deriving `mode`
from an ACL in ruling (c).

The two admitted features name platform-neutral *properties* that the Windows
mechanism genuinely provides. Admission is released when the process dies, because
the OS closes the handle; and admission is bound to the directory object rather
than to a path, because it is held on a retained handle.

The two refused features name POSIX *mechanisms*, not properties.
`nonblocking-directory-flock` names `flock`, which Windows does not have; the
Windows analogue is share-mode denial, and R-4 records that the exact
`DesiredAccess` / `ShareAccess` pair is still unconfirmed on a real host, so the
claim would be unverified as well as misnamed. `exec-closed-admission` names
release-on-`exec`, and Windows has no `exec`; its nearest analogue is handle
non-inheritance, which is a different guarantee the port would have to establish
separately. If a later closure wants either property on Windows, add a
Windows-named feature that says what Windows actually does, rather than reusing a
POSIX name.

**The `PosixFilesystemPortV1` Protocol name is deliberately NOT renamed in this
closure.** A Windows class satisfying a Protocol whose name says POSIX is a
misnomer, and it is recorded as follow-up F-1. It is not fixed here because the
rename is pure cosmetics that would touch the `local_io_v1` export surface and
several test imports, spending diff risk that belongs to the durability and
admission rulings. The two gate methods are renamed because their *behaviour*
changes regardless, so the rename costs nothing extra.

#### The retired invariant, and the two tests that encode it

Before this closure, `win32` was excluded from `_POSIX_PLATFORMS`, so a
`LocalFilesystemV1` on `win32` was metadata-only *even when a working port was
injected*: it reported its capability, refused every effectful operation with
`CAPABILITY_UNAVAILABLE`, and made zero calls into the port. Ruling (d) and the
gate widening above retire exactly that. Under S1, `win32` **with** a port is a
supported, available composition, and effectful calls are expected to reach the
port.

An earlier draft of this ruling claimed the whole baseline passes unmodified. That
was wrong. Two tests assert the retired invariant directly and now fail
`DID NOT RAISE` (HEAD numbering):

| Test | Line | What it pins |
|---|---|---|
| `test_windows_borrow_is_capability_unavailable_without_port_call` | `test_filesystem.py:2207` | `borrow_root` on `win32` **with** a port raises `CAPABILITY_UNAVAILABLE` and leaves `port.trace` unchanged. |
| `test_windows_is_metadata_only_and_all_effects_make_zero_port_calls` | `test_filesystem.py:2736` | Every effectful entry point on `win32` **with** a port raises and makes zero port calls. |

Both reach the win32 branch by assigning `filesystem._platform = "win32"` onto a
composition built by `_composition()`, which supplies a port. That port is the
reason they now fail: it is precisely the case S1 makes available.

**Disposition: re-aim both at the win32-with-no-port case. No other edit to that
file.** The fail-closed contract is unchanged, and it is what the re-aimed tests
assert: a `win32` composition with no port stays unavailable and refuses effects.

Two consequences a reviewer should not have to rediscover.

First, `test_filesystem.py:2764`
(`test_native_windows_composition_needs_no_port_and_reports_truthful_capability`)
already covers win32-with-no-port, but only for `capability()` and
`retain_root_authority`. The two re-aimed tests are not redundant with it: they
carry `borrow_root` and the all-effects sweep, which `:2764` never reaches. Keep
the three distinct; do not collapse them.

Second, the "makes zero port calls" assertion cannot survive the re-aim in its
present form. With no port, `filesystem._port` is `None`, so there is no `trace`
to compare against. Drop that assertion rather than fabricating a trace against
`None`. What remains, and what matters, is that the call raises
`CAPABILITY_UNAVAILABLE`. The zero-port-call property is not being relocated; it is
genuinely gone, because the composition it described is now a supported one. Its
replacement is the positive coverage in section 9.2: on `win32` with a port,
effects must reach the port.

---

## 6. Interface contracts

### 6.1 `WindowsRetainedHandlePortV1`

New module `synaptic_host/local_io_v1/windows.py`. Structural conformance to
`PosixFilesystemPortV1` (`filesystem.py:300-331`). The Protocol is never checked
at runtime; conformance is by the 21 method names and signatures below.

**The port must implement all 21. A publication-scoped subset is forbidden.**
`LocalFilesystemV1` is a general coordinator, not a publication-only object, so a
partial port makes it a partly-functional object rather than a loudly unavailable
one. A missing method raises `AttributeError`, which
`except BaseException: raise _closed(LocalIOCodeV1.IO_FAILED)` converts into a
generic `IO_FAILED` (`filesystem.py:2003-2004` is one of several such wrappers) —
a silent degradation, not the loud `CAPABILITY_UNAVAILABLE` ruling (a) requires and
exactly the degradation path ruling (d) forbids. `mkdir_at` is the method most
likely to be dropped, because its only current upstream caller
(`bundle_io_v1/bundle.py:1051` via `mkdir_borrowed` at `filesystem.py:1991-1998`)
is the bundle subsystem rather than publication. Implement it anyway.

| Method | Windows primitive |
|---|---|
| `retain_directory(absolute_path)` | Anchor open by path with `FILE_FLAG_BACKUP_SEMANTICS` + `FILE_FLAG_OPEN_REPARSE_POINT` (`docker_staging.py:441-448`), then descend component by component. Drive or UNC prefix replaces the POSIX `/` anchor (gap C3, wholly inside the port). |
| `open_directory_at(directory, component)` | `NtCreateFile` with `RootDirectory` = parent handle, `OBJ_DONT_REPARSE`, `FILE_DIRECTORY_FILE` (`docker_staging.py:471-503`). |
| `close_directory` | `CloseHandle`. |
| `list_names_at(directory, maximum)` | `GetFileInformationByHandleEx(FILE_ID_BOTH_DIR_INFO)`. Enforce `MAX_DIRECTORY_ENTRIES`. |
| `stat_at(directory, component)` | Handle-relative open + `FILE_BASIC_INFO` + `FILE_STANDARD_INFO` + `FILE_ID_INFO`. Returns `None` if absent. |
| `open_read_at` | `NtCreateFile`, `FILE_READ_DATA`, `FILE_NON_DIRECTORY_FILE`. New access right; `docker_staging.py:481-485` requests attributes only. |
| `create_exclusive_at` | `NtCreateFile` with `FILE_CREATE` (2). New: staging only opens existing (`_FILE_OPEN`, `docker_staging.py:500`). |
| `mkdir_at` | `NtCreateFile` with `FILE_CREATE` plus `FILE_DIRECTORY_FILE`, `RootDirectory` = parent handle. **Returns `bool`, and the collision case must NOT raise**: map `STATUS_OBJECT_NAME_COLLISION` to `False`, mirroring the POSIX `FileExistsError` to `False` contract at `posix.py:506-515`. `mkdir_borrowed` type-checks the result and converts a non-`bool` into `IO_FAILED` (`filesystem.py:1998-1999`). The POSIX mode `0o700` has no Windows analogue; access control is the SDDL DACL per ruling (c). |
| `read` / `write` | `ReadFile` / `WriteFile`, partial-write loop as at `posix.py:741-747`. |
| `stat_file(file)` | Same three info classes on the file handle. |
| `close_file` | `CloseHandle`. |
| `fsync_file` | `FlushFileBuffers` on the file handle (`security.py:174-175, 469`). |
| `fsync_directory` | `FlushFileBuffers` on the directory handle. **Probed at the first retention of each root, before any mutation through it; never a no-op.** Rulings (a) and 6.2. |
| `link_at(directory, source, destination)` | `NtSetInformationFile` + `FileLinkInformationEx`, `RootDirectory` = directory handle. Ruling (c). |
| `unlink_at(directory, component)` | `SetFileInformationByHandle(FILE_DISPOSITION_INFO_EX, FILE_DISPOSITION_DELETE)` (`docker_staging.py:811-816`). |
| `acquire_directory_admission` | Second, asymmetrically shared open of the same directory. Adds no namespace entry. Ruling (b). |
| `validate_directory_admission` | Re-prove node identity via `FILE_ID_INFO`; confirm the handle is still held. |
| `release_directory_admission` | `CloseHandle` on the admission handle. |
| `publish_journal` | Mirrors `posix.py:731-790` exactly: exclusive create, write, `fsync_file`, `link_at`, `fsync_directory`, `unlink_at`, `fsync_directory`, read back and compare. |
| `snapshot_journal` | Mirrors `posix.py:791+`. |

Invariants the port must uphold, matching the POSIX port:

- Every mutation is handle-relative. No operation takes a full path except
  `retain_directory`, which is the anchor and re-proves identity at every
  component (`posix.py:257-266` is the POSIX model).
- Reparse points are never traversed: `OBJ_DONT_REPARSE` plus
  `FILE_OPEN_REPARSE_POINT`, and the *matched* entry is rejected if it carries a
  reparse attribute (`docker_staging.py:393, 414-415`). The rejection is
  per-matched-entry, never per-listing — see defect 3 below for why the wider form
  is both wrong and unnecessary.
- **Share mode is asymmetric by handle kind, and the asymmetry is the mechanism
  behind ruling (b)'s admission exclusion.** See the ruling below for why.
  - *File handles* omit `FILE_SHARE_DELETE` (`_FILE_SHARE_READ_WRITE = 0x3`,
    `docker_staging.py:193`), blocking rename-out and delete-out.
  - *Directory handles* share read, write and delete
    (`_FILE_SHARE_ALL = 0x7`, `docker_staging.py:192`).
  - *The admission handle* requests `DELETE` access and shares read and write only.
- Construction-process affinity, mirroring `_require_construction_process` in the
  POSIX port (`posix.py:112-114` establishes the process identity).

#### Ruling: the admission exclusion runs on the DELETE axis, and the omit-share-DELETE rule is scoped to file handles

An earlier draft of this section stated the omit-`FILE_SHARE_DELETE` rule for all
retained handles. That contradicted ruling (b), which needs an asymmetric share
mode capable of excluding a second admission on the same directory. **Confirmed:
run the exclusion on the DELETE axis, and scope the omit rule to file handles.**

*The axis is forced, not chosen.* Windows share arithmetic has three axes: read,
write and delete. Directory handles must hold write-flavoured access, because
creating, linking and unlinking entries inside a directory requires it, so write
asymmetry cannot separate an admission from an ordinary directory open. Read
asymmetry would break every stat. DELETE is the only axis left, and it is the one
axis no ordinary directory operation requests: `DELETE` on a directory handle means
deleting the directory itself, not touching its entries.

*The exclusion holds in both orders.* Share checks are mutual and evaluated against
every existing handle. A second admission requests `DELETE`; the first admission
does not share `DELETE`, so it fails with `ERROR_SHARING_VIOLATION` (32), which maps
to `ROOT_IN_USE` exactly as `EAGAIN` from `flock` does on POSIX (`posix.py:401-405`).
An ordinary retained-directory open requests no `DELETE`, so the first admission's
read-write sharing permits it, and its own read-write-delete sharing permits the
admission handle's `DELETE` access. This is order-independent: opening the retained
directory first does not block a later admission, and holding admission first does
not block later directory opens.

*Nothing load-bearing is lost.* The dropped protection was rename-out on directory
handles, and POSIX never had it. A retained `dirfd` does not prevent its directory
being renamed, and `flock` does not block rename either. Identity here is carried by
the retained handle, which survives a rename on both platforms, and a rename changes
no file id, so `_same_node` and the journal comparisons are unaffected. The earlier
blanket rule made Windows stricter than the POSIX port it mirrors, and that extra
strictness was never a stated requirement of any ruling. Scoping it back to file
handles restores parity rather than conceding ground.

*What must not be lost.* File handles keep omitting `FILE_SHARE_DELETE`, and that
one is load-bearing: the 1 → 2 → 1 commit proof depends on the staged artifact
remaining the same node between `fsync` and `link`. Do not widen file-handle sharing
for symmetry with directories.

Two constraints follow, both testable.

1. **The `DELETE` access on the admission handle is an exclusion token and nothing
   else.** Requesting `DELETE` access is not deleting; the port must never issue a
   disposition through that handle. If a future change needs to remove the data
   directory, it opens a separate handle for it.
2. **Assert both directions when verifying R-4.** A second admission must raise
   `ROOT_IN_USE`, *and* an ordinary retained-directory open of the same directory
   must still succeed while admission is held. A test asserting only the first would
   pass for a port that excluded everything, which is the more likely bug.

One property is gained rather than merely preserved, and is worth asserting: while
admission is held, no opener can acquire `DELETE` on the data directory, so it
cannot be renamed or removed out from under a live publication. POSIX `flock` gives
no such guarantee.

### 6.2 `detect_windows_capability_v1`

New in the same module. Signature mirrors `detect_posix_capability_v1`
(`posix.py:64-66`) and returns the same `LocalFilesystemCapabilityV1`.

Reports `AVAILABLE` only when all of the following hold, and `UNAVAILABLE`
otherwise. The conditions split by when they can be evaluated at all, because
ruling (d)'s factory constructs the port before any path is known.

Checked at construction, failing closed there:

1. `os.name == "nt"`.
2. `kernel32` and `ntdll` bind, with `NtCreateFile`, `NtSetInformationFile`,
   `GetFileInformationByHandleEx`, `SetFileInformationByHandle`,
   `FlushFileBuffers`, `GetFinalPathNameByHandleW` all resolvable.

Checked at the first retention of each root, before any mutation through that root,
failing closed there with `CAPABILITY_UNAVAILABLE`:

3. The target volume is NTFS (`security.py:284-293` pattern).
4. `FILE_ID_INFO` is retrievable on a probe handle.
5. **The `fsync_directory` barrier probe succeeds.** Ruling (a).

**Why 3 and 5 moved, and why the move makes them stronger.** An earlier draft put
all five at construction. That is not implementable under ruling (d) — the factory
has no path, so there is no volume to interrogate — and it would have been weaker
even if it were. A construction-time probe has to run against some scratch
location. On a host with more than one volume, a scratch probe can pass while the
volume that actually receives the artifacts fails, reporting a capability the port
does not have on the path it will use. Probing per root asks the question of the
volume that will answer it.

The invariant is unchanged, and it is the invariant, not the timing, that must be
tested: **no mutation ever reaches a root whose volume has not answered conditions
3 through 5.** Probing later is sound only because it is still before first use. A
probe deferred past a mutation, or skipped because a path looked familiar, would be
a silent softening of ruling (a) rather than a relocation of it.

Condition 4 is grouped with 3 and 5 here because `FILE_ID_INFO` retrievability is a
property of the volume, exactly like NTFS-ness and the barrier, and a probe handle
needs a path to open. If coder-port reports that it can be established at
construction without a target path, move it up; the grouping is a consequence of
what the check needs, not a preference.

`platform_family` is `"windows"`. The feature tuple names the Windows analogues of
the POSIX features at `posix.py:52-61`; it is hashed into the capability digest,
so it must be a fixed sorted tuple.


#### Implementation findings from the real Windows host (TEST, Task #19)

TEST reached a native Windows host and ran the closure there. Two defects surfaced.
Both are plumbing, not design: **ruling (b) and this section stand unchanged**, and
neither finding altered a contract above. They are recorded here because each is a
place where a correct-looking NT call is wrong, and a later reader retracing the
design would otherwise reintroduce them.

**Defect 1 — the admission re-open must use an empty `ObjectName`.** The first
implementation re-opened the admission handle with `_open_relative(handle, ".")`.
Windows rejects that twice over: the port's own name validator rejects `"."` as
`PATH_INVALID`, and `NtCreateFile` itself returns `0xC0000033`
(`STATUS_OBJECT_NAME_INVALID`). The canonical NT re-open-by-handle is an **empty
`ObjectName` with `RootDirectory` set to the existing handle**, measured
`STATUS_SUCCESS`. The `"."` and `".."` rejection stays for ordinary component
names, where it is correct. `_ADMISSION_ACCESS` and the share mask were confirmed
correct and did not change.

**Defect 2 — ancestors and the retained leaf need different access masks.** The
first implementation requested the full directory access mask on every ancestor
during descent. A non-elevated process cannot obtain write access to `C:\`
(`ERROR_ACCESS_DENIED`, 5), so **every root on the system volume was unreachable**,
including the default pytest temporary directory. Ancestors are only traversed,
listed and stat-ed; nothing is ever created, linked, unlinked or stamped in them.
The fix is a separate named ancestor constant, not a weakening of the leaf mask.

| Mask | Value | Members | Applies to |
|---|---|---|---|
| Ancestor | `0x001000A1` | `FILE_LIST_DIRECTORY`, `FILE_TRAVERSE`, `FILE_READ_ATTRIBUTES`, `SYNCHRONIZE` | Every directory on the way down |
| Leaf | `0x001001A7` | The ancestor set plus `FILE_WRITE_ATTRIBUTES`, `FILE_ADD_FILE`, `FILE_ADD_SUBDIRECTORY` | The retained root only |
| Admission | `0x001101A7` | The leaf set plus `DELETE` | The admission handle only |

Each of the four ancestor bits is load-bearing and none may be dropped:
`FILE_LIST_DIRECTORY` because the exact-case check enumerates the parent,
`FILE_READ_ATTRIBUTES` because the descent stats each opened directory,
`FILE_TRAVERSE` to open a child relative to it, and `SYNCHRONIZE` because the opens
are synchronous. The ancestor mask is a strict subset of the leaf mask, which is
the property to assert: a regression that widens it re-breaks the system volume,
and one that narrows it breaks the descent.

**Defect 3 — the reparse refusal was too wide, and it was found only because
defect 2 was fixed first.** Directory enumeration rejected the *entire* listing if
*any* entry carried `FILE_ATTRIBUTE_REPARSE_POINT`. `C:\` carries exactly one, the
legacy `Documents and Settings` junction (tag `0xA0000003`), so every path under the
system volume stayed unreachable even after defect 2 was fixed. The refusal is now
scoped to the *matched* entry rather than the whole listing.

This narrows a rule that section 7 previously stated too broadly, and the narrowing
is safe for a reason worth stating: the traversal guarantee never rested on the
enumeration in the first place. Every descended component is independently
re-proved by an identity query on its own handle, and the opens still carry
`OBJ_DONT_REPARSE` and `FILE_OPEN_REPARSE_POINT`. A substituted or reparse-backed
component is still caught, one component at a time. The published whole-directory
strictness of the listing operation is untouched. What was removed was an
unrelated-neighbour veto: one junction anywhere in a directory disqualifying every
sibling.

*Provenance.* The mask values above were read from the landed implementation,
recomputed from its own bit constants, and confirmed against Task #24's HANDOFF,
which reports `0x001000A1` as measured rather than assumed. Coder-port probed the
narrower `LIST | TRAVERSE | SYNCHRONIZE` set that blocker #20 floated and found it
fails: the identity query on an ancestor handle needs `FILE_READ_ATTRIBUTES`,
because the file-id query is an attribute query. That is why the fourth bit is
present, and it is the kind of detail that would be silently re-broken by anyone
trimming the mask on inspection.

### 6.3 Error taxonomy — no new codes

Every failure maps onto the existing `LocalIOCodeV1` enum
(`local_io_v1/model.py:16-44`). No enum member is added.

| Condition | Code |
|---|---|
| Non-Windows, non-NTFS, missing entry point, failed barrier probe | `CAPABILITY_UNAVAILABLE` |
| Admission file already held (`ERROR_SHARING_VIOLATION`) | `ROOT_IN_USE` |
| Anchor component changed, reparse point, identity mismatch during the walk | `ROOT_CHANGED` |
| Non-absolute or malformed anchor path | `ROOT_INVALID` |
| Handle-relative open of a child failed | `PATH_INVALID` |
| Admission node identity mismatch | `ADMISSION_INVALID` |
| Journal read-back mismatch | `JOURNAL_INVALID` |
| Any other Win32 or NT status failure | `IO_FAILED` |

Errors stay closed: only the stable code is observable (`model.py:47-49`). No
Win32 error number, path, or handle value may appear in a message.

### 6.4 Evidence and digest implications

- `registry_digest` composition is unchanged
  (`local_artifact_destination.py:171-188`). It absorbs the Windows identity
  values, including the 128-bit `inode` and the synthesised `mode`.
- Signed evidence and the HMAC authority
  (`publication_authority.py:571-608`) are unchanged. The value crossing to the
  engine stays an opaque hex string.
- The capability digest changes only for Windows, because it is computed over the
  Windows feature tuple and family. The POSIX digest is byte-identical.

---

## 7. Security

- **No new credential or network surface.** Publication is Host-side and
  post-verification. The container stays network-disabled and credential-free;
  this design does not touch container composition.
- **No secrets in the design or in evidence.** Identity fields are device, inode,
  mode, times and size. The rejection of credential-shaped configuration keys
  (`artifact_destinations.py:32-41, 87-93`) is untouched.
- **Access control does not weaken.** The POSIX path's `0o600` / `0o700` are
  synthesised for the model only. Real Windows access control remains the SDDL
  DACL applied and ACE-validated in `security.py:250-270, 340-390`, with the
  tighter `FILE_SHARE_READ` share mode at `:68, :308`.
- **Redirect resistance is preserved, not approximated — for content.**
  `OBJ_DONT_REPARSE` plus `FILE_OPEN_REPARSE_POINT` on every open, identity
  re-proof at every component, and file handles omitting `FILE_SHARE_DELETE`
  (scoped to file handles per the share-mode ruling in section 6.1). A staged
  artifact cannot be swapped, renamed or deleted out from under the commit proof.
- **Namespace attachment is a weaker guarantee than content integrity, and the
  difference is deliberate.** Directory handles share `DELETE`, because the
  admission exclusion runs on that axis, so outside the admission window a retained
  directory can be renamed out of its configured path. Operations continue to land
  on the correct object, since identity here is carried by the retained handle and a
  rename changes no file id — but the object is no longer where the operator
  configured it. This is parity with POSIX, where a retained `dirfd` does not block
  rename either, and it is not preventable while the exclusion uses `DELETE`. The
  exclusion is the higher-value guarantee, so it wins. Residual R-6.
- **Correction: the re-retain is a rebind, not a check, and an earlier draft of
  R-6 cited the wrong mechanism.** That draft said the path-to-object binding is
  "re-established on each admission acquisition, which re-opens by path
  (`filesystem.py:754`)". Both halves are wrong. At the citation baseline,
  `filesystem.py:754` passes `authority.data_directory`, which is an
  already-retained handle object and not a path — it carries `.identity` and is
  handed to `close_directory` at `:727`. Admission acquisition performs no path
  re-open at all. The only re-open by path is in `retain_single_root_authority`,
  once per authority, so the substitution window is **across a restart**, not per
  admission. TEST confirmed behaviourally that the re-open compares nothing against
  any recorded identity, so it must never be described or relied on as a check.
  This correction narrows the window compared with what the wrong citation implied,
  and it is the reason R-6 is a documented residual with a named follow-up rather
  than a release blocker.
- **The `_root_component` casefold check stays sound on NTFS.** `posix.py:175-178`
  requires the folded match set to equal `[component]`. On a case-insensitive
  volume at most one entry can fold to a given value, so the check reduces to
  "the configured spelling matches the on-disk spelling exactly". That is
  stricter than on Linux, not weaker. The preparer's gap C5 needs no redefinition;
  it needs a documented requirement that configured absolute paths use exact case.
  Residual R-5.

---

## 8. File-level change list

Create:

| Path | Purpose |
|---|---|
| `synaptic_host/local_io_v1/windows.py` | `WindowsRetainedHandlePortV1` + `detect_windows_capability_v1` + Win32/NT bindings. |
| `tests/synaptic_host/test_publication_local_windows.py` | Native-Windows counterpart to `test_publication_local_posix.py`, `skipif(os.name != "nt")`. **TEST-phase deliverable under S7, not coder-port's.** It cannot run or be verified on this Linux worktree, so writing it during CODE would ship unexecuted assertions. |
| `tests/synaptic_host/local_io_v1/test_windows_port_contract.py` | Linux-runnable fake-port conformance and gate tests. |

Modify:

| Path | Change |
|---|---|
| `synaptic_host/publication_composition.py` | Add `_local_filesystem_port_v1()`; line 433 calls it instead of naming the POSIX port. |
| `synaptic_host/local_io_v1/filesystem.py` | Add `_SUPPORTED_PLATFORMS` near `:72`; rename `_require_posix` to `_require_retained_port` and widen its membership test (`:581-584`, 9 call sites); rename `_require_linux_admission` to `_require_directory_admission` and admit `win32` (`:586-589`, call sites `:675, :718, :746, :822`); widen `capability()` availability at `:557-559` and split its admission-feature gate at `:566-572` per the ruling below. |
| `tests/synaptic_host/local_io_v1/test_filesystem.py` | Re-aim `:2207` and `:2736` at the win32-with-no-port case per ruling (g). Exactly those two tests; no other edit to this file. |
| `synaptic_host/docker_training.py` | Add `_PUBLICATION_SPOOL_ROOT_REF`; import `compose_docker_publication_v1` and `build_local_artifact_destination_registration_v1`; restructure `:846-871` per ruling (e). |

Counts, stated against the tables above so they cannot drift. Source files: **one
created** (`windows.py`) and **three modified** (the three `synaptic_host/` rows in
the Modify table). Test files: **two created** (both test rows in the Create
table), **one modified** (`test_filesystem.py`, the fourth Modify row), and **one
extended**, `tests/synaptic_host/test_docker_prepared_composition.py`, named in
section 9.2 rather than here because it is an extension, not a new file. The Modify
table therefore has four rows, three of them source and one test.

`synaptic_host/local_io_v1/__init__.py` is deliberately NOT modified. The package
declares `__all__: tuple[str, ...] = ()` and its docstring states the rule
verbatim: "This package intentionally has no convenience exports. Host composition
code must name the concrete module that owns each binding or operation." Ruling
(d)'s branch-local import already names the concrete module, so an export would be
both redundant and contrary to the package's stated policy. Do not add one.

Not touched, deliberately:

`synaptic_host/local_io_v1/posix.py`; `synaptic_host/local_io_v1/model.py`;
`synaptic_host/artifact_spool.py`; `synaptic_host/artifact_destinations.py`;
`synaptic_host/local_artifact_destination.py`; `synaptic_host/publication_authority.py`;
`synaptic_host/publication_store.py`; `synaptic_host/verified_artifact_source.py`;
`synaptic_host/docker_execution.py`; `synaptic_host/docker_prepared_composition.py`;
`synaptic_host/docker_staging.py`; `training/artifacts.json`; `training/storage.json`;
`training/smokes/docker-sft.json`; the entire `synaptic-tuner` submodule; `CLAUDE.md`.

Both files PREPARE classified as POSIX-leaking stay untouched. `model.py`'s
`nlink` 1 and 2 invariants and `artifact_spool.py`'s `nlink == 1` check
(`:115-120`) are **satisfied** on NTFS, not relaxed. Ruling (b) deliberately locks
the directory handle rather than adding a lock file precisely so that
`artifact_spool.py` stays off this list.

---

## 9. Test strategy and acceptance

### 9.1 Baseline to reproduce first

Before any change, reproduce the preparer's measured baseline so a regression is
attributable.

**Assert the failures and skips; treat the pass count as informational.** The
stable part is **12 failed, 11 skipped**, and the 12 are pre-existing platform
artifacts of running a Windows-targeted Host on Linux, in three families: 4
Windows drive path, 3 absolute Windows docker executable, 5 locked Git object. They
must stay at exactly 12, and they must stay in those families — check the cause,
not just the count.

The pass count moves whenever anyone adds a test to a file in the subset, so
pinning it creates a number that goes stale and gets copied forward. For the
record: the preparer measured 400 at the baseline commit, TEST reported 408, and a
re-run for this amendment measured **411 passed, 12 failed, 11 skipped**. The
differences are additions, not regressions — `test_docker_prepared_composition.py`
alone went from 8 tests at the baseline to 17. The 408 figure was most likely taken
before TEST's own three counter-tests landed in that same file. If your run shows a
pass count in this region with 12 failures in the three named families and 11
skips, the baseline is healthy.

```
cd /mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean && \
GIT_CONFIG_GLOBAL=/path/to/wsl-safe.gitconfig \
PYTHONPATH="/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean:/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean/synaptic-tuner" \
python -m pytest <explicit file paths> -q -rs --tb=no
```

Measured on CPython 3.12.9; `python` must resolve to that conda environment's
interpreter.

Use `GIT_CONFIG_GLOBAL`, pointed at a file containing:

```
[safe]
	directory = *
```

The `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_0` / `GIT_CONFIG_VALUE_0` triple was
observed both to work and to fail in this environment, by two different agents. Do
not conclude from that it never propagates. It propagates fine to a plain `git`
invocation; the auditor measured rc=0 with it and rc=128 without. `GIT_CONFIG_GLOBAL`
is the form to use because it is the one that survives both measurements, not
because the triple is broken.

**Neither form reaches the git subprocesses in `docker_staging.py`, and that is
deliberate.** `_git_environment()` (`docker_staging.py:1012-1028`) does not inherit
the ambient environment. It rebuilds one from a fixed whitelist — `PATH`,
`SystemRoot`, `WINDIR`, `COMSPEC`, `PATHEXT`, `TEMP`, `TMP`, `LANG`, `LC_ALL` —
which excludes every `GIT_CONFIG_*` name, and then pins `GIT_CONFIG_NOSYSTEM=1`,
`GIT_CONFIG_GLOBAL=os.devnull` and `GIT_CONFIG_SYSTEM=os.devnull`. Those
subprocesses run with no git configuration at all, by design, and `env=` at
`:1042` is what applies it. An exported `GIT_CONFIG_GLOBAL` is overridden by the
`os.devnull` pin; the triple is dropped by the whitelist.

**So the 5 locked-Git-object failures are not a `safe.directory` problem and no
environment variable will fix them.** They surface as
`ValueError("exact locked Git object is unavailable")` at `docker_staging.py:1045`,
which is the `check=True` conversion of any non-zero git exit into one opaque
error. The underlying cause is an unresolvable submodule gitlink. Count them as
part of the pre-existing 12 and do not spend time on git config trying to clear
them. The `GIT_CONFIG_GLOBAL` export above is still needed for the rest of the
suite and for read-only git in this worktree, which do not go through
`_git_environment()`.

Use explicit file paths, never a directory glob: the rtk proxy reports
"No tests collected" for globs, and it reformats output so an anchored pattern can
read as a false clean pass. Cross-check any zero with a count that cannot be free.
The proxy also truncates `sed -n` and `awk` line ranges without saying so, so do
not derive a line number from proxied output; run the command under `rtk proxy`,
or have it print its own `FNR`.

### 9.2 Tests to add

**Linux-runnable, using a fake port** — `tests/synaptic_host/local_io_v1/test_windows_port_contract.py`.

Test 0 is mandatory and comes first: assert that `WindowsRetainedHandlePortV1`
exposes every callable name in `PosixFilesystemPortV1`, derived from the Protocol
at runtime rather than from a hand-copied list, so the check cannot drift from the
Protocol the way this document's own count did. It must fail if any method is
missing, `mkdir_at` included. This test needs no Windows host: it inspects the
class, it does not call it.

1. `_require_retained_port` admits `win32` and still rejects `darwin` and the BSDs.
2. `_require_directory_admission` admits `linux` and `win32`, rejects `darwin`.
3. `capability()` reports family `windows` and `AVAILABLE` for a Windows-family
   platform string with a port present, and its `features` are exactly the sorted
   five: the three base features plus `crash-released-admission` and
   `directory-inode-admission`. Assert the absence of `exec-closed-admission` and
   `nonblocking-directory-flock` explicitly, so a later widening of the gate cannot
   add them silently. Assert in the same test that `linux` still reports all seven,
   which is what pins the POSIX result as unchanged.
4. A fake port driving `LocalFilesystemV1` through the full create-commit sequence
   returns identities with `nlink` 1, 2, 1 and passes the commit proof at
   `filesystem.py:3040` and the unlink proof that follows it through `:3068`.
   This proves the shared invariants are satisfiable by a non-POSIX backend
   without touching `model.py`.
5. A fake port whose `fsync_directory` raises causes construction or commit to
   fail, never to succeed silently. This is the regression test for ruling (a).
6. `LocalFileIdentityV1` accepts a 128-bit `inode` and `digest_v1` over its
   `canonical()` is stable and lossless. This is the regression test for the
   retired most-likely-wrong item.
7. Acquiring the directory admission adds **no** entry to the spool root, so
   `_startup_reclaim` (`artifact_spool.py:193-217`) sees an unchanged namespace
   and does not raise. This is the regression test for ruling (b): it fails if a
   coder reintroduces a lock file.

**Linux-runnable, wiring** — extend `tests/synaptic_host/test_docker_prepared_composition.py`:

8. The activation path constructs a publication only when the loaded phase is
   `ARTIFACTS_VERIFIED`, and not for `CREATED`, `SUBMITTED`, or
   `PROCESS_SUCCEEDED`.
9. `publication.close()` runs even when `reconcile` raises.

**Tests 8 and 9 have a static ceiling, and it is structural rather than
circumstantial.** Their constructing half and the whole of test 9 are verified by
static analysis over the shipped source, not behaviourally, and that is the correct
ceiling — but not for the reason CODE first gave. CODE reported the activation
function was unreachable because its fixture died on a git clone. That is false:
with `GIT_CONFIG_GLOBAL` set the fixture runs, and on a real Windows host the whole
file passes including the activation test. The actual limit is deeper. Reaching the
publish branch requires the run to already be at `ARTIFACTS_VERIFIED`, and that
phase is carried by an integrity-sealed aggregate that cannot be reached without a
real container run. Forging it would mean fabricating an integrity record, which is
a worse thing to put in a test suite than an unverified branch.

So the runtime half of test 8's constructing branch and all of test 9 belong to the
section 9.3 GPU smoke, which is the first place a genuine `ARTIFACTS_VERIFIED`
exists. Do not "fix" this later by patching the phase or the composition function
into place: a test that forges the aggregate proves the mock, not the system, and
the static assertion it would replace is strictly stronger.

**Native Windows, skipif** — `tests/synaptic_host/test_publication_local_windows.py`,
guarded `@pytest.mark.skipif(os.name != "nt", reason="real Windows retained-handle publication")`,
mirroring the structure of `test_publication_local_posix.py:146-156`:

10. End-to-end publication through `compose_host_publication_v1` on NTFS, asserting
    a publication record and `published == True`.
11. Restart safety: a second identical compose-and-publish produces no duplicate.
12. Admission exclusion: a second port instance against the same spool root raises
    `ROOT_IN_USE`.
13. Non-NTFS or missing barrier raises `CAPABILITY_UNAVAILABLE` at first root
    retention, before any mutation reaches the root. Assert both halves:
    constructing the port succeeds regardless of the volume, and the first
    `retain_directory` against a bad volume raises. A test that only asserted a
    construction failure would now pass for the wrong reason, or fail for it.

### 9.3 Acceptance verification sequence for the later GPU smoke

Run in this order. Step 1 is first by design so the smoke fails fast on a missing
role rather than after training.

1. **Role inventory check (residual R-3).** After the container exits and
   verification runs, assert the verified inventory has exactly five entries with
   roles `final_model, tokenizer, training_lineage, training_metrics,
   workload_record`. This confirms from runtime what section (f) established from
   source. If it fails, stop: the closure is not at fault and publication is not
   the defect.
2. **Reach `ARTIFACTS_VERIFIED`.** Call reconcile repeatedly. `reconcile` advances
   one cut per call (`docker_execution.py:1103-1129`), so the verify cut and the
   publish cut are different calls. **Call reconcile at least twice before asserting
   anything about publication.** A single reconcile is not sufficient: it reports
   `published == False` on a completely healthy system, and reading that as a
   failure sends someone hunting a defect that does not exist. TEST re-raised this
   independently after tracing the same one-cut-per-call behaviour, so treat it as
   the most likely way this smoke gets misread rather than as a footnote.
3. **Publish cut.** Call reconcile again with the phase already
   `ARTIFACTS_VERIFIED`. Assert a `publication_id` is set and
   `DockerPreparedRunOutcomeV1.published` is `True` (`docker_execution.py:256-258`).
4. **Durable record.** Assert one row in `publication_records_v1` with the expected
   `destination_ref` (`publication_store.py:162-185`).
5. **Idempotent replay.** Repeat the identical activation. Assert no second
   container, no second publication record, and no
   `"Docker publication composition differs from the run"`
   (`docker_publication.py:381-409`).
6. **POSIX non-regression.** Re-run the WSL baseline. Still 12 failed in the three
   named families and 11 skipped; the pass count is informational and rises with
   test additions (see 9.1). The count is unchanged because the two tests ruling (g) retires are
   re-aimed rather than deleted. It only holds once the re-aim lands: the gate
   widening alone takes the suite to 398 passed, 14 failed. Land the re-aim in the
   same commit as the widening, so no commit in the history has a red baseline.

---

## 10. Implementation roadmap

| Stage | Deliverable | Depends on | Acceptance |
|---|---|---|---|
| S1 | Gate widening in `filesystem.py`, the two renames, and the re-aim of `test_filesystem.py:2207` and `:2736` | — | Baseline back to 400/12/11; tests 1-3 pass. |
| S2 | `windows.py`: bindings, `detect_windows_capability_v1`, read-only methods | S1 | Test 13 on Windows; import-clean on Linux. |
| S3 | `windows.py`: create, write, `link_at`, `unlink_at`, barriers, journal | S2 | Tests 4-6 with the fake port; test 10 on Windows. |
| S4 | Directory-handle admission; confirm the share-mode pair on a Windows host | S3 | Tests 7, 12. Closes R-4. |
| S5 | Port factory at `publication_composition.py:433` | S3 | POSIX path byte-identical; baseline unchanged. |
| S6 | `docker_training.py` wiring (Gap A) | S5 | Tests 8, 9. Closes the gap on Linux and Windows alike. |
| S7 | Native-Windows suite, including `test_publication_local_windows.py` | S4, S6 | Tests 10-13 on a real Windows host. TEST phase owns this stage; CODE does not write it. |

S1 through S5 are Linux-verifiable. S6 closes Gap A and is independently valuable:
it makes publication real on the POSIX path too, where it is equally unwired
today. S7 is the only stage requiring a Windows host.

---

## 11. Risks and residuals

| Id | Residual | Severity | Disposition |
|---|---|---|---|
| R-1 | Directory-entry durability on Windows is NTFS-log-backed, not an independently proven synchronous barrier. | Medium | Barrier is probed per root at first retention, before any mutation through it, and fails closed there. TEST asserts the call succeeds, never crash-durability. Elevating requires a power-loss rig, out of scope. |
| R-2 | The synthesised `mode` is compared by full value, not only by its file-type nibble: `filesystem.py:417-430` (`_same_node`) and `model.py:747` (full dataclass equality). Both sit on the commit proof (`filesystem.py:3040`) and the recovery proof (`filesystem.py:3259, 3268`). It also enters `registry_digest`. | Medium | Two named module constants, one per file type, byte-identical for every stat of that type. No file attribute may leak into the permission bits; never ACL- or umask-derived. Because `recover_create` compares against a `mode` persisted in the on-disk journal by an earlier process, the constants are part of the journal format and are stable across builds, not merely across a process lifetime. Changing one silently turns resumable mutations into `CONFLICT`. |
| R-3 | Five-role emission is read from engine source; no container was run. | Low | First check in the acceptance sequence, section 9.3 step 1. |
| R-4 | **CONFIRMED on a real Windows host (TEST, Task #19).** Was: the admission handle's exact `DesiredAccess` / `ShareAccess` pair is a runtime property not verifiable from source. | Closed | Measured on the host with only the defect-1 open form corrected: a second admission open returns `STATUS_SHARING_VIOLATION` (`0xC0000043`), which maps to `ROOT_IN_USE`; and while that admission is held, both an ordinary directory open and a full `retain_directory` by path still succeed. Both directions hold, which is what this residual required — a denial-only result would also have been produced by a port that excludes everything. TEST proved the kernel is the source of the exclusion by using two separate port instances, so the result cannot come from the in-process live-admission bookkeeping. Closes when the shipped tests go green against the shipped defect fixes; the measurement itself is no longer in doubt. |
| R-5 | `_root_component` requires exact-case path spelling on case-insensitive NTFS. | Low | Stricter than Linux, not weaker. Document that configured absolute paths must match on-disk case. |
| R-6 | Namespace attachment is not continuously enforced, and the re-retain is a **rebind, not a check**. A different directory placed at the configured spool path between two compositions is accepted silently: no `ROOT_CHANGED`, no `ADMISSION_INVALID`, the replayed publication equals the original, and verify returns `True` (TEST measured the inode changing 831383 to 831397). | Medium | Raised from Low on the lead's ruling after TEST answered it. The S5 line is not crossed: an actor able to substitute the directory across a restart already holds write access to the project directory and could rewrite the SQLite store or the signing key instead, so the exposure sits inside the Host's existing local trust boundary. But the evidence chain attesting `True` about the wrong object is an internal inconsistency this design must own, and POSIX parity does not excuse it, because POSIX has no such chain. Not gating this release. Follow-up F-3 names the fix. The security reviewer at peer-review may overrule this and the user has been informed with the option to override. |
| R-7 | The entry cap applies to **ancestors**, not only to the root the Host owns. `_root_component` enumerates the full parent listing for every component during descent (`windows.py:833`), and `MAX_DIRECTORY_ENTRIES = 4096` (`filesystem.py:70`) trips at the 4097th entry (`windows.py:628`, strictly greater). `%TEMP%` on the TEST host holds 4049 entries, so a default `C:` basetemp run has 47 entries of headroom before an unrelated directory fails retention with `LIMIT_EXCEEDED`. | Low | Latent, not observed, and unrelated to any of the three host defects. Production spool roots sit under the project directory, whose ancestors are small; the TEST lane is the exposed path, and only when basetemp defaults to `%TEMP%`. Not a Windows-port regression: POSIX `_root_component` enumerates and caps ancestors identically at the same strictly-greater boundary (`posix.py:166-170`), so this is shared pre-existing behaviour newly exercised because Windows test roots land under a large `%TEMP%` while Linux ones land under a small per-run `/tmp` tree. The failure is loud rather than silent, but the diagnosis misleads: `LIMIT_EXCEEDED` names the Host's own limit while the cause is a directory the Host neither owns nor writes. Follow-up F-4. |

| Id | Follow-up, deliberately not in this closure |
|---|---|
| F-1 | Rename `PosixFilesystemPortV1` to a platform-neutral name. Cosmetic; competes with the real risk budget of this change. |
| F-2 | Extend the Windows port to `darwin` and the BSDs, which `_POSIX_PLATFORMS` lists but `_require_linux_admission` excludes today. Unrelated to this closure. |
| F-3 | **Detect root substitution across a restart (R-6).** Persist the retained root's identity — `FILE_ID_INFO` on Windows, `st_dev` + `st_ino` on POSIX — in the existing journal record at first retention, and compare it on re-retain, raising `ROOT_CHANGED` on mismatch. No new table and no new framework: the journal already carries `LocalFileIdentityV1` values and already compares them on the recovery path, so this reuses a mechanism the design has rather than adding one. Deliberately not in this closure, because it changes a durable record format and belongs with its own migration reasoning. |
| F-4 | **Stop enumerating ancestors to resolve one component (R-7).** Enumerate-then-match is ownership-grade purity applied to a directory the Host only passes through — the same category error as defect 3, where the reparse veto was narrowed from the whole listing to the matched entry. The descent needs exactly two facts about each ancestor: that the named component exists with the configured spelling, and that it is not a reparse point. Both are obtainable from the component itself — open it handle-relative, then read the canonical on-disk name back off the opened handle and compare — instead of scanning its parent to find it. That also answers whether the cap should apply to ancestors at all: it should not. A cap bounds work over a directory whose size is another owner's property, and no bound over that directory is load-bearing for a descent that names exactly one entry in it. The retained leaf keeps the cap, which is where the Host's ownership and the published `list_names_at` contract actually live. The exact-case guarantee of R-5 survives, because comparing the canonical name off the handle is the same comparison, sourced from the object rather than from its parent. Deliberately not in this closure: it changes the failure modes of a path every retention runs, and the Windows call for reading a handle's canonical name back is named here but not yet verified against this module's existing helpers. |

**Risks that were investigated and closed as non-risks:** cross-platform
`registry_digest` reproducibility (section 5(c)); lossy 128-bit file id reduction
(section 1, item 2); registry provider neutrality (section 4.1); the smoke's two
`required_kinds` (section 5(f)); the casefold anomaly criterion (section 7).

**Constraint check.** No Docker-specific destination model, no downloader, no
generic cache framework, no compatibility layer or shim, no new database table, no
legacy composition fallback. No blocker escalation required.

**Note for HANDOFF.** A tracked `CLAUDE.md` exists in this worktree. It was read,
never written or edited.
