# Environment Model: Prepared-Path Alpine CPU Diagnostic

PREPARE phase, feature #73 (plan step 3). Host-facts half, owned by `preparer-host`.
The code-path half is owned by `preparer-path` (task #80); where the two meet, that
agent's output is authoritative.

- **Worktree**: `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean`
- **Branch / head**: `feat/submodule-cloud-api-v1-host-clean` @ `e1439de3` [measured]
- **Engine submodule pin**: `aec998ee` (untouched) [measured]
- **Measured on**: 2026-09-02

## Tag legend

| Tag | Meaning |
|---|---|
| `[measured]` | Observed by running a command on this host during this task. Each row says which interpreter or binary produced it. |
| `[read-from-source]` | Read out of checked-in code or a checked-in document in this worktree, cited by `file:line`. Not executed. |
| `[assumed]` | Neither run nor read here. Source of the belief is named. Must be treated as unverified by the architect. |

### Where each measurement ran

The NT layer executes zero lines under Linux, so "measured from WSL" and "measured
on Windows Python" are not interchangeable. Every `[measured]` row below is
attributed to one of these three:

| Runner | What it is | What it can prove |
|---|---|---|
| `docker.exe` (Windows binary, invoked from WSL) | `/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe` | Engine, context, image and endpoint facts. The binary is native Windows; only the invocation crosses from WSL. |
| Windows Python 3.12.7 | `C:\Users\Joseph\AppData\Local\Programs\Python\Python312\python.exe` | NT-layer behavior: `NtCreateFile`, `ntpath.realpath`, `os.stat` reparse flags, Host package import. |
| WSL shell | Ubuntu-22.04 | Linux-side filesystem types, mount table, POSIX path facts. Proves nothing about NT semantics. |

## 1. Docker

### Binary and version

| Fact | Value | Tag |
|---|---|---|
| `docker.exe` (Windows form) | `C:\Program Files\Docker\Docker\resources\bin\docker.exe` | [measured] docker.exe |
| `docker.exe` (WSL form) | `/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe` | [measured] WSL shell |
| Client version | `29.3.1`, build `c2be9cc`, API `1.54`, `windows/amd64` | [measured] docker.exe |
| Docker Desktop | `4.67.0 (222858)` | [measured] docker.exe |
| Server engine | `29.3.1`, build `f78c987`, API `1.54` (min `1.40`), `linux/amd64` | [measured] docker.exe |
| containerd / runc | `v2.2.1` / `1.3.4` | [measured] docker.exe |
| Engine running? | Yes. Answered every query; 5 containers exist, 3 running. Not started or altered by this task. | [measured] docker.exe |

**Trap: there are two different docker CLIs on PATH.** `/usr/bin/docker` inside WSL is
the Ubuntu package at `29.1.3`, a *different build* from the `29.3.1` Windows binary,
and `/Docker/host/bin/docker.exe` is the Docker Desktop WSL-integration shim.
[measured] WSL shell. The TEST run must use the absolute Windows path above, never a
bare `docker` resolved from PATH.

### Endpoint

The npipe string inherited from the pin was a claim with no measured provenance.
It is now verified.

| Fact | Value | Tag |
|---|---|---|
| Current context | `desktop-linux` (marked `*`) | [measured] docker.exe |
| `desktop-linux` endpoint | `npipe:////./pipe/dockerDesktopLinuxEngine` | [measured] docker.exe |
| `default` context endpoint | `npipe:////./pipe/docker_engine` (**not** the one to use) | [measured] docker.exe |
| Other contexts present | `colima-qwoted`, `colima-sbox-qwoted` (both `unix:///home/profsynapse/.colima/...`) | [measured] docker.exe |
| `-H <npipe> version` answers? | Yes: server `linux/amd64`, engine `29.3.1`, API `1.54` | [measured] docker.exe |

Two unrelated Colima contexts exist. Because the run must not depend on whichever
context happens to be current, passing `-H npipe:////./pipe/dockerDesktopLinuxEngine`
explicitly is load-bearing, not decorative.

### Image availability

**An `alpine` image is already present. Nothing needs to be pulled.**

| Fact | Value | Tag |
|---|---|---|
| Tag | `alpine:3.20` | [measured] docker.exe |
| `.Id` and `RepoDigest` | `sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc` (identical) | [measured] docker.exe |
| OS / arch | `linux/amd64` | [measured] docker.exe |
| Created / size | `2026-04-16T23:53:26Z` / 3,641,182 bytes on disk, 12.2 MB reported | [measured] docker.exe |
| Default `Cmd` | `[/bin/sh]` | [measured] docker.exe |
| Other local images | `postgres:15-alpine`, `python:3.12-slim`, `unsloth/unsloth:latest`, `mechinterp-runner:local`, `mechinterp-runner:tf550-rebuild`, `mcp/playwright` (8 total) | [measured] docker.exe |

**`.Id` equals the RepoDigest because the containerd image store is enabled**
(`UseContainerdSnapshotter: true`, storage driver `overlayfs`). The descriptor
mediaType is `application/vnd.oci.image.index.v1+json`, so `.Id` here is the **OCI
index digest**, not the image *config* digest that the classic `overlay2` store would
report. [measured] docker.exe. Any expectation elsewhere that `.Id` is a config digest
was formed against a different storage backend and does not hold on this host.

The composition contract requires a **bare** digest matching `sha256:[0-9a-f]{64}`
(`synaptic_host/docker_v1/control_contract.py:578`) [read-from-source], and emits it
as the image argument directly (`control_private.py:411`) [read-from-source]. That
exact form was exercised read-only, over the explicit endpoint:

```
docker.exe -H npipe:////./pipe/dockerDesktopLinuxEngine inspect --type image \
  sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
```

It resolves to `alpine:3.20` with no network access. [measured] docker.exe. Note the
verb is top-level `docker inspect --type image` (`model.py:1016` defines the verb as
`inspect`) [read-from-source]. `docker image inspect --type ...` is a *different*
command that rejects `--type` on CLI 29.3.1 [measured] docker.exe, so the distinction
matters when reading or reproducing the argv.

## 2. Mount translation

> **AMENDMENT 2026-09-02, after `architect-run` review.** The recommendation later in
> this section — put mount sources on Ubuntu-22.04 ext4 under `/home/profsynapse` — is
> **SUPERSEDED and unreachable on the prepared path**. Two code facts I had not read:
> `prepared.py:44-52` (`_wsl_path`) *raises* unless the stage path is a Windows drive
> path and returns `/mnt/<letter>/<relative>`, and `local_io_v1/config.py:113-119`
> refuses a UNC project root. So the POSIX path is always `/mnt/<drive>/...`.
>
> Worse, the distro in the concatenation is **not** `Ubuntu-22.04`. It is pinned to
> `docker-desktop` at `training/providers/docker.json:39` [measured]. Inside that
> distro `/mnt` is the distro's **own ext4** (`/dev/sde`); drives are projected at
> `/mnt/host/c`, `/mnt/host/e`, `/mnt/host/f` (9p, `symlinkroot=/mnt/host/`)
> [measured]. `/mnt/f` exists there but is an **empty 5-entry skeleton with no files**,
> and `/mnt/f/Code/Toolset-Training` does not exist [measured], while
> `/mnt/host/f/Code/Toolset-Training/...` does [measured].
>
> **Net: the emitted mount source is a path that does not exist — a one-segment
> translation defect (`/mnt/f/` where the distro needs `/mnt/host/f/`), not an
> impossibility.** Escalated as a BLOCKER. The measurements below still stand; only
> the ext4-under-`/home` recommendation is withdrawn.
>
> Also measured: the `wsl.localhost` UNC reads a distro's own ext4 fine but is denied
> (`WinError 5`) on a 9p drvfs re-export in *both* distros. That is a filesystem-type
> rule, not a UNC-form or distro rule. Caveat: Windows-side UNC browsability is a
> proxy, not the engine's own bind resolution, which cannot be tested without starting
> a container.


**This is the section most likely to change the design, and the headline is negative:
the prepared path cannot bind a `F:\` drive-letter path at all.**

`docker_safe_unc_v1` (`control_contract.py:124-165`) validates every mount source and
rejects anything that does not literally start with `\\wsl.localhost\`
(`:129`), contains a forward slash (`:130`), exceeds 4096 UTF-8 bytes
(`:131`, `model.py:571`), is not NFC-normalized (`:128`), or contains a comma, quote,
control character, reserved DOS device name, or a component ending in space or dot
(`:132-159`). [read-from-source]

The translator builds the UNC by string concatenation, with no drive-letter branch
anywhere (`paths.py:109`, and identically at `prepared.py:223` and `model.py:993`):

```python
unc = "\\\\wsl.localhost\\" + mapping.distro + path.replace("/", "\\")
```

[read-from-source]

| Consequence | Detail | Tag |
|---|---|---|
| Drive-letter sources are rejected | `F:\Code\...` fails the `startswith("\\wsl.localhost\\")` guard before any filesystem access | [read-from-source] `control_contract.py:129` |
| Sources must be POSIX paths inside the integrated distro | Rendered as `\\wsl.localhost\Ubuntu-22.04\<posix path with backslashes>` | [read-from-source] `paths.py:109` |
| The mount flags | `--mount type=bind,source=<unc>,destination=/source,readonly` and `...,destination=/artifacts` (writable) | [read-from-source] `control_private.py:404-407` |
| Source and artifact roots must differ | Enforced: identical `unc_path` raises | [read-from-source] `control_private.py:377` |
| Purposes are typed | `SOURCE_READ` and `ARTIFACT_WRITE`, checked before argv assembly | [read-from-source] `control_private.py:374-376` |

**The worktree itself is not an eligible mount source.** `/mnt/f` is a 9p mount of the
`F:` drive [measured] WSL shell, so its Windows form is `F:\...`, which the contract
rejects. A caller could smuggle it through as
`\\wsl.localhost\Ubuntu-22.04\mnt\f\Code\...`, which passes the *string* contract,
but that routes Windows to 9p to WSL and back out to 9p for every I/O. That is
exactly the shape the lead's addendum warns against. It must not be used.

**Recommendation for the TEST run**: put both the source and artifact roots on the
distro's native ext4 (for example under `/home/profsynapse/...`, which renders as
`\\wsl.localhost\Ubuntu-22.04\home\profsynapse\...`), never under `/mnt/f` or
`/mnt/c`. Rationale in section 5.

### What is NOT established here

| Question | Status |
|---|---|
| uid/gid and permission bits as seen *inside* the container for a `\\wsl.localhost\` bind | [assumed]. Measuring it requires starting a container, which this task is forbidden to do. Memory holds no mount-translation fact for this project either. Deferred to TEST. |
| Case sensitivity as presented inside the container | [assumed], same reason. The source side is ext4 (case-sensitive) [measured] WSL shell, but the presentation through the bind is unverified. |
| Whether the registered root mapping already covers an ext4 path | Not read. Registration lives in the mapping registry / authority, which is `preparer-path`'s area (`paths.py:74-100`). Flagged as an open question. |

## 3. Windows Python

All rows measured by executing Windows Python, not by reading.

| Fact | Value | Tag |
|---|---|---|
| Interpreter | `C:\Users\Joseph\AppData\Local\Programs\Python\Python312\python.exe` | [measured] Windows Python |
| Version | `3.12.7` | [measured] Windows Python |
| Platform | `Windows-11-10.0.26200-SP0` | [measured] Windows Python |
| `os.name` | `nt` (confirms the NT layer is live, not a WSL shim) | [measured] Windows Python |
| Imports `synaptic_host`? | Yes, from `F:\Code\...\synaptic_host` | [measured] Windows Python |
| Imports `synaptic_host.docker_v1`? | Yes (`paths`, `control_contract`) | [measured] Windows Python |

### The invocation recipe

`scratch/test-phase/winpy.sh` is the checked-in recipe [read-from-source]. It sets
`WSLENV=PYTHONPATH` so the variable crosses the WSL/Windows boundary, and sets
`PYTHONPATH` in **Windows form with `;` separators and `\` separators**:

```
WINROOT='F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host-clean'
export WSLENV=PYTHONPATH
export PYTHONPATH="$WINROOT;$WINROOT\\synaptic-tuner"
```

The same recipe with `python.exe -c` instead of `-m pytest` is what produced the
import rows above. [measured] Windows Python.

### GIT_CONFIG_GLOBAL

| Fact | Detail | Tag |
|---|---|---|
| WSL `git` fails in this worktree | `fatal: detected dubious ownership` on the worktree and on the submodule | [measured] WSL shell |
| Windows `git.exe` works without it | `C:\Program Files\Git\cmd\git.exe`, version `2.44.0.windows.1`; returns branch, head `e1439de3`, submodule `aec998ee` | [measured] docker.exe-style direct invocation (Windows binary) |
| Required form | `GIT_CONFIG_GLOBAL` pointed at a file containing `[safe]` / `directory = *` | [read-from-source] `docs/architecture/native-windows-publication-closure.md:1188-1196` |
| `GIT_CONFIG_COUNT`/`KEY_0`/`VALUE_0` triple | Observed both to work and to fail by two different agents; `GIT_CONFIG_GLOBAL` is preferred because it survived both measurements | [read-from-source] same doc `:1198-1204` |
| It does **not** reach staging subprocesses | `_git_environment()` rebuilds the environment from a fixed whitelist (`PATH`, `SystemRoot`, `WINDIR`, `COMSPEC`, `PATHEXT`, `TEMP`, `TMP`, `LANG`, `LC_ALL`) and pins `GIT_CONFIG_NOSYSTEM=1` plus `GIT_CONFIG_GLOBAL=os.devnull`, by design | [read-from-source] same doc `:1207-1218`, describing `docker_staging.py:1012-1028` |
| `core.longpaths` | Unset in both WSL git and Windows git | [measured] both |

## 4. Network isolation and credentials

### Flags the Host emits today

The container is created with a fixed argument prefix
(`synaptic_host/docker_v1/control_private.py:391-395`) [read-from-source]:

```python
arguments = [
    "--name", labels.container_name, "--pull", "never",
    "--network", "none", "--cpus", str(runtime.cpu_count),
    "--memory", str(runtime.memory_bytes),
]
```

| Flag | Value | Effect | Tag |
|---|---|---|---|
| `--network` | `none` | No network namespace. Nothing can reach a registry or the internet from inside. | [read-from-source] `control_private.py:393` |
| `--pull` | `never` | The image is never fetched. A missing image is a hard failure, not a silent download. | [read-from-source] `control_private.py:392` |
| `--cpus` / `--memory` | from `runtime` | Always emitted; the diagnostic must supply both. | [read-from-source] `control_private.py:393-394` |
| `--gpus` | `driver=nvidia,device=0`, only when `accelerator_devices.kind == "nvidia"` | A CPU-only Alpine workload must not set this, and then no GPU flag is emitted. | [read-from-source] `control_private.py:396-397` |
| `--label` | 1 per owned label name | Ownership marking. | [read-from-source] `control_private.py:398-402` |
| `--env` | 1 per resolved pair | **Explicit allow-list only** (see below). | [read-from-source] `control_private.py:410` |
| verb | `create` (not `run`) | Creation and start are separate steps. | [read-from-source] `control_private.py:414-415`, `model.py:1013` |

A second copy of the same prefix appears at `cli.py:93` [read-from-source].

The pairing of `--network none` with `--pull never` is what makes the diagnostic safe
to run offline, and it is also why the already-present `alpine:3.20` matters: with
both flags set, an absent image cannot be recovered at runtime.

### Environment reaching the container

Environment is **not** inherited. It is resolved to explicit `(key, value)` pairs and
cross-checked three ways before use: the workload digest, the requested key tuple, and
the actual key order must all agree, or the build raises
(`control_private.py:384-390`) [read-from-source]. A stray ambient variable therefore
cannot leak in by accident.

### Credential-bearing files present on this host

Names only. No contents were read, and no values appear in this document or in any log
produced by this task.

| Path | Present? | Tag |
|---|---|---|
| `~/.git-credentials` | Yes | [measured] WSL shell |
| `~/.docker/config.json` | Yes | [measured] WSL shell |
| `~/.cache/huggingface/token` | Yes | [measured] WSL shell |
| `~/.netrc` | No | [measured] WSL shell |
| `~/.aws/credentials` | No | [measured] WSL shell |
| `~/.config/gh/hosts.yml` | No | [measured] WSL shell |
| Any `.env`, `*.pem`, `*.key`, `*secret*`, `*credential*` in the worktree (depth 3, excluding the submodule) | None found | [measured] WSL shell |

`~/.docker/config.json` declares `credsStore` and a `credHelpers` entry for
`europe-west2-docker.pkg.dev`; its `auths` object is empty. Structure only was
inspected, never values. [measured] WSL shell.

**Assessment**: the credential exposure risk for this diagnostic is low, because
`--pull never` means no registry authentication is attempted and `--network none`
means nothing inside the container could exfiltrate a secret even if one were mounted.
The residual risk is on the *host* side of the run: the artifact directory is mounted
writable, so it must not be pointed at a directory containing any of the files above.

## 5. Filesystem facts

| Drive | Filesystem | Label | Tag |
|---|---|---|---|
| `C:` | NTFS | (none) | [measured] Windows Python |
| `D:` | FAT32 | `WINDOWS11` | [measured] Windows Python |
| `E:` | exFAT | `T7` | [measured] Windows Python |
| `F:` | **NTFS** | `Storage` | [measured] Windows Python |
| `G:` | FAT32 | (removable) | [measured] Windows Python |

| WSL mount | Type | Meaning | Tag |
|---|---|---|---|
| `/` | **ext4** on `/dev/sdf` | The distro's native VHD. Reachable from Windows as `\\wsl.localhost\Ubuntu-22.04\`. | [measured] WSL shell |
| `/mnt/c` | **9p** | `C:` drive projected into WSL. | [measured] WSL shell |
| `/mnt/f` | **9p** | `F:` drive projected into WSL. **The worktree lives here.** | [measured] WSL shell |

WSL automount options are `metadata,umask=22,fmask=11`, and `systemd=true`
[measured] WSL shell (`/etc/wsl.conf`).

### Which paths the TEST run should use, and why

| Path class | Verdict | Reason |
|---|---|---|
| `/home/profsynapse/...` (ext4) | **Use for mount sources and artifact destinations.** | Native ext4 in the distro; renders to a `\\wsl.localhost\Ubuntu-22.04\...` UNC, which is the only form the mount contract accepts. No 9p hop. |
| A native Windows NTFS path driven by Windows Python | Fine for *host-side* files (probe scripts, the worktree itself). | `F:` is real NTFS, and the NT layer reaches it directly. |
| `/mnt/f/...` or `/mnt/c/...` as a **container mount source** | **Do not use.** | 9p. Its Windows form is a drive letter, which the contract rejects; forcing it through as `\\wsl.localhost\Ubuntu-22.04\mnt\f\...` adds a Windows-to-9p-to-WSL-to-9p round trip. |

### Long paths and reparse points

| Fact | Value | Tag |
|---|---|---|
| `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled` | `REG_DWORD 0x1` (enabled) | [measured] `reg.exe` |
| A 460-character directory chain under the worktree | Created and removed successfully | [measured] Windows Python |
| `core.longpaths` in git | Unset (WSL git and Windows git alike) | [measured] both |
| Worktree root a reparse point? | **No** | [measured] Windows Python |
| `F:\Code\Toolset-Training` a reparse point? | **No** | [measured] Windows Python |
| `F:\` a reparse point? | **No** | [measured] Windows Python |
| `scratch/prepare-host` a reparse point? | **No** | [measured] Windows Python |

The worktree is reparse-clean from the drive root down to the scratch directory.

## 6. The two queued host probes

Both were written **and executed**, because each touches only a scratch directory and
starts no container. Scripts are checked in under
`<worktree>/scratch/prepare-host/`. Both ran on Windows Python 3.12.7.

### Probe (a): `NtCreateFile` with an empty or missing relative name

Script: `scratch/prepare-host/probe_nt_empty_name.py`. It opens a directory handle
with `FILE_FLAG_BACKUP_SEMANTICS`, then issues relative `NtCreateFile` calls with
disposition `FILE_OPEN` (never `FILE_CREATE`), so it creates nothing.

**The queued question offered two candidate answers and the real answer is neither.**

| Case | Result on `F:` (NTFS) | Result on `\\wsl.localhost\Ubuntu-22.04\...` (ext4) | Tag |
|---|---|---|---|
| **Empty** name, `Length=0`, `RootDirectory` set | `0x00000000` **STATUS_SUCCESS** | `0x00000000` **STATUS_SUCCESS** | [measured] Windows Python |
| **Missing** name, `ObjectName=NULL` | `0xC0000033` STATUS_OBJECT_NAME_INVALID | `0xC0000033` STATUS_OBJECT_NAME_INVALID | [measured] Windows Python |
| Nonexistent name `zzz-no-such` (control) | `0xC0000034` STATUS_OBJECT_NAME_NOT_FOUND | `0xC0000034` STATUS_OBJECT_NAME_NOT_FOUND | [measured] Windows Python |

Neither hypothesised code appears for the empty-name case. `STATUS_NO_SUCH_FILE`
(`0xC000000F`) was not returned in any case. An **empty relative name under a
directory handle reopens the directory itself and succeeds**, which is the documented
NT behavior for a relative open with a zero-length name.

**Why this matters**: any code that treats "empty relative name" as a reliable way to
provoke a not-found error is wrong on this host. It will instead receive a second
valid handle to the same directory. The `0xC0000034` code that the question expected
belongs to the *nonexistent-name* case, which is a different situation. The result is
identical on NTFS and on the WSL ext4 share, so it is not filesystem-dependent.

### Probe (b): does `ntpath.realpath` ever emit a `\\?\` prefix?

Script: `scratch/prepare-host/probe_realpath_prefix.py`.

**Answer: no. `ntpath.realpath` never *adds* the prefix. It only preserves one that
was already in the input.** [measured] Windows Python.

| Input | Output length | `\\?\` prefix? | Tag |
|---|---|---|---|
| Worktree root | 73 | No | [measured] Windows Python |
| `F:\` | 3 | No | [measured] Windows Python |
| Scratch dir | 94 | No | [measured] Windows Python |
| Path containing `..` | 94 | No (normalized) | [measured] Windows Python |
| Lowercased drive letter `f:` | 94 | No; **drive letter normalized back to uppercase `F:`** | [measured] Windows Python |
| `\\wsl.localhost\Ubuntu-22.04\home\profsynapse` | 45 | No (stays a plain UNC) | [measured] Windows Python |
| **460-character** path | 460 | **No** | [measured] Windows Python |
| Input already prefixed `\\?\F:\...` | 98 | **Yes**, preserved | [measured] Windows Python |

Length alone does not trigger the prefix: a 460-character path came back plain, well
past the 260 `MAX_PATH` threshold. The drive-letter normalization is a small bonus
finding worth knowing, since a lowercase drive letter in an input silently becomes
uppercase in the output.

### Probe coverage gap

| Untested case | Status |
|---|---|
| Substituted drive (`subst`) | [assumed] not to add a prefix, by consistency with the cases above. **Not measured**: creating a substituted drive is a host state change, outside the read-only boundary. |
| Junction or symlink in the project root path | Not applicable here. Every level from `F:\` down is reparse-clean [measured], so no junction exists on this path to test. |

## 7. Other facts the architect needs

### Docker Desktop configuration

From `C:\Users\Joseph\AppData\Roaming\Docker\settings-store.json` [measured] WSL shell:

| Setting | Value | Why it matters |
|---|---|---|
| `UseContainerdSnapshotter` | `true` | Explains `.Id` == index digest and storage driver `overlayfs`. Expectations formed against `overlay2` do not transfer. |
| `IntegratedWslDistros` | `["Ubuntu-22.04"]` | Exactly the distro the UNC translation targets. The pieces line up. |
| `CustomWslDistroDir` | `F:\DockerDesktopWSL` | Docker's own WSL data lives on `F:`. Unrelated to bind-mount routing, but it is why `F:` free space affects the engine. |
| `AutoStart` | `false` | The engine will not restart itself. If it is down at TEST time, someone must start Docker Desktop by hand. |
| `SettingsVersion` | `43` | — |

**There is no drive file-sharing list in the settings store.** [measured] WSL shell.
That is expected for the WSL2 backend, where bind mounts arrive through the WSL
integration rather than through the Hyper-V-era shared-drives mechanism. This is a
second, independent reason the design must route mounts through
`\\wsl.localhost\Ubuntu-22.04\` rather than through `F:`.

### Engine state to respect

Three containers are running and must not be disturbed: `cc-test-pg`
(`postgres:15-alpine`), `heuristic_lamarr` and `youthful_margulis` (both
`unsloth/unsloth:latest`). [measured] docker.exe. Container names are unique per
engine, so the diagnostic's `--name` must not collide with these.

Engine capacity: 16 CPUs, 20,971,155,456 bytes of memory, `DockerRootDir`
`/var/lib/docker`, kernel `6.18.33.2-microsoft-standard-WSL2`. [measured] docker.exe.
`--cpus` and `--memory` are mandatory in the emitted argv, so the diagnostic must pick
values at or below these.

### Note on CLAUDE.md

The task brief stated that `CLAUDE.md` is gitignored and absent from worktrees. **It is
in fact present** at the worktree root, 22.2 KB. [measured] WSL shell. This task did
not read, modify, or write it. Flagging only because the brief's premise was
inaccurate and a later phase might rely on it.

## Summary for the architect

1. **The endpoint pin is verified.** `npipe:////./pipe/dockerDesktopLinuxEngine` is the
   `desktop-linux` context and answers. Pass it explicitly; two Colima contexts also
   exist, so relying on the current context is fragile.
2. **No pull is needed.** `alpine:3.20` is local at
   `sha256:d9e853e87e55...b6bc`, and that bare digest resolves over the explicit
   endpoint in exactly the form the contract emits.
3. **Drive-letter mounts are impossible on this path**, and the worktree is on 9p.
   Source and artifact roots must sit on distro ext4 and render as
   `\\wsl.localhost\Ubuntu-22.04\...`. This is the single most design-relevant finding.
4. **Probe (a) refuted its own premise.** An empty relative name succeeds; it does not
   return either candidate error code.
5. **Probe (b) is a clean negative.** `ntpath.realpath` never introduces a `\\?\`
   prefix, not even at 460 characters.
6. **Container-internal uid, permissions and case behavior remain unmeasured** and are
   tagged `[assumed]` throughout, because measuring them requires starting a container.
   They are the natural first assertions for the TEST phase.

## Open questions for the architect and for `preparer-path`

| # | Question | Owner |
|---|---|---|
| 1 | Is a WSL root mapping already registered for an ext4 path, or must the diagnostic register one? The registry and authority path was not read here. | `preparer-path` |
| 2 | What uid/gid does the container see on a `\\wsl.localhost\` bind, and is `/artifacts` actually writable by the workload user? | TEST |
| 3 | Does any consumer assume `.Id` is a config digest rather than the index digest the containerd store reports? | `preparer-path` |
| 4 | Which `--cpus` / `--memory` values should the CPU-only diagnostic request, given 16 CPUs and ~20.9 GB on the engine? | architect |
| 5 | Does the Alpine stand-in traverse the same activation branch as the engine workload, given `--gpus` is emitted only for `kind == "nvidia"`? If the paths diverge before container start, the diagnostic's coverage claim is narrower than plan step 3 assumes. | architect |
