# Relaunching archived phase-1 probe machinery

Read this before launching any cell that imports from or re-runs
`archive/experiment/phase1/probe/` machinery (regeneration, re-score, and
parity cells; anything whose entry point tees or drives the archived
extractors/amendment scripts). The archived launch surface has drifted from
the tree those scripts were written against, and the same failure classes
recur. One cell (`experiments/wide-instrument-control-rescore`, resolved
2026-08-20) hit six pre-GPU stops in a row from this list; two sibling
experiments independently hit and fixed the same config-path break. Budget
for these up front instead of rediscovering them one stop at a time.

Master rule: fixes are ENVIRONMENT-ONLY. Never edit an archived or pinned
script — that changes its recorded sha and breaks the provenance chain. If a
fix cannot be expressed as a restored file, a PYTHONPATH entry, an untracked
shim, or a submodule checkout, stop and escalate. A parity gate against the
committed summaries (WG-G0 style) is the final arbiter that the environment
fixes preserved fidelity; environment fixes never substitute for it.

## Failure classes and remedies

1. **Gitignored inputs do not survive checkouts.** Pool files, mining
   outputs, and expansion candidates under `archive/.../probe/analysis/`
   are gitignored and will be absent from a fresh checkout even though the
   archived scripts require them. Remedy: locate byte-identical copies in
   sibling cells' gitignored staging or regenerate via the owning cell's
   own pinned script, and certify against a committed sha256 record (e.g.
   another cell's `analysis-committed` provenance JSON) BEFORE launch.
   Never let a launch proceed on an uncertified restore, and never assume
   the file's absence means the step is optional.

2. **Relocations and renames break bare-name imports and hardcoded
   paths.** The archive has been reorganized since the scripts were
   written (e.g. wrapper files moved into `legacy-wrapper-tree/`; a config
   rename dropped a `phase3_` prefix in a NOT-content-pure rename).
   Remedies, in order of preference: extend PYTHONPATH (the known-good set
   for the probe extractors is `amendments/` + `legacy-wrapper-tree/` +
   the repo root) rather than editing imports; for a hardcoded stale path,
   place an untracked verbatim copy of the tracked successor at the old
   expected path (shim), after verifying the consumed subset of the file
   is byte-identical across the rename. Never commit the shim. When a
   rename is claimed to be pure, verify the claim on the consumed bytes —
   R-scores below R100 mean content changed somewhere.

3. **The archived tree is compatibility wrappers, and untracked helpers
   can be load-bearing.** Archived modules may be thin wrappers delegating
   to promoted implementations under `experiments/common/` via
   namespace-package imports (hence repo root on PYTHONPATH). Conversely,
   an untracked file sitting in the archive (e.g. a probe-root
   `backends.py`) may be a byte-identical copy of a promoted module that
   satisfies a bare import the chain needs. Verify by sha256 against the
   promoted candidate before declaring any such file cruft or moving it —
   deleting one of these breaks the import chain at launch time.

4. **Offline prep has ordering dependencies with fail-closed checks.**
   Where a mining step feeds an extractor feeds a materializer, run them
   in dependency order (for the 4.5-lineage cells: mining, then anchor
   extraction, then materialize) and trust only the scripts' own printed
   fail-closed counters (`missing_question=0`, expected
   `known_correct_answered` totals) — an extract run before mining
   completes silently covers a subset and fails much later with a
   row-key KeyError inside the GPU stage. If ordering was violated,
   re-running the SAME pinned command unchanged after the inputs exist is
   the fix; check the startup log shows the full row population.

5. **Submodule regression-by-upgrade.** A parity-locked cell must
   regenerate under the engine the source cell actually ran, not current
   submodule main: later tuner commits can add code paths (e.g. a
   readback snapshot with a device bug) that crash or perturb historical
   pipelines. Remedy: check out, per cell, the tuner sha pinned by that
   cell's own evidence commit (working-tree only, no commits anywhere),
   record the sha actually run in the cell's provenance output, and
   restore the repo's pinned submodule pointer before scoring. Verify the
   historical sha lacks the offending code before trusting it.

## Worked example

`experiments/wide-instrument-control-rescore/` NOTEBOOK.md (launch attempts
1–6, 2026-08-18/19) and RUNBOOK.md section 0/1 record each stop, the
ruling, and the exact remedy commands; its byte-exact WG-G0 parity result
(0.0pp on all 13 rate pairs) is the demonstration that this environment-only
discipline preserves regeneration fidelity.
