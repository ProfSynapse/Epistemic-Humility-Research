# Peer review: native-Windows artifact publication closure

- PR: https://github.com/ProfSynapse/Epistemic-Humility-Research/pull/596 (base `main`, head `feat/submodule-cloud-api-v1-host`)
- Review scope: commit `0273793af01a4f4a42cf3ff51980f634df878a72` (`85b922fc..0273793a`, 12 files, +5415/-34); engine submodule `synaptic-tuner` unchanged at `aec998ee`
- Reviewers: architect (design coherence, task #35), test-engineer (coverage and testability, #37), reviewer-backend (implementation quality, fresh backend coder, #39), reviewer-security (adversarial, #41)
- Date: 2026-09-02

## Verdict

Changes requested: one Blocking finding (B-1), remediated in this PR before merge. All four reviewers otherwise recommend approve-with-minors. No forbidden addition (downloader, cache framework, compatibility layer, new table, legacy composition fallback, Docker-specific destination model) crept in; the strongest evidence is that the destination builder and `compose_docker_publication_v1` sit outside the change set. Both host-found `#24` fixes were re-derived independently from NT semantics and are correct on their own merits; no handle leak was found on any early-return or exception path.

R-6 (spool root silently rebound across restart) stays **not gating**. The security reviewer verified rather than inherited the containment argument: the HMAC key is hard-confined below `project_root/.synaptic` (`publication_authority.py:576-582`), the spool path is read as a committed git blob at a pinned commit (`docker_training.py:637-640`), digest-bound into the stage key (`docker_staging.py:1743-1752`) and re-validated at `docker_publication.py:358-363`, and nothing derived from `verify()==True` leaves the local trust boundary because `verify()` has no production consumer at all (`publication_composition.py:313`). Mid-life re-opens are identity-checked (`filesystem.py:1576-1590`), so the unbound window is first retention only. The disposition is conditional on two properties no code enforces: the spool root being project-relative by configuration (`config.py:134-140` accepts any absolute path for a non-`project://` location) and the absence of a `verify()` consumer. Under the premise of a lower-trust spool parent, R-6 becomes Blocking and F-3 (detect on re-retain) is insufficient; the fix would then be admission-time (restrictive DACL, ownership check).

## Findings

### Blocking

| ID | Location | Finding | Reviewer |
|----|----------|---------|----------|
| B-1 | `windows.py:526` with `:958-978`; `filesystem.py:3241-3253` | `_nt_open_relative`'s catch-all maps every unnamed NT status to `PATH_INVALID`; `stat_at` treats `PATH_INVALID` as keep-probing and returns `None`; `filesystem.py` turns `None` into `RecoveryStatusV1.DEFINITELY_ABSENT`. `STATUS_ACCESS_DENIED`, `STATUS_DELETE_PENDING`, `STATUS_INSUFFICIENT_RESOURCES`, `STATUS_REPARSE_POINT_ENCOUNTERED` all report a name as absent. POSIX (`posix.py:321-328`) returns `None` only for `FileNotFoundError` and raises `IO_FAILED` otherwise, so this is Windows-only fail-open at a predicate the design needs fail-closed. Lead confirmed by reading the lines. Fix: name `STATUS_FILE_IS_A_DIRECTORY` (0xC00000BA), `STATUS_NOT_A_DIRECTORY` (0xC0000103) and `STATUS_OBJECT_PATH_NOT_FOUND` (0xC000003A) explicitly, default the remainder to `IO_FAILED`, and let `stat_at` continue only on not-found and wrong-type codes. Security reviewer logged the same site as S-6 (Future) under a narrower framing; the backend framing governs. | reviewer-backend (S-6 reviewer-security) |

### Minor

| ID | Location | Finding | Reviewer(s) |
|----|----------|---------|-------------|
| M-1 | `windows.py:887-900` (invariant at `:25-26`; POSIX `posix.py:258-266`) | Descent does not bind the enumerated entry to the opened handle: `_root_component` returns a name, `_query_identity` proves directory-and-not-reparse, nothing compares its identity to the entry matched at `:833`. Contradicts design rule 1 ("re-proves identity at every component") and design doc §7. Rated Minor because it grants no capability over plain R-6 substitution; a defence-in-depth loss. `_directory_entries` already parses each entry's 128-bit FileId (field 12, unpacked at `:604`, discarded at `:627`); returning it and comparing to `_query_identity(child).inode` restores the invariant and delivers the descent half of F-3. Security reviewer recommends fixing in this PR. | reviewer-security |
| M-2 | `windows.py:1504` | `_unlink_raw` iterates `_admission_leases.values()` without `_admission_lock`; POSIX uses a lock-refreshed snapshot (`posix.py:376-380`). A concurrent acquire/release raises `RuntimeError` out of `unlink_at`, escaping the closed taxonomy. | reviewer-backend, reviewer-security |
| M-3 | `windows.py:806-815` | `_retain_file_handle` collapses every `_query_identity` failure to `IO_FAILED` (`raise _closed() from None`), while the directory sibling re-raises; a reparse-point file loses the `ROOT_CHANGED` signal. | reviewer-backend, reviewer-security |
| M-4 | `windows.py:595` (`_query_identity`) | The post-open reparse re-check has no behavioural test; its only test reference is a constants assertion. The `_root_component` docstring justifies the defect-3 narrowing partly on this second refusal, so the permissive half of defect 3 leans on an unexercised branch. Deleting it turns nothing red. | test-engineer |
| M-5 | `test_windows_port_contract.py:490` | The defect-1 Linux belt asserts the double-quoted `"."` literal is absent from the admission source; a single-quoted reintroduction passes. Demonstrated, not asserted. Fix: AST walk instead of substring match. | test-engineer |
| M-6 | `windows.py:876`, `:892` | The defect-2 test pins the mask constants and the subset relation but not the call sites; reverting a call site leaves Linux green and fails on Windows only under a system-volume basetemp. Nothing in the repo records that the Windows suite is diagnostic for defect 2 only on a system-volume basetemp. | test-engineer |
| M-7 | `windows.py:651`; `filesystem.py:2682-2686` | `_directory_names` vetoes the whole listing on any reparse entry and `filesystem.py` rewrites that to bare `IO_FAILED`; one junction or OneDrive placeholder in the destination fails every create on Windows, while POSIX has no reparse check. Conflict: the architect confirms whole-directory strictness for `list_names_at` is the design as ruled (#26); the backend reviewer calls the sibling veto over-broad, the same shape removed one hop up in `_root_component`. Needs an architect ruling before any change. | reviewer-backend (design conflict with architect) |
| M-8 | `docker_execution.py:1106-1107` | `if self._publication is None: return from_record(current)` is silent success that publishes nothing; the line is unchanged but this commit's wiring makes `publication=None` reachable there for the first time. | reviewer-backend |
| M-9 | `windows.py:574-640` | `_directory_entries` stops only at 64 KiB batch boundaries so it can return far more than `maximum`; the internal `LIMIT_EXCEEDED` trip uses the module constant, not the parameter. Security reviewer confirmed truncation is fail-closed (every consumer rejects strictly-more-than-maximum: `filesystem.py:1982`, `:2685`, `windows.py:1352`). | reviewer-backend |
| M-10 | `windows.py:427` | `_close_handle_quietly` catches `BaseException`, swallowing `KeyboardInterrupt` and `SystemExit`. | reviewer-backend |
| M-11 | `windows.py:105-116` vs `filesystem.py:579-590` | The port publishes feature string `directory-id-admission` while `filesystem.py` adds `directory-inode-admission` for the same Windows property; both are hashed into capability digests. Question for the architect: deliberate? | reviewer-backend |
| M-12 | `windows.py:1161-1163` | The DELETE-axis admission is symmetric in a direction the doc does not state: any pre-existing handle on the spool root whose share mask omits `FILE_SHARE_DELETE` denies the Host's own admission as `ROOT_IN_USE`; holding one needs only read access. Availability only, fail-closed. Argued from documented semantics, not executed; confirm on the host that ran the R-4 measurement. Backend reviewer logged the mirror case (`:1136-1160`) as Future. | reviewer-security, reviewer-backend |
| M-13 | `publication_composition.py:313`; design doc §11 R-6 | `verify()` has no production consumer; the R-6 deferral is safe because of an absence. The ledger should record the two trigger conditions (first production consumer of `verify()`; a deployment pointing the spool root at a non-project absolute path) that would make F-3 gating. Doc-only amendment on a file the architect owns. | architect |
| M-14 | `docker_prepared_composition.py:313-314` | `DockerPreparedCompositionV1.prepare_admission` is now unused in production (pure delegation; `docker_training.py:857` calls the builder directly). Dead delegation on a public surface invites reintroducing the eager-composition cost. | architect |
| M-15 | `publication_composition.py:394` | `_local_filesystem_port_v1` is annotated `-> object` at the one seam where both ports must satisfy the same contract. | architect |

### Future

| ID | Location | Finding | Reviewer(s) |
|----|----------|---------|-------------|
| F-1 | `config.py:134-140` (with `windows.py:656-671`) | A storage root whose `location` does not begin with `project://` is accepted as any absolute path with no containment to `project_root` and no UNC refusal; `_require_ntfs` would pass a UNC root because `GetVolumeInformationW` reports the server-asserted filesystem name. Not reachable today given the committed-blob source; hardening only. Pre-existing, outside the change set. | architect, reviewer-security |
| F-2 | `windows.py:441-459` | `_windows_name` does not reject NTFS reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) or components longer than 255 UTF-16 units. | reviewer-backend |
| F-3 | `windows.py:1548-1560` | `snapshot_journal` maps every `LocalIOErrorV1` from `_read_journal_handle` to `CONFLICT`; the trailing `else ABSENT` is unreachable. | reviewer-backend |
| F-4 | `windows.py:628` | No test drives the ancestor enumeration cap on the Windows retain path; the two `LIMIT_EXCEEDED` tests use the fake port at the filesystem layer. Already booked as R-7 / follow-up F-4 in the design doc; F-4 changes a path every retention runs and there is no net at the boundary it moves. | test-engineer |
| F-5 | design doc `:1075` (§9.1) | The baseline asserts the 12 pre-existing failures stay at exactly 12; a legitimately fixed pre-existing failure would report as a regression. One-directional asymmetry, not a defect. | test-engineer |

## Coverage summary (test-engineer)

- Defect 1 (admission re-open): behavioural on Windows via tests 10, 11 and both halves of 12 (4 failed pre-fix, 6 passed post-fix on both basetemp arms); Linux belt at `contract:473`.
- Defect 2 (ancestor mask): Linux constants test at `contract:436`, counter-checking that the leaf keeps each write flavour; behavioural only on a system-volume basetemp.
- Defect 3 (reparse narrowing): `contract:494` asserts sibling reparse tolerated, matched entry refused, exact-case strictness unchanged, `_directory_names` any-reparse contract not relaxed; runs on Linux.
- All six committed test files are byte-identical to the versions executed during TEST, so the measured runs are evidence about this commit.
- What the tests cannot prove: R-1 crash durability (needs a power-loss rig); the runtime half of design tests 8 and 9 (needs a real container and an HMAC-sealed aggregate); NT-only paths (the Windows file contributes 6 skips on Linux, so a Linux-only CI proves nothing about tests 10 to 13).
- Intermittents (`test_post_durable_indeterminate_recovers_after_full_recomposition`, `test_real_linux_publication_is_restart_safe_and_project_owned`): recommendation is to leave them unmarked and document them in the run ledger. The DrvFs first-read-after-write diagnosis is a hypothesis with one observation and 24 non-reproductions; an xfail on a durability test would suppress the exact signal it exists to emit.
- §9.1 baseline: sound; asserting failures and skips by family while treating the pass count as informational is the right shape.
- Performance: no avoidable hot-path cost; `_root_component` enumerates the parent per ancestor only at retention, not per publish.

## Verification figures cited by reviewers

- Six change-set test files at HEAD on Linux: 237 passed, 4 failed, 6 skipped; the 4 failures are pre-existing and environmental (`ValueError("prepared Docker stage requires a Windows drive path")`, `docker_v1/prepared.py:47`), present identically at `85b922fc`.
- `test_docker_prepared_composition.py`: 8 tests at baseline, 17 at the commit. `test_publication_local_posix.py`: 2 at baseline, 4 at the commit.
- Import hygiene: pass on all four changed source files.

## Non-findings cleared by the security reviewer

Eight hypotheses were checked and withdrawn; the one worth naming is `_directory_entries` truncation: it returns strictly more than `maximum` entries and every consumer rejects exactly that condition, so a reparse entry sorting past the cut cannot evade the whole-directory veto.

## Unexecuted NT claims needing host confirmation

- M-12 share-mode symmetry of the DELETE-axis admission.
- F-1 UNC volume-name behaviour of `GetVolumeInformationW`.
- Uniformity of reparse refusal across name-surrogate tags (LX symlink, AppExecLink, cloud-file placeholders).

## Open questions routed

- To the architect: M-7 (is the whole-listing veto in `_directory_names` a deliberate ruling that should stand against the usability cost?), M-11 (feature-string split deliberate?), M-13 (ledger amendment).
- To the user: which Minors to fix in this PR; disposition of Futures (issue or skip).

## Process notes

- `task_claim_gate` hook auto-flipped a blocked task (#41) to `in_progress` during the architect's Bash call; owner unchanged; second occurrence after #30. Recorded on #35.
- `test_publication_local_posix.py` carries 4 test functions; an earlier note citing 8/8 was wrong.

## Architect rulings (remediation cycle 1)

| Item | Ruling | Consequence |
|---|---|---|
| M-7 | NARROW. The architect overturns the #26 whole-directory strictness ruling after tracing both callers (`filesystem.py:2682` `_reject_collision`, `filesystem.py:1979` `list_borrowed_directory`); neither leans on a whole-listing reparse veto, and the substitution boundary is at open time (matched-entry veto, `FILE_FLAG_OPEN_REPARSE_POINT`, post-open identity check, mid-life re-open identity checks). | Delete the whole-listing veto at `windows.py:651-652`. `list_names_at` still refuses casefold collisions (`ROOT_CHANGED`), the entry cap (`LIMIT_EXCEEDED`) and undecodable names. Restores POSIX parity. Assigned to reviewer-backend as a #44 amendment. |
| M-11 | DEFECT, not deliberate. One vocabulary: both ports and the gate build the same capability dict through the same digest. POSIX port and the gate for both platforms already publish `directory-inode-admission`; `windows.py:108` is the outlier. | Rename `windows.py:108` to `directory-inode-admission`. Only `detect_windows_capability_v1`'s digest changes; `LocalFilesystemV1.capability()` is unaffected; no recorded Windows digest exists before release. Assigned to reviewer-backend as a #44 amendment. |
| A-1 (new, Minor) | Found by the architect while tracing M-7: `filesystem.py:2683-2684` catches bare `BaseException` and rewrites to `IO_FAILED`, flattening port codes (`LIMIT_EXCEEDED`, `ROOT_CHANGED`); the sibling at `filesystem.py:1992-1995` re-raises `LocalIOErrorV1` first. | Match the sibling pattern at `:2683`. Fix now; assigned to reviewer-backend (no other writer on `filesystem.py` this cycle). |

Line numbers are against `0273793a`; they shift under the cycle-1 edits.

## Cycle-1 follow-ups raised by fixers

| Item | Source | Finding | Disposition |
|---|---|---|---|
| A-2 (Minor) | coder-wiring, #50 HANDOFF | `docker_training.py:906-912` derives `SUBMITTED` from `container_ref` and `submitted_at` only and never reads `outcome.reconcile_required`, so the M-8 `RECONCILE_REQUIRED` outcome (and any genuine `RECONCILE_REQUIRED` record carrying a `container_ref`) still reports `SUBMITTED` at the command boundary; the M-8 fix is honest at the outcome type and invisible one layer up. | Fix now (same user goal as M-8: a smoke run must not pass while publishing nothing). Same fixer, follow-up task. |
| M-8 note | coder-wiring | Fixed as a `RECONCILE_REQUIRED` outcome with diagnostic token `PUBLICATION_COMPOSITION_ABSENT`; the durable record stays `ARTIFACTS_VERIFIED` (first outcome whose phase differs from the record's; `_require_reconcile` deliberately not used). Single meaning proven by construction-site enumeration and a structural test on `compose_docker_publication_v1`. Gap A pin re-expressed. | Architect to state the outcome/record decoupling in Stage 3. Diagnostic token set left open (one caller, one token). |
| A-2 outcome | coder-wiring, #52 HANDOFF | Fixed. `SUBMITTED` now requires `not outcome.reconcile_required` in addition to the two identity checks; both victims covered (M-8 outcome and the durable observe-process `RECONCILE_REQUIRED`). Container ref carried on both statuses; `submitted_at` only on `SUBMITTED`, because `cli.py:289-305` admits exactly that shape at `RECONCILE_REQUIRED` (the fixer corrected its own teachback on this). Result tail extracted to `_docker_command_result_v1` so the mapping is executable on Linux; the activation itself is still Linux-unreachable (drive-path check), so the wiring into the helper closes on the host run. | Verify-only re-review to look at the eight-argument helper shape; architect Stage 3 to re-cite ruling (e) and section 9.3 line numbers and add the "now enforced" sentence. |
| F-6 (Future, deferred) | coder-wiring, #52 open question | The `RECONCILE_REQUIRED` command result carries no reason: `TrainingRunCommandResultV2` has no diagnostic field, so `PUBLICATION_COMPOSITION_ABSENT` dies at the outcome boundary. | Deferred; needs a result-model change, out of bounds for this cycle. |
| Observation | coder-wiring, #52 | `test_active_dirty_worktree_outer_command_is_resolution_unavailable` fails on Linux at baseline (pre-existing, unrelated to this change set). | test-engineer to classify on the #46 host run; not fixed this cycle. |

## Cycle-1 host verification (test-engineer, #46 Part 1)

Windows suite 6/6 on both arms (`--basetemp` on F:, default C:) against the staged cycle-1 tree; the M-1 identity binding did not redden either arm. Contract file on the host: 26 passed, 2 failed, 2 skipped of 30 (30/30 on Linux). Both failures are test defects, not production defects: the M-1 test (`:920`) passes a driveless rooted path that is not absolute on Windows and dies at `ROOT_INVALID` before any M-1 logic; the M-10 test (`:1034`) asserts the off-Windows `CAPABILITY_UNAVAILABLE` counter-check where the real host returns `IO_FAILED`. Ruling: test-engineer fixes both with platform-chosen values (no skips); M-6 is treated as covered by the call-site check already inside the `:920` test.

### Discrepancy resolved: `test_docker_training.py` on Linux (coder-wiring, #54)

Both `test_activation_stages_bridge_bundle_and_persists_initial_pair` and `test_active_dirty_worktree_outer_command_is_resolution_unavailable` fail at HEAD on Linux with all cycle-1 files reverted: the first because the prepared stage requires a Windows drive path and the fixture roots the project under `/tmp`; the second asserts `RESOLUTION_UNAVAILABLE` and gets `CONFIG_UNAVAILABLE`. Neither is a cycle-1 regression. reviewer-backend's "passes at HEAD" came from a `git archive` extraction, which carries no submodule content, so the fixture's `git clone --shared` exits 128 and the test ERRORS at setup rather than failing; an errored test reads as an absent failure in a summary scan. Environment note for the whole team: a `git clone` whose destination is under `/mnt/f` fails on `chmod .git/config.lock` (DrvFs); clone destinations and pytest basetemps for cloning fixtures belong on ext4. Disposition: no skip marker; test-engineer confirms both pass on the Windows host during #46.

## Design-doc sync (architect, #48 Stage 3)

`docs/architecture/native-windows-publication-closure.md` synced to the cycle-1 code (117 insertions / 12 deletions): baseline note now names `docker_execution.py` and `docker_training.py` as modified with their shift magnitudes (citations stay pinned to `85b922fc`, the `git show` check is preserved); ruling (e), the 6.1 method table, the 6.2 defect-3 narrative, the 6.3 error taxonomy and 9.3 step 3 rewritten to the landed behaviour; M-12 and M-13 ledger rows; F-3 re-scoped to the across-restart half now that M-1 binds handles by file id; UNC clause ruled KEEP (containment does not subsume it when `project_root` is itself on a share). The design doc's residual table runs its own F-n sequence; its new deferred row is design F-5 and cross-references review F-6. Confirmed landed with no doc change: M-2, M-3, M-10, M-11. M-9 confirmed unlanded (user deferred; cycle 2).

### Cycle-1 verification, final (test-engineer, #46 revision 2)

Windows publication suite 8/8 on both arms (F: basetemp, default C:). Contract file on the host 30 passed / 2 skipped / 0 failed (32 on Linux); the two Part 1 host failures were one defect class (platform-neutral claim, platform-bound fixture or expected reason) and were repaired without skips. `test_docker_training.py` on the host, Python 3.12.7: 14 passed, including both tests that fail on Linux for environmental reasons, which localises the dirty-worktree red to the Linux config-resolution path. Linux, explicit Python 3.12, four files: 219 passed / 8 skipped / 0 failed. Tests per finding: M-4 behavioural post-open reparse re-check; M-5 three-function AST walk (the caller-only walk was not diagnostic; the substring form was a false positive on helper docstrings); F-4 twin tests per evidence class; M-12 measured (refusal at `acquire_directory_admission`, control arm); M-6 docstring note, pin covered by the M-1 test; M-9 characterization pinned and labelled for cycle 2. Five scratch mutants each kill their assertion. Note for Linux runs: `test_docker_training.py` cannot be collected under Python 3.10 (`dataclass(weakref_slot=True)`); use an explicit 3.11+ interpreter and `rtk proxy` with an absolute interpreter path.
