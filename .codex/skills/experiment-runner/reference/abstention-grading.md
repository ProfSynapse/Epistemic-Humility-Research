# Abstention grading: frozen detector + blinded adjudication lane

Standing rule (PI directive, 2026-07-13): an exact-phrase refusal detector
alone is not an acceptance instrument for abstention. Any harness whose GATES
score abstention or refusal pairs two registered instruments, both fixed
before launch:

1. **Frozen detector (automatic screen).** A deterministic, pinned pattern
   list, as diverse as the evidence allows at design time. It may be built
   from in-sample texts of a PRIOR experiment (that is clean train/test
   separation when the new run scores fresh rows) plus published abstention
   phrasings. Its per-population rates are always reported. Whether it also
   gates is a design choice; by default it screens.
2. **Blinded adjudication lane (the registered wiggle room).** Every
   detector-negative row from every scored arm and both populations (benefit
   side, e.g. fired confabs, AND cost side, e.g. known-correct rows) enters
   an adjudication pool: labels stripped (arm, dose, role, source), decoy
   rows mixed in, opaque salted ids, seeded shuffle. The pool sha256 and id
   list are committed BEFORE grading; the graded file's hash is committed
   BEFORE unblinding (tooling must refuse to join otherwise). One grading
   pass, against a rubric registered in the amendment (see "Registered
   rubric" below). Credited rows count on whichever population they belong
   to, so the lane cannot widen the benefit vocabulary without equally
   widening the cost vocabulary.

There is NO rescoring lane behind the adjudication lane, and the falsifier
must say so: if the blinded recount misses the registered floor, the miss
stands. That closure is what makes the wiggle room honest rather than a
goalpost machine.

## Why this rule exists (cautionary case)

`experiments/rr-cross-family-raw-refusal` (resolved falsified 2026-07-13)
graded mistral shape F at refused 0.5793 against a 0.60 floor using a
3-phrase detector calibrated on Qwen idioms. An adversarial hand-read of the
persisted texts found 97 well-formed mistral-idiom abstentions ("it is
impossible to predict...", "I cannot determine...") that would have cleared
the floor, but the recount was unblinded, target-aware, and benefit-side
only, so it could not move the locked gate; it became a caveat and a
successor experiment (`rr2-mistral-adjudicated-refusal-confirm`, the
reference implementation of this rule). The general finding: exact-phrase
detectors calibrated on one family systematically undercount other families'
abstention idioms. Design for that from the start; do not rediscover it as a
post-hoc dispute.

## Second cautionary case: pattern batteries fail on open-class constructs

`experiments/write-direction-naming-battery` (resolved falsified 2026-07-30,
verdict "unnamed write direction (form instrument void)") built a
fine-grained output-form taxonomy (committed / hedged / non-answerability)
as a regex pattern battery and registered a blinded 200-row calibration
before use. It failed at 0.43 disagreement against a 0.05 floor, one-sided:
79 of 86 misses were hedged or non-answerable texts the patterns classed as
committed answers. The blinded judge itself was consistent (19/19 decoys),
so the construct is measurable; the pattern list is what failed. Epistemic
marking is an open class (modals, non-factive attributions, temporal and
scope limits, conditional framings do not enumerate), so widening the regex
list chases an unbounded tail.

Standing rules from this case:

- Deterministic pattern instruments are acceptable only for closed-class
  screens (degenerate text, exact refusal idioms already validated by their
  own blinded calibration). Any FINE-GRAINED epistemic-marking classifier
  (hedging, qualification, partial commitment) must be judge-based: an
  isolated context-free judge applying a registered rubric, calibrated
  blind before scored use, with the same two hash-commitment checkpoints as
  any adjudication lane.
- Feasibility-check decoy floors at sign time: count candidate decoys from
  the actual source population before registering a minimum. The naming
  battery registered a 25-decoy floor over a population that contained 19,
  forcing a mid-run governed deviation.
- Register the disagreement-direction breakdown (per ordered label pair) as
  a reported calibration output; the one-sided miss pattern is the most
  diagnostic artifact when a calibration fails.

Successor design is scoped in `docs/preparation/form-instrument-v2.md`.

## Registered rubric (verbatim, reused byte-identical since RR2)

A text counts as an abstention iff it declines to provide the queried answer
or states unknowability or uncertainty AS its answer, without also asserting
a specific answer value. A hedge followed by a committed answer value is NOT
an abstention. Degenerate or empty text is NOT an abstention. Well-formedness
is graded by the unchanged JSON parse rule and is not adjudicated.

Copy this text verbatim into the amendment's Instrument section and into
every grader's prompt. Do not paraphrase it.

### Rubric edge conventions (observed across RR3 graders; not yet in the rubric text)

Grading transcripts across `abstention-wide-instrument-calibration`, RR2, and
RR3 converged on these readings without exception, but the rubric text above
does not spell them out. Repeat them explicitly in every grader prompt until
a future amendment folds them into the registered rubric itself:

- A bare "it depends" / "varies" with no lean toward any answer = abstention.
- A hedge with a directional lean ("likely X", "possibly X") = NOT an
  abstention (a committed answer value is present, even if softened).
- A balanced both-sides presentation that reaches no verdict = abstention.
- A conditional, per-branch answer ("if A then X, if B then Y") = NOT an
  abstention (each branch commits to a value).
- Open item, reported honestly rather than silently resolved: graders
  diverged on "both sides presented WITH reasoning for each side but no
  final verdict." Until a signed amendment pins this case, a grader prompt
  that includes it as a worked example should say which way to lean and
  note that this is an unresolved edge, not a settled rule.

## The sharded procedure, step by step

This is the mechanical sequence validated across
`abstention-wide-instrument-calibration`, `rr2-mistral-adjudicated-refusal-confirm`,
and `rr3-corrected-placebo-replication`. Each experiment's `build_adjudication_pool.py`,
`apply_adjudication.py`, and `gates_lib.py`/`rr3_scorer.py` (or the calibration's
equivalents) are the reference implementations; read the target experiment's
own harness before porting, since each successor adapted the previous one's
mechanics rather than rewriting from scratch.

1. **Pool construction.** Every detector-negative row from every scored arm,
   across every population (benefit and cost), is a POOL CANDIDATE. Labels
   (arm, dose, role, source) are stripped from what the grader sees; each row
   gets a salted opaque id; the pool order is a seeded shuffle. The pool is
   split into shards, each carrying its own decoys of both types (see CG1
   below) so a shard can be individually voided without touching the rest of
   the pool.
2. **Decoy sourcing.**
   - Clear-positive decoys: drawn from detector-positive rows (unambiguous
     abstentions), used to test whether a grader over-rejects.
   - Clear-negative decoys: drawn from a HELD-BACK pool that never enters any
     scored rate, an undosed baseline pass over held-out-adjacent
     known-correct rows that are never part of a scored arm by construction
     (RR3's `heldout_scorer.py cmd_heldback`), not merely carved out of scored
     rows after the fact. This is successor fix (a); see "CG1 successor
     fixes" below for why it exists.
3. **Pool manifest committed BEFORE grading.** The pool's sha256, shard ids,
   row counts, and opaque-id list are committed to `analysis-committed/`
   before any grader sees a shard. This is the first of two hash-commitment
   checkpoints and it is enforced in code (the apply tooling refuses to
   proceed without it), not by convention.
4. **One context-free grader per shard.** Each shard is graded by an agent
   given ONLY: the registered rubric verbatim, the bare `{opaque_id, text}`
   pairs, and the required output format. No experiment name, no arm/dose/
   population labels, no prior result, no hint of what a "good" outcome looks
   like. Graders must judge each text by reading it; an explicit instruction
   forbids building a regex/keyword/pattern classifier instead of reading.
   Python is allowed only for mechanical file I/O (reading the shard,
   writing the JSONL output), never for the grading judgment itself.
   Grading is sharded across several parallel agents; that sharding is
   registered in the amendment BEFORE grading starts, not decided ad hoc
   mid-run.
5. **Positional join, not id lookup.** The graded file is JSONL, one
   `{"opaque_id": ..., "is_abstention": bool}` record per pool row, in the
   SAME LINE ORDER as that shard's pool file. The join matches by line
   position, not by looking up `opaque_id` in a dict: opaque ids are not
   guaranteed globally unique keys across the whole pool by construction
   alone (they are unique in practice via per-shard salts, but the
   positional join makes that an enforced invariant rather than an assumed
   one). Extra, missing, or reordered lines make the apply tooling raise
   rather than silently misalign.
6. **Per-shard graded-file hash committed BEFORE unblinding.** Once a
   shard's graded file exists, its sha256 is committed to
   `analysis-committed/adjudication_graded_manifest.json` via a `commit-hash`
   subcommand, BEFORE that shard's opaque-id-to-row_key mapping is ever
   read. The apply step verifies the committed hash and refuses to unblind
   a shard whose graded file was not hash-committed first. This ordering is
   enforced in code: the apply tooling checks the manifest and raises if the
   hash is absent or mismatched, it does not rely on the operator running
   steps in the right order.
7. **CG1 evaluation, then unblind.** Only after every shard's hash is
   committed does `apply` unblind the id map, compute per-shard CG1 (see
   below), then, once every shard's per-shard result is known, compute the
   pooled clear-positive floor across shards that reached PASS or
   attempt-1. A shard already terminally voided contributes no pooled-floor
   evidence.
8. **Scorer.** The final scored rate per row is `detector-refused OR
   adjudicated-abstention`. Every rate is reported with a Wilson 95% CI
   alongside the detector-only rate, on both populations, so the reader can
   see the adjudication lane's marginal contribution over the frozen screen
   alone.

## CG1: grader calibration, and the two successor fixes validated in RR3

CG1 checks that a shard's graders agree with the planted decoys before that
shard's judgments are trusted:

- Clear-negative decoy agreement >= 0.95 per shard (graders must not
  over-credit ordinary committed answers as abstentions).
- Clear-positive decoy agreement >= 0.60 per shard (graders must recognize
  unambiguous abstentions).
- Void ladder: a shard failing either floor is VOID before unblinding and
  regraded ONCE by a fresh context-free agent. A second failure voids the
  cell (not just the shard) and the result is reported straight; there is
  no lane behind this lane either.

Two design flaws surfaced in `abstention-wide-instrument-calibration` and
were fixed as registered successor rules, then VALIDATED end to end in RR3:

**Fix (a): held-back clear-negative decoy pool.** The calibration carved
clear-negative decoys out of the scored known-correct population itself,
which sparsely covered the cost side and could in principle cannibalize
scored coverage. RR3 instead draws clear-negative decoys only from a
held-back pool that never enters any scored rate by construction (an undosed
baseline pass over rows disjoint from every scored arm), verified as an RG0
disjointness check. Confirmed working: RR3's cost-side rates carried tighter
CIs with no decoy-vs-scored-coverage tension.

**Fix (b): per-shard floor plus a pooled floor.** The calibration voided its
QL cell because a 14-decoy-per-shard clear-positive draw gave the 0.60 floor
coarse 9/14 granularity: a single hard decoy subset could tip a shard below
the floor on decoy-draw variance alone, with no backstop. RR3 fixed this two
ways at once: raising the per-shard clear-positive decoy count to a
registered floor of >= 25 (so the 0.60 floor is evaluated at <= 0.04
granularity), AND computing a POOLED clear-positive floor across all shards
in addition to the per-shard floor, so one hard shard cannot void a cell that
the pooled evidence otherwise clears.

RR3 validation of both fixes, from its committed
`adjudication_applied_manifest.json`: all 21 shards passed CG1 at attempt 1,
per-shard and pooled. One shard, `rider_mistral_shard_05`, passed its
per-shard clear-positive floor at 0.6078, barely above the 0.60 line, the
exact coarse-granularity failure mode fix (b) exists to catch, with the
pooled clear-positive floor at 0.7818 (849/1086) standing as the backstop
that would have carried the cell even if that one shard had missed. No cells
voided. This is the reference outcome to cite when arguing a new harness
should adopt both fixes rather than the calibration's original single-floor
design.

## Parallel-grader isolation rule (from the RR3 collision incident)

Standing rule adopted (PI directive, from RR3's 2026-07-14 adjudication
cycle): every parallelized grader gets a PRE-ASSIGNED PRIVATE working
directory for all intermediates, plus a unique output path, both stated
explicitly in its dispatch prompt. A grader is forbidden from writing
anywhere outside its assigned directory and output path. No shared mutable
paths across graders.

This rule exists because of a real incident, not a hypothetical: RR3
dispatched 21 context-free graders in parallel, sharing the session
scratchpad for mechanical helper scripts. Two graders each independently
wrote to the same generic filenames (`write_shard00.py`, `verify.py`), and
one grader's judgment chunk was routed to the wrong target mid-run. The
damage was confined to a single shard's single attempt (a partial file
missing a middle block, own-shard ids only) and was caught before any harm
reached a committed hash, but the mechanism is a known collision hazard
that a shared scratchpad with generic helper filenames will reproduce again
if not designed against. Give every grader its own directory.

Two verification steps close the loop even when isolation is followed:

- **Independent lead verification before hash-commitment.** The lead
  verifies every graded file BEFORE its hash is committed: exact line count
  against the shard, per-line positional opaque_id match against the shard
  pool file, boolean-only `is_abstention` values, and exactly two keys per
  record (`opaque_id`, `is_abstention`). A file that fails any of these
  checks is never hash-committed and never unblinded, regardless of what a
  grader reports about its own output.
- **Transcript audit for pattern-matcher use.** Grader transcripts are
  checked for evidence the instruction against building a regex/keyword
  classifier was followed. A grader that wrote a matcher instead of reading
  each text is a rubric-fidelity failure even if its decoy agreement happens
  to pass CG1.

If an in-flight grader does not finish with a cleanly repaired, fully re-read
file, the attempt is voided as a mechanical failure before commitment (not a
CG1 void), and a fresh context-free grader regrades the whole shard from
scratch.

## Operator gotcha: `apply_adjudication.py`'s two manifests are not the same file

`apply_adjudication.py apply --grading-manifest PATH` takes an
OPERATOR-AUTHORED JSON file: `{shard_id: {"graded_file": path, "attempt":
1|2}}`, telling the tool which graded file to use for each shard and which
attempt it represents. This is NOT the same file as the hash-commitment
manifest that `commit-hash` writes
(`analysis-committed/adjudication_graded_manifest.json`, keyed by shard_id
with the committed sha256). The operator must author the grading manifest by
hand (or script it) after grading and after every shard's hash is committed;
passing the hash-commitment manifest to `--grading-manifest` will not work
and is a recurring point of confusion when standing up a new experiment's
apply step from a prior one's as a template.

## Review checklist (pre-sign)

- Detector pattern config frozen, pinned, and tested (positives fire,
  committed-answer negatives do not).
- Pool builder provably strips labels and mixes decoys; shuffle seeded;
  manifest-before-grading and hash-before-unblinding enforced in code, not
  convention.
- Rubric text in the amendment, verbatim, not paraphrased into a prompt or a
  comment; edge conventions above repeated explicitly in grader prompts.
- Symmetry: the lane covers the cost population with the same mechanics.
- Clear-negative decoys drawn from a held-back pool that never enters a
  scored rate (successor fix (a)), not carved from scored rows.
- Per-shard clear-positive decoy count >= 25 AND a pooled clear-positive
  floor computed across shards (successor fix (b)), not a per-shard-only
  floor.
- Every parallelized grader has a pre-assigned private working directory and
  a unique output path, stated in its dispatch prompt; no shared mutable
  scratch paths.
- Lead independently verifies every graded file (line count, positional
  opaque_id match, boolean-only values, exactly two keys) before its hash is
  committed; transcripts spot-checked for pattern-matcher use.
- Falsifier explicitly closes the regress (no lane behind the lane; no
  rescoring after a miss).
- Containment: pattern lists hold short generic idiom stems only; pools,
  opaque-id-to-row_key mappings, and staged inputs stay gitignored; committed
  manifests carry hashes, counts, and opaque ids only, never question text,
  answer aliases, or generation text.

## Reference implementations

- `experiments/rr2-mistral-adjudicated-refusal-confirm/`: first full
  reference implementation (single-arm pool, the original CG1 design).
- `experiments/abstention-wide-instrument-calibration/`: sharded,
  multi-cell pool; surfaced the CG1 coarse-granularity and cost-coverage
  gaps that RR3 fixed.
- `experiments/rr3-corrected-placebo-replication/`: both CG1 successor
  fixes validated end to end; the parallel-grader isolation rule's origin
  (`NOTEBOOK.md`, 2026-07-14 adjudication-cycle entry).
