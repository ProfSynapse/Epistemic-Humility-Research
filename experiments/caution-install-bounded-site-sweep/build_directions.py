#!/usr/bin/env python3
"""Stage 3 (CPU): trained substrate FITS u_d / pos_ctrl / neg_ctrl / c_hat and
the answerability gate (tau via Youden J) at every registered site. raw_base
IMPORTS its directions instead (see below) -- it never fits.

Trained-substrate method matches cell.yaml `directions.recipe` exactly
(verbatim port of
`experiments/j-space-cross-family-layer-contrast/build_directions.py` +
`gate_fit.py`, generalized from that cell's per-family safetensors bundle to
this cell's per-row `mechinterp extract` output files):

  u_d      = unit(mean(H[known_correct_answered FIT]) - mean(H[unknown_refused]))
  pos_ctrl = unit(mean(H[unknown_refused]) - mean(H[confab FIT]))            (mass-mean)
  neg_ctrl = unit(LogisticRegression(saga, C=1.0, tol=1e-3, max_iter=5000,
             random_state=20260707) on StandardScaler(H), coefficient
             rescaled by scale_)
  c_hat    = unit(pos_ctrl orthogonalized against {u_d, neg_ctrl} via QR)

G0c (byte-identical reproducibility across two fixed-seed fits) and G0d (FIT
gate AUC >= 0.90, neg_z_d = -z_d, z_d clipped [-2,2]) are checked here and
recorded per site; a G0 failure is a registered STOP, not a behavioral null
(gates.yaml g0_integrity).

raw_base (BLOCKER #8, lead adjudication 2026-08-10): raw_base is a paired
replication of `j-space-midband-write-sweep-qwen3-4b`'s own hs23/hs29
directions -- "a paired replication reuses the replicated operating point;
it never refits." Its Stage 3 therefore does not fit anything: it IMPORTS
that amendment's committed `c_hat_hs{23,29}.json` / `u_d_hs{23,29}.json`
unchanged (`sweep_lib.raw_base_direction_import`), hard-failing if either
source file is absent or malformed, and records each file's sha256 and a
human-readable identity string (source amendment, role, hs_index,
decoder_block_index, fit_population) both in the written copy's
`import_provenance` block and in `build_gate_manifest.json`. G0c/G0d are
reported as N/A-imported (trivially true: re-reading the same committed file
twice is byte-identical by construction; the source amendment's own G0d gate
already governs these directions -- its measured AUC is carried through for
provenance), not silently defaulted to pass.

Output: `directions/<substrate>/<site>/{u_d,c_hat}_<site>.json` +
`source_directions/{pos_ctrl,neg_ctrl}_<site>.json` (mechinterp-direction/v1,
gitignored; raw_base has no source_directions/, since pos_ctrl/neg_ctrl are
never fit for an imported direction) and
`analysis-committed/<substrate>/build_gate_manifest.json` (fit statistics +
G0c/G0d results for trained, import provenance for raw_base; no vectors, no
row text).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    DIRECTIONS_DIR,
    direction_record,
    load_cell,
    load_jsonl,
    load_split_manifest,
    raw_base_direction_import,
    rows_with_text_path,
    sites_for,
    split_manifest_path,
    write_json,
)

RANDOM_STATE = 20260707


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-12:
        raise ValueError("direction has near-zero norm; cannot normalize")
    return v / n


def sanitize_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_").replace("/", "_")


def load_site_activations(extract_dir: Path, hs_index: int, row_keys: list[str]) -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file

    out = {}
    for rk in row_keys:
        safe = sanitize_key(rk)
        path = extract_dir / f"{safe}__anchor.safetensors"
        if not path.exists():
            continue
        tensors = load_file(str(path))
        key = f"L{hs_index}"
        if key not in tensors:
            continue
        out[rk] = np.asarray(tensors[key][0], dtype=np.float64)
    return out


def role_and_split(substrate: str) -> tuple[dict[str, str], dict[str, str]]:
    # F4 fix: split_manifest.json is a pretty-printed JSON OBJECT (written via
    # write_json), not JSON-Lines -- load_jsonl mis-parsed it as one
    # json.loads per physical line and crashed with a JSONDecodeError on line
    # 1. load_split_manifest (sweep_lib) reads it correctly with json.loads.
    # F8 fix: rows_with_text_path/load_split_manifest are per-substrate, so
    # raw_base no longer silently reads the trained substrate's pool.
    rows = load_jsonl(rows_with_text_path(substrate))
    role_by_key = {r["row_key"]: r["role"] for r in rows}
    split_manifest = load_split_manifest(substrate)
    split_by_key = {}
    for r in split_manifest.get("rows", []):
        split_by_key[r["row_key"]] = r["split"]
    return role_by_key, split_by_key


def _raw_refuse_and_propensity(H: np.ndarray, y_confab: np.ndarray, random_state: int):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    refuse_mean = H[y_confab == 0].mean(0)
    confab_mean = H[y_confab == 1].mean(0)
    refuse_dir = unit(refuse_mean - confab_mean)

    sc = StandardScaler().fit(H)
    Z = sc.transform(H)
    clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0,
                              random_state=random_state).fit(Z, y_confab)
    prop_dir = unit(clf.coef_.ravel() / sc.scale_)
    return refuse_dir, prop_dir


def fit_one_site(activations: dict[str, np.ndarray], known_fit: list[str],
                  confab_fit: list[str], unknown_refused: list[str]) -> dict:
    H_known_fit = np.stack([activations[k] for k in known_fit])
    H_unknown = np.stack([activations[k] for k in unknown_refused])
    u_d = unit(H_known_fit.mean(0) - H_unknown.mean(0))

    order = unknown_refused + confab_fit
    H_ak = np.stack([activations[k] for k in order])
    y_confab = np.array([0] * len(unknown_refused) + [1] * len(confab_fit), dtype=int)
    caution_dir, u_p = _raw_refuse_and_propensity(H_ak, y_confab, RANDOM_STATE)

    M = np.stack([u_d, u_p], axis=1)
    Q, _ = np.linalg.qr(M)
    c_hat = unit(caution_dir - Q @ (Q.T @ caution_dir))

    return {"u_d": u_d, "u_p": u_p, "caution_dir": caution_dir, "c_hat": c_hat}


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict]:
    best_tau, best_j, best_stats = None, -1e9, None
    for tau in np.unique(scores):
        pred = scores >= tau
        tp = int(np.sum(pred & (labels == 1)))
        fn = int(np.sum(~pred & (labels == 1)))
        fp = int(np.sum(pred & (labels == 0)))
        tn = int(np.sum(~pred & (labels == 0)))
        tpr = tp / (tp + fn) if (tp + fn) else 0.0
        fpr = fp / (fp + tn) if (fp + tn) else 0.0
        j = tpr - fpr
        if j > best_j:
            best_tau, best_j = float(tau), j
            best_stats = {"tpr": tpr, "fpr": fpr, "tp": tp, "fn": fn, "fp": fp, "tn": tn, "youden_j": j}
    return best_tau, best_stats


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(labels, scores))
    except ImportError:
        pos, neg = scores[labels == 1], scores[labels == 0]
        count = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
        return float(count / (len(pos) * len(neg)))


def run_import_raw_base(sites: list, substrate: str) -> int:
    """BLOCKER #8: raw_base's Stage 3 imports hs23/hs29 c_hat/u_d unchanged
    from `j-space-midband-write-sweep-qwen3-4b`'s committed artifacts; it
    never fits. Hard-fails via `raw_base_direction_import` (propagated,
    uncaught) if either source file is absent or malformed.

    Round 4 BLOCKER (lead adjudication, 2026-08-10): `gate_scoring.
    load_gate_params` (the shared reader, left unmodified per instruction)
    reads canonical `provenance.mu_d` / `provenance.sigma_d` on the u_d
    record and `manifest["sites"][site]["tau"]` -- fields the raw-base
    import previously never wrote (the source u_d record spells them
    `mu_d_over_fit_pool` / `sigma_d_over_fit_pool`, and carries no tau at
    all, since raw_base never fits a FIT population to freeze one against).
    Fixed here, on the import side: the written u_d copy's provenance maps
    the source spellings onto the canonical keys (keeping the source
    spellings alongside, not replacing them), and each site's manifest
    entry gets `tau` imported from the source amendment's own
    `gate_fit_layers.json` (already G0d-gated there, Youden-J frozen) via
    `sweep_lib.raw_base_gate_fit_params`."""
    report = {"substrate": substrate, "mode": "imported",
              "source_amendment": "j-space-midband-write-sweep-qwen3-4b", "sites": {}}
    overall_g0 = True

    for site in sites:
        imported = raw_base_direction_import(site)

        site_dir = DIRECTIONS_DIR / substrate / site.name
        site_dir.mkdir(parents=True, exist_ok=True)
        import_prov = {
            "imported": True,
            "source_amendment": imported["source_amendment"],
            "source_path": imported["c_hat_source_path"],
            "source_sha256": imported["c_hat_sha256"],
            "identity": imported["c_hat_identity"],
        }
        c_hat_out = {**imported["c_hat"], "import_provenance": import_prov}

        # Round 4 BLOCKER fix: map the source's mu_d_over_fit_pool /
        # sigma_d_over_fit_pool onto the canonical mu_d / sigma_d keys
        # gate_scoring.load_gate_params reads, keeping the source spellings
        # too (source provenance, not replaced). Hard-fail if the source
        # fields this mapping depends on are absent -- never silently write
        # a u_d file the gate reader will KeyError on downstream instead.
        u_d_source_prov = dict(imported["u_d"].get("provenance", {}))
        if "mu_d_over_fit_pool" not in u_d_source_prov or "sigma_d_over_fit_pool" not in u_d_source_prov:
            raise RuntimeError(
                f"raw_base direction import: {imported['u_d_source_path']} "
                "provenance is missing mu_d_over_fit_pool / sigma_d_over_fit_pool "
                "-- cannot map to the canonical mu_d/sigma_d gate_scoring.load_"
                "gate_params requires; refusing to write a u_d file the gate "
                "reader would KeyError on."
            )
        u_d_provenance = {
            **u_d_source_prov,
            "mu_d": u_d_source_prov["mu_d_over_fit_pool"],
            "sigma_d": u_d_source_prov["sigma_d_over_fit_pool"],
        }
        u_d_import_prov = {
            "imported": True,
            "source_amendment": imported["source_amendment"],
            "source_path": imported["u_d_source_path"],
            "source_sha256": imported["u_d_sha256"],
            "identity": imported["u_d_identity"],
        }
        u_d_out = {**imported["u_d"], "provenance": u_d_provenance, "import_provenance": u_d_import_prov}

        (site_dir / f"c_hat_{site.name}.json").write_text(json.dumps(c_hat_out, indent=2))
        (site_dir / f"u_d_{site.name}.json").write_text(json.dumps(u_d_out, indent=2))

        # G0c is reported True because re-reading the same committed source
        # file is byte-identical by construction (verified below, not
        # assumed). G0d is now computed against the REAL source AUC (Round 4
        # minor #2 fix -- the note used to claim a value it never carried);
        # the 0.90 floor is the SAME registered floor used elsewhere, just
        # checked against an imported number instead of a locally-fit one,
        # since raw_base never fits.
        reread = raw_base_direction_import(site)
        g0c_pass = bool(
            reread["c_hat_sha256"] == imported["c_hat_sha256"]
            and reread["u_d_sha256"] == imported["u_d_sha256"]
        )
        g0d_pass = bool(imported["source_auc_neg_z_d_on_fit"] >= 0.90)
        overall_g0 = overall_g0 and g0c_pass and g0d_pass

        report["sites"][site.name] = {
            "hs_index": site.hs_index, "decoder_block": site.decoder_block,
            "imported": True,
            "c_hat_source_path": imported["c_hat_source_path"],
            "c_hat_sha256": imported["c_hat_sha256"],
            "c_hat_identity": imported["c_hat_identity"],
            "u_d_source_path": imported["u_d_source_path"],
            "u_d_sha256": imported["u_d_sha256"],
            "u_d_identity": imported["u_d_identity"],
            "tau": imported["tau_frozen"],
            "tau_frozen_method": imported["tau_frozen_method"],
            "gate_fit_source_path": imported["gate_fit_source_path"],
            "gate_fit_sha256": imported["gate_fit_sha256"],
            "g0c_reproducible": g0c_pass,
            "g0c_note": "N/A_imported: not fit here; reproducibility means "
                        "re-import is byte-identical (verified by re-reading "
                        "the source file and comparing sha256, not assumed).",
            "g0d_pass": g0d_pass,
            "g0d_note": (
                "N/A_imported: not fit here; source amendment's own G0d gate "
                f"(AUC >= 0.90) already governs this direction -- measured "
                f"AUC={imported['source_auc_neg_z_d_on_fit']:.4f} "
                f"(auc_neg_z_d_on_fit), from {imported['gate_fit_source_path']}."
            ),
        }
        print(f"[build-directions:{substrate}] {site.name}: IMPORTED c_hat={imported['c_hat_sha256'][:12]} "
              f"u_d={imported['u_d_sha256'][:12]} tau={imported['tau_frozen']:.6f} "
              f"from {imported['c_hat_source_path']}", flush=True)

    report["g0_overall_pass"] = overall_g0
    out_path = COMMITTED / substrate / "build_gate_manifest.json"
    write_json(out_path, report)
    print(f"[build-directions:{substrate}] wrote {out_path}", flush=True)
    return 0 if overall_g0 else 1


def run(args: argparse.Namespace) -> int:
    cell = load_cell()
    substrate = args.substrate
    sites = sites_for(substrate, cell)

    if substrate == "raw_base":
        return run_import_raw_base(sites, substrate)

    role_by_key, split_by_key = role_and_split(substrate)
    extract_dir = ANALYSIS / f"extract_{substrate}"

    known_fit = sorted(k for k, r in role_by_key.items()
                        if r == "known_correct_answered" and split_by_key.get(k) == "fit")
    confab_fit = sorted(k for k, r in role_by_key.items()
                         if r == "confab" and split_by_key.get(k) == "fit")
    unknown_refused = sorted(k for k, r in role_by_key.items() if r == "unknown_refused")
    print(f"[build-directions:{substrate}] n_known_fit={len(known_fit)} "
          f"n_confab_fit={len(confab_fit)} n_unknown_refused={len(unknown_refused)}", flush=True)
    if not (known_fit and confab_fit and unknown_refused):
        print(f"[build-directions] ERROR: one or more fitting populations is empty "
              f"({rows_with_text_path(substrate)} / {split_manifest_path(substrate)}). "
              "Run extract_anchor.py first.",
              file=sys.stderr)
        return 1

    report = {"substrate": substrate, "random_state": RANDOM_STATE, "sites": {}}
    overall_g0 = True

    for site in sites:
        acts = load_site_activations(extract_dir, site.hs_index,
                                      known_fit + confab_fit + unknown_refused)
        missing = [k for k in known_fit + confab_fit + unknown_refused if k not in acts]
        if missing:
            print(f"[build-directions:{substrate}] {site.name}: {len(missing)} rows missing "
                  f"a cached activation; refusing (would silently shrink the fit population).",
                  file=sys.stderr)
            return 1

        fit1 = fit_one_site(acts, known_fit, confab_fit, unknown_refused)
        fit2 = fit_one_site(acts, known_fit, confab_fit, unknown_refused)
        g0c_two_fit_pass = all(np.array_equal(fit1[k], fit2[k]) for k in ("u_d", "u_p", "caution_dir", "c_hat"))

        u_d, u_p, caution_dir, c_hat = fit1["u_d"], fit1["u_p"], fit1["caution_dir"], fit1["c_hat"]
        H_fit = np.stack([acts[k] for k in confab_fit + known_fit])
        proj_d = H_fit @ u_d
        labels = np.array([1] * len(confab_fit) + [0] * len(known_fit))  # confab=1 (LOW doubt)
        mu_d, sigma_d = float(proj_d.mean()), float(proj_d.std())
        z_d = np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0)
        score = -z_d  # confab rows read LOW on u_d -> high neg_z_d
        tau, tau_stats = youden_tau(score, labels)
        auc = roc_auc(score, labels)
        g0d_pass = bool(auc >= 0.90)

        H_c = np.stack([acts[k] for k in confab_fit + known_fit])
        proj_c = H_c @ c_hat
        sigma_c = float(proj_c.std())
        hidden_dim = int(next(iter(acts.values())).shape[0])

        site_dir = DIRECTIONS_DIR / substrate / site.name
        source_dir = site_dir / "source_directions"
        site_dir.mkdir(parents=True, exist_ok=True)
        source_dir.mkdir(parents=True, exist_ok=True)
        prov = {"substrate": substrate, "hs_index": site.hs_index, "decoder_block_index": site.decoder_block}

        u_d_path = site_dir / f"u_d_{site.name}.json"
        c_hat_path = site_dir / f"c_hat_{site.name}.json"
        u_d_path.write_text(json.dumps(
            direction_record(u_d, site.decoder_block, hidden_dim, 1.0, "doubt_sensor_u_d",
                              {**prov, "mu_d": mu_d, "sigma_d": sigma_d}), indent=2))
        (source_dir / f"pos_ctrl_{site.name}.json").write_text(json.dumps(
            direction_record(caution_dir, site.decoder_block, hidden_dim, 1.0, "positive_control", prov), indent=2))
        (source_dir / f"neg_ctrl_{site.name}.json").write_text(json.dumps(
            direction_record(u_p, site.decoder_block, hidden_dim, 1.0, "negative_control", prov), indent=2))
        c_hat_path.write_text(json.dumps(
            direction_record(c_hat, site.decoder_block, hidden_dim, sigma_c, "caution_write_c_hat",
                              {**prov, "cos_caution_dir_c_hat": float(np.dot(caution_dir, c_hat))}), indent=2))

        # F20 fix: gates.yaml g0c_refit_reproducible says "byte-identical
        # across two fixed-seed fits", but the pre-fix check only compared
        # two in-memory arrays computed back-to-back in the same process --
        # deterministic by construction, never touching the WRITTEN JSON, so
        # a serialization/round-trip bug in direction_record/json.dumps could
        # never fail it. Reload the files just written and compare against
        # the freshly-fit arrays; Python's json module round-trips float64
        # reprs exactly, so this is an exact-equality check, not a tolerance.
        u_d_reloaded = np.asarray(json.loads(u_d_path.read_text())["vector"], dtype=np.float64)
        c_hat_reloaded = np.asarray(json.loads(c_hat_path.read_text())["vector"], dtype=np.float64)
        g0c_roundtrip_pass = bool(
            np.array_equal(u_d_reloaded, u_d) and np.array_equal(c_hat_reloaded, c_hat)
        )
        g0c_pass = bool(g0c_two_fit_pass and g0c_roundtrip_pass)
        overall_g0 = overall_g0 and g0c_pass and g0d_pass

        report["sites"][site.name] = {
            "hs_index": site.hs_index, "decoder_block": site.decoder_block,
            "n_known_fit": len(known_fit), "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown_refused),
            "g0c_reproducible": g0c_pass, "g0c_two_fit_pass": g0c_two_fit_pass,
            "g0c_roundtrip_pass": g0c_roundtrip_pass,
            "g0d_gate_auc": auc, "g0d_pass": g0d_pass,
            "tau": tau, "tau_stats": tau_stats, "mu_d": mu_d, "sigma_d": sigma_d, "sigma_c": sigma_c,
            "cos_u_d_u_p": float(np.dot(u_d, u_p)),
        }
        print(f"[build-directions:{substrate}] {site.name}: G0c={g0c_pass} "
              f"(two_fit={g0c_two_fit_pass} roundtrip={g0c_roundtrip_pass}) "
              f"G0d(auc={auc:.4f})={g0d_pass} tau={tau:.4f} sigma_c={sigma_c:.4f}", flush=True)

    report["g0_overall_pass"] = overall_g0
    out_path = COMMITTED / substrate / "build_gate_manifest.json"
    write_json(out_path, report)
    print(f"[build-directions:{substrate}] wrote {out_path}", flush=True)
    return 0 if overall_g0 else 1


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
