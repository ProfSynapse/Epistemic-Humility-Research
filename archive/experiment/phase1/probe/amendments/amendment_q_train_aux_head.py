#!/usr/bin/env python3
"""Amendment Q — scored run: train the engine's AuxHead (BCE) and eval cold transfer.

Trains the synaptic-tuner `AuxHead` (linear -> sigmoid, BCE via the engine's
`compute_aux_head_loss`, head-only optimizer) on the FAITHFUL representation —
the cached grpo-v2 L35 vectors at the extraction's `final_prompt_token`, which the
pre-flight smoke proved a live engine forward reproduces at cos 0.9998 — then
applies the trained head COLD to SelfAware. Primary metric: transfer AUROC
(falsifier < 0.90, locked in AMENDMENT-Q). Uses the engine's real head module,
loss, and save/load sidecar; the only deviation from train_sft.py's Trainer is the
data path, because its SFT preprocessing reads the end-of-user token (cos 0.54 to
the validated axis), not the gen-prompt token — a documented Phase-B engine gap.

Engine-faithful: the AuxHead reads RAW hidden states (no standardization), as
deployed. `--standardize` runs a labeled DIAGNOSTIC variant to localize any gap as
optimization (standardized recovers it) vs hypothesis class.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file
from sklearn.metrics import roc_auc_score

from path_compat import repo_root  # noqa: E402

REPO = repo_root()
sys.path.insert(0, str(REPO / "synaptic-tuner" / "Trainers" / "sft" / "src"))
from aux_head import AuxHead, compute_aux_head_loss, load_aux_head, save_aux_head  # noqa: E402

LAYER = 35
KUQ_DIR = (
    REPO / "experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-kuq"
    / "hidden_states_kuq_clean_sft_grpo_v2_full/extraction__cfdf25500cf3"
)
SELFAWARE_DIR = (
    REPO / "experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware"
    / "hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f"
)
GATES = {"transfer_auroc_min_falsifier": 0.90, "ece_max": 0.30,
         "over_refusal_max": 67.5, "refusal_recall_min": 82.0}


def load_cached(ext_dir: Path, source: str):
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8") if l.strip()]
    X, y = [], []
    lname = f"L{LAYER}"
    for r in rows:
        label = str(r.get("label", "")).lower()
        if label not in ("known", "unknown"):
            continue
        safe = str(r["probe_pool_row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{source}.safetensors"
        if not shard.exists():
            continue
        X.append(np.asarray(load_file(str(shard))[lname], dtype=np.float32))
        y.append(1 if label == "known" else 0)
    return np.vstack(X), np.asarray(y, dtype=np.float32)


def ece(prob: np.ndarray, y: np.ndarray, n_bins: int = 15) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(prob, bins[1:-1])
    e = 0.0
    for b in range(n_bins):
        m = idx == b
        if not m.any():
            continue
        e += (m.mean()) * abs(prob[m].mean() - y[m].mean())
    return float(e)


def train_head(Xtr, ytr, input_dim, *, lr, epochs, seed, device):
    torch.manual_seed(seed)
    head = AuxHead(input_dim=input_dim, head_type="linear", out_activation="sigmoid").to(device)
    Xt = torch.from_numpy(Xtr).to(device)
    yt = torch.from_numpy(ytr).to(device)
    opt = torch.optim.Adam(head.parameters(), lr=lr)
    head.train()
    for ep in range(epochs):
        opt.zero_grad()
        pred = head(Xt)
        loss = compute_aux_head_loss(pred, yt, "bce")
        loss.backward()
        opt.step()
        if ep % max(1, epochs // 10) == 0 or ep == epochs - 1:
            with torch.no_grad():
                auc = roc_auc_score(ytr, head(Xt).detach().cpu().numpy())
            print(f"  epoch {ep:5d}  bce={loss.item():.4f}  train_auroc={auc:.4f}", flush=True)
    head.eval()
    return head


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="h_lora", choices=["h_base", "h_lora"])
    ap.add_argument("--lr", type=float, default=1e-2)
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=20260629)
    ap.add_argument("--standardize", action="store_true", help="DIAGNOSTIC: z-score inputs (not engine-faithful)")
    ap.add_argument("--out", default=str(REPO / "scratch/amendment_q"))
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[Q] load cached KUQ (fit) + SelfAware (test), source={a.source} L{LAYER}")
    Xtr, ytr = load_cached(KUQ_DIR, a.source)
    Xte, yte = load_cached(SELFAWARE_DIR, a.source)
    print(f"[Q] fit n={len(ytr)} (known={int(ytr.sum())}), test n={len(yte)} (known={int(yte.sum())})")

    tag = "raw" if not a.standardize else "standardized-DIAGNOSTIC"
    if a.standardize:
        mu, sd = Xtr.mean(0, keepdims=True), Xtr.std(0, keepdims=True) + 1e-6
        Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd

    print(f"[Q] train engine AuxHead ({tag}) lr={a.lr} epochs={a.epochs} on {device}")
    head = train_head(Xtr, ytr, Xtr.shape[1], lr=a.lr, epochs=a.epochs, seed=a.seed, device=device)

    # save + reload roundtrip via the engine sidecar (skip for standardized diag)
    out_dir = Path(a.out) / (a.source + ("_std" if a.standardize else ""))
    save_aux_head(head, out_dir, layer=LAYER, token_position="last", loss="bce")
    reloaded = load_aux_head(out_dir)
    with torch.no_grad():
        fp = reloaded.to(device)(torch.from_numpy(Xte).to(device)).cpu().numpy()
    fp = fp.astype(np.float64)

    transfer_auroc = float(roc_auc_score(yte, fp))
    ece_val = ece(fp, yte)
    answer = fp >= a.tau
    km, um = (yte == 1), (yte == 0)
    over_refusal = 100.0 * float((~answer)[km].mean())
    refusal_recall = 100.0 * float((~answer)[um].mean())
    margin = 100.0 * float(answer[km].mean()) - 100.0 * float(answer[um].mean())

    result = {
        "amendment": "Q", "variant": tag, "source": a.source, "layer": LAYER, "tau": a.tau,
        "lr": a.lr, "epochs": a.epochs, "seed": a.seed,
        "n_fit": len(ytr), "n_test": len(yte),
        "transfer": {"transfer_auroc": transfer_auroc, "ece": ece_val, "factual_p_std": float(fp.std())},
        "oracle_action_secondary": {
            "over_refusal_pct": over_refusal, "refusal_recall_pct": refusal_recall,
            "answer_rate_known_pct": 100.0 * float(answer[km].mean()),
            "answer_rate_unknown_pct": 100.0 * float(answer[um].mean()),
            "action_margin_pts": margin,
        },
        "verdict": {
            "primary_falsifier_transfer_auroc<0.90": transfer_auroc < GATES["transfer_auroc_min_falsifier"],
            "passes_primary(auroc>=0.90 & ece<0.30)": (transfer_auroc >= 0.90 and ece_val < GATES["ece_max"]),
        },
        "sidecar_dir": str(out_dir),
    }
    print("\n==================== AMENDMENT Q RESULT ====================")
    print(json.dumps(result, indent=2))
    print("===========================================================")
    Path(a.out).mkdir(parents=True, exist_ok=True)
    rp = Path(a.out) / f"result_{a.source}{'_std' if a.standardize else ''}.json"
    rp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[Q] wrote {rp}")


if __name__ == "__main__":
    main()
