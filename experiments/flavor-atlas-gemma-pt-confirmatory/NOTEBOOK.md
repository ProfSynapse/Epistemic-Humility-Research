# Second-substrate confirmatory: overt-unanswerability flavor separation on pretrain-only Gemma notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-10 - committed smoke runner (smoke_all.py) + reproducibility fix

Prior smokes for every module were run interactively (ad hoc heredoc scripts) and
died with the authoring session, so the lead could not replay them from the
committed tree. Fixed by committing `smoke_all.py`, one runner that exercises
every module's claimed check with hard assertions (not prints) and a nonzero
exit on any failure. Replay with:

```
cd experiments/flavor-atlas-gemma-pt-confirmatory
python3 smoke_all.py
```

Ran twice from the committed tree (fresh process each time) to confirm
determinism. Both runs: **11 passed, 0 skipped, 0 failed**, wall clock ~18s
first run / ~17s second run (dominated by the control-render tokenizer load,
~7-8s, which reads `google/gemma-4-E4B-it` from the local HF cache with
`local_files_only=True`; SKIPPED with an explicit marker rather than failing if
that cache entry is ever absent).

Per-check results (both runs identical):

```
[PASS] render_gemma: primary k-shot determinism + exact block content
[PASS] render_gemma: dual-render subsample selection (1800 rows, deterministic, exact counts)
[PASS] render_gemma: control chat-template render (SKIPPED if -it tokenizer not in local cache)
[PASS] extract_anchor_gemma: primary+control extraction, per-row schema, kill-resume, render-fingerprint invalidation, GG0 hard-stop
[PASS] build_flavor_panels: verify_and_copy positive/negative cases + counts_summary
[PASS] flavor_probe_sweep: require_forward_use_cache hard-stops on inadmissible manifests
[PASS] flavor_probe_sweep: end-to-end G1-G4 + dual-leg decision (both legs, 6 flavors + 2 reference rows) + G6 on synthetic panels/activations
[PASS] surface_residualization: treatment strength, permutation negative control, planted-channel positive control (raw>=0.90, residualized<=0.75)
[PASS] gate_adjudicator: GG0/GG1/GG4 pass+fail branches, P1/F1, P2/F2, fail-closed propagation on a failing GG0
[PASS] kv_seam_paired_smoke.py --mode=synthetic (subprocess, exact committed command)
[PASS] test_leg_b_selection_logic.py (subprocess, exact committed command)
```

The residualization planted-channel control's exact numbers are seed-stable
but not bitwise pinned across sklearn/numpy versions, so `smoke_all.py` asserts
the registered GATE BOUNDS (raw AUROC >= 0.90, residualized AUROC <= 0.75) as
the hard check rather than an exact printed value; both runs landed at
raw=0.9954/residualized=0.2375, same seed and same result both times, well
inside the required bounds.

`kv_seam_paired_smoke.py --mode=synthetic` and `test_leg_b_selection_logic.py`
already had their own committed CLI entry points from the original authoring
pass; `smoke_all.py` invokes them as subprocesses of the exact same committed
command so this one runner also proves those two commands still work, rather
than duplicating their logic inline.

Files touched by this fix: added `smoke_all.py`
(sha256 recorded in `experiment.yaml` instrument.pins), this NOTEBOOK.md entry,
and `experiment.yaml`'s `instrument.persistence` entries (replaced ad-hoc smoke
descriptions with the reproducible `smoke_all.py` commands/results above).
No other file's content changed; `cell.yaml`/`gates.yaml`/all other `.py` file
sha256s are unchanged from the original authoring pass (verified by
recomputing and diffing against the previously recorded pins).

### 2026-08-10 - scaffold authored, five signing prerequisites resolved (CPU-only)

Scaffolded from the PI-approved design draft at
`/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/b069c3f6-b5c7-4ed7-ad9e-371fbb2fe3a9/scratchpad/gemma-flavor-confirmatory-draft.md`
(891 lines, read in full) per the team lead's adjudications, which are final:
slug `flavor-atlas-gemma-pt-confirmatory`, type probe-fit, pretrain-only
`google/gemma-4-E4B` substrate, vendored seam-safe extractor (`mechinterp
extract` PROHIBITED on this substrate, mirroring
`experiments/gemma4-e4b-kv-seam-quarantine/extract_anchor.py`'s
`use_cache=True` pattern), Amendment Y base-mode k-shot render rule, dual-leg
decision surface (hs24 external anchor + nested split-half leg), 0.75 transfer
bar as drafted (the draft's 0.85 F1 limb explicitly rejected, see
AMENDMENT.md "Bands"), GG4 hs0 ceiling 0.55 as drafted, AmbigQA whole-curve
conjunction as drafted, Clause A/B adjudicated separately as drafted.

**RENDER SWAP, the one adjudication that changes the draft's structure, not
just fills a blank.** The draft defaulted to chat-template PRIMARY / k-shot
CONTROL. The lead's instruction ("Amendment Y base-mode k-shot render rule")
invokes the draft's own stated fallback ("If the lead prefers Y's rule, swap
the primary and the control; the arithmetic is unchanged" - draft, Open
Question 3). Implemented as: `render_gemma.py::render_primary_kshot` (vendored
byte-identical from `experiments/common/readouts/
amendment_x_cross_model_extract.py`'s `_BASE_MODE_FEWSHOT` /
`build_base_mode_prompt`) is PRIMARY and drives all of G1-G5 on the full
11657-row panel set; `render_gemma.py::render_control_chat` (google/gemma-4-
E4B-it chat template + the Qwen render's verbatim system prompt) is the
descriptive G6 control on the 1800-row dual-render subsample only. Recorded
in AMENDMENT.md's "Render" section and gates.yaml's header comment so it
cannot be missed or silently reverted at sign-off.

**Signing prerequisite (a): pin the pt revision.**

```
python3 -c "
from huggingface_hub import HfApi
info = HfApi().model_info('google/gemma-4-E4B')
print('sha:', info.sha)
print('gated:', info.gated)
print('private:', info.private)
"
```

Result: `sha: 411aa17b749aa952df1359d2dcea73917a544d9a`, `gated: False`,
`private: False`. No weight download; `model_info` is metadata-only. The
instruct sibling's pin (`fee6332c1abaafb77f6f9624236c63aa2f1d0187`) is a
different checkpoint and was not reused.

Operational note: the shared HF cache at
`~/.cache/huggingface/hub/.locks/` is owned by a uid that does not map to
`profsynapse` and is not writable in this environment, so subsequent
metadata-only fetches (config.json) were routed through a scratchpad-local
`cache_dir` rather than the default shared cache. The shared cache itself was
never touched or modified.

**Signing prerequisite (b): hub access.** Folded into (a)'s result above:
`gated: False`, `private: False`, metadata fetch succeeded with no auth token.

**Signing prerequisite (c): confirm the pt config shape.**

```
python3 -c "
import json
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id='google/gemma-4-E4B', filename='config.json',
    revision='411aa17b749aa952df1359d2dcea73917a544d9a',
    cache_dir='<scratchpad>/hf_cache_gemma')
cfg = json.load(open(path))
print('model_type:', cfg['model_type'])
print('architectures:', cfg['architectures'])
tc = cfg['text_config']
print('num_hidden_layers:', tc['num_hidden_layers'])
print('hidden_size:', tc['hidden_size'])
print('num_kv_shared_layers:', tc['num_kv_shared_layers'])
"
```

Result: `model_type: gemma4`, `architectures: ['Gemma4ForConditionalGeneration']`,
`text_config.num_hidden_layers: 42`, `text_config.hidden_size: 2560` -> 43
hidden states, matching the draft exactly (config.json fetched only, no
weights). `text_config.num_kv_shared_layers: 18` was not asked for by the
draft but independently corroborates the KV-seam hazard footprint the whole
extractor design depends on: exactly the 18 blocks (24 through 41) the draft
names as sharing K/V with blocks 22/23.

**Signing prerequisite (d): verify the runner image digest.**

```
docker image inspect mechinterp-runner:local --format '{{.Id}}'
docker image inspect mechinterp-runner:local --format '{{json .RepoDigests}}'
```

Result: `sha256:2471502c3110a96d4955b48eb58da41e96a90276d22c4d5f1eac2c99b60a2cf8`
both ways, matching the draft's pin char for char (read-only inspect; no
`docker run`, no pull, no build).

**Signing prerequisite (e): author + CPU-smoke every module.** Done this
entry's authoring pass, then made reproducible in the follow-up entry above
(`smoke_all.py`). Modules: `render_gemma.py`, `extract_anchor_gemma.py`,
`build_flavor_panels.py`, `flavor_probe_sweep.py`, `surface_residualization.py`,
`gate_adjudicator.py`, `kv_seam_paired_smoke.py`, `test_leg_b_selection_logic.py`.

**Judgment call flagged for lead review before sign-off (not resolved by any
committed pin):** `gates.yaml` `gg5_residualization_controls.checks.
outer_folds`/`inner_folds` (5/3) is not lifted from a prior registered pin --
none was on record at signing time for this exact fold structure. 5 matches
the probe protocol's own established `StratifiedKFold(5)` discipline
elsewhere in the program; 3 matches the draft's explicit "inner three-fold"
language. Recorded in `gates.yaml`'s `gg5_residualization_controls.derivation`
so it is not silently treated as inherited.

**Not run in this pass (explicitly out of scope, called out in AMENDMENT.md
and gates.yaml):** the live 32-row GG1 paired GPU smoke
(`kv_seam_paired_smoke.py --mode=live` correctly refuses without a GPU
runtime), the real ~15-16 GB pt weight download, and `build_flavor_panels.py`
`main()` against the real upstream `flavor-atlas-rawbase` panel shas (those
panels are gitignored and were not present in this fresh worktree checkout;
the reuse-and-verify MECHANISM itself, `verify_and_copy`, is exercised by
`smoke_all.py` against synthetic fixtures with self-computed shas instead).
No GPU verb, no `docker run`, and no weight download were issued anywhere in
either authoring pass.
