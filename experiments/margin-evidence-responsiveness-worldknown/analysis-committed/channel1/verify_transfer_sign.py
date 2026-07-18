#!/usr/bin/env python3
"""CPU-only, read-only re-derivation of channel1 confab-vs-correct AUROC for the
transfer and native directions from the committed per_row_projections.jsonl.
Verifies the reported floor_inputs.json numbers. No writes to evidence."""
import json, sys

PATH = "experiments/margin-evidence-responsiveness-worldknown/analysis-committed/channel1/per_row_projections.jsonl"

def auroc(pos, neg):
    # rank-based Mann-Whitney AUROC with tie handling
    data = sorted([(v,1) for v in pos] + [(v,0) for v in neg])
    # assign average ranks
    ranks = [0.0]*len(data)
    i=0
    while i < len(data):
        j=i
        while j+1 < len(data) and data[j+1][0]==data[i][0]:
            j+=1
        avg = (i+j)/2.0 + 1.0  # 1-based avg rank
        for k in range(i,j+1):
            ranks[k]=avg
        i=j+1
    rank_pos = sum(r for r,(_,lab) in zip(ranks,data) if lab==1)
    n_pos=len(pos); n_neg=len(neg)
    return (rank_pos - n_pos*(n_pos+1)/2.0)/(n_pos*n_neg)

rows=[json.loads(l) for l in open(PATH)]
confab=[r for r in rows if r['role']=='confab']
correct=[r for r in rows if r['role']=='correct_on_answerable']

for d in ['transfer','native']:
    key=f"no_answer_baseline__{d}_z"
    pos=[r[key] for r in confab]
    neg=[r[key] for r in correct]
    a=auroc(pos,neg)
    print(f"{d}: AUROC(confab>correct)={a:.10f}  n_pos={len(pos)} n_neg={len(neg)}")
    print(f"    1-AUROC = {1-a:.10f}")
    # raw-direction check: median of z, and whether confab z > correct z
    import statistics
    print(f"    median confab_z={statistics.median(pos):.6f}  median correct_z={statistics.median(neg):.6f}")
