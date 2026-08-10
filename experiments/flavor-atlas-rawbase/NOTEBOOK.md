# Flavor atlas: per-flavor known-unknown activations on the raw base notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

### 2026-08-10T00:20Z REGISTRATION and harness smoke

Cell scaffolded, AMENDMENT/gates/cell/recipes drafted by the lead, panel
builder and probe sweep built by a delegated harness agent, then signed
(10 pins). All bands and gate constants were fixed before any GPU verb.
Harness smoke (CPU only): build_flavor_panels.py FG0 PASS with every
count matching gates.yaml exactly (kuq 5540 = 3071 + 2469 with the six
locked flavor counts; ambigqa 2748 = 1245 + 1503; selfaware 3369 = 2337
+ 1032; both source shas exact); flavor_probe_sweep.py smoke against the
existing rawbase-ambigqa-boundary-readout L35 extraction reproduced the
committed 0.6338 (std 0.0104) exactly to 4dp. Deviations accepted by the
lead: deterministic row_key schemes (kuq-{index:06d} over the
sha-pinned file order; selfaware-{question_id}, verified unique), and a
per-layer whole-panel load with in-memory flavor slicing instead of
per-flavor reloads (I/O only, verified numerically identical on the
smoke value).

### 2026-08-10T00:22Z LAUNCH: shape smoke then three extractions

PI directive of 2026-08-09 ("see if we can find actual activations based
on other known unknown flavors") covers this cell's registration and its
local GPU budget (three forward-only extractions, about 11657 rows,
roughly 50 to 70 minutes total on the local 3090). All runs inside the
pinned mechinterp-runner image (experiment.yaml
instrument.runtime_image_digest, sha256:2471502c...) with the digest
verified char for char before each docker verb; one GPU job at a time;
provenance JSON line required in each run log (gates.yaml fg2).

Order of verbs: (1) a 4-row all-layer SHAPE SMOKE using an unpinned
throwaway recipe under analysis/ (instrument verification only, no M
reading; verifies that omitting `layers` captures all 37 hidden states
before the long runs); (2) extract_ambigqa_alllayers.yaml; (3)
extract_kuq.yaml; (4) extract_selfaware.yaml. Model args for every verb:
--model unsloth/Qwen3-4B --model-revision
64033659d5caf1b8ed7f929b29de705e93a4d468, no adapter.

Nothing in this entry is a result.

2026-08-10T00:30Z shape smoke result: 4/4 rows, manifest layers "all",
n_hidden_states 37, per-row anchor file carries 37 keys L0..L36 each
(1, 2560) float32. Instrument verified; production extractions launched
in registered order (ambigqa, kuq, selfaware), sequential, logs captured
per run under analysis/extraction/.

2026-08-10T00:35Z infrastructure note: the first chain attempt aborted
before any docker verb ran (the shape-smoke run had left
analysis/extraction/ root-owned, so the shell could not create the run
log). Fixed with the documented throwaway-container chmod remedy;
chain relaunched, first container up with the provenance line in its
log. No GPU work lost, no result touched.

2026-08-10T01:05Z instrument fix before any M reading: the production
sweep crashed at startup because discover_layers assumed
manifest["layers"] is a list of ints, while all-layer extraction
manifests record the string "all" (the harness smoke could not catch
this: the only existing extraction then had layers [35]). Patched to
map "all" to range(n_hidden_states) and fail closed on anything else;
flavor_probe_sweep.py repinned. No AUROC had been computed when the
crash occurred; no band, threshold, or protocol constant was touched.

### 2026-08-10T01:55Z RESULT and gate adjudication

Sweep completed (pinned protocol, fold seeds fixed; counts-only JSON at
analysis-committed/atlas_sweep.json). fg0 re-verify PASS inside the
sweep; FG1 and FG2 were adjudicated PASS at extraction time (manifests
2748/5540/3369 exact, 37 hidden states each, provenance line with the
pinned digest in all three run logs).

M1, KUQ flavors vs the 3071-row KUQ known pool (best layer, best OOF
AUROC; value at L35 in parentheses):

- ambiguous          n=411  best L26 0.9800 (L35 0.9766)
- controversial      n=490  best L20 0.9960 (L35 0.9949)
- counterfactual     n=403  best L19 0.9963 (L35 0.9952)
- false assumption   n=368  best L29 0.9918 (L35 0.9912)
- future unknown     n=490  best L17 0.9994 (L35 0.9990)
- unsolved problem   n=307  best L28 0.9937 (L35 0.9915)
- pooled all unknowns n=2469 best L27 0.9887 (L35 0.9874)

M2, AmbigQA: best L25 0.6590 (L35 0.6338, matching the resolved
rawbase-ambigqa-boundary-readout value exactly). Below 0.75 at every
one of the 37 layers.

M3, SelfAware reference: best L25 0.9937 (L35 0.9925).

M4, transfer matrix at source-best layers: every pair among {six KUQ
flavors, SelfAware} transfers at 0.8331 to 0.9996 (min is unsolved
problem probe on ambiguous). Every probe fails INTO AmbigQA (0.4878 to
0.5746) and the AmbigQA-trained probe fails everywhere else (0.4332 to
0.5853).

Adjudication against the bands fixed at signing:

- P1 SUPPORTED: future unknown 0.9994 and unsolved problem 0.9937 both
  clear the 0.90 discovery floor.
- P2 FAILED as registered: KUQ ambiguous reaches 0.9800, far above the
  0.75 ceiling (the AmbigQA half of P2 held: 0.6590 max).
- F1 (universal code) DOES NOT FIRE: AmbigQA never reaches 0.90 and
  transfers into it sit near chance.
- F2 (dataset-specific) DOES NOT FIRE: every KUQ flavor clears 0.75.
- Registered consequence: MIXED ATLAS, reported descriptively.

Descriptive reading (exploratory, not a claim): the pretrained base
carries a broad, freely transferring unanswerability code covering all
six KUQ flavors AND SelfAware, including overtly ambiguous KUQ
questions. What it cannot read, at any layer, is AmbigQA: naturally
occurring questions whose ambiguity is covert. The operative boundary
looks like overt vs covert unanswerability, not flavor vs flavor. This
REFINES the resolved rawbase-ambigqa-boundary-readout verdict: the
signal is not narrowly "SelfAware-flavored"; it is broad across overt
flavors, and AmbigQA fails because nothing on the question's surface
marks it as unanswerable.

Registered caveat (stated before any confirmatory use): KUQ and
SelfAware unknowns are stylistically distinctive question types, so
within-dataset known-vs-unknown probes may partly ride surface style;
cross-dataset transfer (KUQ probes reading SelfAware at 0.91 to 0.98
and vice versa) argues against a pure dataset artifact but does not
eliminate style as a shared carrier. A style-controlled confirmatory
cell (matched surface form, flavor varied) is the natural follow-up and
must be registered before any promotion of this atlas to a claim.

Proposed verdict one-liner (resolve stamp awaits PI approval):
"Mixed atlas as registered: P1 supported (every KUQ flavor including
overt ambiguity separates at 0.98 to 0.999 with free cross-transfer to
SelfAware), P2 failed (only the AmbigQA half held), neither falsifier
fired; the pretrained unanswerability code is broad across overt
flavors and the boundary is overt vs covert unanswerability, with
AmbigQA unreadable at every layer."
