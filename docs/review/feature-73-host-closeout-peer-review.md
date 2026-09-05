# Peer review synthesis: feature #73 Host closeout

Branch `feat/submodule-cloud-api-v1-host`, range `636aa90f..7c4c83a4` (10 commits, 13 code files, +1127/-52), engine pin `ce539b70`. PR #596 is review only by user ruling (2026-09-02): nothing merges to main. Reviewed 2026-09-05 by four reviewers on team `session-832e1b8a`: architect-review (#362), coder-review (#364, pact-backend-coder), security-review (#365), test-review (#367, coverage; re-dispatch of #363 after its scratch tree filled the WSL disk).

## Verdict

**No Blocking finding from any reviewer.** The delta lands the B-18 fix (`5e7b6a76`), the section 27 rulings, the 27.12 items (`5d816658`) and the docs bundle correctly; it breaks nothing, regresses nothing, and adds 23 passing nodes (WSL lane: passed 177 to 200, failing node-id set identical at base and head, zero error nodes). Every reviewer re-measured its own figures.

## Findings

| Id | Severity | Site | Finding | Recommendation |
|---|---|---|---|---|
| ARCH-M1 / CODE-M4 | Minor (pre-existing) | `synaptic_host/docker_staging.py:1784` | Boolean-flag handler destroys the cause: the `except` at 1781-1782 sets a flag, the `raise` at 1784 carries no `from`, so the cause chain ruled in 27.4 is broken at a site inside a function the same arc repaired. Coverage shows the handler never executes in the suite; unpinned for cause. | Fix now in the 27.12 shape: `from` the captured exception, C7-style red-first test, one-paragraph 27.2 Correction recording the third census blind spot. |
| ARCH-M1 (second site) | Ruled: no change | `synaptic_host/artifact_destinations.py:396` | Same shape as :1784, but `test_post_callback_binding_reread_never_invokes_hostile_equality` (`tests/synaptic_host/test_artifact_destinations.py:486-488`) asserts `__cause__ is None`, `__context__ is None`, and that the hostile adapter's marker is absent from `str(exc)`. The destroyed cause is a deliberate non-leak property, not a defect. | Leave as landed. Record the reviewer conflict (architect and coder called it a destruction; test-review measured the pin) and its resolution in 27.2. |
| ARCH-M2 / CODE-M3 | Future | `synaptic_host/artifact_spool.py:498, :512`; `_within` case semantics | In-handler `_closed(IO_FAILED)` substitution on the spool streaming path (Class A under 27.2, outside the narrow-fix boundary); `_within` vs `==` case disagreement, both fail-closed, branch unreachable while both paths derive from one `project_root`. | File with #209; reconcile `_within` when a second `project_root` derivation appears, preferring the component-wise form `local_io_v1/config.py` already uses. |
| ARCH-M3 | Minor (docs) | two private edges | Two private-edge dependencies deserve one docs sentence each. | Fold into the next docs-only commit. |
| CODE-M1 / CODE-M2 | Housekeeping | `tests/synaptic_host/test_artifact_spool.py:23`, `:228` citations; `_create_private_chain` docstring | Stale `:228` citations (the chained call is `publication_store.py:236` at HEAD); unused `BorrowPurposeV1` import; one docstring sentence recording that the path in the :234/:271 messages is present for recoverability and never reaches the operator (Y1 governs). | Bundle in follow-up #355. |
| SEC-M1 | Minor (invariant unenforced, pre-existing) | `synaptic_host/artifact_destinations.py:32-41, :88-93` | The destination-config credential rule is a denylist on key names; defensible while every destination is local, but a cloud lane is exactly where a real credential first appears. | Decide allowlist keyed on `configuration_schema_version` before any cloud lane reuses this path. |
| SEC-F1 / SEC-F2 | Future | containment; check-to-create ACL | Lexical containment vs junctions; check-to-create ACL adoption under `.synaptic`. | Disposition SEC-F2 together with #170 (durable rows database keeps inherited ACEs after B-11 repair). |
| TEST-M1 | Minor (coverage) | `synaptic_host/publication_composition.py:269-273` | The raise that replaced the deleted ancestor walk (27.12 Y1) is executed by no test in all 63 test files. Behaviour did change for a declared root nested below `.synaptic`; audit #347's behaviour-preserving finding holds for documents that declare no nested creatable root (run 14's document), not for the code. True sibling of the A' gap. | One red-first test via the existing `roots=` knob on `_compose_declared` / `_write_declared_configs` (all five call sites use the default). Architect rules first whether the refusal is intended. Follow-up #369. |
| TEST-M2 | Minor (coverage) | `publication_composition.py:232-235` | Absent `.synaptic` arm uncovered, zero references. | Same knob, one test. Follow-up #369. |
| TEST-M3 | Minor (coverage) | `publication_composition.py:246-249` | `_within` `ValueError` arm uncovered; `commonpath` raises only on a drive mismatch, so the arm is Windows-only and unreachable on the WSL lane. | Record; pin only if a Windows-lane test is cheap. |
| TEST-M4 | Minor (test hygiene) | `tests/synaptic_host/test_docker_prepared_composition.py:225, :315, :351`; `test_docker_training.py` | Six permanent WSL reds are platform-bound tests carrying no gate; `_WINDOWS_LANE` exists at :413 but decorates only :419/:441/:459. | Apply the marker; bundled in #355. |
| ARCH-F1 / ARCH-F2 | Future | `synaptic_host/docker_v1/composition.py`; #326 | `docker_v1/composition.py` is dead at the executed path (judged by reachability, not file existence); #326 is less urgent than filed; no Windows-gated R2 counterpart exists. | Fold into #209 and the POSIX plan. |

## The A' gap and its class

On #349 arm A' reinstated the deleted ancestor walk and reddened nothing; the zero was predicted, so the arm measured coverage rather than correctness and the ruling was record-not-fix. Test-review's pinning map over changed-line coverage finds that the class has exactly three members, all in `publication_composition.py` (TEST-M1, M2, M3); every other added executable statement across the six sources is executed, including both arms of the B-17 helper in `docker_staging.py` (the apparently uncovered lines 1342/1348/1351/1360/1363/1367 are multi-line-statement artifacts, not gaps). The two mission-named destroyed-cause sites resolved opposite ways by measurement: :396 is pinned (see the table), :1784 is unpinned for cause.

## Conventions recorded as measured facts

1. Sparse basetemp outside every git tree is the sole Windows-lane discriminator (#349; applied but not re-measured on #367, which ran no Windows lane).
2. Same-code control on baseline divergence: base and head are compared with the same engine tree (both commits pin `ce539b70`), so a failing-set delta is attributable to the Host delta alone.
3. A zero-red mutation arm is a measurement, not a failed arm, when its zero was pre-registered (vacuity probe); a green arm at a site with no constructible faithful inverse proves nothing.

## Framing correction

`local_io_v1` is Host-owned under `synaptic_host/`; the engine seam is `synaptic_tuner.api.v1.*`. Earlier dispatch text that called it "the engine's local_io_v1" is corrected here so the wording does not propagate into the cloud-lane dispatches that reuse this path.

## Reviewer conflicts and resolutions

1. Coder-review's first census reported zero cause destruction outside the ruled seven; architect-review's MINOR-1 named :396. Lead read the site: the architect's finding stood; coder-review corrected its instrument (a display filter dropped implicit no-`from` raises) and reported two sites (:396, :1784).
2. Test-review then measured that :396 is pinned by a deliberate non-leak assertion, so the fix-now recommendation narrows to :1784. Resolved in test-review's favour by direct read of `test_artifact_destinations.py:486-488`.

## Process notes

- #363 (first coverage review) was stopped after its scratch tree reached 72 GB and filled the WSL root disk; re-dispatched as #367 with a hard scratch budget (reuse `_ct349`, stop below 40 GB free). #367 ran 7.6 GB against a 5 GB target; no stop condition fired.
- Third wake-delivery failure of the session recorded on #363 (#334, #348, #359); durable acceptance stamps on disk remain the mitigation.
- Pre-existing failing residuals: 122 WSL / 103 Windows at #349; on the seven touched files the failing set is six nodes at both base and head.

## Next steps

Step A gate (user): fix-now on :1784 plus the two coverage tests (#369) and the #355 hygiene bundle, or record and proceed. Either way PR #596 stays open and unmerged; the cloud-lane smokes (Modal, then HF Jobs, then RunPod) follow the branch, and SEC-M1's allowlist decision precedes them.
