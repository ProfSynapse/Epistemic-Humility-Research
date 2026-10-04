# Decision-model calibrated choice notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-10-04: draft scaffolded, engine pinned, Stage 0 added (drafting agent)

- Scaffolded with `bin/exp new` (type `eval`) in worktree
  `.worktrees/amendment-decision-model-calibrated-choice`, branched from
  `origin/main` at `e1a0bdf84`.
- `synaptic-tuner` gitlink moved from `6b01834b` (no `decision` method) to
  `26cb57c72c68c382cf9299096bce535d4a606929` (branch
  `jev-models-tuner-training-b55d92`, pushed). `31962293` adds the decision
  method, `26cb57c7` the confidence analysis. Verified
  `Trainers/decision/analyze_confidence.py` and
  `Trainers/decision/configs/experiments/confidence_analysis_{pointer,letter_logits}.yaml`
  exist at that commit. Interim pin; see AMENDMENT "Lane, runtime and engine
  pin".
- Stage 0 (base-model KU extraction -> probe-fit -> freeze) added at the PI's
  request through the coordinator. It is kept inside this amendment; the tier
  reasoning is in AMENDMENT "Stage 0".

### 2026-10-04: pre-sign feasibility probe (no model, no labels, no outcome)

Required by amendment-vs-lab-notebook.md ("every arm must be constructible
from real data"). Run on the HF-cached PopQA file only.

- Source: `akariasai/PopQA` @ `098765c79ea10a2cb19c828324e33281b8336ec0`,
  `test.tsv`, sha256 `9a5227f41bff0e4c331d4a774d946b12f95307892b58f860a9606ef356e6089b`.
- Rows: 14,267, ids unique. Fields present: id, subj, prop, obj,
  possible_answers, s_pop, question (plus aliases, URIs and o_pop). No row
  is missing a needed field.
- Every row has at least one alias that survives EH `normalize_answer`.
- Distractor feasibility: all 14,267 rows have >= 3 same-relation objects
  whose normalized text matches no gold alias.
- Relations (rows / distinct objects): director 1999/1521, screenwriter
  1999/1468, genre 1619/283, producer 1520/1133, author 1514/1158, composer
  978/624, country 838/107, capital 645/584, place of birth 584/434, father
  570/524, sport 547/49, occupation 532/84, capital of 363/356, religion
  338/70, mother 187/173, color 34/5.
- Pointer checkpoint
  `decision-qwen35-2b-pointer/20261004_122756/final_model`: tree sha256
  (bin/exp algorithm) `e0cc616de238cfad85a8627aaa47583dba7689ece63c9bedc4c63a6e9a4acbfc`.
  Files: adapter_model.safetensors `7d66a8a9d34f85eb3661b458598ed85e727a6748a4831effec83a820d3770ab6`,
  readout_head.safetensors `d7d979817375367ccec4bf09bfa54e2ffbea07872958b7462e328608c0857989`,
  decision_config.json `7cd67f757c189a44e0f00eecbb4e599519a8dc43ac74d3e57861e30094ad247e`
  (readout pointer, base revision b1485b2f, LoRA r16/alpha 32, max_length 4096).
- Base chat template (`final_model/chat_template.jinja`, copied from the base
  tokenizer): lines 149-152 implement `enable_thinking`. When it is off they
  render an empty `<think>\n\n</think>\n\n` marker, which probe.py's
  `assert_no_think_scaffolding` accepts. Read only; nothing rendered or
  generated.
- Harness split port: on 3,000 synthetic rows (no PopQA content), the
  harness's `engine_split` gave FIT/CAL/TEST lists identical, element for
  element, to the engine's `split_fit_cal_test` at `26cb57c7`. The helpers
  `auroc` / `wilson` / `three_way` returned the expected values on toy inputs
  (Wilson upper at 0/35 is 0.0989 and at 0/73 is 0.04999, matching the
  gates.yaml floor derivation).

### Pending before sign

See AMENDMENT "Pre-sign checklist". The coordinator owns the engine
capability request (per-row TEST states, `probs_r1`, `ku_probe_score`).
