# POSIX-first local execution for the Host — ARCHITECT

**Phase:** ARCHITECT (plan consultation, #295) for plan #291 / user ruling Q4.
**Author:** `architect-posix`. Prior rulings cited as **rev:N.N** (`architect-simplify`,
`docs/architecture/host-path-simplification-review.md`) and **diag:N** (`architect-run`, sections 17-25
of `docs/architecture/prepared-path-alpine-diagnostic.md`).
**Upstream:** `docs/preparation/posix-first-local-execution-inventory.md` (`preparer-posix`, #293)
**landed while this was being written and is fully reconciled below**, cited as **inv:N.N**. Where we
agree I say so and do not re-derive. Where we disagree I rule and give the evidence: section 3.4 is the
one substantive disagreement, and section 2.4 is a correction my peer's research forced on my own draft.

**Tree read:** `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean` at HEAD
`06aa717751c687f0a269b717b33aa22a18ec723f`; engine submodule pin `ce539b70`.

**Citation baseline.** `coder-verifier` is editing `synaptic_host/docker_staging.py` and
`tests/synaptic_host/test_docker_staging.py` under ruling (4). **Every `docker_staging.py:N` below was
read from `git show 06aa7177:synaptic_host/docker_staging.py`**, not from the working tree, so the
numbers do not drift as that edit lands. My peer pinned the same two files the same way; its line
numbers for them sit a few lines from mine, so where that matters I name the symbol as well.

**Dual citation against `043b0554`.** `coder-verifier`'s edit has since landed as `043b0554`
(`docker_staging.py` is 1,939 lines there against 1,899 at `06aa7177`). Every `docker_staging.py`
citation below now carries the `043b0554` line beside the `06aa7177` line, and **appendix A** is the
full symbol-to-line map at both commits so a reader can repoint any citation I did not annotate inline.
The `06aa7177` number stays first because it is the baseline this document was written and reviewed
against; re-verifying these citations against a working tree still under edit manufactures failures.
**One correction, and it is mine, not drift.** Three places in the draft said the source-manifest digest
comparison "fails at `:1717`". At `06aa7177` the `observed_digest` clause is `:1715`, `:1717` is the
unrelated `closure_bytes` clause, and the `raise` is `:1719`. The argument survives untouched; the
citation did not. It is corrected in section 1.7, section 3.4 and section 7.4.

**Nothing was executed.** No code changed, nothing staged, committed or pushed. No container, image,
daemon or socket was touched. The one measurement in this consultation is my peer's `GET /version` over
the WSL socket (inv:2.1), tagged Docker-Desktop-on-Windows-through-WSL; I cite it and did not reproduce
it.

**The standing warning.** Nobody on this team can execute macOS or Linux Docker today. Every verdict
that depends on runtime behaviour I could not observe is marked **[PROVISIONAL-ON-FIRST-POSIX-RUN]**,
and section 5.4 names the run that settles each one. A verdict without that tag was derived from source
text and will stand or fall on a re-read, not on a run.

---

## 0. The rulings, up front

| # | Question | Ruling |
|---|---|---|
| **6** | Transport on POSIX: `docker` CLI vs stdlib Engine API over the unix socket | **KEEP THE CLI**, made portable behind a policy-ref-keyed sibling factory. **My peer reads this the other way** (inv:8 row 1, "Engine API is now cheap enough to be the default"). I rule against it on one number neither the peer's costing nor `rev:2.2` contains: migration destroys about 2,540 lines of *already-portable* subprocess-mechanism tests, and on POSIX it deletes **no** sealing layer, because the layer it was going to delete does not exist there. Section 2. |
| **7** | Per-layer shape on POSIX, and what to do once portably | Three layers **disappear**, three **change shape**, six are **unchanged**. The SHARED gate is **discharged**, and the shared layer is not the one the plan named: it is layer 5. Two of `rev:4.8`'s three "free deletions" are not free on POSIX and are re-decided here. Section 3. |
| **8** | Sequencing | **Linux first, macOS second, Windows last**, which is not the user's stated ship order and is justified by a tested predicate, not preference. Two one-command spikes come before any design work. Run 12 ships untouched. Section 5. |
| **9** | `platform_mode` in the source-manifest digest | **KEEP IT**, and this is the ruling that makes ruling 7's exec-bit deletion safe. My peer asks whether it belongs in a digest at all (inv:1.4, inv:8 row 5). It does: on POSIX it is what preserves the mode-integrity property the deleted check was carrying. Sections 1.7 and 3.4. |

**The finding that should change the plan.** The Host contains a deliberate, test-pinned refusal of
macOS on the prepared path. `detect_posix_capability_v1` grants availability only when the platform
string starts with `linux`; the only POSIX port raises `CAPABILITY_UNAVAILABLE` when it is not
available; publication composition constructs that port on every non-Windows platform; and publication
is on the prepared path. **On macOS, as the code stands, the prepared path cannot complete.** My peer
found the same predicate independently (inv:1.3) and priced the fix, which is the one place its research
made my own answer materially better: I had declined to guess the size, and it is one predicate plus a
three-fact measurement, not a port. Sections 1.1 and 6 Q1.

---

## 1. What I verified myself

Findings 1.1 to 1.6 are mine, taken from source at `06aa7177`. Finding 1.7 is new since the inventory
landed and is the evidence that settles section 3.4.

### 1.1 macOS is refused by a tested predicate, and the refusal is reachable from the prepared path

Four facts, each [SOURCE].

```
synaptic_host/local_io_v1/posix.py:67-99   detect_posix_capability_v1
    available = False                                              # :71
    if family == "posix" and platform_value.startswith("linux"):   # :73
        ...
        available = (...)                                          # assigned ONLY here
    status = AVAILABLE if available else UNAVAILABLE                # :96
```

`available` is assigned in exactly one branch and that branch requires `startswith("linux")`. On
`darwin` the family is `posix` but the second conjunct is false, so `available` keeps its initial
`False`. No execution is needed to see this.

```
synaptic_host/local_io_v1/posix.py:104-107   PosixRetainedDirfdPortV1.__init__
    self.capability = detect_posix_capability_v1()
    if self.capability.status is not CapabilityStatusV1.AVAILABLE:
        raise LocalIOErrorV1(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
```

```
synaptic_host/publication_composition.py:407-413   _local_filesystem_port_v1
    if os.name == "nt":
        from .local_io_v1.windows import WindowsRetainedHandlePortV1
        return WindowsRetainedHandlePortV1()
    from .local_io_v1.posix import PosixRetainedDirfdPortV1
    return PosixRetainedDirfdPortV1()
```

It is reached from the prepared path: `publication_composition.py:454` calls it inside
`compose_host_publication_v1`, which `docker_publication.py:460` calls. Run 12's acceptance row for
publication is that call.

The refusal is deliberate and pinned:

```
tests/synaptic_host/local_io_v1/test_posix_spool_admission.py:199-201
    assert detect_posix_capability_v1(
        platform_name="darwin", os_name="posix"
    ).status is CapabilityStatusV1.UNAVAILABLE
```

**Do not read this as "macOS was forgotten".** `filesystem.py:72-81` puts `darwin` inside
`_POSIX_PLATFORMS` and therefore inside `_SUPPORTED_PLATFORMS`, while excluding it from
`_DIRECTORY_ADMISSION_PLATFORMS = ("linux", "win32")` with the comment "darwin and the BSDs remain
excluded exactly as before". `tests/synaptic_host/local_io_v1/test_windows_port_contract.py:239-242`
states the split in its own words: the family gate "still admits them; it is the admission gate that
excludes them." The family widening was done and the port was not, so the widening is unreachable.

My peer adds the fact I lacked: every primitive `detect_posix_capability_v1` then checks for
(`O_CLOEXEC`, `O_DIRECTORY`, `O_NOFOLLOW`, `os.supports_dir_fd`, `os.supports_follow_symlinks`,
`fcntl.flock`, `os.register_at_fork`) exists on macOS [SPEC] (inv:1.3). So this is one predicate plus a
measurement, not a port, and it must not be widened blind, because the body's own assertions are the
specification. That repricing changes section 6 Q1 and I say so there.

### 1.2 The endpoint descriptor is a one-value type

```
synaptic_host/docker_v1/model.py:1193-1203   DockerLocalEndpointDescriptorV1.__post_init__
    if (
        self.source_context_ref != "desktop-linux"
        or self.host != "npipe:////./pipe/dockerDesktopLinuxEngine"
        or type(self.tls) is not bool
        or self.tls is not False
    ):
        raise ValueError
```

Both fields are pinned to literals, so the type cannot represent a unix socket. Any POSIX transport, CLI
or API, must change this before anything else is implementable. My peer independently ranks this first
in its recommended order (inv:10 item 3) and I agree. `canonical()` (`:1205-1211`) feeds
`descriptor_digest` (`:1213-1215`), so the change moves a digest; section 7.2 records that.

### 1.3 Layer 6 on POSIX is not a tuple to relax, it is a validator that rejects POSIX paths

`rev:4.6` rules that the four-key tuple equality be relaxed to a required-subset check, about ten lines,
keeping the denylist. Correct for Windows, and it does not transfer.

```
synaptic_host/docker_v1/model.py:1140-1161   DockerCLIEnvironmentV1.__post_init__
    expected_keys = ("SystemRoot", "TEMP", "TMP", "WINDIR")
    ...
    for key, value in self.entries:
        ...
        _windows_drive_path_v1(value)          # :1155  -- EVERY value
        upper = key.upper()
        if upper.startswith("DOCKER_") or "TOKEN" in upper or "AUTH" in upper or "PROXY" in upper:
            raise ValueError
```

```
synaptic_host/docker_v1/model.py:1035-1053   _windows_drive_path_v1
    or value[1:3] != ":\\"
    or "/" in value
```

Every environment **value** must be an uppercase-drive Windows path with no forward slash. A POSIX
`PATH` of `/usr/bin` fails both clauses. The executable validator is the same predicate plus a `.exe`
suffix check (`:1079-1081`).

Layer 6 therefore has four components, not the two `rev:4.6` frames: the key tuple, the per-value
drive-path check, the executable `.exe` check, and the key-name denylist. On POSIX the first three are
inapplicable by construction and the fourth, the part `rev:4.6` correctly identifies as carrying the
actual property, is **portable verbatim**, since it only uppercases key names and looks for `DOCKER_`,
`TOKEN`, `AUTH`, `PROXY`.

That is a better outcome than `rev:4.6` predicted: on POSIX the property survives at full strength and
the mechanism that produced B-13 does not exist. Section 2.3 uses this.

### 1.4 The staged source-manifest digest is platform-dependent by construction

```
docker_staging.py:917-920 (@06aa7177; :926-929 @043b0554)   _mode_projection
    if os.name == "nt":
        return "windows-regular"
    return f"posix-{stat.S_IMODE(info.st_mode):04o}"
```

and that value is recorded per file and digested:

```
docker_staging.py:1557-1573 (@06aa7177)   _source_manifest
    for path in _walk_regular_files(root, "staged source"):
        ...
        entries.append({..., "platform_mode": _mode_projection(info)})
    digest = _digest(b"synaptic-host-docker-source-manifest/v1", entries)
```

The manifest digest differs across platforms for byte-identical content. Within one machine this is
harmless and not a defect. My peer swept the consumers and found no golden constant and no cross-machine
comparison (inv:1.4). I rule on it in sections 3.5 and 6 Q4, because it turns out to be load-bearing in
the opposite direction from the one my peer expected.

### 1.5 The two file-mode call sites are vacuous on Windows and live on POSIX

`rev:1.1` establishes that `_verify_file_mode` returns `True` unconditionally on `nt`
(`docker_staging.py:168-174` @`06aa7177`, `:177-183` @`043b0554`), that its two call sites are `:1289`
and `:1492` (`:1298` and `:1538` @`043b0554`), and that all
66 closure members carry `git_mode` `100644`. I confirm all three. The half `rev` does not draw, because
it was ruling for Windows, is that `_apply_file_mode` acts on **both** platforms:

```
docker_staging.py:161-165 (@06aa7177; :170-174 @043b0554)   _apply_file_mode
    path.chmod(stat.S_IREAD if os.name == "nt" else 0o444)
```

| | Windows | Linux and macOS |
|---|---|---|
| Exec-bit arm (`:1289`, `:1298` @`043b0554`, in `_verify_staged_closure`) | vacuous **by platform** | live by platform, unexercised **by data** (66/66 are `100644`) |
| Read-only arm (`:1492`, `:1538` @`043b0554`, in `_verify_inventory_at`) | vacuous **by platform** | **live and exercised**, `0o444` really set and really checked |

`rev:4.8` deletes the exec-bit arm as free and adds: "if non-Windows execution later enters scope,
reintroduce it there deliberately." Q4 fired that clause on the same day the ruling was written. Section
3.4 takes it up, and it is where my peer and I disagree.

### 1.6 GPU is already representable as CPU-only, and one line stands in the way

```
synaptic_host/docker_v1/control_contract.py:109-116
    if rebuilt == AcceleratorDeviceRequestV1("cpu", (), ()):
        projection = ()
    elif rebuilt == AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",)):
        projection = (("nvidia", 0, ("0",), (("gpu",),), ()),)
    else:
        raise ValueError
```

Two accelerator shapes are admitted and one is CPU-only with an empty projection.
`control_private.py:411-412` emits `--gpus driver=nvidia,device=0` only when `kind == "nvidia"`, so the
CPU shape emits no GPU flag. What blocks a CPU run is one hard-coded constructor:

```
synaptic_host/docker_training.py:924-928
    runtime=DockerRuntimeV1(
        snapshot.profile.cpu_count, snapshot.profile.memory_bytes_maximum,
        plan.resources.timeout_seconds,
        AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",)),
    ),
```

A macOS CPU smoke needs this one expression to become conditional: no new mechanism, no new field, no
compatibility layer, which is exactly what submodule-first asks be proved before anything is added.

### 1.7 On POSIX the source-manifest digest already carries every staged file's full mode

This is the finding that settles section 3.4, and I went looking for it only because my peer and
`rev:4.8` reached opposite conclusions about the same check.

`_verify_prepared_stage` re-derives the source manifest over the whole staged source tree and compares
its digest **one statement before** it calls the closure verifier:

```
docker_staging.py:1709-1720 (@06aa7177; :1763-1774 @043b0554)
    observed_entries, observed_digest = _source_manifest(source)
    if (
        ...
        or observed_digest != projection.source_manifest_digest
        ...
    ):
        raise ValueError("content-addressed Docker stage differs from preparation")
    _verify_staged_closure(source / "engine", closure)
```

`_source_manifest` walks recursively (`:1559`, `:1613` @`043b0554`, calls `_walk_regular_files`, which
calls `_walk_tree`), so
`source/engine` is a subtree of the tree it digests, and by section 1.4 every entry carries
`platform_mode`, which on POSIX is the file's real four-digit mode.

**Therefore, on POSIX, any mode change to any staged source file, including the exec bit of any closure
member, flips the `observed_digest` clause at `:1715` and raises at `:1719`, before
`_verify_staged_closure` at `:1720` is even called.**
The exec-bit check at `:1289` is redundant with a strictly stronger check that runs first, and the
stronger one covers all 66 members' full modes rather than one bit of the zero members whose `git_mode`
is `100755`. [SOURCE]

Two boundaries on this claim, stated because they are the parts that could be wrong. It holds for the
**source** stage only: `_verify_inventory_at` operates on `root / "cache"` (`:1545`, `:1599`
@`043b0554`), a different tree
under the artifacts topology which the source manifest does not cover, and that tree keeps its own
read-only arm at `:1492`, which nobody proposes deleting. And it holds **only on POSIX**: on Windows
`_mode_projection` returns the constant `"windows-regular"`, so the digest carries no mode information
and subsumes nothing. On Windows the exec-bit check is vacuous anyway, so both platforms end up in the
same place by different routes.

---

## 2. RULING (6) — transport on POSIX

### 2.1 I retire my own pre-registered contingency clause

My teachback (#294, `teachback_submit.reasoning_reconstruction.contingency_clause`) pre-registered this
prediction: that Q4 weakens `rev:2.3`'s cost argument because "the Windows-shaped parts of `test_cli.py`
must be rewritten for POSIX under EITHER transport option, so those lines stop being a differential cost
of migrating and become a sunk cost of going portable at all", and that if the re-derivation confirmed
it, "the deferral's own arithmetic points the other way."

**I measured it and it is false.** Reported as retired, not softened.

| File | Total lines | Lines carrying a Windows literal | Share |
|---|---|---|---|
| `tests/synaptic_host/docker_v1/test_cli.py` | 1,843 | 49 | 2.7% |
| `tests/synaptic_host/docker_v1/test_interop.py` | 369 | 63 | 17.1% |
| `tests/synaptic_host/docker_v1/test_real_docker_wsl.py` | 531 | 34 | 6.4% |
| `tests/synaptic_host/test_docker_prepared_composition.py` | 1,145 | 41 | 3.6% |
| `tests/synaptic_host/docker_v1/conftest.py` | 725 | 12 | 1.7% |

Counted with `grep -c 'C:\\|\.exe\|npipe\|SystemRoot\|WINDIR\|os\.name\|win32\|WSL\|wsl'`, a pattern
that over-counts if anything, since one test can carry several matches. [MEASURED]

A line count alone would be weak evidence, so I read what the file tests. `test_cli.py` holds 80 test
functions whose names say what they exercise: `..._both_streams_are_drained_in_bounded_chunks...`,
`..._timeout_terminates_and_reaps_both_readers`,
`..._thread_construction_and_start_failures_cannot_escape_or_leak`,
`..._clock_failures_after_spawn_are_cleaned_without_raw_escape`,
`..._reader_join_and_liveness_exceptions_fail_closed`, `..._close_unblocks_readers_before_bounded_joins`,
`..._permanently_blocked_reader_makes_cleanup_indeterminate`,
`..._terminate_timeout_escalates_to_kill_and_cleanup_uncertainty_dominates`. Six or eight names carry a
Windows concern.

**That is a subprocess-lifecycle suite, not a Windows suite.** Reader threads, bounded draining,
terminate-then-kill escalation, reaping, clock failure and close-uncertainty ordering are not Windows
properties, and none of them survives a move to HTTP, where the failure modes are connection refused,
partial body, chunked-stream truncation and server-side timeout instead.

**My peer's independent measurement strengthens this rather than qualifying it.** inv:1.6 reports 1,053
tests across the whole Host suite with only 25 skip markers and only two files carrying `os.name != "nt"`
gates, and concludes "the test tree is not the obstacle", because the suite was written platform-neutral
against fakes. That is the right conclusion for the question my peer was asking, which is whether the
test tree obstructs a **port**. It does not. But the reason it does not is that these tests exercise the
subprocess mechanism against fakes rather than a real platform, and that is precisely why an HTTP
transport invalidates them. Platform-neutrality means the lines are already portable, so migration is
not paying down a Windows debt. It is discarding finished, portable work.

The 2,743 lines therefore split the opposite way from my prediction:

| Option | Test lines destroyed | Test lines preserved |
|---|---|---|
| Keep the CLI, made portable | about 199 Windows-literal lines to parametrise across the five files | about 2,540 of the mechanism suite, unchanged |
| Migrate to the stdlib Engine API | the whole 2,743, plus new HTTP-failure-mode tests to write | none |

`rev:2.3`'s reason one, that paying a 2,700-line test rewrite to delete a layer you can fix for ten
lines is the wrong trade, survives Q4 intact.

### 2.2 Where my peer and I disagree, and the number that decides it

inv:8 row 1 rules that the Engine API is now cheap enough to be the default, and inv:2.3 supports it
well: on a unix socket there is no `CreateFileW`, no ctypes, no overlapped-I/O unknown; `http.client`
over an `AF_UNIX` socket is ordinary blocking I/O, and my peer measured it working end to end against a
real daemon (inv:2.1, `GET /version` returned 200, API 1.54). It prices the transport module honestly at
250 to 400 stdlib lines and names the log-stream demultiplexer as the one real re-implementation cost.

**I grant every one of those points and still rule the other way, on two the costing does not contain.**

**First, migration deletes nothing on POSIX.** `rev:2.3` costed the Engine API as buying one blocker
(B-13) by deleting the roughly 138-line sealing layer. Section 1.3 shows that layer has no POSIX form:
the drive-path validator, the `.exe` check and the four-key tuple are all inapplicable, and the denylist
that carries the real property is portable verbatim under either transport. So on POSIX the Engine API's
headline benefit is already free, and it buys **zero** blockers relative to a portable CLI.

**Second, the 250 to 400 lines added is the smaller half of the trade.** The unpriced half is about
2,540 lines of finished, portable, passing mechanism tests destroyed (section 2.1). Both numbers are
correct; the trade is decided by the second, and it is an order of magnitude larger.

Two smaller corrections in the same direction. The log demultiplexer my peer calls the one real cost is
**not needed** by the prepared path, because `docker_publication.py:275-276` refuses container logs
outright, which lowers the Engine API's cost but also removes its most distinctive capability, since
that capability is one the design has already declined. And `POST /containers/{id}/wait` really would be
better than the `docker events` polling instrument (#219): that is a genuine, specific benefit of the
API route and the strongest single argument my peer makes. It is worth roughly one instrument, not a
runner rewrite.

| Item | Keep the CLI (portable) | Stdlib Engine API over `AF_UNIX` |
|---|---|---|
| Production files touched | 3 | 5 plus a new transport module (`rev:2.2`) |
| Production lines removed | about 0 | about 427 runner plus 120 child-process framing; **about 0 sealing** (section 1.3) |
| Production lines added | 60 to 90 | 250 to 400 (inv:2.3) |
| Test lines rewritten | about 199 | about 2,743 plus new coverage |
| Blockers bought versus a portable CLI | — | **zero** (section 1.3) |
| Specific capability gained | — | `/containers/{id}/wait` replaces the #219 poller |
| New unmeasured failure classes | CLI discovery on `PATH` | HTTP framing, socket permissions, API version negotiation, stream demux |

### 2.3 Ruling: keep the CLI, behind a policy-ref-keyed sibling factory

**Keep `docker` on `PATH`, invoked by the existing `DockerCLIRunnerV1`.** Do not migrate.

The portable shape is not a new pattern and must not become a compatibility layer. The codebase already
contains it, with a docstring that pre-answers the constraint, and my peer independently nominates the
same model (inv:10 item 4, "it is the house style"):

```
synaptic_host/publication_composition.py:394-406   _local_filesystem_port_v1
    """Build the retained-handle port for the running platform.

    Two branches, one real port each. This is not a compatibility layer: it
    adds no re-export, no dual signature, no deprecated wrapper and no
    degradation path, and neither branch can serve the other platform. ...

    The imports are branch-local on purpose: ...
    """
```

`compose_docker_prepared_platform_v1` (`docker_prepared_composition.py:94-181`) is already keyed on a
policy ref and already refuses what it does not recognise:

```
docker_prepared_composition.py:105-115
    if (
        os_name != "nt" or docker_policy_ref != "docker-desktop-windows-v1"
        ...
    ):
        raise ValueError("Windows Docker Host policy is unavailable")
```

The POSIX work is a **sibling policy ref**, say `docker-engine-posix-v1`, whose factory returns the same
`DockerPreparedPlatformV1`, with:

1. a POSIX environment type beside `DockerCLIEnvironmentV1`, carrying the **denylist verbatim** (section
   1.3) and a POSIX absolute-path value check instead of `_windows_drive_path_v1`;
2. a POSIX executable validator requiring an absolute path with basename `docker`, replacing `.exe`;
3. the endpoint change ruled in section 2.4;
4. the same constructed-endpoint-plus-explicit-`--host`-version-probe liveness proof the Windows branch
   already performs at `:172-178`, unchanged in shape. My peer reaches the same conclusion from the
   other direction (inv:2.2): "Swap the constant from an npipe URL to `unix:///var/run/docker.sock` and
   that entire mechanism ports without redesign."

**The two Windows fields are the leak, and they resolve by absence.** `DockerPreparedPlatformV1` carries
`wsl_distro` and `drive_mount_root` (`:64`, `:180`), which are WSL concepts with no POSIX meaning. Do
not invent a neutral mount-translation strategy to hold both: B-1 and B-1' translation is a Windows
artifact, and inv:4 class A confirms the whole class vanishes. The POSIX branch simply does not populate
those fields, and the profile validator (`docker_provider.py:144-145`, `:175`) requires them for the
Windows policy ref and refuses them for the POSIX one. That keeps the no-compatibility-layer rule, and
re-attaching Windows later costs nothing because the npipe branch stays exactly as written.

**Trigger for revisiting.** Re-open the Engine API if a POSIX blocker is diagnosed whose cause is CLI
discovery, CLI argv construction, or CLI environment, that is, a B-13-shaped failure on POSIX. A second,
independent trigger: if the product ever requires container log streaming or attach semantics, the CLI's
bounded-drain design (`cli.py:723`, `:758`) is the wrong shape and the API is the right one. Today
`docker_publication.py:275-276` refuses logs, so that requirement does not exist.

**This second trigger interacts with a free deletion, and the interaction must survive into the plan.**
`preparer-posix` accepts ruling (6) partly BECAUSE logs are refused and `DockerVerb.LOGS` has zero call
sites, and rev:4.8 lists that verb among the free deletions. Both are correct today. But once the verb
is deleted, a future log-streaming requirement would find neither the capability nor this trigger, and
the transport question would be re-opened from scratch with the evidence gone. The deletion is still
right; what must not be lost is the record of WHY it was free. Whoever lands the rev:4.8 deletions
should carry this trigger into the deletion's own commit message or the plan's revisit list, so the
condition that made the deletion free is the same condition that would reverse it.

### 2.4 Correction forced by my peer's research: the endpoint is a candidate list, not a constant

My draft of this section ruled that the endpoint predicate must stay closed as a set of two literals,
reasoning from B-13's ruling (diag:22.6) that the endpoint is constructed, never operator-supplied.
inv:2.4 shows that would ship broken, and I accept the correction:

- Docker Desktop for Mac creates `~/.docker/run/docker.sock`; the `/var/run/docker.sock` symlink is
  opt-in and needs a privileged helper at install time, so a design hard-coding `/var/run/docker.sock`
  **fails on a default macOS install** [SPEC].
- Rootless Docker on Linux uses `$XDG_RUNTIME_DIR/docker.sock`, mode `0600`, with `DOCKER_HOST` normally
  set by the user's profile [SPEC].

A single pinned constant is therefore wrong for the platform that ships first and for every rootless
Linux user. But my peer's phrasing, an ordered candidate list with `DOCKER_HOST` honoured first (inv:2.4,
inv:8 row 2), concedes more than the evidence requires, because those are two separable changes with
different risk.

**Ruling.** The endpoint is a **closed, ordered candidate list of Host-authored constants**, each probed
with `S_ISSOCK` before use, in the order `/var/run/docker.sock`, `~/.docker/run/docker.sock`,
`$XDG_RUNTIME_DIR/docker.sock`. Every candidate is a constant this codebase authors and the selection
rule is deterministic, so B-13's property, that the Host knows which daemon it talks to without
depending on operator configuration, is preserved. The chosen path is then passed explicitly as
`--host`, exactly as the Windows branch passes its npipe URL, so the CLI's own context resolution never
runs and the B-13 class stays closed.

**`DOCKER_HOST` is different and gets a different answer.** It is operator-supplied, and honouring it
first would make the daemon environment-determined, which is the property B-13's fix removed. Ignoring
it silently is worse: the Host would talk to a different daemon than the user's own CLI does, and
nothing would say so. **So: if `DOCKER_HOST` is set and does not name the candidate the Host selected,
refuse with a named cause rather than honouring or ignoring it.** That keeps determinism, makes the
rootless and remote-daemon cases visible instead of silent, and turns a design guess into a user
decision (section 6 Q3). [PROVISIONAL-ON-FIRST-POSIX-RUN] on the candidate ordering, which is [SPEC]
until a macOS box and a rootless Linux box are measured; inv:2.4 gives both spikes as one command each.

---

## 3. RULING (7) — per-layer shape on POSIX

### 3.0 The SHARED gate is discharged, and two premises in the dispatch were wrong

The plan gated SHARED-layer verdicts behind a provider inventory. That pass is done (inv:2.5) and the
answer is clean, but it also corrects the framing.

**There is no HF Jobs provider.** The dispatch names "the Modal and HF Jobs providers
(`synaptic_host/*modal*`, `*hf*`; about 2,512 lines)". The 2,512 is exactly `modal_provider.py` (1,077)
plus `modal_resolver.py` (775) plus `modal_training.py` (660); no file in the package matches `*hf*`
[MEASURED] (inv:0.1). I carried that premise into my own draft's SHARED marking and it was wrong. Any
downstream document should stop saying "Modal and HF Jobs".

**The three Modal files import nothing from the local Docker path.** Not from `docker_staging`, not
`docker_v1/*`, not `docker_execution`, not `local_io_v1`, not `publication*`, not `artifact_*`. They
carry zero platform branches. `SourceLock`, `ExecutionSourceV1` and `ArtifactPolicy` come from
`synaptic_tuner.api.v1`, the engine [SOURCE] (inv:2.5).

Three consequences I rely on. A transport change **cannot** fork the providers. The "shared layers 1 and
7" framing is better stated as: the providers share the *engine's* source-lock contract, not the Host's
staging or transport code. And the one genuinely shared Host module is **`security.py`**, which is layer
5, the layer the user ruled should be split.

### 3.1 The table

| # | Layer (rev:4 numbering) | On Linux | On macOS | Note |
|---|---|---|---|---|
| 1 | Source lock `ExecutionSourceV1` | unchanged | unchanged | shared via the **engine**, not Host code (3.0) |
| 2 | Staging bound plus scoped staging | unchanged | unchanged | B-12's fix is path logic |
| 3 | Admission resolver plus 19-key env | unchanged | unchanged | values change, mechanism does not |
| 4 | Composition policy plus 3 digests | **changes shape** | changes shape | endpoint digest moves (1.2, 2.4); environment digest is over different keys |
| 5 | HMAC plus `.synaptic` chain | **changes shape, shrinks** | shrinks | **the one shared Host layer** (3.0); see 3.2 |
| 6 | Sealed four-key CLI env | **disappears** (3 of 4 parts) | disappears | 1.3; denylist survives verbatim |
| 7 | Worker closure manifest | unchanged | unchanged | not provider-shared (3.0) |
| 8 | Container user plus cache keys | **changes shape** | changes shape | 4.1 |
| 9 | Network-disabled, credential-free | unchanged | unchanged | the cheap layer stays cheap |
| 10 | Result envelope plus cause line | unchanged | unchanged | |
| 11 | Driver probes P1-P11 | **disappears** | disappears | frozen scaffold (Q5 A); six probes are Windows-shell-shaped |
| 12 | CLI verb enum plus runner | unchanged under ruling (6) | unchanged | 2.3 |
| — | `local_io_v1` retained-handle port (**not in rev:4**) | unchanged | **REFUSES** | 1.1 — the new row |

The last row is the point of the table. All twelve inventoried layers are portable or shrinking. What
stops macOS is a thirteenth layer the simplification review never inventoried, because its scope was the
prepared Docker path's hardening layers and `local_io_v1` is not one of them.

### 3.2 Layer 5 gets cheaper POSIX-first, and it is the layer that needs provider care

`rev:4.5` prices the Q1/Q2 split at about 490 production and 800 test lines and flags the risk that
B-11-R1's mechanism is recorded as a hypothesis, so the team would remove code it does not fully
understand.

**On POSIX that risk largely evaporates, because the expensive half is Windows-only.** The POSIX arms
are written, small, and caused zero blockers:

```
security.py:712-720   _create_private_directory    -> os.mkdir(path, 0o700)
security.py:750-775   _repair_private_directory    -> fchmod(descriptor, mode & 0o700) on a live fd
security.py:779-805   _validate_private_directory  -> S_IMODE == 0o700 and st_uid == os.geteuid()
```

```
security.py:746-748
    POSIX modes do not propagate, so the Windows propagation hazard has no
    counterpart here and a populated directory is repaired with no effect on
    its children.
```

B-11 and B-11-R1 are both `_win_*` failures, and B-11-R1's mechanism is inheritance, which POSIX does
not have. My peer confirms the POSIX arms are real implementations rather than fallbacks, five of the
eight `os.name` branches being true dispatches with no no-op and no raise on the POSIX side (inv:0.3),
and predicts the whole class vanishes (inv:4 class B). So the roughly 490 lines the user ruled removable
are, in the main, the `_win_*` machinery POSIX never calls.

**Doing this POSIX-first means deleting code the live lane does not execute**, which is the safest
possible order for a removal whose failure mechanism is a hypothesis. Windows-first means deleting code
the only working lane does execute.

Three constraints belong in any CODE task's scope, and the third is new since the inventory:

- `tests/synaptic_host/test_security.py:1091-1092` is a source-scraping pin over
  `inspect.getsource(FileHmacAuthenticator._key)` asserting the literal
  `_ensure_private_storage_directories(repair=False)` and the absence of `repair=True`. Any rename, any
  reformat across two lines, any move of that call breaks it while the behaviour is correct.
- The excision has **three** call sites (`security.py:701` repairing, `:882` and `:972` validating), not
  one.
- **The provider-shared boundary is FOUR symbols, not one.** My first draft said `FileHmacAuthenticator`
  was the Modal providers' only Host import; `preparer-posix` corrected that from the tree and I accept
  the correction, and I re-read the tree to confirm it: `modal_training.py:46-51` imports
  `BoundedGrantProvider`, `FileHmacAuthenticator`, `ScopedGitRemoteReader` and `utc_now` in one
  `from .security import (...)` block. The layer-5 split must be scoped against all four, not one.
- **The two constructors belong to different paths, and only one of them is the providers'.**
  `from_context` (`security.py:664`) is the Modal path's, called at `modal_training.py:518`;
  `for_docker` (`security.py:672`) is the Docker path's, called at `docker_training.py:868`. So the
  PROVIDER-safety constraint is on `from_context`, while `for_docker` is Docker-path-internal. `for_docker` is still the only call site passing `repair=True` (`:701`) and
  therefore still the sharpest seam, but it is a Docker-path seam, not a provider seam. That narrows the
  cross-provider risk of the split and it also means the two concerns must not be conflated in the CODE
  task's scope.
- **One shared symbol carries a Windows branch, and it is inert on POSIX.**
  `ScopedGitRemoteReader._run` (`security.py:1130`) holds the B-7 `nt` arm at `:1142` that carries
  `SystemRoot` into the scrubbed environment. It is dead on POSIX rather than forked, so it creates no provider divergence, but a
  reader sweeping the shared four for platform branches will find it and should not file it as one.

### 3.3 What to do once, portably, rather than twice

| Item | `rev:4.8` verdict | POSIX verdict | Do it |
|---|---|---|---|
| `DockerVerb.STOP`, `DockerVerb.LOGS` (`model.py:1015`, `:1018`) | delete, 2 lines, zero call sites | identical on POSIX | **Once, now, on the Windows path.** Genuinely platform-independent. |
| Four-key tuple to required subset (`model.py:1144-1149`) | relax, about 10 lines | the whole validator is absent on POSIX (1.3) | **Windows-only, and no longer urgent.** Section 6 Q5. |
| Exec-bit arm (`docker_staging.py:1289`, `:1298` @`043b0554`) | delete, "no property lost on Windows" | live on POSIX (1.5) | **Delete, on a different argument, in the POSIX cycle.** Section 3.4. |
| Layer 5 ACL chain (Q1/Q2) | split, about 490 plus 800 lines | Windows-only machinery (3.2) | **Once, portably, POSIX-first**, own cycle, security-engineer review. |
| Driver freeze (Q5 A) | docs only | six probes are Windows-shell-shaped | **Once, now.** Platform-neutral. |

### 3.4 The exec-bit deletion: where I overrule my peer, and why

This is the one substantive disagreement in the consultation, and both plans currently point opposite
ways, so I rule rather than note it.

**My peer's position** (inv:3.5, inv:8 row 4, inv:9 row 2, inv:10 item 6): keep the check and let the
port bring it to life. Its argument is that on POSIX the predicate becomes real, that the apply and
verify pair is self-consistent by construction so it should pass, and that its most likely failure mode,
a filesystem that silently clamps modes via `noexec`, `fmask`/`dmask`, or a network mount, "is the POSIX
shape of exactly the DrvFs problem that caused B-14". It ranks deleting it as a high-likelihood risk if
the two plans are executed independently.

**That argument is well made and it identifies a real property.** I would accept it outright but for
section 1.7, which says the property is already held, and held better, by something that runs first.

On POSIX, `_verify_prepared_stage` re-derives the source manifest over the whole staged source tree and
compares its digest at `docker_staging.py:1715` and raises at `:1719`, **before** calling
`_verify_staged_closure` at `:1720`.
By section 1.4 every entry in that manifest carries `platform_mode`, which on POSIX is the file's real
mode. So a filesystem that clamps modes anywhere under the source stage fails at `:1719` with
`"content-addressed Docker stage differs from preparation"`, covering all 66 members' full modes, not
one bit of the zero members whose `git_mode` is `100755`. The exec-bit check cannot fire on a tree that
already failed the digest.

Add `architect-run`'s two facts, which survive the platform change untouched: nothing ever execs a
staged member, because the engine loads them via `runpy.run_path` in process; and the engine's real
defence against a substituted module is import-origin based, not mode based. My peer agrees on the
first (inv:3.5 failure mode 3).

**Ruling: delete the exec-bit call site at `docker_staging.py:1289` (`:1298` @`043b0554`). Keep
`_verify_file_mode` itself and its read-only call site at `:1492` (`:1538` @`043b0554`).** The mode-integrity property my peer is protecting survives in two
stronger forms: the source-manifest digest for the source tree, and the read-only arm for the artifacts
cache tree, which `_verify_inventory_at(entries, root / "cache")` (`:1545`, `:1599` @`043b0554`) covers
and which is the arm
that actually fires on data. Nothing is lost and one redundant check goes.

**Two consequences that are not optional.** First, this ruling is *conditional on ruling (9)*: it is
`platform_mode` in the digest that makes the deletion safe on POSIX, so removing `platform_mode`, which
inv:8 row 5 recommends, and deleting the exec-bit arm are individually defensible and jointly wrong.
They must be decided together, and I decide them together in ruling (9). Second, `rev:4.8`'s stated
reason, that the arm is vacuous on Windows, is false on POSIX, so the deletion must land with the
section 1.7 reason written down. A future reader who remembers only the verdict will otherwise
reintroduce the check the next time someone notices POSIX has modes.

**Sequencing consequence:** hold the exec-bit deletion out of the post-run-12 free-deletions commit. Let
that commit carry the two dead enum members alone, and delete the exec-bit arm in the POSIX cycle
alongside the `platform_mode` comment, so the pair lands together with its reason.

### 3.5 RULING (9): `platform_mode` stays in the digest

inv:1.4 establishes the divergence precisely, sweeps the consumers, finds no golden constant and no
cross-machine comparison, and asks the architect to decide whether `platform_mode` belongs in a digest at
all; inv:8 row 5 leans toward removing it.

**Ruling: keep it.** On POSIX it is a live integrity property. It is the mechanism that detects a mode
change to any staged source file between preparation and verification, and by section 3.4 it is what
makes the exec-bit deletion safe rather than lossy. Removing it would delete a real check and a
redundant one in the same cycle, leaving the source stage with no mode coverage at all.

The hazard my peer identifies is real but is a hazard of *interpretation*, not of the field: a future
design that compares a staging digest across machines gets a failure that looks like corruption. The
proportionate remedy is a comment at `_mode_projection` recording that the source-manifest digest is
platform-scoped and must never be compared across machines, landed in the same commit as the exec-bit
deletion. If a portable cross-machine digest is ever needed, the closure manifest's sha256-and-size pair
already provides one, which is the B-14 lesson restated.

Section 6 Q4 puts the one question that could overturn this to the user: whether any planned design
compares a staging digest across machines. If the answer is yes, `platform_mode` must leave the digest,
and the exec-bit arm must then stay.

**A note on `rev:7.2`.** That section records that the environment-enumeration failure has happened
three times (B-7, B-9-R1, B-16) and that a fourth instance should trigger a contract change rather than
a fourth allowlist edit. POSIX will need its own environment key set. **That is not a fourth instance**;
it is a new platform's first enumeration, not a repeat of the same failure, and I flag it because a
future agent counting instances could miscount it as the trigger.

---

## 4. Container user, mount ownership and the verifiers

All of section 4 is [PROVISIONAL-ON-FIRST-POSIX-RUN] except where a citation is given: bind-mount uid
semantics are runtime behaviour of a Docker installation and nobody here can observe one.

### 4.1 What B-9, B-16 and B-9-R1 become

My peer and I reached the same conclusion independently on the item that matters most, so I state the
agreement rather than re-deriving it.

| Ruling | Linux, root-ful | macOS Docker Desktop |
|---|---|---|
| `--user` (B-9) | **still needed, for a different reason.** The DrvFs `metadata,umask=22` cause vanishes, but without `--user` the container runs as root and every artifact it writes is root-owned on the user's own machine, needing `sudo` to delete (inv:3.2). | **probably redundant.** VirtioFS maps ownership, presenting bind-mount files as owned by the container's effective uid, so a `--user` mismatch that breaks on Linux may silently work (inv:3.3). |
| `USER=synaptic` (B-16) | **recurs unchanged.** | needed if `--user` is set at all |
| Cache redirect (B-9-R1) | **recurs unchanged.** `HOME` derivation is container-side. | same |

**B-16 is an image property, not a Windows blocker, and this is the ruling to make first.** Its cause
was that `--user <uid>` names a uid absent from the image's `/etc/passwd`, so `getpass.getuser()` falls
through to `pwd.getpwuid` and raises inside the torch inductor cache during the unsloth import. That
fires on Linux exactly as it fired here. My peer rates it the single blocker most likely to be wrongly
assumed Windows-specific and puts ruling it first at the top of its recommendations (inv:3.2, inv:9 row
1, inv:10 item 1). I agree without reservation and section 5.3 puts it at step 0.

**Two things I take from my peer and had not ruled.** The `--user` value should be **derived from
`os.getuid()` and `os.getgid()`**, not the literal `1000:1000` currently validated by
`_CONTAINER_USER_V1` at `docker_prepared_composition.py:112-113`. And **rootless Docker inverts the
remedy**: it maps container uid 0 to the invoking user and container uid 1000 into the `/etc/subuid`
range, so a bind-mounted host directory owned by the user is writable by container root and *not* by
`--user 1000:1000` [SPEC] (inv:3.4). A Host that hard-codes `1000:1000` is broken under rootless Linux in
the specific way B-9 described. That is a new blocker class Windows never had, it depends on a daemon
property the Host does not currently ask about, and it is section 6 Q3.

### 4.2 The verifiers

**Ruling (4)'s verifier is unaffected, and I did not re-open it.** Scoping `_verify_inventory_at` to
`cache/model` is `PurePosixPath` prefix logic over staged relative paths, with no platform branch, no
mode read and no ACL. It behaves identically on all three platforms. Worth stating because ruling (4) is
in flight as #290 and a POSIX plan that appeared to disturb it would be a false alarm; my peer reaches
the same verdict from the interface side (inv:7).

**The read-only arm becomes live and is the one to watch.** Per section 1.5, `_apply_file_mode(...,
read_only=True)` really sets `0o444` on POSIX and `:1492` (`:1538` @`043b0554`) really checks it.
Predicted failure mode,
flagged as a prediction: if anything alters an inventory file's mode between preparation and the verify
cut, the cut fails on POSIX where it passed on Windows. My peer's mount-clamping cases (inv:3.5) are the
plausible mechanism. This is section 5.4 row 5.

**B-14 seen from POSIX.** The engine's staged-member exec-bit equality was deleted because DrvFs
synthesised `0744` for every Windows-written file. On a native Linux bind there is no synthesis, so that
predicate would have passed. The deletion is permanent and I am not proposing to revisit it, since
sha256 subsumes the mode and always did, but the record should say B-14 was a Windows-mount-driven
change that removed a check which works on the platform now scheduled first.

---

## 5. GPU, image, and sequencing

### 5.1 What "local execution" means on each platform

| | Linux plus NVIDIA plus nvidia-container-toolkit | macOS |
|---|---|---|
| Accelerator | real CUDA; `--gpus driver=nvidia,device=0` as today | **no CUDA.** Docker Desktop for Mac exposes no GPU to Linux containers [SPEC] |
| Accelerator request | `AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",))` unchanged | `AcceleratorDeviceRequestV1("cpu", (), ())`, already admitted (1.6) |
| The pinned image `sha256:5266c57b...` | usable as pinned if it is linux/amd64 on an amd64 host | **almost certainly unusable on Apple silicon**: an amd64 CUDA image on arm64 runs only under emulation, if at all |
| What a run proves | real training, as run 11 | composition, staging, admission, lifecycle and publication, **not** training |

**The honest statement about macOS:** a CUDA-stack trainer image cannot train on a Mac, so "local
execution on macOS" means one of two different things and the answer changes what gets built. My peer
independently reaches the same fork and calls it a product question rather than a port question (inv:3.3,
inv:5.2 Q3). It is section 6 Q2 and it is the highest-value question here.

My peer also raises a hazard I had not: **macOS bind-mount throughput over VirtioFS is materially worse
than native**, and the prepared path stages a scoped project archive plus a model inventory, so a
multi-gigabyte model cache is a plausible new performance blocker with no Windows analogue (inv:3.3).
Unmeasured. It belongs in section 5.4 as an observation, not a gate.

### 5.2 What must be true before the first POSIX run

1. A machine on the team can run Linux Docker. **None can today. This is the gating item and nothing in
   this document substitutes for it.**
2. The two spikes in inv:2.4 have been run: one command on native Linux, one on macOS, plus a rootless
   repeat, plus a print of `os.supports_dir_fd`, `os.supports_follow_symlinks` and `fcntl.flock` on
   darwin. Everything in section 4 and half of section 2.4 is [UNVERIFIED-BY-EXECUTION] until then. My
   peer puts "spike before designing" second in its recommendations and I adopt it as a precondition
   rather than a recommendation.
3. `DockerLocalEndpointDescriptorV1` can represent a POSIX endpoint (1.2, 2.4). Until it can, neither
   transport is implementable.
4. The POSIX policy ref and its factory exist (2.3), and the profile validator enforces the `wsl_distro`
   and `drive_mount_root` split.
5. For Linux: `nvidia-container-toolkit` installed and `docker run --gpus` working outside the Host, an
   operator precondition checked before the run exactly as Docker Desktop was on Windows.
6. For macOS additionally: **either** the `posix.py:73` predicate widened after the three-fact
   measurement (1.1), **or** the user's answer to Q2 removes macOS local execution from scope. There is
   no third option, because publication is on the path and its port refuses to construct.

### 5.3 Sequencing, and where it departs from the user's stated order

The user ruled that the desktop app ships macOS and Linux first, Windows most likely last. For the
**Host's local Docker path** I recommend a different internal order, on section 1.1 rather than
preference:

**Linux, then macOS, then Windows.**

Linux has a built and tested retained-handle port, real GPU support, and no mount translation. It is the
cheapest platform on which to learn what POSIX actually breaks, and everything learned there transfers.
macOS needs the predicate widened and the measurement taken first, and needs Q2 answered before that is
worth doing. My peer supplies an independent reason for the same order: VirtioFS *masks* B-9's failure
mode, which makes macOS the weaker acceptance surface even if it ships first (inv:3.3). This is an
ordering within the POSIX work; it does not contradict Q4, which is about which platforms the product
ships on.

| Step | What | Gate |
|---|---|---|
| 0 | **Rule B-16 as image-class, not Windows-class**, in the record. Costs nothing, most expensive to get wrong. | now |
| 0b | **Run 12 ships as planned, untouched.** Ruling (4) alone, single-cause. | nothing here touches it |
| 1 | Free deletions commit: **two dead enum members only**. Exec-bit arm held back per 3.4. | after run 12 |
| 2 | Driver freeze (Q5 A), docs only | any time; platform-neutral |
| 3 | **Answer Q1 to Q4 (section 6)** | blocks everything below |
| 4 | **Run the inv:2.4 spikes** on Linux, macOS and a rootless daemon | a POSIX machine exists |
| 5 | Widen `posix.py:73` as its own small, measured change, not folded into transport work | spike 4 green |
| 6 | Layer-5 split, POSIX-first framing, own cycle plus security-engineer review | Q1/Q2 answered |
| 7 | Endpoint descriptor (2.4), then POSIX policy ref (2.3); exec-bit deletion plus `platform_mode` comment (3.4, 3.5) | steps 4-5 done |
| 8 | **First Linux run**, section 5.4 rows | step 7 released |
| 9 | macOS lane, only if Q2 keeps local execution on macOS in scope | first Linux run green |
| 10 | Modal and RunPod smokes | independent of 5-9; 3.0 shows they cannot be forked by this work |

**Single-cause discipline.** Steps 1, 5, 6, 7 and 9 each change something a run could blame. Do not
bundle them. The specific trap: bundling the layer-5 split with the transport factory makes a failed
first Linux run ambiguous between a permissions change and a transport change, and those two families
produced eight of the twenty-one Windows blockers.

### 5.4 Acceptance rows for the first Linux run

| Row | Observation | Settles |
|---|---|---|
| 0 | The POSIX policy factory constructs; the explicit `--host` version probe succeeds. No container yet. | 2.3, the transport ruling |
| 1 | `docker` is discovered on `PATH`; the selected socket candidate and the child environment key set are recorded. | 2.4, the candidate-list ruling |
| 2 | Staging completes; source-manifest entries carry `posix-0644`-shaped modes, not `windows-regular`. | 1.4, 3.5 |
| 3 | The container is created and started as the derived `--user`, and writes artifacts the host user can read without `sudo`. | 4.1, B-9 on a native bind |
| 4 | The unsloth import passes at `train_sft.py:137`, as at run 11 row 0. | 4.1, whether B-16 transfers |
| 5 | The verify cut succeeds, with the model inventory at `0444` and `_verify_file_mode` actually comparing. | 1.5, 4.2 — the newly live arm |
| 6 | Publication completes; `PosixRetainedDirfdPortV1` constructs. | 1.1 on Linux |
| 7 | The submodule pin is unchanged across the release range. | that the POSIX work cost no engine change |
| 8 | Wall-clock of the staging phase recorded, for later comparison against macOS. | inv:3.3's VirtioFS throughput hazard |

Row 5 has no Windows precedent, because the arm it exercises has never executed. Row 4 is the one most
likely to surprise, because it is where an image property everyone associates with Windows either
transfers or does not.

---

## 6. Questions only the user can answer

**Q1. Which POSIX platform is the Host's local Docker path for?** This decides whether section 1.1 is
urgent or moot, and it is separable from which platforms the app ships on.

- *(a) Linux only, for now.* The retained-handle port exists and is tested; the first run is reachable as
  soon as a Linux machine is. macOS users of the desktop app drive cloud compute. Cheapest.
- *(b) Linux and macOS both.* **Repriced downward since my draft.** I had said the size was unknown and
  declined to guess; inv:1.3 shows every primitive the detector checks exists on macOS [SPEC], making
  this one predicate at `posix.py:73` plus a three-fact measurement, not a port. **My recommendation
  now**, conditional on that measurement passing. If `os.supports_dir_fd` on CPython and macOS does not
  contain the five functions the body requires, this reverts to (a) and the cost is a port after all.
- *(c) macOS first, matching the ship order literally.* Most faithful to Q4 and the most expensive: it
  needs the measurement, cannot do real training (5.1), and is the weaker surface for B-9 (inv:3.3), so
  the first run proves the least.

**Q2. On a Mac, does "local execution" mean real training, or exercising the path?** A CUDA trainer image
cannot train on a Mac.

- *(a) Exercise the path with a CPU-only smoke image.* One-line change at `docker_training.py:927` (1.6)
  plus a CPU-capable image. Proves composition, staging, admission, lifecycle, publication. Not training.
- *(b) macOS drives cloud compute only; no local Docker path there.* Zero Host work for macOS; section
  1.1 leaves the critical path. Cheapest, and may be what the product needs.
- *(c) Real training on a Mac.* Needs a different image and an MPS-capable engine path. An engine
  question, outside this consultation.

**Q3. Is rootless Docker on Linux supported, and what should happen when `DOCKER_HOST` is set?** These
are one question because both decide how much the Host must ask about the daemon.

- *(a) Root-ful only; refuse loudly otherwise.* `--user` derives from `os.getuid()` and `os.getgid()`; a
  `DOCKER_HOST` that does not name the selected candidate is a named refusal (2.4). Simplest, and makes
  every unsupported configuration visible instead of silent. **My recommendation.**
- *(b) Support rootless.* The Host must interrogate the daemon's mode, because rootless inverts the
  `--user` remedy (inv:3.4), and `--user` becomes daemon-mode-dependent. A real feature, not a flag.
- *(c) Honour `DOCKER_HOST` first, as my peer proposes.* Maximum compatibility, and it re-opens B-13's
  property: the daemon becomes environment-determined. I do not recommend it, but it is the user's call
  if rootless support matters more than endpoint determinism.

**Q4. Is a staging digest ever compared across machines?** This is the only input that could overturn
ruling (9) (section 3.5).

- *(a) No; digests are within-run and within-machine.* `platform_mode` stays in the digest and the
  exec-bit arm is deleted (3.4). **My ruling assumes this**, on the basis that my peer swept the
  consumers and found no cross-machine comparison today.
- *(b) Yes, or planned*, such as a cloud lane reproducing a local stage, a cached stage moved between
  machines, or a recorded expected value in a release record. Then `platform_mode` must leave the digest
  **and** the exec-bit arm must stay, because the deletion's safety argument disappears with it.

**Q5. Does the four-key relaxation (`rev:4.8`) still earn a slot, now that Windows is last?** About ten
lines, preventing a B-13-shaped failure on the last-scheduled platform, in a class impossible on the
first two.

- *(a) Land it whenever Windows work next happens.* **My recommendation.** Still correct, costs nothing
  to defer.
- *(b) Land it in the post-run-12 free-deletions commit.* Cheaper than remembering it; makes that commit
  two changes instead of one.

A sixth question is on my peer's list and not on mine: whether Windows stays supported while POSIX
ships, deciding whether W1 to W8 are deleted (about 4,374 lines lighter) or kept behind a branch
(doubling the acceptance surface). I do not restate it as my own because Q4's "Windows most likely last"
is not the same as "dropped", and the answer changes no ruling here. It changes the size of the eventual
Windows cycle, and it should be asked before that cycle is scoped rather than now.

---

## 7. Scope, dependencies, decisions, risks

### 7.1 Scope in my domain

Mine: rulings (6) through (9); the per-layer POSIX table; the do-once-portably split; the acceptance
rows; the sequencing; the adjudication of the exec-bit disagreement.

Not mine, and deliberately absent: any code change (none was made); ruling (4), which I did not re-open
and which section 4.2 confirms is unaffected; the acceptance of run 12; the spikes, which are my peer's
to specify and an operator's to run; and the five questions in section 6.

### 7.2 Dependencies and interface contracts

**Contracts that move under rulings (6) and (7),** all internal, none public:

- `DockerLocalEndpointDescriptorV1.__post_init__` widens from two literals to a closed ordered candidate
  list with an `S_ISSOCK` probe (2.4). `descriptor_digest` therefore takes more than one value; no
  persisted Windows digest changes.
- A POSIX sibling of `DockerCLIEnvironmentV1` is added. The Windows type is **not** modified by this
  ruling; the `rev:4.6` relaxation is separate and optional (section 6 Q5).
- `compose_docker_prepared_platform_v1` gains a second policy ref. The Windows branch is untouched.
- `DockerPreparedPlatformV1`'s `wsl_distro` and `drive_mount_root` become Windows-policy-only, enforced
  at `docker_provider.py:144-145`, `:175`.
- `_CONTAINER_USER_V1` (`docker_prepared_composition.py:112-113`) admits a derived uid and gid rather
  than the literal `1000:1000` (4.1).
- `docker_staging.py:1289` (`:1298` @`043b0554`) is deleted; `_mode_projection` gains a comment
  (3.4, 3.5).

**Contracts that do NOT change and must be protected:** the closure manifest and its digest; the
`_ARTIFACT_DIRECTORY_NAMES` topology; the thirteen required environment keys; the engine contract in both
directions; `ExecutionSourceV1`; the FOUR provider-shared `security.py` symbols
`FileHmacAuthenticator`, `BoundedGrantProvider`, `ScopedGitRemoteReader` and `utc_now`, of which
`FileHmacAuthenticator.from_context` is the constructor the Modal path uses and `.for_docker` the one
the Docker path uses at `docker_training.py:868` (3.2); and the legacy `docker_v1/composition.py`
route, out of scope entirely.

**Host to engine stays one-directional.** The engine never learns the transport
(`providers/docker_provider_v1/ports.py:1`: "No shell, daemon client, or SDK is imported here"). Rulings
(6) through (9) require **no engine change, no closure regeneration and no pin move**, which is why
section 5.4 row 7 is an acceptance row.

### 7.3 Key decisions and trade-offs

1. **Measure the test tree before pricing a migration, and read what the tests exercise.** Ruling (6)
   turns on section 2.1, and section 2.1 turns on reading 80 test names rather than counting Windows
   literals. A grep said 2.7% Windows and left the direction ambiguous; the names said subprocess
   lifecycle.
2. **Platform-neutral tests are an argument against migrating, not for it.** My peer and I measured the
   same suite and drew opposite conclusions because we were asking different questions. Both readings are
   correct: the suite does not obstruct a port, and that is exactly why discarding it is expensive.
3. **A layer that disappears beats a layer that is relaxed.** Layer 6 on POSIX keeps its real property at
   zero cost and loses the three parts that produced B-13.
4. **Copy the existing portability pattern; do not invent one.** `_local_filesystem_port_v1` already
   solved two platforms with no compatibility layer here, and wrote down why. My peer nominated the same
   model independently.
5. **Absence beats abstraction for the WSL fields.** POSIX has no mount translation, so the fields are
   not populated there. No neutral strategy object.
6. **"Free deletion" is platform-relative.** Two of `rev:4.8`'s three items stop being free the moment
   the platform changes. Any verdict resting on `os.name == "nt"` being a short-circuit has a platform
   precondition, and Q4 revoked it.
7. **When two checks look redundant, find which one runs first.** The exec-bit disagreement resolved only
   after reading the eleven lines between the digest comparison and the closure verifier. Both plans had
   read the check; neither had read its caller.

### 7.4 Risks and concerns

- **Nothing here has been executed, and the largest claims concern a platform nobody can run.** Section
  5.1's macOS GPU and arm64 image claims are [SPEC].
- **Section 1.1 is the strongest finding and the one I most want a second reader on.** It is a four-step
  chain across three files; if any step is wrong the macOS conclusion collapses. My peer found the same
  predicate independently, which raises my confidence in the predicate but not in the reachability chain,
  which only I traced.
- **Section 1.7 is load-bearing and one day old.** Ruling (9) and the exec-bit deletion both rest on the
  ordering of `docker_staging.py:1715-1719` and `:1720` and on `_source_manifest` walking recursively.
  Both
  are cited; both should be re-read by whoever implements the deletion, because if the digest comparison
  ever moves after the closure verifier the argument inverts.
- **I am recommending a deletion whose justification I changed.** `rev:4.8` deleted the exec-bit arm
  because it is vacuous on Windows; I keep the deletion on the section 1.7 argument, because the original
  is false on POSIX. A reader who remembers the verdict and not the reason will reintroduce it.
- **B-16 is the highest-likelihood, highest-cost misfiling in the record.** Both consultants flag it
  independently. If the port drops `USER=synaptic` as "a Windows thing", the first Linux run dies in the
  unsloth import for a cause already solved.
- **Rootless Docker is a blocker class Windows never had** and the Host has no way to detect it today
  (4.1, section 6 Q3).
- **Citation drift is a measured hazard in this record** (diag:4353-4356). Every `docker_staging.py` line
  here was read from `git show 06aa7177:` because that file is under concurrent edit; symbols are named
  alongside line numbers so a reader on a later commit can re-find each site.

### 7.5 Recommended approach, in one paragraph

Rule B-16 as image-class before anything else, because it is free and expensive to get wrong. Ship run 12
untouched. Take the two dead enum members and the driver freeze as genuinely free, and hold the exec-bit
deletion for the POSIX cycle where it lands with its real reason and the `platform_mode` comment. Answer
the five questions, then run the two spikes on Linux, macOS and a rootless daemon before designing
anything, because section 4 is reasoning until they are run. Widen the macOS capability predicate as its
own measured change. Do the layer-5 split POSIX-first, where the deleted code is code the live lane does
not execute, keeping `FileHmacAuthenticator`'s two constructors intact for the Modal providers. Then
change the endpoint descriptor to a probed candidate list, add the POSIX policy ref as a sibling factory
keeping the `docker` CLI, and take the first Linux run against the nine rows in section 5.4. Do not
migrate the transport: on POSIX the Engine API deletes nothing, because the layer it was going to delete
does not exist there, and it costs 2,540 lines of finished, portable subprocess-lifecycle tests that the
CLI keeps.

---

## Appendix A — `docker_staging.py` symbol-to-line map

Every symbol this document cites, at both commits. `06aa7177` is the citation baseline; `043b0554` is
`coder-verifier`'s landed ruling-(4) edit. Derived by locating each symbol in `git show <sha>:` output,
not by adding an offset: the drift is **not** uniform. Sites above `_verify_inventory_at` moved by +9,
sites from the read-only verify call onward moved by +46 to +54, because the edit inserted in two
places.

| Symbol or site | `06aa7177` | `043b0554` | Cited in |
|---|---|---|---|
| `_walk_regular_files` def | 135 | 144 | 1.7 |
| `_apply_file_mode` def | 161 | 170 | 1.5, 3.4 |
| `_verify_file_mode` def | 168 | 177 | 1.5, 3.3, 3.4 |
| `_mode_projection` def (body 917-920 / 926-929) | 917 | 926 | 1.4, 3.5 |
| `_apply_file_mode(path, executable=False)` | 914 | 923 | 3.4 |
| `_verify_staged_closure` def | 1278 | 1287 | 1.7, 3.4 |
| closure `_apply_file_mode(target, executable=member.git_mode == "100755")` | 1274 | 1283 | 3.4 |
| **exec-bit `_verify_file_mode(...)` call — the site ruling (9) deletes** | **1289** | **1298** | 1.5, 1.7, 3.3, 3.4, 7.2 |
| `_apply_file_mode(target, executable=mode == "100755")` | 1363 | 1372 | 3.4 |
| inventory `_apply_file_mode(target, executable=False, read_only=True)` | 1452 | 1461 | 4.2 |
| `_verify_inventory_at` def | 1459 | 1468 | 1.7, 3.4 |
| **read-only `_verify_file_mode(info, executable=False, read_only=True)` — the site that STAYS** | **1492** | **1538** | 1.5, 1.7, 3.4, 4.2 |
| `_verify_inventory_at(entries, root / "cache")` | 1545 | 1599 | 1.7, 3.4 |
| `_source_manifest` def | 1557 | 1611 | 1.7 |
| `_walk_regular_files(root, "staged source")` call | 1559 | 1613 | 1.7 |
| `"platform_mode": _mode_projection(info)` | 1570 | 1624 | 1.4, 1.7, 3.5 |
| `_digest(b"synaptic-host-docker-source-manifest/v1", entries)` | 1572 | 1626 | 1.7 |
| `observed_entries, observed_digest = _source_manifest(source)` | 1709 | 1763 | 1.7, 3.4 |
| **`or observed_digest != projection.source_manifest_digest` — the digest clause** | **1715** | **1769** | 1.7, 3.4, 7.4 |
| `or closure_bytes != closure.manifest_bytes` | 1717 | 1771 | (not cited; this is the line the draft wrongly named) |
| **`raise ValueError("content-addressed Docker stage differs from preparation")`** | **1719** | **1773** | 1.7, 3.4 |
| **`_verify_staged_closure(source / "engine", closure)`** | **1720** | **1774** | 1.7, 3.4, 7.4 |

The two bold rows at `:1715` and `:1720` carry ruling (9) and the exec-bit ruling. The ordering claim is
that the digest comparison at `:1715` raises at `:1719` **before** `_verify_staged_closure` is called at
`:1720`, and that ordering is preserved verbatim at `043b0554` (`:1769` / `:1773` / `:1774`).

---

*Ruled by `architect-posix` for task #295. Read-only against `06aa7177` and engine `ce539b70`;
`docker_staging.py` citations taken from `git show 06aa7177:` because that file is under concurrent
edit. The only file written was this one. No code change, no commit, no push, no execution of any kind.
Section 1 reports findings I verified myself; section 2.1 retires a prediction I pre-registered in my own
teachback; section 3.4 overrules my peer with evidence rather than preference; section 2.4 accepts a
correction from my peer that my own draft had wrong.*
