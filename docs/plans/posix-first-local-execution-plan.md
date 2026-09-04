# Plan: POSIX-first local execution for the Host

**Status:** DRAFT, awaiting user decisions (section 8).
**Planning task:** #291 (team session-fd2a12ec, 2026-09-04). Consultations: preparer-posix #293
(`docs/preparation/posix-first-local-execution-inventory.md`, commit d697d3d2), architect-posix #295
(`docs/architecture/posix-first-local-execution-review.md`, commit f1396b21).
**Trigger:** user ruling Q4 (2026-09-04, `docs/plans/host-path-simplification-plan.md`): the desktop app
ships on macOS and Linux first, Windows most likely last. That fired the named trigger of ruling (3)
(`docs/architecture/host-path-simplification-review.md` 2.3), so the transport question re-opened.
**Baseline read by both consultants:** Host worktree HEAD `06aa7177`, engine pin `ce539b70`. Ruling (4)
(commit `043b0554`, run 12) is not re-opened and is confirmed platform-independent by both.

Consumers are named generically throughout: a desktop app on a user's machine, a web app driving cloud
compute. Nothing in this plan changes the engine, the closure manifest, or the submodule pin.

---

## 1. Summary

The premise that the Host is Windows-shaped was wrong in both directions. About 4,374 of 40,109
production lines (10.9 percent) are Windows-only by construction and only about 1,973 of those have no
POSIX counterpart; the filesystem port already has a complete, tested POSIX arm
(`synaptic_host/local_io_v1/posix.py`, 835 lines, all 21 port methods) dispatched by a two-branch
`os.name` factory, and five of `security.py`'s eight platform branches enforce stricter permissions on
POSIX than on Windows. In the other direction, no POSIX transport exists at all: zero occurrences of
`AF_UNIX`, `unix://` or `docker.sock` in the package, and `DockerLocalEndpointDescriptorV1` cannot
represent a POSIX endpoint today.

The finding that changes the plan: **macOS is refused on the prepared path by a tested predicate.**
`detect_posix_capability_v1` (`posix.py:73`) grants availability only when the platform string starts
with `linux`; `PosixRetainedDirfdPortV1` raises `CAPABILITY_UNAVAILABLE` otherwise (`:104-107`);
`publication_composition.py:411-413` constructs that port on every non-Windows platform; publication is
on the prepared path; `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py:199-201` pins
darwin as UNAVAILABLE. The platform the user ruled ships first cannot complete a run as the code stands.
The lead re-read every link of that chain from the tree (acceptance record on #295).

The architect's rulings, numbered on from the simplification review:

| # | Ruling | Where |
|---|---|---|
| (6) | **Keep the `docker` CLI on POSIX**, made portable behind a policy-ref-keyed sibling factory copying the `local_io_v1` shape. No Engine API migration. | review 2 |
| (7) | Per-layer shape on POSIX: three layers disappear, three change shape, six unchanged, plus a thirteenth layer the simplification review never inventoried. The SHARED gate is discharged; the one shared Host layer is layer 5 (HMAC half of `security.py`). Two of review 4.8's three "free deletions" are not free on POSIX. | review 3 |
| (8) | **Sequence Linux, then macOS, then Windows** for the Host's local Docker path. This is an internal order justified by the macOS predicate, not a change to Q4's ship order. | review 5.3 |
| (9) | **`platform_mode` stays in the source-manifest digest.** This is what makes the exec-bit arm deletion safe; the two are coupled and must land together or not at all. | review 1.7, 3.4, 3.5 |

Two dispatch premises were wrong and are corrected in both documents: there is no HF Jobs provider in
`synaptic_host` (the 2,512 lines are `modal_provider.py` 1,077, `modal_resolver.py` 775,
`modal_training.py` 660; verified by the lead), and those providers import nothing from the local Docker
path. The shared boundary is four `security.py` symbols, not one: `modal_training.py` imports
`FileHmacAuthenticator`, `BoundedGrantProvider`, `ScopedGitRemoteReader` and `utc_now`; `modal_provider.py`
imports `FileHmacAuthenticator` only; `modal_resolver.py` imports nothing from it. The Modal path calls
`FileHmacAuthenticator.from_context`, the Docker path `for_docker` (`docker_training.py:868`).
`ScopedGitRemoteReader._run` carries the B-7 `os.name == "nt"` SystemRoot passthrough, inert on POSIX; it
does not reintroduce the fork risk, but the layer-5 split is scoped against the real four (preparer
correction at agreement check, adopted by the architect into review 3.2 and 7.2). Consequence: the
provider-safety constraint sits on `from_context` only; `for_docker` (`security.py:672`, `repair=True` at
`:701`) is a Docker-path-internal seam, still the sharpest one, and the CODE task for the layer-5 split
must not conflate the two.

## 2. What the consultants agree on

1. B-16 is an image property (a uid absent from the image passwd, `getpass.getuser` falling to
   `pwd.getpwuid` inside the inductor cache during the unsloth import), not a Windows property. It
   recurs unchanged on Linux. The `USER=synaptic` binding must survive the port. Both rank this the
   highest-likelihood, highest-cost misfiling in the record.
2. Spike before designing. Two one-command spikes (inventory 2.4), one on native Linux and one on
   macOS, plus a rootless repeat and a print of `os.supports_dir_fd`, `os.supports_follow_symlinks` and
   `fcntl.flock` on darwin. Everything about container user, mount ownership and the socket on real
   hardware is `[UNVERIFIED-BY-EXECUTION]` until then.
3. Change the endpoint descriptor first, transport second: `DockerLocalEndpointDescriptorV1.__post_init__`
   pins the npipe URL as an invariant, so neither transport option is implementable until it widens.
4. The endpoint on POSIX is a closed, ordered candidate list of Host-authored socket constants probed
   with `S_ISSOCK`, never a single pinned path (a pinned `/var/run/docker.sock` breaks default macOS
   installs and every rootless Linux user). The preparer's research corrected the architect's draft here.
5. Copy the existing portability pattern (`PosixFilesystemPortV1`: one Protocol, two branch-local
   implementations, a factory that never cross-imports). Do not invent a neutral strategy object; the
   WSL fields (`wsl_distro`, `drive_mount_root`) are simply absent on POSIX.
6. Widen `posix.py:73` as its own small, measured change after the three-fact measurement, never folded
   into transport work.
7. Rootless Docker on Linux inverts the B-9 `--user 1000:1000` remedy (container uid 1000 maps into the
   subuid range): a blocker class Windows never had, undetectable by the Host today.
8. The one measurement taken (preparer, authorised, read-only): `/var/run/docker.sock` inside WSL
   Ubuntu-22.04 is a plain `AF_UNIX` socket, mode 0660 root:docker, and `GET /version` from 33 lines of
   standard library returned HTTP 200, API 1.54. Tagged Docker-Desktop-on-Windows-through-WSL; it settles
   the client shape only and is not evidence about native Linux or macOS.
9. Run 12 ships untouched, single-cause. Nothing in this plan touches ruling (4).
10. `docker_staging.py:1612` feeds `platform_mode` into the source-manifest digest, so byte-identical
    trees digest differently across platforms; harmless while digests are produced and verified within
    one run on one machine (no golden constant found), corruption-shaped the moment one crosses machines.
    On POSIX it is also the ONLY mode coverage of the source stage, which is why it must stay (ruling 9):
    deleting the closure-arm call site AND removing `platform_mode` are each defensible alone and jointly
    leave the stage with no mode coverage at all. State the coupling as a coupling; each half read alone
    looks like a cleanup. Both consultants hold this after the preparer withdrew its 1.4 lean.

## 3. Conflicts and how they were resolved

| Conflict | Preparer | Architect | Severity | Resolution |
|---|---|---|---|---|
| Transport on POSIX | "Engine API is now cheap enough to be the default" (inventory 8 row 1): Route B's Windows cost was ctypes plus unverified overlapped I/O; on POSIX it is stdlib and measured, the remaining cost is the log-stream demultiplexer alone, sized 250-400 lines. | KEEP the CLI (ruling 6): migration destroys about 2,540 lines of already-portable subprocess-mechanism tests (`test_cli.py` is 49 Windows-literal lines of 1,843; its 80 tests are subprocess-lifecycle tests), and on POSIX it deletes no sealing layer because three of layer 6's four components are inapplicable there and the fourth (the denylist carrying the real property) is portable verbatim. The Engine API buys zero blockers relative to a portable CLI. | Major, resolved by concession | Resolved in the review with evidence, then CONCEDED by the preparer at the agreement check after verifying from the tree: `docker_publication.py` refuses logs with `CAPABILITY_UNAVAILABLE` and `DockerVerb.LOGS` has zero call sites package-wide, so the demultiplexer it priced was a cost for a capability the Host declines; and its test-tree measurement answered feasibility (the suite does not obstruct a port), not desirability (migration destroys it). The architect retired its own pre-registered contingency (sunk-cost reading) as measured false. Ruling (6) stands, with the preparer's condition on record: it is a decision to PORT the CLI path, not a finding that it works today (`DockerLocalEndpointDescriptorV1.__post_init__` still pins `desktop-linux` and the npipe URL). Revisit triggers (review 2.3, two): the first POSIX blocker whose cause is CLI discovery, argv construction or CLI environment; and any product requirement for container log streaming or attach semantics, for which the CLI's bounded-drain design (`cli.py:723`, `:758`) is the wrong shape. The second interacts with step 1 below: the preparer's concession rests partly on `DockerVerb.LOGS` having zero call sites, and that verb is one of the free deletions, so the deletion's commit message must record the condition that made it free, or a future logs requirement finds neither the capability nor the trigger. |
| Exec-bit arm `_verify_file_mode` | KEEP: vacuous only on nt (`docker_staging.py:180-183`, verified by the lead), it becomes a live 0o444/0o755/0o644 predicate on POSIX; deleting it as "free" removes a check about to start working. | DELETE, on a third argument neither prior plan had: `_verify_prepared_stage` compares the source-manifest digest one statement before calling the closure verifier (digest clause `06aa7177:1715`, raise `:1719`, `_verify_staged_closure` call `:1720`; at `043b0554` `:1769`, `:1773`, `:1774`; the architect's original `:1717` cite was its own error, corrected at the agreement check), and `platform_mode` makes that digest carry every staged file's real mode, so a mode-clamping filesystem fails at the digest first across all 66 members. | Major, withdrawn | The preparer WITHDREW its KEEP finding at the agreement check after verifying the architect's argument from the tree (`_walk_tree` is recursive so `_source_manifest` digests `source/engine`; the digest comparison precedes `_verify_staged_closure`; `platform_mode` carries every file's full mode on POSIX), so the reason for the disposition is the architect's, not the preparer's. Resolution: DELETE only the closure-arm call site (old `:1289`, now `:1298`), keep the function and its read-only site (old `:1492`, now `:1538`), held for the POSIX cycle where it lands with its real reason and a `_mode_projection` comment, coupled with ruling (9). The preparer's residual concern (deletion as "free" before the port, under the vacuity reason) is honoured: the post-run-12 free-deletions commit is the two dead enum members only. A reader who remembers the verdict and not the reason will reintroduce it (review 7.4). |
| `platform_mode` in the digest | Remove, or rule explicitly that digests never cross machines (withdrawn at the agreement check: removal is wrong for the same reason the exec-bit KEEP was). | KEEP (ruling 9); it preserves the mode-integrity property the deleted arm carried. | Minor, conditional | Ruling (9) stands on the assumption that no digest crosses machines (preparer swept the consumers, found none). User Q4 below can overturn it; if a digest ever crosses machines, `platform_mode` leaves the digest AND the exec-bit arm stays. |
| Sequencing vs the user's ship order | (no ruling; inventory only) | Linux, then macOS, then Windows. | Minor | Adopted as the internal order of the Host's POSIX work. It does not contradict Q4 (which platforms the product ships on). Surfaced to the user as an explicit acknowledgement item. |
| `DOCKER_HOST` | Candidate list honouring `DOCKER_HOST` first. | Closed candidate list, `DOCKER_HOST` never honoured first; a `DOCKER_HOST` that disagrees with the selection is a named refusal, because honouring it re-opens the property B-13's fix removed (environment-determined daemon). | Minor | Architect's shape adopted as the default; surfaced as user Q3 option (c) because rootless support may matter more than endpoint determinism. |

No blocking conflict remains.

## 4. Specialist perspectives (what moves, by phase)

**PREPARE (done for planning; required again before design):** the inventory stands. Open research
(inventory 5.1): native Linux socket path, mode and group; macOS socket path and VirtioFS uid mapping;
whether `os.supports_dir_fd` on CPython/darwin contains the five functions `posix.py` requires; rootless
repeat; macOS bind-mount throughput; B-8 identity; per-blocker fix sizes.

**ARCHITECT (rulings 6-9 done; descriptor and factory detail specified in review 2.3-2.4, 7.2):**
contracts that move, all internal: `DockerLocalEndpointDescriptorV1.__post_init__` widens to the probed
candidate list (`descriptor_digest` takes more than one value, no persisted Windows digest changes); a
POSIX sibling of `DockerCLIEnvironmentV1`; `compose_docker_prepared_platform_v1` gains a second policy
ref, Windows branch untouched; `wsl_distro` and `drive_mount_root` become Windows-policy-only, enforced at
`docker_provider.py:144-145, :175`; `_CONTAINER_USER_V1` (`docker_prepared_composition.py:112-113`)
admits a derived uid and gid; `docker_staging.py:1289` deleted with a `_mode_projection` comment.
Protected: the closure manifest and digest, `_ARTIFACT_DIRECTORY_NAMES`, the thirteen required
environment keys, the engine contract in both directions, `ExecutionSourceV1`, the four `security.py`
symbols the Modal path imports (section 1), the legacy `docker_v1/composition.py` route (out of scope).

**CODE (future cycles, each single-cause):** endpoint descriptor; POSIX policy ref and factory; derived
`--user`; `posix.py:73` widening (own change); exec-bit deletion plus `platform_mode` comment (own
change, coupled); layer-5 split POSIX-first (own cycle with security review, carrying the
`test_security.py` source-scraping pin); free deletions after run 12 (two dead enum members only).

**TEST:** acceptance rows for the first Linux run are review 5.4 rows 0-8 (row 5, the newly live
exec-bit arm actually comparing, has no Windows precedent; row 4, the unsloth import at
`train_sft.py:137`, is where B-16 either transfers or does not; row 7, pin unchanged across the release
range). The OSError re-raise clause added under ruling (4) (`_verify_inventory_at`, untested by
construction on DrvFs) gets its real test on the first POSIX lane, where a chmod fixture is portable.

## 5. Roadmap

| Step | What | Gate | Owner |
|---|---|---|---|
| 0 | Record B-16 as image-class, not Windows-class (blocker #256 metadata, ruling record). | now | lead |
| 0b | Run 12 ships as planned, untouched: audit #297, counter-test #299, push, release, run 12. | in flight | auditor-run, test-engineer, test-host |
| 1 | Free deletions commit: two dead enum members (`DockerVerb.STOP/LOGS`) only; exec-bit arm held. The commit message records why `LOGS` is free (logs refused with `CAPABILITY_UNAVAILABLE`, zero call sites) and names the second transport revisit trigger. | after run 12 | coder |
| 2 | Driver freeze (Q5 A of the prior plan), docs only. | any time | coder-workflow |
| 3 | User answers section 8. | blocks everything below | user |
| 4 | Run the inventory 2.4 spikes on Linux, macOS and a rootless daemon; print the darwin `os.supports_*` facts. | a POSIX machine exists | operator (user) plus preparer |
| 5 | Widen `posix.py:73` as its own measured change. | spike green, Q1 keeps macOS in scope | coder, small |
| 6 | Layer-5 split, POSIX-first, own cycle with security-engineer review. | Q1/Q2 of the prior plan answered (they are) | orchestrate |
| 7 | Endpoint descriptor (review 2.4), then POSIX policy ref (2.3); exec-bit deletion plus `platform_mode` comment (3.4, 3.5), coupled. | steps 4-5 done | orchestrate |
| 8 | First Linux run against review 5.4 rows 0-8. | step 7 released | test-host on a Linux box |
| 9 | macOS lane, only if Q2 keeps local execution on macOS in scope. | first Linux run green | test-host on a Mac |
| 10 | Modal and RunPod smokes. | independent of 5-9 (the providers cannot be forked by this work) | orchestrate |

Single-cause discipline: steps 1, 5, 6, 7 and 9 each change something a run could blame; do not bundle
them. Bundling the layer-5 split with the transport factory would make a failed first Linux run ambiguous
between a permissions change and a transport change, the two families that produced eight of the
twenty-one Windows blockers.

## 6. Cross-cutting concerns

- **Security:** no third-party dependency ever (Q3 A of the prior plan); endpoint determinism is a
  property (B-13's fix removed environment-determined daemon selection) and `DOCKER_HOST` must not
  silently re-open it; the layer-5 split keeps keyed-HMAC evidence and drops ACL enforcement, and needs
  its own security review; on POSIX the file-mode integrity property moves from the exec-bit arm to the
  digest (ruling 9), which is why the two changes are coupled.
- **Performance:** macOS bind-mount throughput over VirtioFS is materially worse than native and the
  prepared path stages a scoped archive plus a model inventory; a multi-gigabyte model cache is a
  plausible new blocker with no Windows analogue. Unmeasured; review 5.4 row 8 records the staging
  wall-clock on Linux for later comparison.
- **Observability:** the acceptance rows record the selected socket candidate and the child environment
  key set (row 1), and source-manifest entries carrying `posix-0644`-shaped modes (row 2).
- **Engine boundary:** Host to engine stays one-directional; rulings (6) to (9) need no engine change,
  no closure regeneration, no pin move (row 7 is the acceptance of that).

## 7. Require further research (before step 7 is designed)

- [ ] Native Linux spike (inventory 2.4): socket path, mode, group; `GET /version` from stdlib.
- [ ] macOS spike: socket path under the supported runtime; VirtioFS uid mapping; the three
      `os.supports_*` facts on darwin.
- [ ] Rootless repeat of the Linux spike (needed only if Q3 answers "support rootless").
- [ ] macOS bind-mount throughput on a multi-gigabyte stage (needed only if Q2 keeps macOS local execution).
- [ ] B-8 identity (gap in the blocker series, carried from the prior inventory).
- [ ] Per-blocker fix sizes from `git log --stat` over the release clones (prior plan's open item).

## 8. Open questions (user decisions)

- [ ] **Q1. Which POSIX platform is the Host's local Docker path for?** (a) Linux only for now; macOS
      users of the desktop app drive cloud compute. Cheapest; the first run is reachable as soon as a Linux
      machine is. (b) Linux and macOS both; repriced downward to one predicate at `posix.py:73` plus a
      three-fact measurement, conditional on that measurement passing. **Architect recommends (b),
      conditional.** (c) macOS first, literally matching the ship order; most expensive and proves the least.
- [ ] **Q2. On a Mac, does "local execution" mean real training or exercising the path?** A CUDA trainer
      image cannot train on a Mac and the pinned image is almost certainly unusable on Apple silicon. (a)
      Exercise the path with a CPU-only smoke image (one-line change at `docker_training.py:927` plus a
      CPU-capable image); proves composition, staging, admission, lifecycle, publication, not training.
      (b) macOS drives cloud compute only; zero Host work for macOS, the macOS predicate leaves the critical
      path. (c) Real training on a Mac: a different image and an MPS-capable engine path, an engine question.
      **Highest-value question in this plan.**
- [ ] **Q3. Rootless Docker and `DOCKER_HOST`.** (a) Root-ful only, refuse loudly otherwise; `--user`
      derived from `os.getuid()`/`os.getgid()`; a `DOCKER_HOST` naming a different daemon is a named
      refusal. **Architect recommends (a).** (b) Support rootless: the Host must interrogate the daemon's
      mode, a real feature. (c) Honour `DOCKER_HOST` first: maximum compatibility, re-opens B-13's property.
- [ ] **Q4. Is a staging digest ever compared across machines?** (a) No: `platform_mode` stays in the
      digest and the exec-bit arm is deleted (ruling 9, coupled). **Assumed by the rulings.** (b) Yes or
      planned (a cloud lane reproducing a local stage, a cached stage moved between machines, a recorded
      expected value): `platform_mode` leaves the digest and the exec-bit arm stays.
- [ ] **Q5. The four-key relaxation (review 4.6/4.8, about ten lines, Windows-only class).** (a) Land it
      whenever Windows work next happens. **Architect recommends (a).** (b) Land it in the post-run-12
      free-deletions commit (makes that commit two changes).
- [ ] **Q6. Which macOS runtime is supported: Docker Desktop, Colima, Podman, or any socket?** Decides
      whether the endpoint is a candidate list or a supported matrix; the preparer calls it the largest
      unpriced fork. Only needed if Q1 keeps macOS in scope.
- [ ] **Q7. Does the Windows path stay supported while POSIX ships?** Deleting W1-W8 is about 4,374 lines
      lighter; keeping them behind a branch doubles the acceptance surface for every future change. Q4
      ("Windows most likely last") is not "dropped". Changes no ruling here; should be asked before the
      Windows cycle is scoped, not now, unless the user wants it settled.
- [ ] **Acknowledge:** the internal order Linux, then macOS, then Windows (ruling 8), and that the gating
      item for every step from 4 onward is a machine on the team that can run Linux Docker; none can today.

## 9. Risk

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `USER=synaptic` dropped in the port as "a Windows thing"; first Linux run dies in the unsloth import for a solved cause | High | High | Step 0 ruling; review 5.4 row 4 |
| Exec-bit arm deleted as "free" before the port, or reintroduced by a reader who remembers the verdict and not the reason | High if the two plans run independently | Medium | Held to step 7, coupled with ruling 9; the deletion's reason recorded in the `_mode_projection` comment |
| A pinned socket path ships | Medium | High | Probed candidate list (agreement 4) |
| `posix.py:73` widened without measuring the darwin facts; `posix.py`'s own assertions start failing at runtime instead of reporting UNAVAILABLE | Medium | High | Step 4 before step 5 |
| Rootless daemon undetected; `--user` wrong in the B-9 direction | Medium | Medium | Q3; root-ful only refuses loudly |
| `test_security.py` source-scraping pin trips mid layer-5 split | High if unbriefed | Low | Carry the pin in the CODE task scope |
| Everything platform-specific is reasoned, not run; the largest claims concern a platform nobody can execute | Certain until step 4 | High | `[PROVISIONAL-ON-FIRST-POSIX-RUN]` marking; review 5.4 names the row that settles each |
| The digest-before-verifier ordering (`06aa7177:1715`, `:1719`, `:1720`) moves and the ruling 9 argument inverts | Low | High | Implementer of step 7 re-reads both lines by symbol |

## 10. Limitations

- Nothing was executed on native Linux or macOS. The one measurement is Docker Desktop through WSL.
- No test engineer, security engineer or devops engineer was consulted; the layer-5 split and the
  endpoint change each need their own review when scoped.
- The architect overruled the preparer on transport with evidence; the preparer's document records its
  reading as "my reading", not a ruling, but the disagreement is real and is verified in the agreement
  check below rather than assumed away.
- File counts differ between the two inventories (57 vs 58 production files; 40,028 vs 38,101 test
  lines); the production line total (40,109) agrees. Neither number is load-bearing for a ruling.
- Review section 1.7 (digest before verifier) is one day old and load-bearing for ruling (9); the preparer
  re-verified the ordering by symbol at the agreement check, and the architect found its own `:1717` cite
  was wrong at both commits (clause `:1715`, raise `:1719` at `06aa7177`); the argument is unchanged.
- Both consultation documents cite `docker_staging.py` at baseline `06aa7177`; ruling (4) (`043b0554`)
  landed mid-consultation and shifted every cite (`:1545` is now `:1599`, `:1289` is `:1298`, `:1492` is
  `:1538`, `:1715`, `:1719` and `:1720` moved). Nothing in either analysis is wrong because of it (audit #275
  YELLOW-3 recurring); both documents are repointed by symbol in one docs commit (683b268d), the review carrying a
  full symbol-to-line map at both commits (Appendix A). The drift is not uniform (+9 above
  `_verify_inventory_at`, +46 to +54 from the read-only verify call onward), so never repoint by offset.
- The macOS refusal chain is four steps across three files; the lead re-read each step, the preparer
  found the predicate independently, only the architect traced the reachability.

## 11. Phase requirements

| Phase | Required | Why |
|---|---|---|
| PREPARE | REQUIRED | Section 7 has unchecked research items; section 8 has unresolved user questions; the spikes are investigation tasks in the roadmap. |
| ARCHITECT | REQUIRED (narrow) | Rulings 6-9 stand; the endpoint descriptor widening and the POSIX policy factory need their design landed against the spike results before CODE (review 2.3, 2.4, 7.2 specify the shape). |
| CODE | REQUIRED | Steps 1, 2, 5, 6, 7. |
| TEST | REQUIRED | Review 5.4 rows; both-lane counter-tests carry a third lane once a Linux box exists. |

## 12. Next steps

1. Lead: agreement verification with both consultants on this synthesis; fold corrections; then present
   section 8 to the user as decisions with priced options.
2. Lead: step 0 now (B-16 image-class record on #256), step 0b in flight (#297, #299, run 12).
3. After run 12 and the user's answers: `/PACT:comPACT` for step 1 (two enum members) and step 2 (driver
   freeze); a PREPARE spike task for step 4 once a POSIX machine is named; then `/PACT:orchestrate`
   for steps 5-7 as separate single-cause cycles, layer-5 split first.
