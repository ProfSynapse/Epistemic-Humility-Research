# Handoff: jspace-layer-replication-qwen3-4b

Status as of 2026-07-08T20:46Z.

## Current State

- PR #256 was merged to `main` as `253dfc27`:
  `Scaffold J-space layer replication`.
- Local canonical `main` was fast-forwarded to `253dfc27`.
- Active scanner worktree:
  `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication`
- Experiment:
  `experiments/j-space-layer-contrast-replication-qwen3-4b`
- Exhaustive census command completed:
  `python3 experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py --scan-all-candidates`
- Output log:
  `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_scan_all.log`
- Private checkpoint files:
  `analysis/fresh_pool_generations.jsonl` and `analysis/fresh_eval_rows.jsonl`

## Latest Persisted Counts

Final census:

- generated rows: 12,923
- generated unknown rows: 3,305
- generated known rows: 9,618
- selected confab rows: 306
- selected known_correct_answered rows: 1,957
- G0 confab floor: cleared (`>=200`)
- G0 known-correct floor: cleared (`>=300`)

Public-safe HF dataset:

- Repo: `professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`
- Revision: `3add102ce930f73a29013f572f03e7325da30825`
- URL: `https://huggingface.co/datasets/professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b`
- Boundary: ID/provenance/role/behavior flags only. No raw question text,
  aliases, prompt text, generation text, hidden states, or intervention outputs.

## Resume Commands

Check final private and public-safe artifacts:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
wc -l experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_generations.jsonl \
      experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_eval_rows.jsonl \
      experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path('experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_eval_rows.jsonl')
counts = {}
for line in p.open(encoding='utf-8'):
    if line.strip():
        r = json.loads(line)
        counts[r.get('role')] = counts.get(r.get('role'), 0) + 1
print(counts)
PY
rg -n "\\[mine-fresh\\] (unknown|known) scanned|wrote selected|ERROR" \
  experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_scan_all.log | tail -n 20
```

Rebuild the public-safe manifest if needed:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
python3 experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py \
  --scan-all-candidates \
  --manifest-only
```

## Next Steps

Prep completed after the HF release:

- Fresh anchor extraction: completed for all 2,263 selected rows at
  hs23/26/29/34.
- Smoke summary: `analysis/smoke_summary.json`
- Smoke result: `g0_smoke_pass=true`
- Readback means: hs23=24.9998, hs26=74.9788, hs29=125.0104, hs34=174.9906.
- Dosed-row collapse: 0.0 for every layer.

Next steps:

1. PR and merge the prep checkpoint docs.
2. Record the user's prediction in the amendment scoreboard.
3. Run `bin/exp sign j-space-layer-contrast-replication-qwen3-4b`.
4. Launch the full layer contrast locally:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
python3 experiments/j-space-layer-contrast-replication-qwen3-4b/run_contrast.py \
  --mode full \
  --i-know-this-is-the-fresh-replication-run
```
