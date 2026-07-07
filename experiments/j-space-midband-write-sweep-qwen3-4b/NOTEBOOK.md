# j-space-midband-write-sweep-qwen3-4b notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-07 - signed, prelaunch

Scaffolded and signed the exploratory layer-site amendment. Direct predecessor
is `doubt-gated-caution-tighten`, whose governed outcome passed G1/G2/G3 on
bf16 raw-base Qwen3-4B and established the key mechanism lesson: the caution
write is not selective by itself; selectivity comes from the doubt gate deciding
which rows receive the fixed snap.

This experiment holds that mechanism fixed and sweeps the refit/write layer:
hs23, hs26, and hs29 as the J-space mid-band candidates, with hs34 as the late
predecessor-reference site. The promoted common split manifest is ID-only; row
text, aliases, activations, and generations remain local/gitignored.

Status after signing: instrument pinned in `experiment.yaml`, registry
regenerated, and validation passed. No GPU run has been launched yet.
