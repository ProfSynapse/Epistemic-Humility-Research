# Modal smoke: the Windows pre-existing failing set, pinned by node id

Task #430 (PREPARE, feature #420 / phase #421).  Read-only measurement.
Recorded 2026-09-05.

Tree identity for every number below, re-read at measurement time, not quoted:

| Item | Value |
|---|---|
| Worktree | `_worktrees/ehr-submodule-cloud-api-v1-host-clean` |
| Host HEAD | `d0888ed6` |
| Engine submodule pin | `ce539b70` |
| Suite | `tests/synaptic_host` |
| Collected nodes, all lanes | 2200 |

## 1. The headline

**The Windows pre-existing failing set at `d0888ed6` is 102 nodes, and the
102-vs-103 discrepancy is fully reconciled.**  It is one node, and its cause is
the `--basetemp` volume, not the platform, the interpreter or the tree.

`tests/synaptic_host/test_security.py::test_windows_repairs_a_whole_chain_the_operator_created_first`
asserts, at `tests/synaptic_host/test_security.py:930`, that its `tmp_path`
fixture resolves to the same drive as `tempfile.gettempdir()`.  The assertion is
deliberate: it is the B-11-R1 acceptance gate (W6, task #178, architecture
section 20.21), and its own docstring says relocating the fixture off the
temporary volume "is exactly how it would go green without ever reaching the
state it exists to test".

- Run with `--basetemp` on `F:` the test FAILS, and the Windows lane reads 103.
- Run with `--basetemp` on `C:` (the temp volume) the test PASSES, and the
  Windows lane reads 102.

Nothing else moves.  The two failing sets differ by exactly that one node.
**102 supersedes 103.**  103 is the count produced when a Windows lane is given
a basetemp on a non-temporary volume, which is what a run driver working out of
`F:\` naturally does.

Both lane arms are otherwise identical, so this is a single-variable control.

## 2. Lane table

| Lane | Interpreter | pytest | basetemp | failed | passed | skipped |
|---|---|---|---|---|---|---|
| Windows A | Python 3.12.7 | 8.4.1 | `C:` | **102** | 2048 | 50 |
| Windows B | Python 3.13.9 | 9.0.3 | `C:` | **102** | 2048 | 50 |
| Windows A | Python 3.12.7 | 8.4.1 | `F:` | 103 | 2047 | 50 |
| Windows B | Python 3.13.9 | 9.0.3 | `F:` | 103 | 2047 | 50 |
| WSL | Python 3.12.9 | 9.0.2 | ext4, short PATH | **105** | 2057 | 38 |
| WSL | Python 3.12.9 | 9.0.2 | ext4, ambient PATH | 117 | 2045 | 38 |

The two Windows interpreters produce **byte-identical failing sets** at every
basetemp: the symmetric difference of the two 102-node sets is empty, and so is
the symmetric difference of the two 103-node sets.  The Windows number does not
depend on the interpreter or on the pytest major version.

All three lanes collect the **same 2200 node ids** (set equality after a
lossless normalisation that splits on the first `::` and rewrites only the path
half, so parametrisation ids containing `\n`, `\x85` and `\x7f` survive).

## 3. Method, and how each count could have failed

Every lane ran the same runner file; only the interpreter differed.

- **Engine binding is asserted, not assumed.**  The runner inserts the worktree
  root and `worktree/synaptic-tuner` into `sys.path` **in process**, imports
  `synaptic_tuner` and `synaptic_host`, prints both `__file__` values and
  raises `SystemExit` unless both live under the worktree root.  Every lane
  reported the worktree engine.  This is the countermeasure to the failure that
  matters here: the worktree carries no pytest config, so `rootdir` resolves to
  the parent repository and its `pytest.ini` becomes `configfile`; the parent
  repository carries its **own** `synaptic_tuner`, so a run started from the
  parent working directory can bind the wrong tree silently at exit 0.
- **`PYTHONPATH` is never exported** (rule 21.2).  The path binding is
  in-process only.  A Windows child-environment probe confirmed `PYTHONPATH`
  is `None` in the Windows lanes.
- Flags held constant: `-c <parent pytest.ini>`, `--rootdir <worktree>`, `-q`,
  `--tb=no`, `-p no:cacheprovider`, `--basetemp <outside every git tree>`,
  `python -B`.
- Outcomes are recorded per node id by a `pytest_runtest_logreport` plugin, not
  parsed from terminal text.

**What each count enumerates, and how it could have been wrong:**

| Count | Set enumerated | How it could have failed |
|---|---|---|
| 2200 collected | every node under `tests/synaptic_host` | binding the parent repo's engine; lossy node-id normalisation collapsing parametrised ids (this one did happen once, 2200 -> 2195, and was fixed) |
| 102 Windows failing | nodes whose `call` phase failed, or that errored in any phase | a basetemp on a non-temp volume (this happened: it gave 103); a `__main__`-guard defect in the runner (this happened on WSL: it gave 118) |
| 105 WSL failing | same | an ambient `PATH` over 4096 bytes (this happened: it gave 117) |
| 231 engine modal nodes | the twelve `synaptic-tuner/tests/execution/providers/test_modal_*.py` files | none observed; measured by running them, 2 failed + 229 passed = 231 |
| 107 Host modal nodes | the three Host files named `test_modal_*` | none observed; `--collect-only` count |

**The plan's "261 nodes: Host 107, engine 154" needs correcting.**  The Host 107
is the three Modal-named Host test FILES, not the Host suite (the suite is 2200
nodes across 56 files).  The engine figure is **231**, not 154.  Modal-named
total is 338, not 261.

## 4. Two instrument defects found and corrected

Both were producing false reds.  Neither is a property of the tree.

1. **Missing `if __name__ == "__main__":` guard** in the lane runner.  The
   runner called `pytest.main()` at module level, so
   `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py::test_cross_process_contention_release_and_crash_recovery`
   re-imported `__main__` in its multiprocessing-spawn child and re-ran the whole
   session.  The WSL lane read 118 instead of 117.  Guarding the runner removed
   the node from the failing set.  The Windows lanes were unaffected.
2. **`--basetemp` on `F:`**, described in section 1.  The Windows lane read 103
   instead of 102.

A run driver that pins this failing set must guard its runner and must place
its basetemp on the temporary volume.  Both belong in the TEST-phase recipe.

## 5. Inter-lane diff, with a cause for every differing node

Clean lanes: **WSL 105, Windows 102, common 101, WSL-only 4, Windows-only 1.**

### WSL-only (4)

| Node | Windows outcome | Cause | Class |
|---|---|---|---|
| `docker_v1/test_prepared.py::test_prepared_adapter_binds_exact_staged_roots` | passed | `ValueError: prepared Docker stage requires a Windows drive path` raised at `synaptic_host/docker_v1/prepared.py:53`, called from `:112` `__init__`, entered at `tests/synaptic_host/docker_v1/test_prepared.py:101` | **missing platform gate** on Windows-only production code |
| `docker_v1/test_prepared.py::test_prepared_adapter_rejects_root_replacement` | passed | same site | same |
| `docker_v1/test_prepared.py::test_prepared_adapter_rejects_different_stage_keys` | passed | same site | same |
| `docker_v1/test_real_docker_wsl.py::test_released_facade_starts_real_offline_pinned_container` | skipped | `DockerHostCompositionErrorV1` raised at `synaptic_host/docker_v1/composition.py:111` `_fail`, from `:510`, entered at `tests/synaptic_host/docker_v1/test_real_docker_wsl.py:434` | **environment precondition**; it needs a reachable Docker daemon, and it is platform-gated to skip on Windows |

### Windows-only (1)

| Node | WSL outcome | Cause | Class |
|---|---|---|---|
| `test_publication_authority.py::test_key_path_or_key_content_substitution_invalidates_authority` | passed | `ValueError: HMAC private storage validation failed` raised at `synaptic_host/security.py:805`, from `:876` `_ensure_private_storage_directories`, from `:882` `initialize`, entered at `tests/synaptic_host/test_publication_authority.py:358` | **real Windows-path defect, cause swallowed** (see section 6) |

Stable across both basetemp volumes and both interpreters.  On Windows,
`_validate_private_directory` delegates at `synaptic_host/security.py:781` to
`_win_validate_directory`, and whatever that raises is discarded at `:804-805`
by `raise _private_storage_error() from None`.  The real cause is unnamed by
construction, so the node cannot be classified further without a source edit,
which this task does not make.

### The common 101, by file

| Nodes | File |
|---|---|
| 59 | `tests/synaptic_host/docker_v1/test_authority.py` |
| 34 | `tests/synaptic_host/docker_v1/test_binding.py` |
| 6 | `tests/synaptic_host/docker_v1/test_capabilities.py` |
| 1 | `tests/synaptic_host/docker_v1/test_composition.py` |
| 1 | `tests/synaptic_host/test_docker_training.py` |

**100 of the 102 pinned Windows failures are in the legacy `docker_v1`
subtree**, and 99 of them raise one error: `ValueError: Docker authority
operation failed`, at `synaptic_host/docker_v1/authority.py:608`, inside
`except BaseException: raise failure_factory() from None`.  Their real cause is
unnamed by the same mechanism B-18 was opened for.

The remaining node,
`test_docker_training.py::test_active_dirty_worktree_outer_command_is_resolution_unavailable`,
is the "sixth WSL red" already carried as FOLLOW-UP #379.

This is decision-relevant for the Modal smoke: the pre-existing red is
concentrated in the subtree the standing user ruling excludes from the
acceptance gate ("do not use the legacy Alpine Docker test as the acceptance
gate").  Outside `docker_v1`, the Windows lane at `d0888ed6` carries exactly
**two** failing nodes.

## 6. Three unfixed cause-swallowing sites

The B-18 fix (architecture section 27) restored the cause chain at six sites on
the publish path.  The pinned failing set is produced at three sites it did not
cover:

| Site | Statement | Nodes it accounts for |
|---|---|---|
| `synaptic_host/docker_v1/authority.py:608` | `raise failure_factory() from None` inside `except BaseException` | 99 |
| `synaptic_host/security.py:805` | `raise _private_storage_error() from None` | 1 (the Windows-only node) |
| `synaptic_host/docker_v1/composition.py:111` | `_fail` | 1 (the WSL-only Docker node) |

101 of the 107 failing nodes across both lanes therefore report a message that
does not name their cause.

## 7. WSL is environment-dependent in a way that matters for the smoke

The WSL lane reads 117 with this shell's ambient `PATH` and 105 with a short
one.  The 12 extra nodes are all in `tests/synaptic_host/test_cold_bootstrap.py`
(the ten parametrisations of
`test_launcher_never_forwards_partial_or_invalid_modal_credentials`, plus
`test_launcher_parent_binds_argv_and_digest_without_real_process` and
`test_launcher_rejects_credential_string_subclasses`).  All twelve fail at one
site: `synaptic_host/launcher.py:628`, `raise RuntimeError("child environment
value is invalid")`.

**Cause, established by single-variable control with the interpreter held
fixed:** `_validated_child_environment_value` (`synaptic_host/launcher.py`)
returns `None` for any value whose UTF-8 encoding exceeds **4096 bytes**, and
`ensure_and_reexec` raises at `:628` when any name in `_ALLOWED_CHILD_ENV`
(`HOME`, `LANG`, `LC_ALL`, `PATH`, `TMPDIR`, `SSL_CERT_FILE`, `SSL_CERT_DIR`)
fails that check.  The tests monkeypatch only the credential keys, so the
ambient `PATH` reaches the validator.

| Environment | PATH bytes | Cold-bootstrap outcome |
|---|---|---|
| This WSL shell, ambient | 5248 | 12 failed, 84 passed, 1 skipped |
| Same interpreter, `PATH` shortened | 46 | 96 passed, 1 skipped |
| Windows lane | 3903 | 0 failed |

**This is a production finding, not only a test-hygiene one.**  `ensure_and_reexec`
is the Modal launcher's re-exec.  On any operator machine whose `PATH` exceeds
4096 bytes the Modal launcher raises `RuntimeError: child environment value is
invalid`, with no indication of which key was rejected.  The Windows lane sits
**193 bytes** below the bound.  A single additional entry on the operator's
`PATH` turns the Modal lane red before any Modal code runs, and the message will
not say why.

## 8. Scenario X3 and the Host-to-Modal seam, measured

The plan records seam coverage as "0%, DERIVED by census".  **Confirmed by
instrument, and the derivation was right.**

Measured with `coverage` 7.13.1 at `run:dynamic_context = test_function`, so
executed lines carry the node ids that executed them.

### The seam

`synaptic_host/modal_training.py` is the only Host module that loads the real
Modal SDK:

```
363  def _default_sdk_loader() -> object:
364      return importlib.import_module("modal")
...
443  def execute_modal_training_run_v2(
450      sdk_loader: Callable[[], object] = _default_sdk_loader,
502          sdk = sdk_loader()
```

Over the whole Host suite (2200 nodes):

| Line | Executed | Contexts |
|---|---|---|
| 363 (the `def` statement) | yes | none: it runs at import, outside any test |
| **364 (the real SDK import)** | **no** | **none** |
| 502 (`sdk = sdk_loader()`) | yes | many `test_modal_training` nodes, all injecting a substitute loader |

This is a green-by-omission on an injectable default: the call site is heavily
covered, the default factory is never reached, because every test injects.

Over the engine's Modal test files (231 nodes across the twelve
`synaptic-tuner/tests/execution/providers/test_modal_*.py` files): **zero
executed lines in any `synaptic_host` file.**  The engine tests cannot reach the
Host seam, because they never import the Host.

So of the 2431 nodes measured (Host 2200 + engine modal 231), **the number that
execute `synaptic_host/modal_training.py:364` is zero.**

### X3

Scenario X3 is the "golden-fixture observe/verify/reverify drill, pre-submit".

- **"Golden fixtures" have no referent in this tree.**  A case-insensitive
  `git grep -l golden` restricted to `tests`, `synaptic_host` and
  `synaptic-tuner` at `d0888ed6` returns **nothing**.  Across the whole tree it
  returns only `datasets/`, `archive/experiment/`, `experiments/`,
  `library/concepts/mechanisms` and documentation directories.  No Host or
  engine test or fixture uses the word.
- **X3 reaches no Modal code path from the Host.**  The observe/verify/reverify
  surface is `synaptic_host/verified_artifact_source.py` (`show` at `:185` and
  `:197`, `reverify` at `:189`, `artifacts` at `:243`), which takes an injected
  `RunsAPI`.  The only production construction of `RunsAPI` in `synaptic_host`
  is `synaptic_host/docker_publication.py:459`, whose operations object defines
  `reverify` at `docker_publication.py:240` (aliased `verify` at `:250`).  It is
  the **Docker** reverify.
- Nothing in `synaptic_host` constructs `ModalTrainingOperations`; a grep for
  `ModalTrainingOperations`, `TrainingOperations` and `modal.training` over
  `synaptic_host` returns nothing.
- The engine does own a Modal `reverify`, at
  `synaptic-tuner/tuner/execution/providers/modal/training.py:1748`.  Under the
  whole Host suite its **body is never executed** (coverage over lines
  1749-1789: empty).  It is reachable only through engine-side
  `ModalTrainingOperations`, which the Host never builds.

This confirms the outcome the plan anticipated at line 62: X3 exercises the
Docker reverify path, not a Modal one.  It is a recorded finding, not a stop.

**Correction to an earlier statement of mine (#416).**  I reported that "the
Modal path has no publication and no reverify at `d0888ed6`".  That is true of
`synaptic_host` only.  The engine has a Modal `reverify` at
`providers/modal/training.py:1748`.  The claim must be read Host-scoped.

## 9. For the ARCHITECT

What the reconciliation fix must change:

1. **Adopt 102 as the pinned Windows baseline** and record the basetemp rule
   beside it: a Windows lane pinning this set places `--basetemp` on the
   temporary volume.  A driver that uses `F:` measures 103 and the extra node is
   the B-11-R1 W6 gate refusing to run off its volume.  Neither number is
   "wrong"; the volume is a parameter of the measurement and must be declared.
2. **Make the runner `__main__`-guarded a stated requirement.**  An unguarded
   `pytest.main()` re-runs the session inside the one multiprocessing-spawn
   test and inflates the WSL count by one.
3. **Record the environment parameters that move the count**, alongside the tree
   identity: basetemp volume, `PATH` byte length, and the asserted
   `synaptic_tuner.__file__`.  A pinned failing set with none of these declared
   is not reproducible.
4. **Rule on the `PATH` bound at `launcher.py:628`.**  This is the one item that
   is a defect rather than a measurement artefact, and it is on the Modal
   launcher's own path.  Two things are wrong: the 4096-byte bound rejects an
   ordinary operator `PATH`, and the message does not name the rejected key.
   The Windows lane clears the bound by 193 bytes.  At minimum the error must
   name the key; whether the bound should apply to `PATH` at all is the ruling.
5. **Decide the disposition of the legacy `docker_v1` red.**  100 of the 102 sit
   there, behind `authority.py:608` `raise failure_factory() from None`.  Either
   the subtree is declared out of scope for the smoke's gates (consistent with
   the standing ruling that the legacy Alpine Docker test is not the acceptance
   gate), or its cause chain is restored the way section 27 restored the publish
   path.  Leaving it undeclared means every gate below inherits 100 reds whose
   cause nobody can name.
6. **Rule on the Windows-only publication-authority failure.**  It is the only
   pre-existing Windows red outside `docker_v1`, it is on the publication path
   the smoke will exercise, and its cause is swallowed at `security.py:805`.

What gates G1 to G4 need from this:

- **G1 (SEAM).**  The seam is 0% by measurement, not by inference:
  `modal_training.py:364` is executed by zero of the 2431 nodes measured.  G1
  needs at least one test that reaches the default loader rather than injecting
  past it.  The measurable acceptance criterion is now concrete: line 364
  executes under at least one named node id.  G1 must also not accept coverage
  of `:502` as coverage of the seam, which is exactly the confusion the
  injectable default invites.
- **G2 (SUBMIT).**  Submit runs through `ensure_and_reexec`.  G2 must be
  measured on an operator environment whose `PATH` length is recorded, or the
  launcher bound will surface as an unexplained red at submit time.
- **G3 (DURABLE) and G4 (OUTCOME).**  Both need the 102 as their subtraction
  baseline, taken on the same lane, same basetemp volume, same guarded runner.
  Any Modal-lane red must be differenced against the 102 by node id, never by
  count.  Outside `docker_v1` the baseline is two nodes, which makes a
  node-id difference cheap and a count difference misleading.
- **X3** should be relabelled: it is a Docker observe/verify/reverify drill.
  Nothing about it exercises Modal, and no golden fixtures exist for it to use.

## 10. Untracked-file snapshot

Snapshot taken before and after every run in this task, with
`git status --porcelain --untracked-files=all`.

Before:

```
 M .claude/CLAUDE.md
?? docs/plans/modal-smoke-prepared-path-plan.md
?? docs/preparation/modal-blocker-applicability-census.md
?? docs/preparation/modal-smoke-prepared-path.md
```

After:

```
 M .claude/CLAUDE.md
A  docs/preparation/modal-smoke-prepared-path-external-surface.md
?? docs/plans/modal-smoke-prepared-path-plan.md
?? docs/preparation/modal-blocker-applicability-census.md
?? docs/preparation/modal-smoke-prepared-path.md
```

**The runs created nothing in the repository.**  The one new entry,
`docs/preparation/modal-smoke-prepared-path-external-surface.md`, is a peer
artifact (devops-modal, task #429) that appeared during my runs and was staged
by its author.  Every basetemp used was outside every git tree, on
`/home/profsynapse/_bt_430*` and `C:\Users\Joseph\_bt430\*`, plus the two `F:`
basetemps whose effect section 1 reports.

## Appendix A: the pinned Windows failing set, 102 node ids

Measured at `d0888ed6`, engine pin `ce539b70`, Python 3.12.7 with pytest 8.4.1
and Python 3.13.9 with pytest 9.0.3 (identical sets), `--basetemp` on `C:`.
Paths are relative to the worktree root.

`tests/synaptic_host/docker_v1/test_authority.py` (59)

- `test_all_constructor_trust_decisions_ignore_rebound_module_globals[opaque/local-cpu]`
- `test_all_constructor_trust_decisions_ignore_rebound_module_globals[opaque/registry-cpu]`
- `test_callback_substitution_cannot_change_later_constructor_semantics[opaque/local-cpu]`
- `test_callback_substitution_cannot_change_later_constructor_semantics[opaque/registry-cpu]`
- `test_callback_time_global_pin_and_schema_substitution_is_inert[opaque/local-cpu]`
- `test_callback_time_global_pin_and_schema_substitution_is_inert[opaque/registry-cpu]`
- `test_callback_time_reconstruction_substitution_preserves_live_identity[opaque/local-cpu]`
- `test_callback_time_reconstruction_substitution_preserves_live_identity[opaque/registry-cpu]`
- `test_empty_workload_environment_round_trip_and_key_identity_pin`
- `test_engine_binding_authority_and_host_view_share_one_signer[opaque/local-cpu]`
- `test_engine_binding_authority_and_host_view_share_one_signer[opaque/registry-cpu]`
- `test_engine_evidence_view_boolean_authenticates_exact_envelopes`
- `test_exact_authority_schema_is_literal_pinned_and_subclasses_reject[opaque/local-cpu]`
- `test_exact_authority_schema_is_literal_pinned_and_subclasses_reject[opaque/registry-cpu]`
- `test_global_schema_and_class_rebinding_before_construction_are_inert[opaque/local-cpu]`
- `test_global_schema_and_class_rebinding_before_construction_are_inert[opaque/registry-cpu]`
- `test_hostile_exact_authenticator_results_fail_closed`
- `test_kernel_domain_mutation_during_sign_and_verify_fails_closed[opaque/local-cpu]`
- `test_kernel_domain_mutation_during_sign_and_verify_fails_closed[opaque/registry-cpu]`
- `test_live_class_mutation_during_sign_cannot_change_constructed_schema[opaque/local-cpu]`
- `test_live_class_mutation_during_sign_cannot_change_constructed_schema[opaque/registry-cpu]`
- `test_nested_pair_callback_substitution_uses_sealed_dispatcher[opaque/local-cpu]`
- `test_nested_pair_callback_substitution_uses_sealed_dispatcher[opaque/registry-cpu]`
- `test_pair_accepts_exact_artifact_adjacency[opaque/local-cpu]`
- `test_pair_accepts_exact_artifact_adjacency[opaque/registry-cpu]`
- `test_pair_authority_authenticates_outer_and_both_nested_envelopes[opaque/local-cpu]`
- `test_pair_authority_authenticates_outer_and_both_nested_envelopes[opaque/registry-cpu]`
- `test_pair_is_structural_and_preserves_exact_live_verification_identity[opaque/local-cpu]`
- `test_pair_is_structural_and_preserves_exact_live_verification_identity[opaque/registry-cpu]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-other-mapping-SOURCE_READ-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-source-mapping-ARTIFACT_WRITE-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-source-mapping-SOURCE_READ-/mnt/other]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-other-mapping-SOURCE_READ-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-source-mapping-ARTIFACT_WRITE-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-source-mapping-SOURCE_READ-/mnt/other]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authenticator_key]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authenticator_path]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authority_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-kernel]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-key_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-purpose]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authenticator_key]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authenticator_path]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authority_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-kernel]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-key_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-purpose]`
- `test_reconstruction_dispatch_is_sealed_before_authority_construction[opaque/local-cpu]`
- `test_reconstruction_dispatch_is_sealed_before_authority_construction[opaque/registry-cpu]`
- `test_remaining_typed_host_authorities_round_trip[opaque/local-cpu]`
- `test_remaining_typed_host_authorities_round_trip[opaque/registry-cpu]`
- `test_replacing_global_authority_lookup_cannot_substitute_trust_anchor[opaque/local-cpu]`
- `test_replacing_global_authority_lookup_cannot_substitute_trust_anchor[opaque/registry-cpu]`
- `test_replacing_module_pin_type_does_not_change_original_pin_identity[opaque/local-cpu]`
- `test_replacing_module_pin_type_does_not_change_original_pin_identity[opaque/registry-cpu]`
- `test_same_key_cannot_replay_across_authority_or_domain[opaque/local-cpu]`
- `test_same_key_cannot_replay_across_authority_or_domain[opaque/registry-cpu]`
- `test_typed_authorities_reject_subclasses_and_reconstruct[opaque/local-cpu]`
- `test_typed_authorities_reject_subclasses_and_reconstruct[opaque/registry-cpu]`

`tests/synaptic_host/docker_v1/test_binding.py` (34)

- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/local-cpu-authenticate]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/local-cpu-issue]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/registry-cpu-authenticate]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/registry-cpu-issue]`
- `test_pair_binder_concurrent_calls_converge_on_exact_binding[opaque/local-cpu]`
- `test_pair_binder_concurrent_calls_converge_on_exact_binding[opaque/registry-cpu]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-declared-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-pair-digest]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-storage-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-wsl-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-declared-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-pair-digest]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-storage-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-wsl-ref]`
- `test_pair_binder_derives_requests_proofs_and_preserves_source_identity[opaque/local-cpu]`
- `test_pair_binder_derives_requests_proofs_and_preserves_source_identity[opaque/registry-cpu]`
- `test_pair_binder_reauth_detects_callback_live_identity_and_pin_mutation[opaque/local-cpu]`
- `test_pair_binder_reauth_detects_callback_live_identity_and_pin_mutation[opaque/registry-cpu]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/local-cpu-authenticate]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/local-cpu-issue]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/registry-cpu-authenticate]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/registry-cpu-issue]`
- `test_pair_binder_rejects_pre_call_equal_looking_live_identity_replacement[opaque/local-cpu]`
- `test_pair_binder_rejects_pre_call_equal_looking_live_identity_replacement[opaque/registry-cpu]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-artifact-path]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-artifact-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-containment]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-roles]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-source-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-artifact-path]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-artifact-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-containment]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-roles]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-source-ref]`

`tests/synaptic_host/docker_v1/test_capabilities.py` (6)

- `test_pair_registry_compares_callback_to_untouched_pair_baseline[opaque/local-cpu]`
- `test_pair_registry_compares_callback_to_untouched_pair_baseline[opaque/registry-cpu]`
- `test_pair_registry_is_single_authenticated_source_for_every_projection[opaque/local-cpu]`
- `test_pair_registry_is_single_authenticated_source_for_every_projection[opaque/registry-cpu]`
- `test_pair_registry_rejects_role_confusion_forgery_and_unknown_required_keys[opaque/local-cpu]`
- `test_pair_registry_rejects_role_confusion_forgery_and_unknown_required_keys[opaque/registry-cpu]`

`tests/synaptic_host/docker_v1/test_composition.py` (1)

- `test_real_released_graph_composes_without_process_or_transfer_gap`

`tests/synaptic_host/test_docker_training.py` (1)

- `test_active_dirty_worktree_outer_command_is_resolution_unavailable`

`tests/synaptic_host/test_publication_authority.py` (1)

- `test_key_path_or_key_content_substitution_invalidates_authority`
## Appendix B: the WSL failing set, 105 node ids

Same tree, Python 3.12.9 with pytest 9.0.2, ext4 basetemp, `PATH` under the
4096-byte launcher bound.

`tests/synaptic_host/docker_v1/test_authority.py` (59)

- `test_all_constructor_trust_decisions_ignore_rebound_module_globals[opaque/local-cpu]`
- `test_all_constructor_trust_decisions_ignore_rebound_module_globals[opaque/registry-cpu]`
- `test_callback_substitution_cannot_change_later_constructor_semantics[opaque/local-cpu]`
- `test_callback_substitution_cannot_change_later_constructor_semantics[opaque/registry-cpu]`
- `test_callback_time_global_pin_and_schema_substitution_is_inert[opaque/local-cpu]`
- `test_callback_time_global_pin_and_schema_substitution_is_inert[opaque/registry-cpu]`
- `test_callback_time_reconstruction_substitution_preserves_live_identity[opaque/local-cpu]`
- `test_callback_time_reconstruction_substitution_preserves_live_identity[opaque/registry-cpu]`
- `test_empty_workload_environment_round_trip_and_key_identity_pin`
- `test_engine_binding_authority_and_host_view_share_one_signer[opaque/local-cpu]`
- `test_engine_binding_authority_and_host_view_share_one_signer[opaque/registry-cpu]`
- `test_engine_evidence_view_boolean_authenticates_exact_envelopes`
- `test_exact_authority_schema_is_literal_pinned_and_subclasses_reject[opaque/local-cpu]`
- `test_exact_authority_schema_is_literal_pinned_and_subclasses_reject[opaque/registry-cpu]`
- `test_global_schema_and_class_rebinding_before_construction_are_inert[opaque/local-cpu]`
- `test_global_schema_and_class_rebinding_before_construction_are_inert[opaque/registry-cpu]`
- `test_hostile_exact_authenticator_results_fail_closed`
- `test_kernel_domain_mutation_during_sign_and_verify_fails_closed[opaque/local-cpu]`
- `test_kernel_domain_mutation_during_sign_and_verify_fails_closed[opaque/registry-cpu]`
- `test_live_class_mutation_during_sign_cannot_change_constructed_schema[opaque/local-cpu]`
- `test_live_class_mutation_during_sign_cannot_change_constructed_schema[opaque/registry-cpu]`
- `test_nested_pair_callback_substitution_uses_sealed_dispatcher[opaque/local-cpu]`
- `test_nested_pair_callback_substitution_uses_sealed_dispatcher[opaque/registry-cpu]`
- `test_pair_accepts_exact_artifact_adjacency[opaque/local-cpu]`
- `test_pair_accepts_exact_artifact_adjacency[opaque/registry-cpu]`
- `test_pair_authority_authenticates_outer_and_both_nested_envelopes[opaque/local-cpu]`
- `test_pair_authority_authenticates_outer_and_both_nested_envelopes[opaque/registry-cpu]`
- `test_pair_is_structural_and_preserves_exact_live_verification_identity[opaque/local-cpu]`
- `test_pair_is_structural_and_preserves_exact_live_verification_identity[opaque/registry-cpu]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-other-mapping-SOURCE_READ-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-source-mapping-ARTIFACT_WRITE-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/local-cpu-source-mapping-SOURCE_READ-/mnt/other]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-other-mapping-SOURCE_READ-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-source-mapping-ARTIFACT_WRITE-/mnt/synaptic/source]`
- `test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root[opaque/registry-cpu-source-mapping-SOURCE_READ-/mnt/other]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authenticator_key]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authenticator_path]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-authority_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-kernel]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-key_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/local-cpu-purpose]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authenticator_key]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authenticator_path]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-authority_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-kernel]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-key_ref]`
- `test_pair_revalidates_complete_outer_trust_after_each_nested_callback[opaque/registry-cpu-purpose]`
- `test_reconstruction_dispatch_is_sealed_before_authority_construction[opaque/local-cpu]`
- `test_reconstruction_dispatch_is_sealed_before_authority_construction[opaque/registry-cpu]`
- `test_remaining_typed_host_authorities_round_trip[opaque/local-cpu]`
- `test_remaining_typed_host_authorities_round_trip[opaque/registry-cpu]`
- `test_replacing_global_authority_lookup_cannot_substitute_trust_anchor[opaque/local-cpu]`
- `test_replacing_global_authority_lookup_cannot_substitute_trust_anchor[opaque/registry-cpu]`
- `test_replacing_module_pin_type_does_not_change_original_pin_identity[opaque/local-cpu]`
- `test_replacing_module_pin_type_does_not_change_original_pin_identity[opaque/registry-cpu]`
- `test_same_key_cannot_replay_across_authority_or_domain[opaque/local-cpu]`
- `test_same_key_cannot_replay_across_authority_or_domain[opaque/registry-cpu]`
- `test_typed_authorities_reject_subclasses_and_reconstruct[opaque/local-cpu]`
- `test_typed_authorities_reject_subclasses_and_reconstruct[opaque/registry-cpu]`

`tests/synaptic_host/docker_v1/test_binding.py` (34)

- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/local-cpu-authenticate]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/local-cpu-issue]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/registry-cpu-authenticate]`
- `test_pair_binder_checks_source_identity_around_each_output_callback[opaque/registry-cpu-issue]`
- `test_pair_binder_concurrent_calls_converge_on_exact_binding[opaque/local-cpu]`
- `test_pair_binder_concurrent_calls_converge_on_exact_binding[opaque/registry-cpu]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-declared-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-pair-digest]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-storage-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/local-cpu-wsl-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-declared-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-pair-digest]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-storage-ref]`
- `test_pair_binder_constructor_rejects_direct_colliding_envelopes[opaque/registry-cpu-wsl-ref]`
- `test_pair_binder_derives_requests_proofs_and_preserves_source_identity[opaque/local-cpu]`
- `test_pair_binder_derives_requests_proofs_and_preserves_source_identity[opaque/registry-cpu]`
- `test_pair_binder_reauth_detects_callback_live_identity_and_pin_mutation[opaque/local-cpu]`
- `test_pair_binder_reauth_detects_callback_live_identity_and_pin_mutation[opaque/registry-cpu]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/local-cpu-authenticate]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/local-cpu-issue]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/registry-cpu-authenticate]`
- `test_pair_binder_rejects_output_callback_mutation[opaque/registry-cpu-issue]`
- `test_pair_binder_rejects_pre_call_equal_looking_live_identity_replacement[opaque/local-cpu]`
- `test_pair_binder_rejects_pre_call_equal_looking_live_identity_replacement[opaque/registry-cpu]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-artifact-path]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-artifact-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-containment]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-roles]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/local-cpu-source-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-artifact-path]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-artifact-ref]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-containment]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-roles]`
- `test_pair_binder_rejects_role_ref_and_component_confusion[opaque/registry-cpu-source-ref]`

`tests/synaptic_host/docker_v1/test_capabilities.py` (6)

- `test_pair_registry_compares_callback_to_untouched_pair_baseline[opaque/local-cpu]`
- `test_pair_registry_compares_callback_to_untouched_pair_baseline[opaque/registry-cpu]`
- `test_pair_registry_is_single_authenticated_source_for_every_projection[opaque/local-cpu]`
- `test_pair_registry_is_single_authenticated_source_for_every_projection[opaque/registry-cpu]`
- `test_pair_registry_rejects_role_confusion_forgery_and_unknown_required_keys[opaque/local-cpu]`
- `test_pair_registry_rejects_role_confusion_forgery_and_unknown_required_keys[opaque/registry-cpu]`

`tests/synaptic_host/docker_v1/test_composition.py` (1)

- `test_real_released_graph_composes_without_process_or_transfer_gap`

`tests/synaptic_host/docker_v1/test_prepared.py` (3)

- `test_prepared_adapter_binds_exact_staged_roots`
- `test_prepared_adapter_rejects_different_stage_keys`
- `test_prepared_adapter_rejects_root_replacement`

`tests/synaptic_host/docker_v1/test_real_docker_wsl.py` (1)

- `test_released_facade_starts_real_offline_pinned_container`

`tests/synaptic_host/test_docker_training.py` (1)

- `test_active_dirty_worktree_outer_command_is_resolution_unavailable`
