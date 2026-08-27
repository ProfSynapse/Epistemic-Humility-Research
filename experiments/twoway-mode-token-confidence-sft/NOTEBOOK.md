# Two-Way Native Mode Token plus Answer-Confidence SFT notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-24 (design draft, unsigned). Scaffolded as the lead+user adjudicated
  successor (option 2) to the falsified `fresh-sft-epistemic-mode-token-grpo`
  Stage-S: two-way native mode token (<ANSWER>/<ABSTAIN>) + gated
  answer_confidence scalar, QUALIFY demoted to a product-layer rendering rule.
  QUALIFY-mapping decision = option (ii): fold the middle band into ANSWER at the
  existing k<=10 Clopper-Pearson ABSTAIN boundary (no new constant). Builder is
  relabel-in-place over the frozen Stage-S split (held-out never opened). Config
  drafts + gate table written; `.py` modules deferred to CODE. `bin/exp validate`
  exits 0 (short-run wall-clock warnings are expected; measured in CODE). No sign,
  no commit, no GPU. Held-out sealed: 0 rows accessed. k-histogram of the frozen
  QUALIFY band computed from train/dev only (train 520 k11-16 / 380 k17-21 / 37
  k>=22-greedy-wrong; dev 97 / 101 / 2).
