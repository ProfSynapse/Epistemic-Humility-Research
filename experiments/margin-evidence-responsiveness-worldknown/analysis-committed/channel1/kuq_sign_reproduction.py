#!/usr/bin/env python3
"""CPU-only, read-only reproduction of the transfer c_hat's KUQ confab-vs-correct
AUROC using THIS harness's exact projection+score convention:
    raw_proj = dot(h - mu, vector)   [mu is the c_hat zero-vector -> dot(h,vector)]
    z_transfer = READOUT_SIGN * (raw_proj - TRANSFER_MU_C) / TRANSFER_SIGMA_C
with READOUT_SIGN=-1.0, TRANSFER_MU_C=-4.031343053353048, SIGMA=1.576023489724997.
Hidden states from the snap experiment's own committed FIT capture. No GPU, no model.

Provenance: written by an independently lead-dispatched sign-check analyst
during M4-WK final analysis (2026-07-18), originally left at the lead's
scratchpad path (not under version control there, which is why the M4-WK
build agent's worktree/scratchpad search for it came up empty -- red-team
item m-4). Copied here verbatim by the M4-WK build agent after independently
re-running it against the same on-disk inputs and confirming it reproduces
AUROC=0.986650 (see kuq_sign_reproduction.json alongside this file for the
full result + input hashes). Not modified from the original except this
provenance header comment.
"""
import json
import numpy as np
from safetensors import safe_open

ROOT = "/home/profsynapse/code/Epistemic-Humility-Research"
CHAT = f"{ROOT}/experiments/qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/c_hat.json"
ST = f"{ROOT}/experiments/qwen35-4b-midband-doubt-snap/analysis/anchor_extract.safetensors"
ROWS = f"{ROOT}/experiments/qwen35-4b-midband-doubt-snap/analysis/fit_rows_for_anchor.jsonl"

MU_C = -4.031343053353048
SIGMA_C = 1.576023489724997
READOUT_SIGN = -1.0

d = json.load(open(CHAT))
vector = np.asarray(d["vector"], dtype=np.float64)
mu = np.asarray(d["mu"], dtype=np.float64)  # zero vector

role_by_key = {}
for line in open(ROWS):
    r = json.loads(line)
    role_by_key[r["row_key"]] = r["role"]

def st_key(row_key):
    return "hs20__" + row_key.replace(":", "_")

def auroc(pos, neg):
    data = sorted([(v,1) for v in pos] + [(v,0) for v in neg])
    ranks=[0.0]*len(data); i=0
    while i < len(data):
        j=i
        while j+1<len(data) and data[j+1][0]==data[i][0]: j+=1
        avg=(i+j)/2.0+1.0
        for k in range(i,j+1): ranks[k]=avg
        i=j+1
    rp=sum(r for r,(_,l) in zip(ranks,data) if l==1)
    return (rp - len(pos)*(len(pos)+1)/2.0)/(len(pos)*len(neg))

confab_raw=[]; correct_raw=[]; missing=0
with safe_open(ST, framework="numpy") as f:
    keys=set(f.keys())
    for rk, role in role_by_key.items():
        k=st_key(rk)
        if k not in keys:
            missing+=1; continue
        h=f.get_tensor(k).astype(np.float64)
        raw=float(np.dot(h - mu, vector))
        if role=="confab": confab_raw.append(raw)
        elif role=="known_correct_answered": correct_raw.append(raw)

print(f"missing keys: {missing}")
print(f"n_confab={len(confab_raw)} n_correct={len(correct_raw)}")

def z(raw): return READOUT_SIGN*(raw-MU_C)/SIGMA_C
cz=[z(r) for r in confab_raw]; kz=[z(r) for r in correct_raw]

print("--- RAW projection (dot(h,vector), pre-sign) ---")
print(f"  confab median raw = {np.median(confab_raw):.6f}")
print(f"  correct median raw = {np.median(correct_raw):.6f}")
print(f"  confab raw MORE-NEGATIVE than correct? {np.median(confab_raw) < np.median(correct_raw)}")
print("--- THIS harness convention (READOUT_SIGN=-1) ---")
print(f"  confab median z = {np.median(cz):.6f}  correct median z = {np.median(kz):.6f}")
a=auroc(cz,kz)
print(f"  AUROC(confab>correct) with -1 sign = {a:.6f}")
print(f"  AUROC with +1 sign (flip)         = {auroc([-x for x in cz],[-x for x in kz]):.6f}")
print(f"  1 - AUROC(-1 sign) = {1-a:.6f}")
