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

## Verify-only re-review of cycle 1 (`b1449da2`)

Three reviewers, each verifying the items they raised, read-only against `b1449da2`.

| Reviewer | Task | Verdict | Detail |
|---|---|---|---|
| reviewer-security | #56 | 7 of 8 resolved; push GO | B-1, M-1 (encoding checked, not shape: both sides decode the `FILE_ID_128` identically so the compare is not vacuous), M-2, M-7 boundary (three compensating legs verified at their lines; nothing follows a junction; the inode compare is sound only together with the reparse refusal, neither may be relaxed alone), F-3, A-1, and the F1/F2 test repairs (added on revision 1; both proven kill-capable by in-memory mutation). Unresolved: F-1 sub-criterion (c), below. No new issues. |
| architect | #58 | 7 of 8 resolved | M-7, M-11 (the port rename reaches exactly one digest: the gate hashes its own literal tuple at `filesystem.py:572-599`), M-12/M-13, A-1, M-8 (phase set on the outcome only; no repository write between load and return), A-2 (mapping matches the `cli.py` shape rule), F-1 as ruled, M-15 informational. Unresolved: two errors in its own Stage-3 text (D-1, D-2 below). |
| reviewer-backend | #60 | ALL_RESOLVED 14/14 | M-8 four sub-points, A-2 four, F1/F2 repairs (labelled NOT INDEPENDENT: repairs to tests reviewer-backend wrote in #44; independent read taken by reviewer-security), M-5 walk, F-4 twins, M-12 measured assertion, M-9 label, two host tests by inspection. Diagnosticity argued read-only per item (exactly one of the three A-2 tests is diagnostic; the other two are declared regression pins). Four new minors N-1..N-4. |

### Findings from the re-review

| Id | Severity | Finding | Disposition |
|---|---|---|---|
| F-1(c) | Future | The two-separator refusal lives only in the non-project arm (`config.py:136-147`); `from_bytes` requires only `project_root.is_absolute()` (`:94-99`), which a UNC path satisfies, and the `project://` arm joins onto `project_root` unchecked (`:131-133`). A share-rooted `project_root` plus `project://training/spool` yields a UNC spool root that `_require_ntfs` accepts because the server reports NTFS. Pre-existing, operator-reachable only. Lead confirmed against file state. | Fixed in cycle 2 (coder-port #64). |
| D-1 | Minor | The citation-baseline note stated shift magnitudes measured against the wrong base (`from_publication` shifts zero from `85b922fc`, not fifty-four; the shift grows at each insertion point so one number per file cannot be right). | Fixed in cycle 2 (architect #62): magnitudes dropped, `git show` instruction kept. |
| D-2 | Minor | Ruling (e) said "eight keyword arguments"; the helper is one positional plus seven keyword-only. | Fixed in cycle 2: "eight parameters (one positional, seven keyword-only)". |
| N-1 | Minor | `test_docker_execution.py:745` comment claimed nested-function returns are ignored; the filter excludes bare returns (asserted empty separately), so a nested helper with a valued return reddens the single-return pin. | User: fold. Fixed in cycle 2 (test-engineer #66), comment rewritten to state the filter and the no-nested-functions precondition; walk not narrowed by ruling. |
| N-2 | Minor | The M-5 hardcoded-"." walk omitted `windows._nt_open_relative`, the function that issues `NtCreateFile`. | User: fold. Fixed in cycle 2: fourth walk entry; counter-check loop untouched. |
| N-3 | Minor | `test_windows_port_contract.py:1524` asserts `len(loose) > 10` where the measured value is 500. | User: defer. |
| N-4 | Minor | `_docker_command_result_v1` lacks a return annotation (same shape as M-15). | User: defer. |
| S-1 | Note | The F2 BaseException half is pinned by `inspect.getsource` substring assertions (`:1131-1133`), the form the M-5 test migrated away from; a behavioural form (patch `_close_handle` to raise `KeyboardInterrupt`, assert propagation) is stronger and equally cheap. | Deferred ledger. |
| Residual | Note | Whether `NtCreateFile` can return `STATUS_NO_SUCH_FILE` for a missing name opened relative to a directory handle; on local NTFS the expected status is in the set, so a legitimate absence would raise `IO_FAILED` (broken flow, not a hole) only if it can. | Settle on the next host run. |

## Remediation cycle 2 (`a064896f`)

Five files, +102/−29, staged by path (the tree carried two authors' hunks in `test_windows_port_contract.py`). Verification before commit: Linux 250 passed / 11 skipped / 0 failed across `local_io_v1` and both publication suites; host contract file 30 passed / 2 skipped / 0 failed (cycle-1 baseline).

- **F-1(c)** (coder-port, #64). `_opens_on_two_separators(value: str)` extracted as the single spelling of the rule; applied to `str(project_root)` in `from_bytes` beside the `is_absolute` check (location (a): names the property once, before the arms split, which is the only place that fixes both arms), and the non-project arm now calls the helper. Round-trip measured before writing: `str(PosixPath('//server/share/proj'))` keeps both separators and is absolute; the Windows flavour renders `\\server\share\proj`, also absolute. New test `test_unc_project_root_is_refused_before_either_arm_can_join_onto_it` with a `tmp_path` positive control (a literal `/proj` is not absolute on Windows and would pass for the wrong reason). The refactor broke the source-inspection detector that grepped the inline literal (blocker #67, ruling (a)); repaired in place to pin the helper at both call sites and to route its corpus counter-check through the real predicate (it had re-implemented the predicate inline and would have passed even if the helper were wrong). Three sabotage checks: anchor guard deleted → new test `DID NOT RAISE` with premises still passing; same deletion → detector `0 == 1`; helper forced `False` → counter-check fails on `\\server\share`. Two pre-existing unused imports at `test_config.py:9` left (residue rule). Accepted cost, ruled at #68: a POSIX `project_root` of `//anchor` is now refused, consistent with cycle 1 already refusing double-separator location strings on POSIX.
- **N-1, N-2** (test-engineer, #66). N-1 comment-only (+7/−1), the claim verified on a synthetic factory (one nested valued return → 2 valued / 0 bare). N-2 demonstrated on an in-memory copy: an empty-name revert inside `_nt_open_relative` survives the three-function walk and is caught by the four-function walk; the opposite-polarity counter-check loop stays a two-entry tuple because `_nt_open_relative` carries no quoted dot.
- **D-1, D-2** (architect, #62). Lead-inspected diff, 1 file +10/−11. A guard-rail sentence records why no figure belongs in the baseline note; the D-2 paragraph was re-flowed to the file's wrap.

### Cycle-2 verify-only

| Reviewer | Task | Verdict |
|---|---|---|
| reviewer-backend | #71 | ALL_RESOLVED 2/2. N-1 comment and code agree, assertions unchanged; the closing clause ("narrow the walk rather than raise the count") turns an unenforced precondition into a documented response. N-2 tuple entry present once; firing demonstrated on a scratchpad copy of `windows.py` (three-function walk False, four-function walk True). No collision with the F-1(c) detector hunk. |
| reviewer-security | #69 | F-1(c) RESOLVED on all five checks; push GO. Guard at `config.py:116` in the top validation block above `json.loads`, so it runs before the roots loop exists; one spelling (predicate body at `:55`); round-trip measured on both pathlib flavours, so the refusal is attributable to the two-separator guard and not to `is_absolute`; three in-memory mutations of `config.py` kill the new test in both the under- and over-refusal directions; detector pins the helper at both sites and the ordering above `Path(location)`; no single-separator POSIX root or drive-letter root newly refused. Notes: POSIX `//anchor` refused (accepted cost); Windows extended-length `\\?\C:\proj` refused as an anchor but unreachable because `ntpath.realpath` strips the prefix (read from CPython 3.12 source, to be confirmed on the host). New Minor S-2, test-only: the anchor assertion orders the guard against `Path(location)` but not against the project-arm `joinpath`, so relocating the guard below the project join would still pass; the shipped placement is correct. S-3: the helper docstring's "none of them is a local volume path" over-generalises for the extended-length form. |

Process note (reviewer-backend, #71): a `task_claim_gate` PreToolUse notice announcing an auto-claim of #69 rendered into reviewer-backend's transcript; #69's owner on disk was and remains reviewer-security. A teammate trusting that notice would start work in another lane.

## Deferred ledger at end of cycle 2

M-9 (characterization flip, cycle 3), M-14, S-2 (anchor-vs-`joinpath` ordering assertion), S-3 (helper docstring sentence), the `ntpath.realpath` extended-length-prefix host check, F-5 (user skipped), F-6 (command-result reason field, model change), N-3, N-4, S-1, the `STATUS_NO_SUCH_FILE` host probe, reviewer-backend q5 (move two storage-config tests into `test_config.py`), two unused imports at `test_config.py:9` (Y-1 class), and the architect's suggestion to write the `config.py` structural-pin sweep into the design doc so a future refactor enumerates the source-inspection tests before moving a literal.

## Deferred ledger additions from the B-9 ruling (architect-run, #130, 2026-09-02)

Ruling of record: `docs/architecture/prepared-path-alpine-diagnostic.md` section
18. Citations below are read at Host `7546169e` / engine `4a01fc55`.

| Id | Severity | Finding | Disposition |
|---|---|---|---|
| B-9-R1 | Future (engine) | The prepared path gives the container no writable `HOME`. Under the ruled `--user`, the id has no `passwd` entry in the image, so the runtime sets `HOME=/`, which that id cannot write. It cannot be fixed on the Host: the engine's `allowed_environment` (`tuner/training/methods/sft.py:52-63`) admits neither `HOME` nor `TMPDIR`, and the subset check at `Trainers/sft/runtime_v1.py:1145-1157` rejects a planned environment that exceeds it. Most of the risk is already retired, because every writable root plus `HF_HOME` and `TRANSFORMERS_CACHE` is redirected under `/artifacts` (`docker_training.py:444-462`, `:474`). | Deferred. P8 reports `home-writable` / `home-not-writable` as a WARNING, never a failure. Settle from run 5's trainer output. If it bites, it is an engine allowlist change plus a Host environment addition plus a closure regeneration of the B-5 shape — a rePACT, not a Host edit. |
| B-9-R2 | Note (pre-existing) | `_verify_artifact_topology` (`docker_staging.py:1446-1481`) requires `artifacts`, `state`, `tmp` and `tracking` to be empty, and runs on the reuse path as well as on fresh staging (`:1791`). A completed run writes into those directories and a replay recomputes the same `stage_key`, so re-staging after a successful run would raise "artifact writable directory is not empty". | Deferred. Not introduced by B-9 and not fixed by it, but it sits directly on run 5's replay path and on the section 10.2 stage-reuse contract, which is still unproven. Classify on run 5. |
| B-9-R3 | Note | Nothing reads `Config.User` back from `docker inspect`, so the effective user the daemon applied is never compared against the one requested. Same shape, same fix and same cost as the entrypoint residual in section 17.11: an addition to `DockerCreateSpecificationV1`, the inspect projection and `verification.py`, which is a durable-record schema change. | Deferred, named rather than silently carried. Interim evidence is P8's echoed `id` line plus the trainer producing output. |
| B-9-R4 | Note | That runs 1-3 mounted the project drive without `metadata` is an inference from timestamps and cannot now be tested; the earlier mount is gone. | Recorded because it explains the run-4 timing. Load-bearing for nothing: section 18 is justified from the current mount options and the composition source only. |

## Ledger amendments from the B-9-R1 addendum (architect-run, #136, 2026-09-02)

Ruling of record: `docs/architecture/prepared-path-alpine-diagnostic.md`
sections 18.18-18.24, written after probe #131. Citations read at engine
`4a01fc55`.

| Id | Severity | Finding | Disposition |
|---|---|---|---|
| B-9-R1 | Future (engine) — **supersedes the #130 entry** | Probe #131 confirmed `HOME=/` and unwritable for uid 1000 on the real image, and that the container starts normally there. Verified at `4a01fc55`: the trainer allowlist is declared in TWO closure members and both must be widened together, the Python list at `tuner/training/methods/sft.py:52-63` and the closed enum at `schemas/synaptic-sft-workload-v1.schema.json` (`properties/runtime_requirements/properties/allowed_environment`), 27 identical entries in each. Neither admits `HOME`, `XDG_CACHE_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR` or `TMPDIR`, while both admit all 14 keys the Host passes today (`docker_training.py:450-464`) — so there is no contradiction with the shipped `HF_HOME`, and no Host-only fix. Widening only the Python list leaves the schema rejecting the four new keys. Both are closure members, so the shape is an engine edit to both copies plus closure regeneration plus a pin move. (Amended 2026-09-02: the #136 citation named only the Python copy; coder-engine-r1 found the second at #147 and widened both, engine `ba844137`.) Caches must go under `/tmp`, not `/artifacts` (see B-10). Proposed keys: `HOME=/tmp/home`, `XDG_CACHE_HOME=/tmp/xdg`, `TORCH_HOME=/tmp/torch`, `TRITON_CACHE_DIR=/tmp/triton`; `TMPDIR` deliberately excluded because `tempfile.gettempdir()` already returns the writable `/tmp`. Precedent: `tuner/cloud/hf_training_image_lock.py:658-666`. | Deferred, and **run 5 goes ahead**. R1 is still unproven as active: probe #131 measured where the caches would go, not whether anything writes to them. Run 5 is a strictly stronger instrument than the proposed probe-4 (`import unsloth` as uid 1000), which would not settle it because triton compiles at first kernel launch, not at import. Settle from run 5's output. |
| B-10 | **Blocker candidate, pre-existing** — supersedes B-9-R2 | Staging re-verifies on **every cut**, not once per run. `execute_docker_training_admission_v1` (`docker_training.py:535-680`) calls `_activate_docker_training_v1` at `:667` with no phase guard, and staging is that function's first substantive statement (`:790`). `stage_docker_worker_v1` runs `_verify_artifact_topology` at `docker_staging.py:1791` on every call; the `if not final_stage.exists()` guard at `:1775` governs only promotion. That verifier requires `artifacts`/`state`/`tmp`/`tracking` to be empty (`:1475-1478`) and `/artifacts/cache` to equal the model inventory exactly, files and directories, recursively (`:1414`, `:1418`). So the first cut issued after the trainer writes anything under `/artifacts` fails, mapped to `START_UNAVAILABLE` at `docker_training.py:673-674`. This also forecloses `/artifacts` as a cache location and puts the shipped `HF_HOME=/artifacts/cache/huggingface` (`:461`) on the same collision course. | Needs its own ruling; the fix is a change to the staging contract, not a line, and it is unrelated to B-9. **Route before run 5**: if it holds, the observe/verify/publish cuts cannot succeed and run 5 cannot produce the evidence B-9-R1 depends on. Honest limit: the code path is proven by reading; no run has yet written to those directories, so the cut at which it first bites is an inference. |

## B-10 ruled (architect-run, #140, 2026-09-02)

Ruling of record: `docs/architecture/prepared-path-alpine-diagnostic.md`
section 19. Host citations at `32b9e93b` plus `82e6fbd0`/`a498e401`; engine at
`4a01fc55`.

| Id | Severity | Finding | Disposition |
|---|---|---|---|
| B-10 | Blocker — RULED | Staging re-verifies the artifact topology on every cut (`docker_training.py:667`, `:790`; `docker_staging.py:1791`; the `:1775` guard governs only promotion), and `_verify_artifact_topology` requires `artifacts`/`state`/`tmp`/`tracking` EMPTY (`:1475-1478`). The first cut after the trainer writes under `/artifacts` therefore fails `START_UNAVAILABLE` (`docker_training.py:673-674`). Pre-existing; B-9 neither caused nor fixes it. | Candidate (c) with candidate (a)'s predicate. `_verify_artifact_topology` and `stage_docker_worker_v1` each take a REQUIRED keyword-only `expect_unused_artifacts` (no default, per 18.3's rule); only the emptiness loop becomes conditional and every identity check stays unconditional. The caller computes it from the durable phase: no row, or `prior.phase in {CREATE_ADMITTED, CREATE_ATTEMPTED, CREATED}` — the same set `docker_training.py:922-925` already uses to pick `.submit()`, because `docker create` does not run the process. Requires moving `run` and `repository` above the stage call; the late `current` read stays. Candidate (b) closed: no Host-side expected value exists for the writable roots post-run, the read-only tree is already covered by `_verify_reuse` and `_verify_inventory_at`, and it would need a new durable column. Skipping staging closed by the replay-equality check at `:917-918`. |
| B-10-R1 | **Superseded 2026-09-02 by B-10-R1 (engine) below** — was Blocker, coder-user lane | `HF_HOME=/artifacts/cache/huggingface` and `TRANSFORMERS_CACHE=/artifacts/cache/transformers` (`docker_training.py:461-462`) write into a READ root: the engine resolves the locked model snapshot at `cache_root/model/<repo>/snapshots/<rev>` (`tuner/runtime/dispatch.py:189-211`, `Trainers/sft/runtime_v1.py:634-660`), and `_verify_inventory_at` demands exact equality there on every cut — a check section 19 rules must never be relaxed. | Both move to `/tmp/hf` and `/tmp/transformers`, in the same single env-dict edit that carries the four B-9-R1 keys. SCOPE NOTE for coder-engine-r1: these two keys are ALREADY in `allowed_environment` (both copies, Python list and schema enum, verified by architect-run 2026-09-02), so changing their values needs no allowlist edit and no closure regeneration. Only the four new keys do. |
| B-10-R1 (engine) | Future (engine), user-deferred | `HF_HOME` and `TRANSFORMERS_CACHE` cannot move off `/artifacts/cache` from the Host: `SourceLockV1.__post_init__` (`tuner/project/execution_source.py:489-502`) pins both to the cache root in `required_environment` and refuses any other value at admission (`RESOLUTION_UNAVAILABLE`); measured 3 regressions with the move, 0 without (coder-user #149). Same pair at `tuner/runtime/verification.py:635-636` and `Trainers/sft/runtime_v1.py:1207-1208`; `execution_source.py` is a closure member, so the fix is the B-5 shape (engine edit, closure regeneration, pin move). The 19.10 collision therefore stays open on the shipped path: a HuggingFace write under `cache` fails `_verify_inventory_at` with `"extra directories"` at the next cut. | Deferred by user ruling (META-BLOCK #154, option A): release engine `ba844137` + Host `ab929102` and let run 5 measure it. The engine runs offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) from the local snapshot, so whether anything writes there in a `max_steps=1` run is a measurement. Cut-2 reading: cache inventory-exact means unproven-as-active; `"extra directories"` means active and an engine rePACT with evidence. Task #153. |
| B-10-N1 | Note | The author's intent is pinned by the tests: `test_docker_training.py:691-692` and `:703-704` assert `_verify_artifact_topology` fires on BOTH the fresh and the replay path. Re-verification on reuse was deliberate, not an oversight. | Preserved. Under this ruling the verifier is still called on every cut and both assertions pass unchanged. If either has to change, the implementation has drifted from the ruling. |

## B-18 closed by run 14 (architect-run, #343, 2026-09-05)

Ruling of record: `docs/architecture/prepared-path-alpine-diagnostic.md` section
27, closed at 27.12. Host citations read at `19c11400`; engine pin `ce539b70`,
unmoved by this release.

| Id | Severity | Finding | Disposition |
|---|---|---|---|
| B-18 | Blocker — **CLOSED by run 14** | `compose_host_publication_v1` caught `BaseException` over `publication_composition.py:446-511` and re-raised `_failed(...) from None` at `:517`, so run 13's cut 6 reported `START_UNAVAILABLE` at the swallowing site and the real defect went unnamed. Measurement #320 recovered it by walking `__context__`: `LocalIOErrorV1 LOCAL_IO_ROOT_CHANGED` at `local_io_v1/windows.py:925` `_root_component`, because the three `read_create` roots declared in `control/storage.json` are created by nothing. Two defects in one — a missing creator, and a chain that destroyed the evidence of it. | Fixed at `5e7b6a76` (with D3/D4 at `a18c24de`): `_ensure_declared_private_roots` creates the declared creatable roots under `.synaptic` before any permit is issued, with no repair and no validation, and the six in-scope sites bind the original and raise from it. Audit #332 GREEN with four YELLOWs, all four dispositioned in section 27 post-run-14. Counter-test #334 GREEN on both lanes. Run 14 seven rows for seven. No engine change, no closure regeneration, no pin move, no `storage.json` change. |
| B-10 | Blocker — **CLOSED by run 14** | The 19.14 acceptance row watched cut 2, and `state` was empty there on runs 12, 13 and 14 — three consecutive DEFERRALs, which the row correctly refused to read as passes. Cuts 4, 5 and 6 of run 14 each show `state` non-empty and each returned `SUBMITTED`, which is row 1 of the 19.14 table. | The row is re-pointed to the first cut with a non-empty `state` (19.14 correction, 2026-09-05). The section 19 `expect_unused_artifacts` guard is unchanged and is what lets those cuts pass; the row was reading the wrong cut, not the wrong predicate. No code change. Task #137. |

**Run 14 acceptance rows** (section 27.8, as corrected).

| Row | Verdict |
|---|---|
| 0 — cut 6 completes, publication phase `verified` | PASS (ruled; `published` is not a member of `PublicationPhaseV1`) |
| 1 — first publication trace carries no path under `cache/` | PASS |
| 2 — three declared roots exist with the 27.3 ACL shape | PASS (`F:`-only reading) |
| 3 — cause line on a failing cut | PASS BY ABSENCE (green run; the two-frame limb is carried by #334) |
| 4 — container census eight, all preserved | PASS |
| 5 — submodule pin `ce539b70` at both ends | PASS |
| 6 — B-17 staging, three staged files, training reaches one step | PASS |

**Follow-ups opened by this closure.**

- **#339** — the publication receipt records `recorded_at =
  '2013-11-22T15:29:11Z'` while the history events for the same publication are
  timestamped 2026-09-05. It affected no acceptance row and is not explicable as
  a timezone or formatting artifact. Read-only investigation, before Modal.
- **#340** — the trainer emits "Unified tracking registration failed
  (non-fatal): owned module `shared.experiment_tracking.adapters` is outside the
  offline SFT closure". Training completed regardless. Engine closure debt,
  parked beside #153.

**Standing convention — Windows counter-test basetemp** (ruled on #334, open
question 2). A Windows counter-test uses a **sparse basetemp outside every git
tree**. The rule exists because #334's unmutated Windows reds turned out to be
host state rather than code: `%TEMP%` held 4430 entries against
`MAX_DIRECTORY_ENTRIES` 4096 (`filesystem.py:70`), so `windows.py:694` raised
`LOCAL_IO_LIMIT_EXCEEDED` on ancestors that had nothing to do with the change
under test. It was legible at all only because the B-18 fix had restored the
cause chain, which is the clearest evidence yet of what that chain is worth.
Pruning `%TEMP%` is a user housekeeping item and is never done by an agent.

**Also recorded.** The thirteen symmetric `docker_training` ERROR nodes stay
parked as a pre-existing residual on #77; they are not part of this change set.
The code items section 27.12 handed to a coder **landed at `5d816658`**: the
`_create_private_chain` ancestor-walk deletion with its named absent-parent
report, the `publication_store.py:228` chain and its `C6` test, three docstring
corrections, and a seventh item this sentence originally omitted — the
corrupt-record test's cause arm, ruled in scope at the #344 teachback because
that test pinned the very cause destruction the chaining removes. Audit #347
returned GREEN on the delta with one docs YELLOW: section 27.12's owed-items
table enumerated six items against the seven that landed, corrected there by a
seventh row and a dated Correction at `6f1dd832`. As of 2026-09-05 the gates
remaining before the push are counter-test #349 on both lanes and the auditor's
narrow re-check of the two docs commits.
