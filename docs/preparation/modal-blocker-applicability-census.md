# Modal-lane blocker applicability census

PREPARE artifact for feature #420 (Modal smoke of the prepared path), phase #421, task #428.
Pins: Host `d0888ed6`, engine `ce539b70`. Plan: `docs/plans/modal-smoke-prepared-path-plan.md`.
Peers: external surface #429 (devops), Windows failing set #430 (test).

Every claim below carries a `file:line` read at the pins above. Where a ruling depends on a
measurement this task did not make, the item is marked PENDING with the owning task id rather
than ruled.

## 1. What "gates" means here

Scope A is the approved boundary: deploy, start, observe, verify one isolated job at
`ce539b70`, stop before publication.

| Verdict | Meaning |
|---|---|
| **GATES A** | Must be resolved before the paid submit, or the submit fails or produces unreadable evidence. |
| **GATES B ONLY** | Touches the publication half, which scope A does not execute. |
| **CLOSEOUT** | Cannot block the submit, but bears on whether the run's own record is trustworthy afterwards. |
| **NO TOUCH** | Structurally unreachable from the Modal arm. |

CLOSEOUT is a fourth bucket the dispatch did not offer. Section 4 argues why it is needed and
which items land in it. Forcing those into NO TOUCH would have hidden them.

## 2. How the list was enumerated, by instrument

Four instruments, in order. The dispatch named 23 items; the instruments reproduce that set
exactly and explain where each half came from.

| # | Instrument | Command shape | Yield |
|---|---|---|---|
| 1 | Issue ids in the plan | `grep -oE '#[0-9]{2,4}'` over the plan | 4 follow-up ids: #153, #170, #339, #391 (the rest are task/PR/feature ids) |
| 2 | Symbolic ids in the plan | `grep -oE '(SEC-[A-Z0-9]+\|B-[0-9]+(-R[0-9])?\|R[0-9]\|C[0-9])'` | SEC-F1, SEC-F2, B-15, B-18, C1-C4, R1, R4, R5, R7 |
| 3 | Open items in the task store | `jq` over every task file, `status != completed`, subject matching `^(FOLLOW-UP\|BLOCKER\|ALERT)` | exactly 15: #153 #170 #175 #184 #209 #260 #274 #277 #326 #339 #340 #355 #379 #380 #391 |
| 4 | Doc-only items | `grep -n "SEC-F"` over the architecture doc and the review ledgers | SEC-F1, SEC-F2 (no task id exists for either) |

Instrument 3 returns 15 and the dispatch names those same 15 issue ids, with no extras and no
omissions. So the numbered half of the dispatch list was enumerated from the task store, and it
is complete against that store.

The symbolic half (8 items: SEC-F1, SEC-F2, B-15 recurrence, B-18 class, R1, R7, C1, redactor
gaps) has no task ids at all. 15 + 8 = 23.

## 3. How this list could still be incomplete

Four modes, two of which already fired.

**3.1 Doc-only findings (FIRED).** SEC-F1 and SEC-F2 exist only at
`docs/architecture/prepared-path-alpine-diagnostic.md:7592` and
`docs/review/feature-73-host-closeout-peer-review.md:19`. A task-store sweep cannot see them.
Anyone rebuilding this census from instrument 3 alone would silently drop two security items,
one of which gates.

**3.2 Consultation findings never filed (FIRED, and it costs two labels).** The security
consultation's finding set is R1 through R7. The plan carries R1, R4, R5 and R7 by label. A
label grep over the plan for `R2`, `R3`, `R6` returns nothing. R2 and R3 survive
*substantively* in the plan's prose but unlabelled:

- **R2** (no egress denial) is the plan's line 22 paragraph on the container being its own
  source materializer, `runtime.py:124-183`, zero `block_network`.
- **R3** (the two lanes disagree by name on the token) is the plan's credential-port bullet,
  `docker_staging.py:60-62` forbids the name that `modal_provider.py:168` requires.
- **R6** is an INFO item recording that image-pull integrity is already covered by the
  digest-pinned refusal at `deployment_v1.py:47-48`.

The risk is real and asymmetric: a census keyed on plan labels would drop a HIGH finding (R2)
because its label did not survive into the document. They are ruled in section 5 under their
security-consultation labels.

**3.3 Items closed in the store with residue (NOT CHECKED).** A completed task can leave a
condition that still holds. This census does not sweep the ~180 completed tasks. Naming it as
an unchecked mode rather than asserting the sweep is clean.

**3.4 Findings nobody has made yet.** The Modal arm has never executed. Seventeen of the
eighteen local blockers were found by running, not by reading. This census is a reading, so its
true error bar is "what a first run discovers", and that is the smoke's purpose.

**3.5 The PENDING convention was declared and not exercised, deliberately.**

Section 1 reserves PENDING for an item whose ruling depends on a measurement this task did not
make. No item in section 5 uses it, and that is a finding rather than an oversight: every one of
the 28 rulings turned on code read at the pins, not on an account property.

The peer-owned unknowns are real, but none of them is a *census ruling*. They are Modal-side
facts (volume and secret existence, retention, whether an artifact survives a failed run, SDK
installability), and they live in the companion document at section 1.4, where each is marked
STRUCTURAL and drained to #429. The Windows failing-set baseline is drained to #430 and is named
in the #274 row as the reason that pin is load-bearing.

If a later reader finds a section 5 ruling that in fact rests on an account property, that ruling
is wrong and should become PENDING with the owning task id and the exact question. The two
candidates most worth re-testing under that light are R6 (image-pull integrity, ruled NO TOUCH
from `deployment_v1.py:47-48`, which proves the *refusal* exists but not that the registry
reference resolves from the account) and the isolation half of SEC-F2 (ruled on the Host-side
mkdir, which is Host code, but whose blast radius depends on what the submit container mounts).

## 4. Why a fourth bucket

Three items cannot be honestly placed in the dispatch's trichotomy.

`#339` (publication receipt carrying a 2013 `recorded_at` on a 2026 record) is filed
"before Modal" by its own subject, yet scope A never publishes, so it cannot gate the submit.
Calling it NO TOUCH would be false: the same clock feeds the Modal lane's own durable rows.
`#274` (intermittent publication-suite flake) cannot block a submit either, but it pollutes the
failing-set baseline that #430 is pinning, so a Modal-lane red could be attributed to it or hidden
by it. `#340` (non-fatal tracking-registration warning from inside the trainer) will recur inside
the Modal container and will appear in the run's log evidence.

Each of these affects the *readability of the run record* rather than the run. That is CLOSEOUT.

## 5. The census

### 5.1 GATES A

| Item | Ruling and evidence |
|---|---|
| **B-15 recurrence** | GATES A. `cli.py:1001` `_establish_engine_import_root` and `:1002` the docker import both sit inside the docker branch, which returns at `:1011`. The modal arm imports `synaptic_host.modal_training` at `:1072` with no establishment call anywhere in `:1012-1072`, and `modal_training.py:35` imports top-level `tuner` at module scope. With `PYTHONPATH` never exported (rule 21.2), the first attempt dies at the import, exactly as run 9 did on the docker arm. Free to find, cheap to fix, and it fires before anything is billed. |
| **B-18 class** | GATES A. `modal_training.py` holds 10 `except BaseException` and 0 `from None`; `modal_provider.py` holds 7 and 8. The worst wraps roughly ninety lines of `execute_modal_training_run_v2` (`:477-566`) and returns an opaque `COMPOSITION_UNAVAILABLE` with the exception unbound, unchained and unlogged. This does not stop a run; it destroys the diagnosis of a run that costs money. On a lane with no cause-line renderer and no diagnosis guide, that is the largest schedule risk in the plan. |
| **SEC-F2** | GATES A, Host side. `modal_provider.py:403-404` creates `.synaptic/state/modal/` with a bare `path.parent.mkdir(parents=True, exist_ok=True)` at three call sites (durable writes at `:542`, `:840-841`, `:993`), with none of the B-11 private-chain construction, none of the B-11-R1 leaf-first repair, and no validation. The `.synaptic` tree is where the lane's evidence key lives (`security.py:669`). The security consultation's not-gating verdict is about the container-side volumes, a different object; both readings are correct about their own object. |
| **#170** | GATES A, riding with SEC-F2. The disposition is recorded at `docs/review/feature-73-host-closeout-peer-review.md:19`: "Disposition SEC-F2 together with #170". Same subtree, same fix surface. It must be named explicitly in the pre-submit item or it drops out silently when SEC-F2 is ruled. |
| **R7 (environment copy)** | GATES A. `launcher.py:365-366` `_uv_environment` opens with `environment = dict(os.environ)`, copying the whole operator environment into the uv subprocesses. The submit host now holds the Modal token pair by user decision, so this is the one code path that hands credentials to a third-party process tree. See the companion document section 3 for why this is one finding and the cache-hit item is another. |
| **R4 (redactor gaps)** | GATES A as a pre-submit fix. `redaction.py:7-12` and `:21-24` miss this lane's two credential shapes. The post-run sweep is the compensating control, not a substitute, because the sweep runs after the money is spent. |
| **R1 (evidence key in the container)** | GATES A as a *user decision*, not a code fix. The key set is mandatory and hardcoded at `modal_provider.py:168` and refused without at `:845`; the container must authenticate its own evidence. Already lifted to Require User Decision in the plan. |
| **R2 (no egress denial)** | GATES A as a *ruling restatement*, already decided. `runtime.py:124-183` makes the container its own source materializer; zero `block_network` anywhere; `restrict_modal_access=True` governs Modal-resource access, not egress. The standing network-disabled wording cannot transfer, and the user restated it on 2026-09-05. Recorded here because its label did not survive into the plan. |
| **C1** | GATES A. `cli.py:874-884` reads the committed blob only on the docker arm; the modal arm falls through to a plain worktree read. Executing a cloud job from the worktree would violate the released-checkout ruling. |

### 5.2 GATES B ONLY

| Item | Ruling and evidence |
|---|---|
| **#391** | GATES B only. Under scope A the destination is the fixed sentinel: `cli.py:23` `_DESTINATION = "provider-staging"`, required for modal and forbidden for docker at `:87-97` and `:847-857`, refused again at `docker_training.py:693`. The value is a literal, not ungoverned text, and it never reaches `parse_artifact_destination_config_v1`. Under scope B a real destination config appears and the ungoverned `_text` values become live. |
| **C2, C3** | GATES B only. Both are publication contracts by construction; the plan marks them not needed for scope A. |
| **#380** | GATES B only. One dated sentence at the end of section 27.3, publication docs. |
| **SEC-F1** | GATES B only *as a new gate*. It gated run 14 exactly as it gates any publication, and scope A does not publish. It re-enters with C3. |

### 5.3 CLOSEOUT

| Item | Ruling and evidence |
|---|---|
| **#339** | CLOSEOUT. Receipt `recorded_at` of `2013-11-22T15:29:11Z` on a 2026 record. Cannot gate a run that stops before publication. But the Modal arm writes its own durable rows with its own clock, so the same defect class would corrupt the run record's ordering. Read the Modal lane's timestamps against an external clock at closeout. |
| **#274** | CLOSEOUT, and a dependency on #430. The flake is in `test_publication_local_posix.py::test_r6_...` at roughly 1 in 15. It cannot gate the submit, but an unpinned flaky baseline is exactly how a real Modal red gets dismissed. #430 pins the failing set by node id; this item is why that pin matters. |
| **#340** | CLOSEOUT. The tracking-registration warning is non-fatal and originates inside the trainer, which also runs in the Modal container, so it will appear in the run's log evidence and must not be read as a Modal-lane defect. |

### 5.4 NO TOUCH

| Item | Ruling and evidence |
|---|---|
| **#153 (B-10-R1)** | NO TOUCH — and this **corrects my own #410 addendum**, which argued #153 must be sequenced before any submit. It must not. `ModalRuntimeLockV1` (`config.py:175`) has a closed key set of exactly `{schema_version, sdk_version, registry_reference, python, locked_files, ml_stack}` and pins **no environment at all**; an environment key would be rejected by `_closed`. The 13-key pin does exist on the Modal path, but by a different route: `resolution.py:563-575` builds a `fixed_environment` identical to `execution_source.py:489-500`, and `:576-578` intersects it against the deployment's declared environment, raising only on a *disagreeing* overlap. Measured at this pin: `training/providers/modal.json` declares `runtime_environment` keys `{LANG, PATH}`; the intersection with the 13 fixed keys is **empty**, so no conflict is possible at the checked-in config. B-10-R1 was a Host-side conflict about moving caches off a DrvFs-bound path; the Modal roots are container-absolute at `/workspace/run/<run_id>/cache` and the Host never tries to move them. **Trap worth recording:** if anyone adds `HF_HOME`, `PYTHONPATH` or any of the other 11 to that config, `resolution.py:577` raises `SourceLockError` and the run refuses. |
| **#175 (B-11-R1)** | NO TOUCH as a wedge. The wedge is a failure *of the chain repair*, and the Modal arm never invokes the repair: `modal_provider.py:403-404` is a bare mkdir. A path that never repairs cannot wedge. The absence of the repair is the finding, and it is ruled above as SEC-F2. |
| **#184** | NO TOUCH. The seam is in the derived staging scope. The Modal arm does not stage; it uses `GitDualCloneMaterializer` (`modal_provider.py:759`) and the container clones its own source. |
| **#326** | NO TOUCH. The overloaded code is in `local_io_v1/windows.py:925` and `:988`. A grep for `local_io` across `modal_provider.py`, `modal_training.py` and `modal_resolver.py` returns nothing, so the Modal arm never reaches the module. Compounding this, the submit host is now a Linux container by user decision, so the Windows arm is not the executing arm either. |
| **#277** | NO TOUCH. Three docs and comment corrections scoped to the docker lane's own documentation. |
| **#260, #379** | NO TOUCH. Both are the docker-lane operator recipe and its WSL test. #379's dirty-worktree assertion is a docker-lane test. |
| **#355** | NO TOUCH. One unused import in a publication test. |
| **#209** | NO TOUCH. A process item (plan-mode simplification review), not a code condition. |
| **R5** | NO TOUCH for scope A. Operator credential files at mode 644 is host hygiene on the operator's own machine; it neither blocks nor corrupts the run. Worth fixing, not here. |
| **R6** | NO TOUCH. INFO only, recording that image-pull integrity is already covered at `deployment_v1.py:47-48`. |
| **R3** | NO TOUCH, deliberately. The two lanes disagree by name on the token: `docker_staging.py:60-62` forbids it, `modal_provider.py:168` requires it. Both are correct for their own lane. Recorded so neither is "fixed" to match the other. |
| **C4** | NO TOUCH. Provider capability descriptor, deferred by the plan. |

## 6. Count

| Verdict | Count |
|---|---|
| GATES A | 9 |
| GATES B ONLY | 4 (counting C2 and C3 as one row each) |
| CLOSEOUT | 3 |
| NO TOUCH | 12 |

Counted from the tables above, not from the dispatch list. The totals exceed 23 because R2, R3
and R6 were recovered by section 3.2 and C2/C3 are listed separately.

## 7. What the architect inherits from this census

1. Six items gate the submit as code or ruling: B-15, the B-18 block, SEC-F2 with #170, R7, R4, C1.
2. Two gate as user decisions already taken: R1 and R2.
3. #153 does **not** gate, contrary to an earlier reading of mine, and the reason is measurable:
   the overlap set is empty at the checked-in config.
4. The CLOSEOUT bucket exists and needs a home in section 29.
