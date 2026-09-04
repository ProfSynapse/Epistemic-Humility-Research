# POSIX-first local execution — factual inventory

> Prepared by `preparer-posix` for task #293 (plan-mode consultation, plan task #291).
> Read-only against the Host worktree at HEAD `06aa7177` (Host origin `557ce1be`, engine pin `ce539b70`).
> No source file was modified. My peer on this consultation is `architect-posix`; it rules, I inventory.

**Provenance tags.** Every claim below carries one:
`[SOURCE]` read from code in this worktree, with `file:line`.
`[SPEC]` read from documentation or a vendor contract, not measured here.
`[UNVERIFIED-BY-EXECUTION]` reasoned, not run.
`[MEASURED]` produced by a command in this session; the command is quoted.

**Concurrency note.** `coder-verifier` is editing `synaptic_host/docker_staging.py` and
`tests/synaptic_host/test_docker_staging.py` under task #290. Every line number I give for those two
files is at HEAD `06aa7177` and will shift. I did not touch them.

**Repoint, 2026-09-04.** That shift happened: `coder-verifier`'s ruling (4) landed as `043b0554`.
Every `docker_staging.py` cite below now carries its defining symbol and its `043b0554` line beside
the `06aa7177` line, so the citation survives the next shift too. The symbol is authoritative; the
numbers are a convenience. Nothing in the *content* of this document changed in the repoint — the
two substantive corrections are the dated paragraphs under 1.4 and 3.5.

---

## 0. Corrections the architect must not inherit

Four premises carried into this consultation are wrong or imprecise at HEAD. Taking them at face value
would misprice the port in both directions.

**0.1 There is no HF Jobs provider in `synaptic_host`.** The brief names "the Modal and HF Jobs
providers (`synaptic_host/*modal*`, `*hf*`; ~2,512 lines)". The 2,512 is exactly
`modal_provider.py` (1,077) + `modal_resolver.py` (775) + `modal_training.py` (660). No file in the
package matches `*hf*`, and only `docker_training.py` mentions HuggingFace at all. `[MEASURED]`

```
find synaptic_host tests/synaptic_host -name '*.py' | grep -i 'modal\|hf\|jobs'
/usr/bin/grep -rli 'huggingface\|hf_jobs\|hfjobs' synaptic_host --include='*.py'
```

**0.2 The Host already has a complete, real POSIX filesystem arm.** The prior inventory's phrase
"the endpoint layer is Windows-only by construction" (inv 5.1) is true of the *endpoint*, and was
read across as if it were true of the package. It is not. `synaptic_host/local_io_v1/posix.py` is
835 lines of working `os`/`fcntl` code implementing all 21 methods of the shared
`PosixFilesystemPortV1` Protocol (`filesystem.py:309-340`), with `O_NOFOLLOW` on every open,
fstat-based identity re-proof, `fcntl.flock` admission, and a fsync-durable journal. No
`NotImplementedError`, no stub bodies. `[SOURCE]` `posix.py:102, 245, 284, 306, 321, 331, 342, 382,
446, 474, 506, 563, 576, 705, 791`

**0.3 `security.py`'s POSIX arms are real implementations, not fallbacks.** Five of the eight
`os.name` branches in that file are true if/else dispatches whose POSIX side independently enforces
`0o700` directories, `0o600` key files, `st_uid == os.geteuid()` ownership, and `O_NOFOLLOW`
opens. `[SOURCE]` `security.py:716, 776, 797, 906, 989, 995, 1000`. None of the eight is a no-op
return or a raise on the POSIX side. The ACL chain is dead code on POSIX, not a hole in it.

**0.4 The `cp1252` defect is not in the driver at HEAD.** The brief names "the driver's cp1252
defects". The literal `cp1252` appears nowhere in `synaptic_host`, its tests, or the driver
`[MEASURED]`; all three driver file reads are explicit `encoding="utf-8"`
(`run_prepared_training.py:336, 1286, 1768`). The real hazard is the *class* the B-3 blocker came
from, `subprocess(..., text=True)`, which uses the locale encoding and translates newlines. It
survives at four sites: `materialize_model_inventory.py:226`, `run_prepared_training.py:176, 1817`,
and in production at `launcher.py:177, 410`. `[SOURCE]` On POSIX the locale encoding is normally
UTF-8 and the newline translation is a no-op, so this class *vanishes* rather than needing a fix
(section 4, class E).

**0.5 Counts differ from the prior inventory; both are stated.** I measure 58 production files /
40,109 lines and 62 test files / 38,101 lines. The prior inventory reported 57 files / 40,109 lines
with a 40,028-line test tree. The production line total agrees exactly; the file count and the test
total do not. I report only what I produced. `[MEASURED]`

```
find synaptic_host -name '*.py' | wc -l        # 58
find synaptic_host -name '*.py' -exec wc -l {} + | tail -1   # 40109 total
find tests/synaptic_host -name '*.py' | wc -l  # 62
find tests/synaptic_host -name '*.py' -exec wc -l {} + | tail -1  # 38101 total
```

---

## 1. Windows-only-by-construction inventory

### 1.0 The sweep

`[MEASURED]`, run from the worktree root with `EHR_SEARCH_OK=1` exported:

```
for pat in 'os\.name' 'sys\.platform' 'platform\.system' 'npipe' 'docker\.exe' \
           'PureWindowsPath' 'WindowsPath' 'wsl' 'WSL' 'DrvFs\|drvfs' 'SystemRoot' \
           'cp1252' 'USERPROFILE' 'ctypes' 'winreg' 'AF_UNIX' 'unix://' 'docker\.sock' \
           'drive_mount_root' 'wsl_distro'; do
  n=$(grep -rn "$pat" synaptic_host --include='*.py' | wc -l)
  t=$(grep -rn "$pat" tests/synaptic_host --include='*.py' | wc -l)
  printf '%-22s prod=%-5s tests=%s\n' "$pat" "$n" "$t"
done
```

| pattern | prod | tests | reading |
|---|---|---|---|
| `os.name` | 20 | 29 | the whole platform-branch surface |
| `sys.platform` | 3 | 2 | capability reporting only |
| `platform.system` | 1 | 1 | one Linux gate in `launcher.py` |
| `npipe` | 3 | 11 | the endpoint constant, three sites |
| `docker.exe` | 6 | 39 | CLI discovery + the WSL proxy constant |
| `PureWindowsPath` | 0 | 2 | **absent from production** |
| `WindowsPath` | 16 | 5 | |
| `wsl` / `WSL` | 183 / 158 | 151 / 181 | an entire WSL interop subsystem |
| `DrvFs` | 0 | 2 | comments only |
| `SystemRoot` | 7 | 28 | the four-key seal + two git scrubs |
| `cp1252` | **0** | **0** | see 0.4 |
| `USERPROFILE` | 0 | 2 | B-13's absent key, still absent |
| `ctypes` | 284 | 27 | three files only |
| `winreg` | 0 | 0 | no registry dependency |
| `AF_UNIX` | **0** | **0** | no POSIX socket anywhere |
| `unix://` | **0** | **0** | confirms inv 5.1 |
| `docker.sock` | **0** | **0** | |
| `drive_mount_root` | 23 | 16 | the B-1' profile field |
| `wsl_distro` | 14 | 11 | |

The three zero rows for `AF_UNIX`, `unix://` and `docker.sock` are the single most important
negative result in this document: **no POSIX transport exists to extend. It must be written.**

### 1.1 Windows-only by construction (no POSIX arm exists)

| # | Site | What it does | Lines | Verdict |
|---|---|---|---|---|
| W1 | `docker_prepared_composition.py` whole module, gate at `:104-115` | Binds one Windows `docker.exe` to the constructed `desktop-linux` npipe endpoint. First predicate is `os_name != "nt" ... raise ValueError("Windows Docker Host policy is unavailable")`. | 355 | **By construction.** Nothing here survives a POSIX port; it is replaced, not branched. `[SOURCE]` |
| W2 | `docker_v1/model.py:1135-1160` `DockerCLIEnvironmentV1` | The four-key seal. `expected_keys = ("SystemRoot","TEMP","TMP","WINDIR")` compared by **tuple equality**, and every value must pass `_windows_drive_path_v1(value)`. | ~40 | **By construction.** On POSIX no value could validate; the key names do not exist. `[SOURCE]` |
| W3 | `docker_v1/model.py:1187-1205` `DockerLocalEndpointDescriptorV1` | Pins `source_context_ref == "desktop-linux"` and `host == "npipe:////./pipe/dockerDesktopLinuxEngine"` in `__post_init__`. Anything else raises `POLICY_INVALID`. | ~20 | **By construction.** This is the transport, hard-coded as a Windows named pipe. `[SOURCE]` |
| W4 | `docker_v1/interop.py` | Closed argv0-only CLI interop for WSL hosts: `_WINDOWS_EXECUTABLE = re.compile(r"([A-Z]):\\...")`, `_INTEROP_PATH = /run/WSL/<n>_interop`, `_DOCKER_DESKTOP_WSL_EXECUTABLE = "/Docker/host/bin/docker.exe"`, plus Windows reserved-device-name rejection (`CON`, `PRN`, `COM1..9`, superscript variants). | 374 | **By construction.** WSL exists only on Windows. `[SOURCE]` |
| W5 | `docker_v1/paths.py` + the WSL types in `model.py` + `binding.py` + `prepared.py` | `DockerWSLPathTranslatorV1` and an HMAC-authenticated WSL root-mapping registry: `DockerWSLRootMappingV1`, `AuthenticatedDockerWSLRootMappingV1`, `DockerWSLRootMappingHmacAuthorityV1`, `DockerWSLPathPurposeV1`, `DockerWSLInteropCodeV1`, `DockerPrivateWSLInteropChannelV1`. | 125 + 808 + 251 + a share of `model.py` (70 WSL lines) | **By construction.** The whole concept is drive-letter-to-`/mnt/<x>` translation. `[SOURCE]` |
| W6 | `security.py:19-649` | The Windows ACL block: 20 distinct Win32 calls through `ctypes.WinDLL` (`CreateFileW`, `CreateDirectoryW`, `GetSecurityInfo`, `SetKernelObjectSecurity`, `GetAclInformation`, `GetAce`, `ConvertStringSecurityDescriptorToSecurityDescriptorW`, `OpenProcessToken`, `GetTokenInformation`, `ConvertSidToStringSidW`, `GetVolumeInformationW`, …). Notably it does **not** call `SetNamedSecurityInfoW`; `security.py:248` records that the path-based editor was deliberately rejected after B-11-M1. | ~609 incl. ~32 dispatch lines | **By construction, and dead on POSIX today.** The POSIX arms already exist beside it (0.3). `[SOURCE]` |
| W7 | `local_io_v1/windows.py` | The native-Windows retained-handle port: 122 `ctypes` references, `NtCreateFile`, `NtSetInformationFile`/`FileLinkInformationEx`, `GetFileInformationByHandleEx`, triple reparse-point defense, an NTFS-by-name requirement at `:745`. | 1,699 | **By construction, and already isolated.** Its POSIX sibling exists and is complete. `[SOURCE]` |
| W8 | `docker_staging.py:335-...` `_windows_native()` (`043b0554:336`) | `if os.name != "nt": raise ValueError("Windows staging cleanup is unavailable")`, then binds `kernel32`/`ntdll`. 93 `ctypes` references in this file. | ~93 ctypes lines | **By construction, with a POSIX arm already present at the call site**: `:1805-1809` (`043b0554:1816-1820`) passes `None` when not `nt`. Deleting it costs nothing on POSIX. `[SOURCE]` |

**Windows-only-by-construction subtotal.** Roughly 355 + 40 + 20 + 374 + 1,184 + 609 + 1,699 + ~93
≈ **4,374 lines**, about 10.9% of the 40,109-line package. This is a *bound on what must be replaced
or excluded*, not a bound on the work: W1-W5 (≈1,973 lines) have no POSIX counterpart and are the
actual port. W6-W8 (≈2,401 lines) already have working POSIX counterparts beside them and cost
nothing but their own exclusion.

### 1.2 Platform branches that already have a working POSIX arm

| # | Site | POSIX behaviour | Verdict |
|---|---|---|---|
| P1 | `publication_composition.py:407-413` | The dispatch. `if os.name == "nt": return WindowsRetainedHandlePortV1() ... return PosixRetainedDirfdPortV1()`. Imports are branch-local by design so a POSIX process never imports `ctypes.WinDLL` and a Windows process never imports `fcntl` (`:397-406`). | **Portable, already dispatched.** `[SOURCE]` |
| P2 | `security.py:714, 751, 780, 886, 973` | Five if/else dispatches. POSIX side: `os.mkdir(path, 0o700)`; `os.fchmod(fd, mode & 0o700)` guarded by uid and non-symlink checks; exact `S_IMODE == 0o700` validation; key create `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` at `0o600`; key read with lstat/open/fstat triple check incl. `nlink == 1` and `size == 32`. | **Portable, POSIX arm is the stronger half.** `[SOURCE]` |
| P3 | `security.py:1142-1147` `ScopedGitRemoteReader._run` | Nine-key scrub plus `SystemRoot` only when `os.name == "nt"`. The comment records that `SystemDrive`, `windir`, `COMSPEC`, `PATHEXT` were each measured unnecessary. POSIX simply omits the tenth key. | **Portable as written.** This is B-7's fix and it is already platform-correct. `[SOURCE]` |
| P4 | `cli.py:623-627` | Seven-key git scrub, but each key is guarded `if key in os.environ`. On POSIX only `PATH` survives, which is what git needs. | **Portable by construction of the guard.** `[SOURCE]` |
| P5 | `docker_staging.py:170-174` `_apply_file_mode` (`043b0554:170-174`) | `path.chmod(stat.S_IREAD if os.name == "nt" else 0o444)`, else `0o755`/`0o644`. | **Portable.** `[SOURCE]` |
| P6 | `docker_staging.py:177-183` `_verify_file_mode` (`043b0554:177-183`) | `if os.name == "nt": return True`. Otherwise requires `S_IMODE == 0o444 / 0o755 / 0o644` exactly. Called at `:1298` (closure arm, `043b0554:1298`) and `:1526` (read-only arm, `043b0554:1538`). | **Portable, and it does change meaning — but see the 2026-09-04 correction under 3.5, which withdraws my recommendation.** `[SOURCE]` |
| P7 | `docker_staging.py:926-929` `_mode_projection` (`043b0554:926-929`) | `"windows-regular"` on nt, else `f"posix-{S_IMODE:04o}"`. | **Portable, but the value is not.** See 1.4. `[SOURCE]` |
| P8 | `local_io_v1/filesystem.py:72-81, 494, 567-591` | `_POSIX_PLATFORMS = ("linux","darwin","freebsd","openbsd","netbsd")`, `_SUPPORTED_PLATFORMS` adds `win32`, `_DIRECTORY_ADMISSION_PLATFORMS = ("linux","win32")`. Capability reporting only; never selects a module. | **Portable.** Note `darwin` is already declared supported here. `[SOURCE]` |

### 1.3 The macOS gate — one predicate, and it is the smallest high-value finding in this document

`local_io_v1/posix.py:73` `[SOURCE]`:

```python
if family == "posix" and platform_value.startswith("linux"):
```

`detect_posix_capability_v1` reports `AVAILABLE` only on Linux. On `darwin` it returns
`UNAVAILABLE` and no features, even though every primitive the body then checks for
(`O_CLOEXEC`, `O_DIRECTORY`, `O_NOFOLLOW`, `os.supports_dir_fd`, `os.supports_follow_symlinks`,
`fcntl.flock`, `os.register_at_fork`) exists on macOS `[SPEC]`. The orchestration layer one file
away already lists `darwin` as a supported POSIX platform (`filesystem.py:72`), so the package
contradicts itself about macOS.

This is a **one-predicate change plus a measurement**, not a port. It must not be widened blind: the
body's own assertions are the specification, and whether `os.supports_dir_fd` and
`os.supports_follow_symlinks` actually contain the five required functions on CPython/macOS is
`[UNVERIFIED-BY-EXECUTION]` here and is the first thing a macOS box should print.

### 1.4 A cross-platform digest divergence, stated precisely and not overstated

`docker_staging.py:1612` (`_source_manifest`, `043b0554:1624`) puts `_mode_projection(info)` into
the `platform_mode` field of every source-manifest entry, and `:1614` (`043b0554:1626`) digests the
list under
`b"synaptic-host-docker-source-manifest/v1"` `[SOURCE]`. Therefore **the source-manifest digest of
byte-identical trees differs between Windows and POSIX** — `"windows-regular"` versus `"posix-0644"`.

What this does *not* mean: it is not a latent blocker today. The digest is written at `:1853-1877`
(`043b0554:1865-1877`) and re-verified at `:1751-1757` (`043b0554:1763-1773`) against the projection recorded **in the same run on the same
machine**, and flows onward only as `mount_verification_digest` (`docker_v1/prepared.py:162`) within
that run. I found no golden constant and no cross-machine comparison. `[MEASURED]` — the consumer
sweep was `/usr/bin/grep -rn 'source-manifest\|source_manifest\|platform_mode' synaptic_host
tests/synaptic_host --include='*.py'`.

What it does mean: the moment any design compares a staging digest produced on one platform against
one produced on another — a cloud lane reproducing a local stage, a cached stage moved between
machines, a recorded expected value in a release record — the comparison fails for a reason that
looks like corruption. The architect should decide now whether `platform_mode` belongs in a digest
at all.

**Correction, 2026-09-04 (preparer-posix).** The last sentence above is answered, and my own lean
was wrong. `platform_mode` **stays in the digest**, ruled by architect-posix and verified by me
against the tree. The reason is the one given in the 3.5 correction below: on POSIX `platform_mode`
carries every staged file's real four-digit mode, and the source-manifest digest is re-verified
before the closure verifier runs, so the projection *is* the source stage's mode coverage. Removing
it and deleting the closure-arm exec-bit call site are individually defensible and jointly fatal —
together they leave the source stage with no mode coverage at all. The divergence documented above
is still real and still bites the first design that compares a staging digest across machines; it is
a constraint on any future cross-machine digest scheme, not a cleanup to perform. Everything else in
1.4 stands as measured.

### 1.5 The portable remainder

Subtracting section 1.1 leaves roughly **35,735 of 40,109 lines, about 89%**, with no platform
branch of any kind. The three largest subpackages are `docker_v1` (13,825 lines total, of which the
WSL/endpoint/seal material in 1.1 is ≈1,600), `local_io_v1` (7,231, already two-armed), and
`bundle_io_v1` (1,798, no platform branch). `[MEASURED]`

The `ctypes` surface — the sharpest proxy for "native Windows" — lives in exactly **three
production files**: `local_io_v1/windows.py` (122), `docker_staging.py` (93), `security.py` (68),
plus one incidental reference in `publication_composition.py`. `[MEASURED]`
`/usr/bin/grep -rc 'ctypes' synaptic_host --include='*.py' | grep -v ':0$'`

### 1.6 The test tree is not the obstacle

`[MEASURED]`:

| measure | value |
|---|---|
| `def test_` across `tests/synaptic_host` | 1,053 |
| `skipif` occurrences, all files | 25 |
| files gating on `os.name != "nt"` (Windows-only) | 2 — `test_docker_staging.py`, `test_security.py` |
| files gating on `os.name == "nt"` (POSIX-only) | 2 |

Of 1,053 tests, 25 skip markers exist in total and only two files carry Windows-only gates. The
suite was written platform-neutral against fakes: `test_windows_port_contract.py` is 32 tests of the
*Windows* port that run on Linux against an in-memory fake, by explicit design
(`test_windows_port_contract.py:1-19`). A POSIX port does not invalidate the suite; it turns
currently-skipped POSIX tests green and currently-green Windows tests into skips.

**One test is a source-scraping pin and must be carried by hand through any `security.py` split.**
`tests/synaptic_host/test_security.py:1091-1092` `[SOURCE]`:

```python
assert "_ensure_private_storage_directories(repair=False)" in source
assert "repair=True" not in source
```

It scrapes `inspect.getsource(FileHmacAuthenticator._key)`. Any rename, any reformat of that call
across two lines, any move of the call out of `_key` breaks it even when the behaviour is correct.

---

## 2. POSIX transport research

### 2.1 The measurement I was authorised to make, and exactly what it proves

The team-lead authorised checking the socket inside WSL Ubuntu-22.04 and making **at most one**
read-only request from the standard library. I did both.

`[MEASURED]` — `python3` script written to the session scratchpad, 33 lines, imports `os`, `stat`,
`socket`, `http.client`, `json` and nothing else:

| property | value |
|---|---|
| path | `/var/run/docker.sock` (also present at `/run/docker.sock`) |
| `S_ISSOCK` | `True` |
| symlink | `False` |
| mode | `0o660` |
| uid / gid | `0` / `1001` (`docker` group) |
| process euid / egid | `1000` / `1000`, with gid `1001` in `os.getgroups()` |
| `os.access` R/W | `True` / `True` |
| HTTP status of `GET /version` | **200** |
| `Version` | `29.3.1` |
| `ApiVersion` | `1.54` |
| `MinAPIVersion` | `1.40` |
| `Os` / `Arch` | `linux` / `amd64` |
| `Components` | `Engine`, `containerd`, `runc`, `docker-init` |

The connection was a plain `socket.socket(AF_UNIX, SOCK_STREAM)` with an
`http.client.HTTPConnection` subclass overriding `connect()`. No ctypes. No third-party package. No
overlapped I/O. No `DOCKER_HOST` was set; the path was hard-coded.

**Tag: Docker-Desktop-on-Windows-through-WSL.** This is Docker Desktop's WSL integration exposing
its engine socket inside the Ubuntu-22.04 distro on this Windows machine. **It is not evidence about
native Linux and not evidence about macOS.** What it does establish, and the only thing it
establishes, is that the shape of the client is right: an `AF_UNIX` stream socket speaking HTTP/1.1
that the Python standard library reaches in a few dozen lines. Proposition (a) from my teachback is
confirmed under one configuration and remains open under the two that matter for shipping.

### 2.2 Route (a) — the `docker` CLI on PATH

| aspect | POSIX behaviour | tag |
|---|---|---|
| discovery | `docker` on `PATH`, no `.exe` suffix, no single-candidate rule needed. The Windows code takes `PATH`, appends `docker.exe`, `resolve(strict=True)`, and demands **exactly one** candidate (`docker_prepared_composition.py:122-133`). | `[SOURCE]` for the Windows half |
| endpoint resolution | The CLI resolves, in order: `--host`/`-H`, `DOCKER_HOST`, the active context from `~/.docker/config.json` + `~/.docker/contexts/`, then the platform default socket. | `[SPEC]` |
| what it reads from the environment | `HOME` (for `~/.docker`), `DOCKER_HOST`, `DOCKER_CONTEXT`, `DOCKER_CONFIG`, `DOCKER_CERT_PATH`, `DOCKER_TLS_VERIFY`, plus proxy variables. | `[SPEC]` |
| credential helpers | `config.json` `credsStore`/`credHelpers` spawn `docker-credential-*` binaries off `PATH`. Only registry auth needs them. The prepared path pulls no image at run time and runs credential-free, so this is inert here. | `[SPEC]` + `[SOURCE]` for the credential-free property |
| what B-13 becomes | B-13 was "the sealed four-key environment omits `USERPROFILE`, so context lookup fails". The POSIX analogue is exact and predictable: seal away `HOME` and `docker` cannot find `~/.docker` either. The failure recurs with a different key name unless the endpoint is constructed rather than discovered — which is what the B-13 fix already does (`docker_prepared_composition.py:150-158`). | `[UNVERIFIED-BY-EXECUTION]` |

The strongest argument for keeping the CLI is that the B-13 remedy already generalises: the Host
constructs the endpoint from constants and proves the daemon alive with an explicit `--host` probe
(`docker_prepared_composition.py:166-178`). Swap the constant from an npipe URL to
`unix:///var/run/docker.sock` and that entire mechanism ports without redesign.

### 2.3 Route (b) — the Engine API over the unix socket, standard library only

The prior Route B costing was written for the Windows named pipe and does not transfer. On POSIX the
cost collapses:

| concern | Windows named pipe (prior costing) | POSIX unix socket |
|---|---|---|
| open the transport | `CreateFileW` via ctypes; overlapped I/O unknown; byte-mode unverified | `socket.socket(AF_UNIX, SOCK_STREAM)`, stdlib, **measured working** |
| HTTP framing | hand-rolled or `http.client` over a ctypes handle | `http.client.HTTPConnection` with `connect()` overridden — **measured working** |
| third-party dependency | none under Route B; Route A (docker-py) refused permanently by Q3(a) | none |
| ctypes surface added | new | **zero** |

**Endpoints the prepared path needs**, mapped to the Engine API `[SPEC]`, against the
`ApiVersion 1.54` / `MinAPIVersion 1.40` measured in 2.1:

| need | endpoint | note |
|---|---|---|
| liveness probe | `GET /version` | the one call I made |
| create | `POST /containers/create?name=<name>` | JSON body carries `Image`, `Cmd`, `Entrypoint`, `Env`, `User`, `HostConfig.Binds`, `HostConfig.NetworkMode: "none"` |
| start | `POST /containers/{id}/start` | |
| wait | `POST /containers/{id}/wait` | blocks; returns `StatusCode`. Replaces the driver's `docker events` polling instrument (#219) with a single blocking call |
| inspect | `GET /containers/{id}/json` | |
| logs | `GET /containers/{id}/logs?stdout=1&stderr=1` | **the one real re-implementation cost**: without `?tty=1` the stream is multiplexed in 8-byte frames (`STREAM_TYPE`, 3 pad, 4-byte big-endian length) and must be demultiplexed by hand |

**What docker-py does that we would re-implement**, so the architect can price it honestly: API
version negotiation, the log-stream demultiplexer, chunked/hijacked stream handling, error mapping
from HTTP status to typed exceptions, and TLS for remote daemons (not needed — Q1(a) puts the Host
on the user's own machine). `[SPEC]`

An honest count of the transport module: connection + request/response, the six endpoints, the
log demultiplexer, and error mapping is on the order of **250-400 lines** of stdlib Python.
`[UNVERIFIED-BY-EXECUTION]`

### 2.4 One-command spike plans

Neither was run. Both are one command. Do not run either on this Windows machine.

**Linux (native, not WSL).** Proves the socket shape, the group permission story, and rootless.

```
python3 - <<'PY'
import os, stat, socket, http.client, json
for p in ("/var/run/docker.sock", f"{os.environ.get('XDG_RUNTIME_DIR','/run/user/%d'%os.getuid())}/docker.sock"):
    try: st = os.lstat(p)
    except FileNotFoundError: print(p, "absent"); continue
    print(p, "socket=", stat.S_ISSOCK(st.st_mode), "mode=", oct(stat.S_IMODE(st.st_mode)),
          "uid/gid=", st.st_uid, st.st_gid, "access=", os.access(p, os.R_OK|os.W_OK))
    class C(http.client.HTTPConnection):
        def connect(self): s=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(5); s.connect(p); self.sock=s
    c=C("localhost"); c.request("GET","/version"); r=c.getresponse()
    d=json.loads(r.read()); print("  ", r.status, d.get("Version"), d.get("ApiVersion"), d.get("MinAPIVersion"))
PY
```

**macOS Docker Desktop.** Same script with the candidate list replaced by
`("/var/run/docker.sock", os.path.expanduser("~/.docker/run/docker.sock"))`. The question it settles
is which of the two exists, whether the first is a symlink to the second, and whether it is readable
without `sudo`. `[SPEC]`: Docker Desktop for Mac creates `~/.docker/run/docker.sock` and offers an
opt-in `/var/run/docker.sock` symlink that requires a privileged helper at install time; a design
that hard-codes `/var/run/docker.sock` will fail on a default macOS install.

**Rootless Docker on Linux** `[SPEC]`: the socket is `$XDG_RUNTIME_DIR/docker.sock`, owned by the
user, mode `0600`, and `DOCKER_HOST` is normally set by the user's profile. A design that ignores
`DOCKER_HOST` and hard-codes a path is wrong for every rootless user.

The design consequence of those three paragraphs is one sentence: **the endpoint must be a small
ordered candidate list with `DOCKER_HOST` honoured first, not a pinned constant** — which is the
opposite of what `DockerLocalEndpointDescriptorV1.__post_init__` enforces today
(`docker_v1/model.py:1194-1198`).

### 2.5 What the Modal provider assumes, and the shared-symbol answer

The prior plan warns that a change to a SHARED layer could "fork the local and cloud providers" and
gates work behind a provider inventory pass. That pass is now done for the three Modal files, and
the answer is clean.

**Platform branches in `modal_provider.py`, `modal_resolver.py`, `modal_training.py`: zero.**
`[MEASURED]` — `grep -nE "os\.name|sys\.platform|platform\.system|WindowsPath|ctypes|SystemRoot|WSL|drive_mount_root"` returns 0 in each of the three files.

**Docker, docker.exe, named pipe, unix socket, host subprocess: none.** They reach Modal through the
SDK object: `client = sdk.Client.from_credentials(...)` (`modal_provider.py:587`),
`objects.app.deploy(...)` (`:782-787`), `sdk.Function.from_name(...)` (`:788-792`). The one
`modal` import is deferred inside a function (`modal_training.py:363-364`,
`importlib.import_module("modal")`), so the package's zero-third-party-at-import-time property
holds. `[SOURCE]`

**Every symbol the three import from `synaptic_host`:** `[SOURCE]`

| from | symbols |
|---|---|
| `.security` | `FileHmacAuthenticator` (`modal_provider.py:34`); `BoundedGrantProvider`, `FileHmacAuthenticator`, `ScopedGitRemoteReader`, `utc_now` (`modal_training.py:46-51`) |
| `.cli` | `TrainingRunCommandCodeV2`, `TrainingRunCommandResultV2`, `TrainingRunCommandStatusV2`, `TrainingRunIngressV1`, `_authenticate_training_run_ingress_v1` (`modal_training.py:37-43`) |
| `.modal_provider` | `ExplicitModalHostSession`, `ModalProviderAuthorityV1` (`modal_training.py:44`); deferred at `modal_resolver.py:427, 489` |
| `.modal_resolver` | `ModalProviderStateV1`, `_closed`, `_read_json`, `_text` (`modal_provider.py:33`); `ModalTrainingIntentV1`, `ModalTrainingResolverV1` (`modal_training.py:45`) |
| `.sqlite_repository` | `SqliteTrainingRepository` (`modal_training.py:52`) |

**Nothing** is imported from `docker_staging`, `docker_v1/*`, `docker_execution`,
`docker_model_inventory`, `local_io_v1`, `publication*`, or `artifact_*`. `SourceLock`,
`ExecutionSourceV1` and `ArtifactPolicy` come from `synaptic_tuner.api.v1` — **the engine**, not the
Host's local-path layers.

**Three consequences the architect can rely on.**

1. Proposition (c) holds. A transport change cannot fork the providers, because the providers do not
   import the transport, the staging layer, or the endpoint. The provider-inventory gate on
   SHARED-layer work (plan Limitations row 1, Open Questions "Provider inventory") is **discharged
   for the three Modal files** as far as the local Docker path is concerned.
2. The one genuinely shared Host module is **`security.py`**, and it is shared for its HMAC half —
   `FileHmacAuthenticator` — which is precisely the half Q1(a) keeps. The layer-5 split is therefore
   provider-safe by construction, provided the split does not disturb `FileHmacAuthenticator`'s
   constructors `from_context` (`security.py:664`) and `for_docker` (`:672`). Note that `for_docker`
   is the **only** call site passing `repair=True` (`security.py:701`), so it is the sharpest seam.
3. The "shared layers 1 and 7" framing in the prior plan is better stated as: the providers share the
   *engine's* source-lock contract, not the Host's staging or transport code.

---

## 3. Container user and bind-mount ownership on POSIX

### 3.1 The rulings at issue

| ruling | as shipped | site |
|---|---|---|
| B-9 | `docker_host.container_user` profile field emitted as `--user`, value `1000:1000` | `docker_prepared_composition.py:112-113` validates against `_CONTAINER_USER_V1` |
| B-16 | `USER=synaptic` in the admission environment dict, admitted in both engine allowlist copies | engine `ce539b70` |
| B-9-R1 | `HOME`, `XDG_CACHE_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR` redirected; `HF_HOME`/`TRANSFORMERS_CACHE` to `/tmp` | |

### 3.2 Linux, root-ful Docker

The container's uid/gid pass straight through to the host filesystem; there is no translation layer.
`[SPEC]` A bind-mounted host directory owned by uid 1000 is writable by `--user 1000:1000` if and
only if the host directory permits it. So:

- **B-9's cause vanishes; B-9's remedy becomes load-bearing for a different reason.** The DrvFs
  `metadata,umask=22` policy that made `/artifacts` unwritable does not exist. But `--user` becomes
  *more* important, not less: without it the container runs as root and every artifact it writes is
  root-owned on the user's own machine, which then needs `sudo` to delete. `--user` should stay, with
  the value derived from `os.getuid()`/`os.getgid()` rather than the literal `1000:1000`.
  `[UNVERIFIED-BY-EXECUTION]`
- **B-16 recurs unchanged, and for the identical reason.** B-16 was never about Windows. The cause
  was that `--user <uid>` names a uid absent from the image's `/etc/passwd`, so `getpass.getuser()`
  falls through to `pwd.getpwuid` and raises inside the torch inductor cache during the unsloth
  import. That is a property of the *image*, and it fires on Linux exactly as it fired here. The
  `USER=synaptic` binding remains the remedy. **This is the single blocker most likely to be
  wrongly assumed Windows-specific.** `[SOURCE]` for the mechanism (session pinned context),
  `[UNVERIFIED-BY-EXECUTION]` for the Linux recurrence.
- **B-9-R1 recurs unchanged.** `HOME` derivation is a container-side property. Unset `HOME` with an
  unknown uid still resolves to `/`, and torch/triton/XDG caches still land somewhere unwritable.

### 3.3 macOS Docker Desktop

Docker Desktop for Mac runs the daemon in a Linux VM and shares host directories through VirtioFS
(default on current versions) or the legacy gRPC-FUSE. `[SPEC]` The sharing layer **maps ownership**:
files in a bind mount are presented to the container as owned by the container's effective uid, so a
`--user`-mismatched write generally succeeds where it would fail on Linux.

Consequences, all `[UNVERIFIED-BY-EXECUTION]` and all needing a macOS box:

- B-9's failure mode is masked rather than fixed. A `--user` value that would break on Linux may
  silently work on macOS. That asymmetry makes macOS the *weaker* test surface for B-9 and argues for
  Linux being the acceptance lane even though macOS may ship first.
- Bind-mount performance on macOS is materially worse than native. The prepared path stages a
  scoped project archive plus a model inventory; a multi-gigabyte model cache over VirtioFS is a
  plausible new performance blocker with no Windows analogue.
- macOS has **no CUDA**. Every GPU assumption in the prepared path is void; local execution on macOS
  is CPU-only, or Metal via a path the engine does not have. This is a product question, not a port
  question (section 5).

### 3.4 Rootless Docker on Linux

`[SPEC]` Rootless Docker maps container uid 0 to the invoking user's uid on the host, and container
uid 1000 to some uid inside the user's `/etc/subuid` range (commonly 100000+). A bind-mounted host
directory owned by the user is therefore writable by container **root**, and *not* by
`--user 1000:1000`. This inverts the B-9 remedy. A Host that hard-codes `--user 1000:1000` is broken
under rootless Docker in the specific way B-9 described, on Linux.

The architect needs a ruling here, because the correct `--user` value is a function of the daemon's
mode, which the Host does not currently ask about.

### 3.5 The exec-bit check goes live — and what it would then do

`docker_staging.py:177-183` (`_verify_file_mode`, `043b0554:177-183`) returns `True`
unconditionally on `nt`. On POSIX it becomes a real
predicate requiring `S_IMODE(info.st_mode)` to equal exactly `0o444` (read-only), `0o755`
(executable) or `0o644`. `[SOURCE]`

**It should pass, because the Host sets those modes itself.** `_apply_file_mode` (`:170-174`,
`043b0554:170-174`)
chmods every staged file to the same constants that `_verify_file_mode` then checks, and `chmod` is
not filtered by umask. The apply/verify pair is self-consistent by construction, and both run
host-side on the staging directory before any container exists. `[SOURCE]`

Three ways it could still fail, in descending likelihood, all `[UNVERIFIED-BY-EXECUTION]`:

1. **A filesystem that does not preserve modes.** On a mount with `noexec`, or an `fmask`/`dmask`
   mount option, or a network filesystem, the chmod is silently clamped and the verify fails. This is
   the POSIX shape of exactly the DrvFs problem that caused B-14 on the engine side.
2. **macOS extended attributes / ACLs.** `S_IMODE` is unaffected by macOS ACLs, so this should be
   benign, but it is unmeasured.
3. **A staged member that is legitimately executable.** The engine's closure records `git_mode
   100644` for all 66 members and nothing execs a staged member (the engine loads them via
   `runpy.run_path`), so the `executable=True` arm should never fire for closure members.

The prior review classified this check as **vacuous** and listed it among the free deletions (review
4.8). That classification is correct *on Windows only*. On POSIX it is a live check with a real
property. **Deleting it as "free" before the POSIX port would remove a check that is about to start
doing work.** This is a direct, actionable conflict between the two plans and the architect should
rule on it: my recommendation is to keep it and let the port bring it to life.

**Correction, 2026-09-04 (preparer-posix). I withdraw the recommendation in the paragraph above.**
The measured facts in 3.5 all stand: the check is vacuous on `nt`, live on POSIX, and the
apply/verify pair is self-consistent. The *inference* from them was wrong. Architect-posix ruled
DELETE for the closure-arm call site (`:1298`), and I verified the argument from the tree rather
than accepting it on report:

- `_walk_tree` is recursive — it drives a `pending` stack that pushes every directory — so
  `_source_manifest(source)` digests the whole `source/` tree, `source/engine` included.
- In `_verify_prepared_stage` the digest is computed and compared **before** the closure verifier
  runs on that same subtree: `_source_manifest(source)` at `043b0554:1763`, the `observed_digest`
  comparison at `:1769`, then `_verify_staged_closure(source / "engine", closure)` at `:1774`.
- On POSIX `platform_mode` carries each file's full four-digit mode, so the earlier check covers the
  property I wanted to protect in a strictly stronger form: the full modes of every staged file,
  versus one bit of the closure members — all 66 of which record `git_mode 100644`, so the
  `executable=True` arm never fires for them anyway.

The disposition therefore is: **delete the closure-arm call site at `:1298`; keep `_verify_file_mode`
itself and its read-only call site at `043b0554:1538`**, which covers a tree the source manifest does
not digest; and **keep `platform_mode`** per the 1.4 correction. The two changes are coupled and must
be ruled together.

My residual concern survives and is honoured by ruling (9): the deletion must not ship in the
post-run-12 free-deletions commit **under the vacuity reason**, because it is not free there. It is
safe only in the presence of `platform_mode`, and that dependency has to be recorded where the
deletion happens.

**Method lesson.** Before arguing that a check must be kept because a property would otherwise be
lost, look for a check *earlier in the same function* that already covers that property more
completely. I did not, and that single omission produced both this finding and the 1.4 lean.

---

## 4. What the 21-blocker record predicts for POSIX

By class, citing the class, not re-deriving the blockers. Base is section 1.

| class | blockers | POSIX prediction | why |
|---|---|---|---|
| **A. WSL/DrvFs path translation** | B-1, B-1' | **Vanishes entirely.** | The whole class exists because a Windows drive letter must become a Linux path inside a VM. On Linux the host path *is* the path. On macOS the VM boundary returns, but Docker Desktop presents host paths unchanged inside the container `[SPEC]`, so no translation table and no HMAC-authenticated root mapping is needed. Deletes W4 and W5, ≈1,558 lines. |
| **B. Windows ACL / private storage** | B-11, B-11-R1, plus open follow-up #170 | **Vanishes.** | The POSIX arms already enforce `0o700`/`0o600`/uid with no inheritance model, so there is nothing to repair, nothing to wedge, and no protected-DACL propagation. `[SOURCE]` `security.py:716, 776, 797` |
| **C. Sealed-environment omissions** | B-7, B-13 | **Recurs, renamed.** | The pattern is "a hardened child environment omits a key the child silently needs". `SystemRoot`→ nothing on POSIX (B-7's fix is already correctly branched, P3). `USERPROFILE`→`HOME` for `~/.docker` (2.2). The *class* survives any transport choice; only the key names change. The B-13 remedy — construct the endpoint, do not discover it — generalises and is the reason this class shrinks rather than repeats. |
| **D. Container user / uid** | B-9, B-9-R1, B-16 | **Changes shape, and one member recurs unchanged.** | B-9's DrvFs cause vanishes on Linux and is *masked* on macOS (3.3); it **inverts** under rootless (3.4). B-9-R1 recurs unchanged. **B-16 recurs unchanged and is not a Windows blocker at all** (3.2). |
| **E. Windows text/encoding** | B-3 | **Vanishes.** | `text=True` uses the locale encoding, normally UTF-8 on POSIX, and the newline translation is a no-op. Four `text=True` sites survive (0.4) but stop being hazards. |
| **F. Platform-independent** | B-5, B-6, B-10, B-10-R1, B-10-R2, B-12, B-14, B-15 | **Recurs unchanged. This is the largest class.** | Closure regeneration, branch/upstream checks, the artifact-topology phase guard, the HF cache pin, the verifier scope, the archive size bound, the exec-bit predicate and the `sys.path` establishment are all pure logic. Eight of twenty-one. B-14 is the interesting one: it was *caused* by DrvFs but the *fix* (drop exec-bit equality, authenticate by size and sha256) is platform-independent and already shipped. |
| **G. Image-level** | B-16 (also class D), B-8 (unidentified) | **Recurs unchanged.** | The image is the same image. |

**Net reading.** Classes A, B and E vanish — that is B-1, B-1', B-3, B-11, B-11-R1 and follow-up
#170, six of twenty-one. Class C recurs renamed. Class D changes shape and adds a *new* rootless
inversion. Classes F and G, nine blockers, recur unchanged. **A POSIX port removes about a third of
the historical blocker surface and creates at least one new one (rootless uid mapping) that Windows
never had.** It does not remove the majority.

---

## 5. Research still missing, and questions only the user can answer

### 5.1 Research not done

| gap | why it matters | how to close it |
|---|---|---|
| No native Linux box measured | Everything in 2.1 is Docker-Desktop-through-WSL. The socket path, mode and group on a real Linux host are unmeasured. | The 2.4 Linux spike, one command |
| No macOS box measured | The socket path, the VirtioFS uid mapping, and whether `os.supports_dir_fd` satisfies `posix.py`'s own gate are all unknown, and macOS ships **first** | The 2.4 macOS spike plus a print of `os.supports_dir_fd`, `os.supports_follow_symlinks`, `fcntl.flock` |
| Rootless Docker unmeasured | It **inverts** the B-9 `--user` remedy (3.4) | Run the Linux spike a second time under a rootless daemon |
| Log-stream demultiplexer unwritten | It is the only real re-implementation cost in Route B (2.3) | A 30-line spike against `GET /containers/{id}/logs` on any Linux daemon |
| Whether `platform_mode` may leave a digest | 1.4 is latent today and load-bearing the moment a digest crosses machines | An architect ruling, not research |
| B-8 still unidentified | A gap in the blocker series, carried from inv 5.1 | Search task history outside #84-#295 |
| Per-blocker fix sizes | Carried from inv 5.1; B-13's size is recorded nowhere | `git log --stat` over the release clones, out of bounds for me |
| macOS bind-mount throughput | A plausible new blocker with no Windows analogue (3.3) | Time a multi-GB stage on a macOS box |

### 5.2 Questions only the user can answer

1. **Which POSIX runtime is supported on macOS: Docker Desktop, Colima, Podman, or "whatever exposes
   a socket"?** They differ in socket path, in whether a `docker` CLI is even present, and Podman's
   API is Docker-compatible but not identical. This decides whether the endpoint is a candidate list
   or a supported matrix, and it is the single largest unpriced fork in this document.
2. **Is rootless Docker on Linux supported?** If yes, `--user 1000:1000` is wrong (3.4) and the Host
   must interrogate the daemon's mode. If no, say so and the `--user` value can stay simple.
3. **Does local execution need a GPU?** macOS has no CUDA. If local runs on macOS are CPU-only
   smoke tests and real training is cloud-only, the port is much smaller. If macOS must train, that
   is an engine question, not a Host question.
4. **Does the Windows path stay supported while POSIX ships?** This decides whether W1-W8 are
   *deleted* or *kept behind a branch*. Deleting is ~4,374 lines lighter; keeping doubles the
   acceptance surface for every future change. Q4 says Windows is "most likely last", which is not
   the same as "dropped".
5. **Is the source-manifest digest ever compared across machines?** (1.4) If yes, `platform_mode`
   must leave the digest now.

---

## 6. Scope in my domain

In: the read-only inventory above; the transport research; the provider assumption pass; the
blocker-class prediction. Out, and deliberately: designing the POSIX transport or endpoint
descriptor (architect-posix), any code change, any spike on a native Linux or macOS host, and any
ruling on sequencing.

## 7. Dependencies and interfaces

- **`PosixFilesystemPortV1`** (`filesystem.py:309-340`) is the existing portability seam and the
  model the transport layer should copy: one Protocol, two branch-local implementations, a factory
  that never imports the other platform's bindings (`publication_composition.py:397-413`).
- **`DockerLocalEndpointDescriptorV1`** (`docker_v1/model.py:1187-1205`) is the interface that must
  change. Its `__post_init__` pins the npipe URL as an invariant, so a POSIX endpoint cannot be
  represented at all today.
- **`FileHmacAuthenticator`** (`security.py:651-1063`) is the one Host module the Modal provider
  shares. Its constructors `from_context` (`:664`) and `for_docker` (`:672`) are the contract; the
  source-scraping pin at `test_security.py:1091-1092` is the tripwire.
- **`_MODEL_INVENTORY_PREFIX` / `_verify_inventory_at`** in `docker_staging.py` are being edited
  (that edit has since landed as `043b0554`: `_MODEL_INVENTORY_PREFIX` at `:59`, `_verify_inventory_at`
  at `:1468`, call site at `:1599`)
  concurrently by `coder-verifier` under ruling (4). Platform-independent; no interaction with this
  work beyond line-number drift.

## 8. Key decisions and trade-offs

| decision | options | my reading | rationale |
|---|---|---|---|
| Transport on POSIX | keep the CLI; Engine API over the unix socket | **Engine API is now cheap enough to be the default**, but the CLI is not the liability it was on Windows | Route B's Windows cost was ctypes + unverified overlapped I/O; on POSIX it is stdlib and measured (2.1). The remaining cost is the log demultiplexer alone (2.3) |
| Endpoint representation | pinned constant; ordered candidate list honouring `DOCKER_HOST` | **Candidate list** | A pinned constant is wrong for macOS Docker Desktop and wrong for every rootless Linux user (2.4) |
| `--user` value | literal `1000:1000`; derived from `os.getuid()`; daemon-mode-dependent | **Derived, pending the rootless answer (Q2)** | Rootless inverts the remedy (3.4) |
| Exec-bit check `_verify_file_mode` | delete as a free deletion (review 4.8); keep | ~~**Keep**~~ — **WITHDRAWN 2026-09-04**, see the correction under 3.5 | The vacuity reading was right and the inference wrong: the source-manifest digest already covers the property, more completely. Delete the closure-arm call site, keep the function and its read-only call site, keep `platform_mode` |
| `platform_mode` in the digest | keep; remove | **Remove, or rule explicitly that digests never cross machines** | 1.4 |
| Windows layers W1-W8 | delete; keep behind a branch | **User decision (Q4 above)** | ~4,374 lines |
| macOS capability gate | widen `posix.py:73`; leave Linux-only | **Widen, after measuring the three `os.supports_*` facts** | 1.3; the package contradicts itself about `darwin` today |

## 9. Risks and concerns

| risk | likelihood | impact | mitigation |
|---|---|---|---|
| B-16 is assumed Windows-specific and the `USER` binding is dropped in the port | **High** | High — the first Linux run dies in the unsloth import for a cause already solved | State in the ruling that B-16 is an image property, class D/G (3.2, 4) |
| The exec-bit check is deleted as "free" before the port | **Reframed 2026-09-04** — the deletion is correct, the *reason* is the risk | Medium — deleting it together with `platform_mode` leaves the source stage with no mode coverage | 3.5 correction; the two changes are coupled and ruled together (ruling (9)) |
| A pinned unix socket path ships and breaks macOS default installs and all rootless users | Medium | High | 2.4; candidate list |
| The macOS gate is widened without measuring `os.supports_dir_fd` on darwin | Medium | High — `posix.py`'s own assertions are the specification and would start failing at runtime instead of reporting UNAVAILABLE | 1.3; measure first |
| `test_security.py:1091-1092` source pin trips mid-refactor during the layer-5 split | High if unbriefed | Low | Carry the pin in the CODE task scope, as the prior plan already says |
| macOS bind-mount throughput makes local training impractical | Unknown | Medium | Measure before promising local macOS training |
| Windows and POSIX both supported doubles the acceptance lane for every future blocker | Medium | Medium | Q4 above |

## 10. Recommended approach

1. **Rule B-16 as image-class, not Windows-class, before any other decision.** It is the cheapest
   ruling here and the most expensive to get wrong.
2. **Spike before designing.** Two commands (2.4), one on native Linux and one on macOS, plus a
   rootless repeat and a print of the three `os.supports_*` facts on darwin. Everything in section 3
   is `[UNVERIFIED-BY-EXECUTION]` until then, and the transport ruling depends on it.
3. **Change the endpoint descriptor first, transport second.** `DockerLocalEndpointDescriptorV1`
   cannot represent a POSIX endpoint at all; until it can, neither route is implementable.
4. **Reuse the `local_io_v1` shape for the transport.** One Protocol, two branch-local
   implementations, a factory that never cross-imports. It already works, it is already tested
   platform-neutrally against a fake, and it is the house style.
5. **Widen `posix.py:73` as its own small, measured change**, not folded into the transport work.
6. ~~**Freeze the exec-bit deletion** until the port lands, and reconcile review 4.8 against 3.5.~~
   **Superseded 2026-09-04** (see the correction under 3.5): delete the closure-arm call site, keep
   `_verify_file_mode` and its read-only call site, keep `platform_mode`, and hold the deletion out
   of the free-deletions commit because it is conditional on `platform_mode`, not free.
7. **Do the free deletions once, portably, after the port shape is ruled** — which is what the
   prior plan's S4 note already says, and this inventory does not disturb it.

---

*Prepared by `preparer-posix` for task #293. Read-only against `06aa7177`. The single execution in
this document is the `GET /version` in 2.1, tagged Docker-Desktop-on-Windows-through-WSL, which is
not evidence about native Linux or macOS. Sections 2.2-2.4 and 3.2-3.4 are research and reasoning,
not measurement.*
