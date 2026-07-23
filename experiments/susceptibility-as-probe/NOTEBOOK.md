# Susceptibility as probe: margin vs readout vs verbalized confidence notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-17 -- Build + run: S1 sanity gate HALT (registered stop), diagnosis recorded

Full arc executed by the build agent: config pins verified (cell d361224f,
gates a19da59d), SC0 staging with local copies and in-code leakage recheck
(0 row_key intersection, 760 vs 1308 FIT rows), SC1 preflight smokes PASS
with code-enforced marker, full hs20 capture 760/760 zero drops, full
elicitation 760/760 completions.

Gate events, in registered order:

- SC2 elicitation integrity: parse rate 0.7684 (584/760) vs floor 0.95.
  The confidence channel is VOID per the registered consequence (reported
  straight, other channels unaffected). Failure mode is model format
  non-compliance in the confidence line (e.g. truncated "CONFIDEN"),
  observed already in the smoke (6/8). Unregistered implementation choice
  flagged by the builder: max_new_tokens=64 for elicitation (cell.yaml
  names no token budget); noted here, not changed post-hoc.
- S1 readout sanity, checked FIRST as registered: AUROC of the raw
  as-pinned z-projection (confab positive) = 0.0179 [0.0100, 0.0270] vs
  floor 0.80. HALT per on_failure, before any criterion quantity (P1
  incremental, paired differences, susceptibility/confidence AUROCs) was
  computed.

Diagnosis (builder, verified by hand at the row level): c_hat is fit
upstream as unit(mean(unknown_refused) - mean(confab)), so a HIGHER
projection means LESS confab-like; the lineage's own committed score
convention is negative z (the build_manifest field is literally
auc_neg_z_d_on_fit), and M2's susceptibility channel was explicitly
registered as negative tipping dose for the same confab-positive
orientation, but cell.yaml's readout entry omitted the analogous sign
instruction. Diagnostic-only readout with the sign corrected: AUROC 0.9821
[0.9730, 0.9900], which would clear the floor comfortably. The gate was
NOT passed using the flipped orientation; the halt stands pending
adjudication.

Drafting error also found during diagnosis: Decision record item 5
anchored the 0.80 sanity floor to committed auc 0.9929 citing it as
c_hat's FIT discrimination; that committed number belongs to the u_d
(doubt) direction, not c_hat, whose own discriminative AUC was never
computed in any prior amendment. The floor value itself is unaffected.

Criterion-relevant observation for the adjudication: every registered
criterion is sign-invariant or sign-agnostic (P1's logistic combiner
learns coefficient signs; paired AUROC comparisons use each channel in its
confab-positive orientation), so the sign convention determines only
whether the sanity gate reads the instrument as wired or inverted; it
cannot move any predictor's registered call. Adjudication lifted to the
PI: resolve as instrument-void, or issue a signed pre-analysis
clarification amendment (readout score = negative z-projection, matching
the lineage convention) with repin and rerun analysis on the unchanged
capture/elicitation artifacts.

## 2026-07-17 -- PI-approved sign clarification, repin, analysis rerun authorized

The PI selected the signed-clarification path (option presented with the
S1 halt): cell.yaml readout score amended to NEGATIVE z-projection
(confab-positive orientation, the lineage's own committed neg_z
convention), Decision record item 5 citation corrected (0.9929 belongs to
u_d, not c_hat; floor unchanged), cell.yaml repinned via bin/exp repin
with reason recorded in instrument.repins. No criterion quantity was
computed before the repin; analysis.py now reruns against the unchanged
capture and elicitation artifacts. The SC2 confidence-channel void stands
as registered (parse 0.7684 vs floor 0.95).

## 2026-07-17 -- Analysis rerun under the repinned convention; lead verification and adjudication

Analysis rerun on the unchanged capture/elicitation artifacts under the
PI-approved sign clarification (results
analysis/results/m2_results.json, sha256 e423207e...). Lead verification:
all headline quantities reproduced independently with a different
implementation (sklearn LogisticRegression + StratifiedKFold vs the
harness stats machinery): readout 0.982062, margin 0.850441, combo
0.997396, incremental 0.0153 against the raw readout baseline and 0.0161
against a cross-fitted readout-only baseline. Both constructions fall
below the 0.02 floor, so the P1 verdict is robust to that convention
choice. Given the end-to-end independent reproduction and the absence of
any verdict-flipping definitional fork (sign convention settled
pre-analysis by the signed repin), no separate red-team pass was
commissioned; this entry records that decision.

Gate results (registered order):
- S1 readout sanity: PASS, 0.9821 [0.9730, 0.9900] vs floor 0.80.
- SC2: FAIL as previously recorded (parse 0.7684 vs 0.95); confidence
  channel VOID for criterion use. Descriptive only: confidence AUROC
  0.1479 [0.1214, 0.1754] on the 584 parseable rows, i.e. strongly
  ANTI-predictive (the model verbalizes higher confidence on rows it
  confabulates); striking descriptive finding, not a criterion.
- SC3: complete coverage (760/760 susceptibility and readout; 584
  confidence; pairwise sets enumerated).

Criterion adjudication (lead):
- P1 complementarity: FAIL. Incremental AUROC 0.0154 [0.0081, 0.0237] vs
  floor 0.02. The increment is statistically nonzero (CI excludes zero)
  but below the registered practical floor; the redundancy falsifier
  fires as registered, no goalpost moves.
- P2 head-to-heads: readout beats margin, paired diff -0.1316 [-0.1588,
  -0.1045], CI excludes zero. Margin-vs-confidence and
  readout-vs-confidence resolve for the internal channels but are
  descriptive given the SC2 void.
- Descriptive: susceptibility AUROC 0.8504 [0.8252, 0.8749];
  censored-excluded sensitivity 0.7242 [0.6446, 0.7988] (much of the
  margin's discrimination rides on the censoring structure).

Predictions scoreboard adjudication:
- Complementarity (differentiator): actual FAIL. Orchestrator (FAIL,
  redundant) RIGHT; PI (PASS, complementary) WRONG.
- Margin vs readout: readout wins; both predictors right.
- Internal channels vs verbalized confidence: VOID (SC2), not scored for
  either predictor.
- Orchestrator bands: margin 0.78-0.90 HIT (0.8504); readout 0.90-0.97
  MISS high (0.9821); incremental 0.000-0.015 MISS high by 0.0004
  (0.0154); confidence band void.

Resolution: status falsified (the registered prediction required the
incremental floor and the confidence leg; the primary redundancy
falsifier fired). Claim 3's dissociation reading is rejected at the qwen
mid-band operating point at the registered floor: the projection already
carries nearly everything the margin knows about confab-vs-known here,
though the margin's increment is statistically real and the channels are
not literally identical. Implications recorded for the cascade: M4's
naming test proceeds unchanged (it tests evidence-responsiveness, not
channel redundancy); M5's training bridge should treat the margin
instrument as mechanistically meaningful (M1 retrodiction) but not as an
independent detector over the readout at this operating point.
