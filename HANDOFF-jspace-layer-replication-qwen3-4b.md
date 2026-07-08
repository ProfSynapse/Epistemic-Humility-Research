# Handoff: jspace-layer-replication-qwen3-4b

Status as of 2026-07-08T17:58Z.

## Current State

- PR #256 was merged to `main` as `253dfc27`:
  `Scaffold J-space layer replication`.
- Local canonical `main` was fast-forwarded to `253dfc27`.
- Active scanner worktree:
  `/home/profsynapse/code/ehr-worktrees/jspace-layer-replication`
- Experiment:
  `experiments/j-space-layer-contrast-replication-qwen3-4b`
- Active command:
  `python3 experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py --scan-all-candidates`
- Output log:
  `experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_scan_all.log`
- Private checkpoint files:
  `analysis/fresh_pool_generations.jsonl` and `analysis/fresh_eval_rows.jsonl`

## Latest Persisted Counts

At the latest checkpoint:

- generated rows: 3,730
- selected confab rows: 306
- selected known_correct_answered rows: 37
- G0 confab floor: cleared (`>=200`)
- G0 known-correct floor: still running (`37/300`)

The scanner is checkpointed every 25 generated rows. If it stops, rerun the same
command from the active scanner worktree; it reuses `fresh_pool_generations.jsonl`.

## Resume Commands

Check scanner:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
pgrep -af 'mine_fresh_eval_pool.py|fresh_pool_scan_all' || true
wc -l experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_generations.jsonl \
      experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_eval_rows.jsonl
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

Restart scanner if needed:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
python3 experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py \
  --scan-all-candidates \
  > experiments/j-space-layer-contrast-replication-qwen3-4b/analysis/fresh_pool_scan_all.log 2>&1
```

After scan completion, rebuild the public-safe manifest with the current script:

```bash
cd /home/profsynapse/code/ehr-worktrees/jspace-layer-replication
python3 experiments/j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py \
  --scan-all-candidates \
  --manifest-only
```

## Next Steps

1. Let exhaustive census complete.
2. Upload public-safe dataset to Hugging Face: ID/provenance/behavior flags only,
   no question text, aliases, prompt text, or generation text.
3. Record HF repo URL and revision in docs/session/TODO.
4. PR and merge that publication record.
5. Record user prediction, sign the amendment, extract fresh anchors, smoke, and
   launch the full layer contrast locally.
