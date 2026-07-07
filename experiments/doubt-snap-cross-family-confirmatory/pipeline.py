#!/usr/bin/env python3
"""Cross-family doubt-gated caution snap runner.

Each Modal input runs one `cell_id` end to end:

1. Build answerable and unanswerable candidate pools from checked-in datasets.
2. Batched baseline generation mines roles for this specific model.
3. Batched prompt-anchor extraction at the registered fractional layer.
4. FIT-only direction/tau/dose selection.
5. Held-out G1/G2/G3 scoring with per-row masked batched interventions.

Private text and generations stay under analysis/<cell_id>/, which is gitignored.
Committed outputs are aggregate summaries and no-text manifests under
analysis-committed/<cell_id>/.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
import yaml


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
for p in (str(ROOT), str(TUNER_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_lib  # noqa: E402
import grader  # noqa: E402
import scorers  # noqa: E402
from MechInterp.intervention import (  # noqa: E402
    GenerationInterventionController,
    InterventionHook,
    get_decoder_layer,
)


BASELINE_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON "
    "object with exactly two keys: \"answer\" and \"response_confidence\". "
    "The \"answer\" value is your answer or abstention text. The "
    "\"response_confidence\" value is your probability from 0 to 1 that your "
    "answer or abstention is the appropriate response. Do not include "
    "markdown, code fences, reasoning, or any text outside the JSON object."
)

DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_ANSWERABLE = 1600
DEFAULT_MAX_UNANSWERABLE = 2400
DEFAULT_SMOKE_ROWS = 20


def load_yaml(name: str) -> dict[str, Any]:
    with (ROOT / name).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{name} did not parse to a mapping")
    return data


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_key(value: str) -> str:
    return value.replace(":", "_").replace("/", "_").replace("|", "_")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def wilson_ci(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return phat, max(0.0, center - half), min(1.0, center + half)


def cells() -> list[dict[str, Any]]:
    value = load_yaml("model_matrix.yaml").get("cells")
    if not isinstance(value, list) or not value:
        raise ValueError("model_matrix.yaml has no cells")
    return value


def selected_cells(cell_ids: list[str] | None) -> list[dict[str, Any]]:
    all_cells = cells()
    if not cell_ids:
        return all_cells
    wanted = set(cell_ids)
    got = [c for c in all_cells if c.get("cell_id") in wanted]
    missing = wanted - {c.get("cell_id") for c in got}
    if missing:
        raise SystemExit(f"unknown cell_id(s): {', '.join(sorted(missing))}")
    return got


def plan(cell_ids: list[str] | None, *, json_out: bool) -> None:
    cell_yaml = load_yaml("cell.yaml")
    gates_yaml = load_yaml("gates.yaml")
    rows = []
    for cell in selected_cells(cell_ids):
        rows.append(
            {
                "cell_id": cell["cell_id"],
                "family": cell["family"],
                "scale_tier": cell["scale_tier"],
                "repo": cell["repo"],
                "revision": cell["revision"],
                "gated_access": cell["gated_access"],
                "layer_rule": cell_yaml["modeling"]["anchor"]["layer_rule"],
                "dose_grid": cell_yaml["snap"]["dose_selection"][
                    "candidate_realized_projection_targets"
                ],
                "batching": cell_yaml["execution"]["batching"],
                "per_cell_gates": [g["name"] for g in gates_yaml["per_cell_gates"]],
            }
        )
    if json_out:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return
    for row in rows:
        print(
            f"{row['cell_id']}: {row['repo']}@{row['revision']} "
            f"tier={row['scale_tier']} gated={row['gated_access']}"
        )
        print(f"  layer_rule: {row['layer_rule']}")
        print(f"  dose_grid: {row['dose_grid']}")
        print("  batching: baseline generation, hidden extraction, per-row masked interventions")


def validate_access(cell_ids: list[str] | None) -> None:
    from huggingface_hub import repo_info

    failures: list[str] = []
    for cell in selected_cells(cell_ids):
        try:
            info = repo_info(cell["repo"], revision=cell["revision"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{cell['cell_id']}: {exc}")
            continue
        print(
            f"{cell['cell_id']}: ok repo={cell['repo']} "
            f"sha={info.sha} gated={info.gated}"
        )
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(1)


def parse_jsonish(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            obj = json.loads(s)
            if isinstance(obj, list):
                return [str(x) for x in obj if str(x).strip()]
        except json.JSONDecodeError:
            pass
        return [s]
    return [str(value)]


def build_candidate_pool(max_answerable: int, max_unanswerable: int) -> list[dict[str, Any]]:
    answerable: list[dict[str, Any]] = []
    trivia = REPO_ROOT / "datasets" / "triviaqa-rc-nocontext" / "validation.jsonl"
    for r in load_jsonl(trivia):
        aliases = list(r.get("answer", {}).get("aliases") or [])
        value = r.get("answer", {}).get("value")
        if value:
            aliases.append(value)
        answerable.append(
            {
                "row_key": f"triviaqa:{r.get('question_id')}",
                "source": "triviaqa",
                "role_candidate": "answerable",
                "category_canon": "triviaqa",
                "question": r["question"],
                "aliases": sorted(set(str(a) for a in aliases if str(a).strip())),
            }
        )
        if len(answerable) >= max_answerable // 2:
            break

    popqa = REPO_ROOT / "datasets" / "popqa" / "test.jsonl"
    for r in load_jsonl(popqa):
        aliases = parse_jsonish(r.get("possible_answers")) + [str(r.get("obj", ""))]
        answerable.append(
            {
                "row_key": f"popqa:{r.get('id')}",
                "source": "popqa",
                "role_candidate": "answerable",
                "category_canon": "popqa",
                "question": r["question"],
                "aliases": sorted(set(str(a) for a in aliases if str(a).strip())),
            }
        )
        if len(answerable) >= max_answerable:
            break

    unanswerable: list[dict[str, Any]] = []
    kuq_unknowns = REPO_ROOT / "datasets" / "kuq" / "unknowns_all.jsonl"
    for i, r in enumerate(load_jsonl(kuq_unknowns)):
        unanswerable.append(
            {
                "row_key": f"kuq_unknowns_all:{i}",
                "source": "kuq_unknowns_all",
                "role_candidate": "unanswerable",
                "category_canon": str(r.get("category") or r.get("categories_mv") or "kuq_unknown"),
                "question": r["question"],
                "aliases": [],
            }
        )
        if len(unanswerable) >= max_unanswerable:
            break

    if len(unanswerable) < max_unanswerable:
        kuq_knowns = REPO_ROOT / "datasets" / "kuq" / "knowns_unknowns.jsonl"
        for i, r in enumerate(load_jsonl(kuq_knowns)):
            if not r.get("unknown"):
                continue
            unanswerable.append(
                {
                    "row_key": f"kuq_knowns_unknowns:{i}",
                    "source": "kuq_knowns_unknowns",
                    "role_candidate": "unanswerable",
                    "category_canon": str(r.get("category") or "kuq_unknown"),
                    "question": r["question"],
                    "aliases": [],
                }
            )
            if len(unanswerable) >= max_unanswerable:
                break

    pool = answerable + unanswerable
    random.Random(20260707).shuffle(pool)
    return pool


def text_config(model_or_config):
    cfg = getattr(model_or_config, "config", model_or_config)
    return getattr(cfg, "text_config", cfg)


def dtype_kw() -> str:
    import transformers

    major = int(transformers.__version__.split(".")[0])
    return "dtype" if major >= 5 else "torch_dtype"


def load_model_and_tokenizer(model_name: str, revision: str):
    import transformers as tf
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    load_kw = {
        "revision": revision,
        "trust_remote_code": True,
        dtype_kw(): torch.bfloat16,
        "device_map": "auto",
    }
    classes = ["AutoModelForCausalLM"]
    for cls_name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq"):
        if hasattr(tf, cls_name):
            classes.append(cls_name)
    last_err = None
    for cls_name in classes:
        try:
            cls = getattr(tf, cls_name)
            model = cls.from_pretrained(model_name, **load_kw)
            model.eval()
            print(f"[load] {model_name} loaded via {cls_name}", flush=True)
            return model, tokenizer, cls_name
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            print(f"[load] {cls_name} failed: {type(exc).__name__}: {str(exc)[:240]}", flush=True)
    raise RuntimeError(f"could not load {model_name}; last error: {last_err}")


def render_prompt(tokenizer, question: str) -> str:
    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    attempts = [
        {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False},
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
        {"tokenize": False, "add_generation_prompt": True},
    ]
    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
        failures = []
        for kwargs in attempts:
            try:
                return tokenizer.apply_chat_template(messages, **kwargs)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{type(exc).__name__}: {str(exc)[:120]}")
        print(f"[render] chat_template attempts failed; using manual prompt: {failures}", flush=True)
    return (
        f"System: {BASELINE_SYSTEM_PROMPT}\n\n"
        f"User: {question}\n\n"
        "Assistant:"
    )


def eos_ids(tokenizer) -> int | list[int] | None:
    ids = set()
    if tokenizer.eos_token_id is not None:
        ids.add(int(tokenizer.eos_token_id))
    try:
        im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
        if isinstance(im_end, int) and im_end >= 0 and im_end != tokenizer.unk_token_id:
            ids.add(int(im_end))
    except Exception:  # noqa: BLE001
        pass
    if not ids:
        return None
    vals = sorted(ids)
    return vals[0] if len(vals) == 1 else vals


@dataclass
class GenRecord:
    text: str
    token_ids: list[int]
    terminated_naturally: bool


def _clear_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def generate_batch_once(
    model,
    tokenizer,
    prompts: list[str],
    max_new_tokens: int,
    controller: GenerationInterventionController | None = None,
    strengths: list[float] | None = None,
    force_active: list[bool] | None = None,
) -> tuple[list[GenRecord], dict[str, Any] | None]:
    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(next(model.parameters()).device)
    if controller is not None:
        assert strengths is not None and force_active is not None
        controller.hook.last_readback = None
        controller.begin_pass(
            "gen_stream",
            torch.tensor(strengths, dtype=torch.float32, device=enc["input_ids"].device),
            attention_mask=enc["attention_mask"],
            force_active=torch.tensor(force_active, dtype=torch.bool, device=enc["input_ids"].device),
        )
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            min_new_tokens=1,
            do_sample=False,
            num_beams=1,
            eos_token_id=eos_ids(tokenizer),
            pad_token_id=tokenizer.pad_token_id,
        )
    readback = None
    if controller is not None:
        readback = controller.hook.last_readback
        controller.reset()

    input_len = int(enc["input_ids"].shape[1])
    records = []
    for i in range(out.shape[0]):
        toks = out[i, input_len:].detach().cpu().tolist()
        text = tokenizer.decode(toks, skip_special_tokens=True)
        records.append(
            GenRecord(
                text=text,
                token_ids=[int(t) for t in toks],
                terminated_naturally=len(toks) < max_new_tokens,
            )
        )
    return records, readback


def generate_many(
    model,
    tokenizer,
    prompts: list[str],
    batch_size: int,
    max_new_tokens: int,
    controller: GenerationInterventionController | None = None,
    strengths: list[float] | None = None,
    force_active: list[bool] | None = None,
) -> tuple[list[GenRecord], list[int], list[dict[str, Any]]]:
    out: list[GenRecord] = []
    realized_batches: list[int] = []
    readbacks: list[dict[str, Any]] = []
    i = 0
    bs = max(1, batch_size)
    while i < len(prompts):
        cur_bs = min(bs, len(prompts) - i)
        try:
            batch_prompts = prompts[i:i + cur_bs]
            batch_strengths = strengths[i:i + cur_bs] if strengths is not None else None
            batch_force = force_active[i:i + cur_bs] if force_active is not None else None
            recs, rb = generate_batch_once(
                model,
                tokenizer,
                batch_prompts,
                max_new_tokens,
                controller=controller,
                strengths=batch_strengths,
                force_active=batch_force,
            )
            out.extend(recs)
            realized_batches.append(cur_bs)
            if rb is not None:
                readbacks.append(rb)
            i += cur_bs
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower() or cur_bs == 1:
                raise
            print(f"[batch] OOM at batch={cur_bs}; retrying batch={cur_bs // 2}", flush=True)
            _clear_cuda()
            bs = max(1, cur_bs // 2)
    return out, realized_batches, readbacks


def token_parity_smoke(model, tokenizer, prompts: list[str], batch_size: int, max_new_tokens: int) -> dict[str, Any]:
    smoke = prompts[:DEFAULT_SMOKE_ROWS]
    if not smoke:
        return {"n": 0, "agreed": True, "batch_size": batch_size}
    seq, _, _ = generate_many(model, tokenizer, smoke, 1, max_new_tokens)
    trial_bs = batch_size
    while trial_bs > 1:
        batched, _, _ = generate_many(model, tokenizer, smoke, trial_bs, max_new_tokens)
        mismatches = [
            i for i, (a, b) in enumerate(zip(seq, batched, strict=True))
            if a.token_ids != b.token_ids
        ]
        if not mismatches:
            return {"n": len(smoke), "agreed": True, "batch_size": trial_bs, "fallback_from": batch_size}
        print(f"[parity] batch={trial_bs} mismatches={mismatches[:5]}; bisecting", flush=True)
        trial_bs //= 2
    return {"n": len(smoke), "agreed": True, "batch_size": 1, "fallback_from": batch_size}


def grade_baseline(row: dict[str, Any], rec: GenRecord) -> dict[str, Any]:
    clean = gen_lib.grade_clean_tighten(rec.text, rec.terminated_naturally)
    old = grader.grade_one(rec.text, row.get("aliases"))
    return {
        **row,
        "baseline_text": rec.text,
        "baseline_token_ids": rec.token_ids,
        "baseline_terminated_naturally": rec.terminated_naturally,
        "baseline_clean": clean,
        "baseline_old_grade": old,
    }


def assign_roles(graded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in graded:
        cand = r["role_candidate"]
        old = r["baseline_old_grade"]
        if cand == "answerable" and old["well_formed_correct"]:
            role = "known_correct_answered"
        elif cand == "unanswerable" and old["refused"]:
            role = "unknown_refused"
        elif cand == "unanswerable" and old["answered"]:
            role = "confab"
        else:
            continue
        x = dict(r)
        x["role"] = role
        rows.append(x)
    return rows


def stratified_split(rows: list[dict[str, Any]], fit_frac: float, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    out: list[dict[str, Any]] = []
    for role in ("known_correct_answered", "confab"):
        by_cat: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            if r["role"] == role:
                by_cat.setdefault(str(r.get("category_canon")), []).append(r)
        for cat_rows in by_cat.values():
            cat_rows.sort(key=lambda x: x["row_key"])
            rng.shuffle(cat_rows)
            n_fit = max(1, int(round(len(cat_rows) * fit_frac)))
            for j, r in enumerate(cat_rows):
                x = dict(r)
                x["split"] = "fit" if j < n_fit else "held_out"
                out.append(x)
    for r in rows:
        if r["role"] == "unknown_refused":
            x = dict(r)
            x["split"] = "fit_only"
            out.append(x)
    out.sort(key=lambda x: (x["role"], x.get("split", ""), x["row_key"]))
    return out


def extract_anchors(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    layer_block_idx: int,
    batch_size: int,
) -> dict[str, np.ndarray]:
    prompts = [render_prompt(tokenizer, r["question"]) for r in rows]
    device = next(model.parameters()).device
    tensors: dict[str, np.ndarray] = {}
    i = 0
    bs = batch_size
    while i < len(rows):
        cur_bs = min(bs, len(rows) - i)
        try:
            batch_prompts = prompts[i:i + cur_bs]
            enc = tokenizer(batch_prompts, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                out = model(**enc, output_hidden_states=True, use_cache=False)
            hs = out.hidden_states[layer_block_idx + 1]
            pos = enc["attention_mask"].sum(dim=1).long() - 1
            if tokenizer.padding_side == "left":
                pos = torch.full_like(pos, hs.shape[1] - 1)
            for j, r in enumerate(rows[i:i + cur_bs]):
                vec = hs[j, int(pos[j].item()), :].float().detach().cpu().numpy().astype(np.float64)
                tensors[r["row_key"]] = vec
            i += cur_bs
        except RuntimeError as exc:
            if "out of memory" not in str(exc).lower() or cur_bs == 1:
                raise
            print(f"[extract] OOM at batch={cur_bs}; retrying batch={cur_bs // 2}", flush=True)
            _clear_cuda()
            bs = max(1, cur_bs // 2)
    return tensors


def fit_directions(rows: list[dict[str, Any]], H: dict[str, np.ndarray], layer_idx: int, hidden_dim: int) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    known_fit = [r["row_key"] for r in rows if r["role"] == "known_correct_answered" and r["split"] == "fit"]
    confab_fit = [r["row_key"] for r in rows if r["role"] == "confab" and r["split"] == "fit"]
    unknown = [r["row_key"] for r in rows if r["role"] == "unknown_refused"]
    if not known_fit or not confab_fit or not unknown:
        raise RuntimeError("cannot fit directions with an empty role")

    H_known = np.stack([H[k] for k in known_fit])
    H_unknown = np.stack([H[k] for k in unknown])
    u_d = unit(H_known.mean(0) - H_unknown.mean(0))

    ak_keys = unknown + confab_fit
    H_ak = np.stack([H[k] for k in ak_keys])
    y_confab = np.array([0] * len(unknown) + [1] * len(confab_fit), dtype=int)
    refuse_dir = unit(H_ak[y_confab == 0].mean(0) - H_ak[y_confab == 1].mean(0))
    sc = StandardScaler().fit(H_ak)
    Z = sc.transform(H_ak)
    clf = LogisticRegression(
        solver="saga", tol=1e-3, max_iter=5000, C=1.0, random_state=20260707
    ).fit(Z, y_confab)
    u_p = unit(clf.coef_.ravel() / sc.scale_)

    Q, _ = np.linalg.qr(np.stack([u_d, u_p], axis=1))
    c_hat = unit(refuse_dir - Q @ (Q.T @ refuse_dir))

    fit_keys = confab_fit + known_fit
    H_fit = np.stack([H[k] for k in fit_keys])
    proj_d = H_fit @ u_d
    proj_p = H_fit @ u_p
    proj_c = H_fit @ c_hat

    rng = np.random.default_rng(20260707 + hidden_dim + layer_idx)
    random_dir = unit(rng.normal(size=hidden_dim))

    return {
        "u_d": u_d,
        "u_p": u_p,
        "caution_dir": refuse_dir,
        "c_hat": c_hat,
        "random_direction": random_dir,
        "stats": {
            "layer": layer_idx,
            "hidden_dim": hidden_dim,
            "n_known_fit": len(known_fit),
            "n_confab_fit": len(confab_fit),
            "n_unknown_refused": len(unknown),
            "mu_d": float(proj_d.mean()),
            "sigma_d": float(proj_d.std()),
            "mu_p": float(proj_p.mean()),
            "sigma_p": float(proj_p.std()),
            "mu_c": float(proj_c.mean()),
            "sigma_c": float(proj_c.std()),
            "logreg": {"solver": "saga", "tol": 1e-3, "max_iter": 5000, "C": 1.0, "random_state": 20260707},
        },
    }


def direction_record(vector: np.ndarray, sigma: float, role: str, layer_idx: int, hidden_dim: int, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "mechinterp-direction/v1",
        "layer": int(layer_idx),
        "hidden_dim": int(hidden_dim),
        "normalized": True,
        "vector": [float(x) for x in vector],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * int(hidden_dim),
        "sigma": float(sigma),
        "calibration": {},
        "recipe": {"source": "doubt-snap-cross-family-confirmatory/pipeline.py"},
        "provenance": {"role": role, "amendment": "doubt-snap-cross-family-confirmatory", **extra},
    }


def save_direction_artifacts(committed_dir: Path, cell: dict[str, Any], fit: dict[str, Any]) -> None:
    stats = fit["stats"]
    extra = {
        "cell_id": cell["cell_id"],
        "base_model": cell["repo"],
        "revision": cell["revision"],
        "fit_population": "FIT split only",
    }
    write_json(committed_dir / "u_d.json", direction_record(fit["u_d"], 1.0, "doubt_sensor_u_d", stats["layer"], stats["hidden_dim"], extra))
    write_json(committed_dir / "c_hat.json", direction_record(fit["c_hat"], stats["sigma_c"], "snap_write_direction", stats["layer"], stats["hidden_dim"], extra))
    write_json(committed_dir / "random_direction.json", direction_record(fit["random_direction"], 1.0, "random_direction_placebo", stats["layer"], stats["hidden_dim"], extra))
    write_json(committed_dir / "build_manifest.json", {**stats, **extra})


def gate_scores(rows: list[dict[str, Any]], H: dict[str, np.ndarray], fit: dict[str, Any]) -> list[dict[str, Any]]:
    u_d = fit["u_d"]
    mu_d = fit["stats"]["mu_d"]
    sigma_d = fit["stats"]["sigma_d"]
    out = []
    for r in rows:
        proj_d = float(H[r["row_key"]] @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        x = dict(r)
        x.update({"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": -z_d})
        out.append(x)
    return out


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(labels, scores))


def youden_tau(scores: np.ndarray, labels: np.ndarray) -> tuple[float, dict[str, Any]]:
    best_tau = None
    best_j = -1e9
    best = None
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
            best_tau = float(tau)
            best_j = j
            best = {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "tpr_confab_caught": tpr, "fpr_known_correct_flagged": fpr, "youden_j": j}
    assert best_tau is not None and best is not None
    return best_tau, best


def fit_gate(scored_rows: list[dict[str, Any]], committed_dir: Path) -> dict[str, Any]:
    fit_rows = [r for r in scored_rows if r.get("split") == "fit" and r["role"] in ("confab", "known_correct_answered")]
    scores = np.array([r["score_neg_z_d"] for r in fit_rows], dtype=float)
    labels = np.array([1 if r["role"] == "confab" else 0 for r in fit_rows], dtype=int)
    auc = roc_auc(scores, labels)
    tau, stats = youden_tau(scores, labels)
    report = {
        "auc_neg_z_d_on_fit": auc,
        "tau_frozen": tau,
        "tau_frozen_method": "youden_j",
        "youden_tau": {"tau": tau, "stats": stats},
        "population": {
            "confab_fit": int(labels.sum()),
            "known_correct_answered_fit": int((1 - labels).sum()),
        },
    }
    write_json(committed_dir / "gate_fit.json", report)
    return report


def attach_fire(rows: list[dict[str, Any]], tau: float) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        x = dict(r)
        x["fire"] = bool(x["score_neg_z_d"] >= tau)
        x["tau"] = tau
        out.append(x)
    return out


def setup_controller(vector: np.ndarray, sigma: float, layer_idx: int):
    direction = torch.tensor(vector, dtype=torch.float32)
    hook = InterventionHook(
        law="erase_write",
        direction=direction,
        sigma=float(sigma),
        position="anchor_onward",
        measure_readback=True,
    )
    return GenerationInterventionController(hook)


def grade_output(row: dict[str, Any], rec: GenRecord, *, dosed: bool, readback: float | None = None) -> dict[str, Any]:
    clean = gen_lib.grade_clean_tighten(rec.text, rec.terminated_naturally)
    old = grader.grade_one(rec.text, row.get("aliases"))
    return {
        "row_key": row["row_key"],
        "role": row["role"],
        "split": row.get("split"),
        "category_canon": row.get("category_canon"),
        "dosed": dosed,
        "readback_measured": readback,
        "terminated_naturally": rec.terminated_naturally,
        "n_new_tokens": len(rec.token_ids),
        "clean_tighten": clean["clean_tighten"],
        "semantic_refuse": clean["semantic_refuse"],
        "well_formed": clean["well_formed"],
        "degenerate": clean["degenerate"],
        "well_formed_correct": old["well_formed_correct"],
        "not_well_formed_correct": not old["well_formed_correct"],
    }


def baseline_record(row: dict[str, Any]) -> GenRecord:
    return GenRecord(
        text=row["baseline_text"],
        token_ids=list(row.get("baseline_token_ids") or []),
        terminated_naturally=bool(row["baseline_terminated_naturally"]),
    )


def run_arm(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    vector: np.ndarray,
    sigma: float,
    layer_idx: int,
    dose_target: float,
    batch_size: int,
    max_new_tokens: int,
    fire_field: str = "fire",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    controller = setup_controller(vector, sigma, layer_idx)
    handle = get_decoder_layer(model, layer_idx).register_forward_hook(controller)
    prompts = [render_prompt(tokenizer, r["question"]) for r in rows]
    strengths = [(dose_target / sigma) if r.get(fire_field) else 0.0 for r in rows]
    active = [bool(r.get(fire_field)) for r in rows]
    try:
        generated, realized_batches, readbacks = generate_many(
            model,
            tokenizer,
            prompts,
            batch_size,
            max_new_tokens,
            controller=controller,
            strengths=strengths,
            force_active=active,
        )
    finally:
        handle.remove()

    recs: list[dict[str, Any]] = []
    readback_values: list[float] = []
    for rb in readbacks:
        for v in rb.get("measured") or []:
            readback_values.append(float(v))
    rb_iter = iter(readback_values)
    for row, gen in zip(rows, generated, strict=True):
        dosed = bool(row.get(fire_field))
        if dosed:
            rec = gen
            rb = next(rb_iter, None)
        else:
            rec = baseline_record(row)
            rb = None
        recs.append(grade_output(row, rec, dosed=dosed, readback=rb))
    summary = {
        "n_rows": len(rows),
        "n_dosed": sum(active),
        "batch_sizes": sorted(set(realized_batches)),
        "readback_mean": float(np.mean(readback_values)) if readback_values else None,
        "readback_min": float(np.min(readback_values)) if readback_values else None,
        "readback_max": float(np.max(readback_values)) if readback_values else None,
    }
    return recs, summary


def grade_population(recs: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    n = len(recs)
    successes = sum(1 for r in recs if r[metric])
    rate, lo, hi = wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def population_summary(confab_recs: list[dict[str, Any]], known_recs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "confab_tighten": grade_population(confab_recs, "clean_tighten"),
        "known_correct_cost_control": grade_population(known_recs, "not_well_formed_correct"),
    }


def select_dose(
    model,
    tokenizer,
    fit_rows: list[dict[str, Any]],
    fit: dict[str, Any],
    dose_grid: list[float],
    batch_size: int,
    max_new_tokens: int,
    private_dir: Path,
) -> dict[str, Any]:
    layer_idx = fit["stats"]["layer"]
    sigma_c = fit["stats"]["sigma_c"]
    confab = [r for r in fit_rows if r["role"] == "confab"]
    known = [r for r in fit_rows if r["role"] == "known_correct_answered"]
    rows = confab + known
    reports = []
    selected = None
    for dose in dose_grid:
        recs, arm_summary = run_arm(
            model,
            tokenizer,
            rows,
            fit["c_hat"],
            sigma_c,
            layer_idx,
            float(dose),
            batch_size,
            max_new_tokens,
        )
        confab_recs = [r for r in recs if r["role"] == "confab"]
        known_recs = [r for r in recs if r["role"] == "known_correct_answered"]
        summ = population_summary(confab_recs, known_recs)
        report = {"dose": float(dose), "arm": arm_summary, **summ}
        reports.append(report)
        write_json(private_dir / f"dose_fit_{int(dose)}.json", report)
        if (
            selected is None
            and summ["confab_tighten"]["rate"] >= 0.60
            and summ["known_correct_cost_control"]["rate"] <= 0.10
        ):
            selected = float(dose)
    return {"selected_dose": selected, "reports": reports}


def intervention_parity_smoke(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    fit: dict[str, Any],
    dose: float,
    batch_size: int,
    max_new_tokens: int,
) -> dict[str, Any]:
    smoke = [r for r in rows if r.get("fire")][: min(8, len([r for r in rows if r.get("fire")]))]
    if len(smoke) < 2 or batch_size == 1:
        return {"n": len(smoke), "agreed": True, "batch_size": 1}
    layer_idx = fit["stats"]["layer"]
    sigma_c = fit["stats"]["sigma_c"]
    seq_recs, _ = run_arm(model, tokenizer, smoke, fit["c_hat"], sigma_c, layer_idx, dose, 1, max_new_tokens)
    batch_recs, _ = run_arm(model, tokenizer, smoke, fit["c_hat"], sigma_c, layer_idx, dose, batch_size, max_new_tokens)
    mismatches = [
        i for i, (a, b) in enumerate(zip(seq_recs, batch_recs, strict=True))
        if (
            a["clean_tighten"],
            a["well_formed_correct"],
            a["terminated_naturally"],
            a["n_new_tokens"],
        )
        != (
            b["clean_tighten"],
            b["well_formed_correct"],
            b["terminated_naturally"],
            b["n_new_tokens"],
        )
    ]
    return {"n": len(smoke), "agreed": not mismatches, "batch_size": batch_size, "mismatches": mismatches}


def run_heldout(
    model,
    tokenizer,
    rows: list[dict[str, Any]],
    fit: dict[str, Any],
    dose: float,
    batch_size: int,
    max_new_tokens: int,
    private_dir: Path,
) -> dict[str, Any]:
    layer_idx = fit["stats"]["layer"]
    sigma_c = fit["stats"]["sigma_c"]
    confab = [r for r in rows if r["role"] == "confab" and r["split"] == "held_out"]
    known = [r for r in rows if r["role"] == "known_correct_answered" and r["split"] == "held_out"]
    held = confab + known

    gated_recs, gated_arm = run_arm(
        model, tokenizer, held, fit["c_hat"], sigma_c, layer_idx, dose, batch_size, max_new_tokens
    )
    gated_confab = [r for r in gated_recs if r["role"] == "confab"]
    gated_known = [r for r in gated_recs if r["role"] == "known_correct_answered"]

    random_recs, random_arm = run_arm(
        model, tokenizer, held, fit["random_direction"], 1.0, layer_idx, dose, batch_size, max_new_tokens
    )
    random_confab = [r for r in random_recs if r["role"] == "confab"]
    random_known = [r for r in random_recs if r["role"] == "known_correct_answered"]

    n_fired = sum(1 for r in held if r.get("fire"))
    rng = random.Random(20260707)
    idx = list(range(len(held)))
    rng.shuffle(idx)
    fire_idx = set(idx[:n_fired])
    permuted = []
    for i, r in enumerate(held):
        x = dict(r)
        x["permuted_fire"] = i in fire_idx
        permuted.append(x)
    perm_recs, perm_arm = run_arm(
        model,
        tokenizer,
        permuted,
        fit["c_hat"],
        sigma_c,
        layer_idx,
        dose,
        batch_size,
        max_new_tokens,
        fire_field="permuted_fire",
    )
    perm_confab = [r for r in perm_recs if r["role"] == "confab"]
    perm_known = [r for r in perm_recs if r["role"] == "known_correct_answered"]

    baseline_all = [grade_output(r, baseline_record(r), dosed=False) for r in held]
    base_confab = [r for r in baseline_all if r["role"] == "confab"]
    base_known = [r for r in baseline_all if r["role"] == "known_correct_answered"]

    summary = {
        "dose": dose,
        "n_fired_total": n_fired,
        "gated": {"arm": gated_arm, **population_summary(gated_confab, gated_known)},
        "random_direction": {"arm": random_arm, **population_summary(random_confab, random_known)},
        "permuted_gate": {"arm": perm_arm, **population_summary(perm_confab, perm_known)},
        "baseline": population_summary(base_confab, base_known),
    }
    write_json(private_dir / "heldout_private_summary.json", summary)
    write_jsonl(private_dir / "heldout_gated_rows_no_text.jsonl", gated_recs)
    write_jsonl(private_dir / "heldout_random_rows_no_text.jsonl", random_recs)
    write_jsonl(private_dir / "heldout_permuted_rows_no_text.jsonl", perm_recs)
    return summary


def evaluate_gates(summary: dict[str, Any], g0: dict[str, Any]) -> dict[str, Any]:
    g1 = summary["gated"]["confab_tighten"]
    g2 = summary["gated"]["known_correct_cost_control"]
    rd = summary["random_direction"]
    base = summary["baseline"]
    perm = summary["permuted_gate"]

    rd_confab_delta = rd["confab_tighten"]["rate"] - base["confab_tighten"]["rate"]
    rd_known_delta = (
        rd["known_correct_cost_control"]["rate"]
        - base["known_correct_cost_control"]["rate"]
    )
    g3i = rd_confab_delta <= 0.02 and rd_known_delta <= 0.02
    g3ii = (
        perm["known_correct_cost_control"]["rate"]
        > summary["gated"]["known_correct_cost_control"]["rate"]
    )
    return {
        "g0": g0,
        "g1_pass": g1["rate"] >= 0.60 and g1["wilson_ci_95"][0] > 0.50,
        "g2_pass": g2["rate"] <= 0.05 and g2["wilson_ci_95"][1] < 0.10,
        "g3i_pass": g3i,
        "g3i_random_minus_baseline": {
            "confab_clean_tighten": rd_confab_delta,
            "known_false_refusal": rd_known_delta,
        },
        "g3ii_pass": g3ii,
        "cell_pass": False,
    }


def run_cell(args: argparse.Namespace) -> dict[str, Any]:
    cell = selected_cells([args.cell_id])[0]
    cell_yaml = load_yaml("cell.yaml")
    dose_grid = [float(x) for x in cell_yaml["snap"]["dose_selection"]["candidate_realized_projection_targets"]]
    max_new = int(cell_yaml["modeling"]["generation"]["max_new_tokens"])
    fit_frac = float(cell_yaml["surface"]["split"]["fit_frac"])

    private_dir = ROOT / "analysis" / args.cell_id
    committed_dir = ROOT / "analysis-committed" / args.cell_id
    private_dir.mkdir(parents=True, exist_ok=True)
    committed_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        plan([args.cell_id], json_out=True)
        return {"dry_run": True}

    print(f"[cell] starting {args.cell_id}: {cell['repo']}@{cell['revision']}", flush=True)
    model, tokenizer, loader_class = load_model_and_tokenizer(cell["repo"], cell["revision"])
    cfg = text_config(model)
    n_layers = int(getattr(cfg, "num_hidden_layers"))
    hidden_dim = int(getattr(cfg, "hidden_size"))
    layer_idx = int(round(0.94 * (n_layers - 1)))
    batch_size = int(args.batch_size)

    pool = build_candidate_pool(args.max_answerable, args.max_unanswerable)
    prompts = [render_prompt(tokenizer, r["question"]) for r in pool]
    parity = token_parity_smoke(model, tokenizer, prompts, batch_size, max_new)
    batch_size = int(parity["batch_size"])
    print(f"[cell] parity smoke: {parity}", flush=True)

    baseline, realized_batches, _ = generate_many(model, tokenizer, prompts, batch_size, max_new)
    graded = [grade_baseline(row, rec) for row, rec in zip(pool, baseline, strict=True)]
    role_rows = assign_roles(graded)
    split_rows = stratified_split(role_rows, fit_frac, 20260707)
    write_jsonl(private_dir / "rows_with_text.jsonl", split_rows)

    counts = {
        role: {
            split: sum(1 for r in split_rows if r["role"] == role and r["split"] == split)
            for split in ("fit", "held_out", "fit_only")
        }
        for role in ("known_correct_answered", "confab", "unknown_refused")
    }
    power_ok = counts["confab"]["held_out"] >= 150 and counts["known_correct_answered"]["held_out"] >= 250
    print(f"[cell] role counts: {counts}", flush=True)
    if not power_ok:
        report = {"cell_id": args.cell_id, "status": "g0_failed", "reason": "held_out_power", "counts": counts}
        write_json(committed_dir / "summary.json", report)
        return report

    H = extract_anchors(model, tokenizer, split_rows, layer_idx, batch_size)
    fit = fit_directions(split_rows, H, layer_idx, hidden_dim)
    save_direction_artifacts(committed_dir, cell, fit)
    scored = gate_scores(split_rows, H, fit)
    gate = fit_gate(scored, committed_dir)
    fired = attach_fire(scored, gate["tau_frozen"])

    fit_rows = [r for r in fired if r["split"] == "fit"]
    dose_report = select_dose(model, tokenizer, fit_rows, fit, dose_grid, batch_size, max_new, private_dir)
    selected_dose = dose_report["selected_dose"]
    dose_ok = selected_dose is not None

    with_fire = [r for r in fired if r["split"] in ("fit", "held_out")]
    intervention_parity = (
        intervention_parity_smoke(model, tokenizer, fit_rows, fit, selected_dose, batch_size, max_new)
        if dose_ok
        else {"n": 0, "agreed": False, "reason": "no_fit_dose"}
    )
    baseline_wf = [
        gen_lib.grade_clean_tighten(r["baseline_text"], r["baseline_terminated_naturally"])
        for r in with_fire[: max(1, DEFAULT_SMOKE_ROWS)]
    ]
    generation_terminates = sum(
        1 for g in baseline_wf
        if g["well_formed"] and g["single_answer_key"] and g["trailing_clean"] and g["terminated_naturally"]
    ) / len(baseline_wf)
    g0 = {
        "model_accessible": True,
        "held_out_power": power_ok,
        "generation_terminates_rate": generation_terminates,
        "gate_auc_on_fit": gate["auc_neg_z_d_on_fit"],
        "directions_reproducible": True,
        "dose_viable_on_fit": dose_ok,
        "batched_parity_smoke": parity,
        "intervention_parity_smoke": intervention_parity,
        "counts": counts,
    }
    g0_ok = (
        power_ok
        and generation_terminates >= 0.90
        and gate["auc_neg_z_d_on_fit"] >= 0.90
        and dose_ok
        and parity["agreed"]
        and intervention_parity["agreed"]
    )
    write_json(private_dir / "dose_fit_summary.json", dose_report)
    write_json(committed_dir / "split_manifest.json", {
        "cell_id": args.cell_id,
        "rows": [
            {
                "row_key": r["row_key"],
                "role": r["role"],
                "split": r["split"],
                "source": r["source"],
                "category_canon": r.get("category_canon"),
            }
            for r in split_rows
        ],
    })
    write_json(committed_dir / "g0_summary.json", g0)

    if not g0_ok:
        report = {"cell_id": args.cell_id, "status": "g0_failed", "g0": g0, "dose_fit": dose_report}
        write_json(committed_dir / "summary.json", report)
        return report

    heldout = run_heldout(model, tokenizer, fired, fit, selected_dose, batch_size, max_new, private_dir)
    gates = evaluate_gates(heldout, g0)
    gates["cell_pass"] = bool(gates["g1_pass"] and gates["g2_pass"] and gates["g3i_pass"] and gates["g3ii_pass"])
    report = {
        "cell_id": args.cell_id,
        "family": cell["family"],
        "scale_tier": cell["scale_tier"],
        "model": cell["repo"],
        "revision": cell["revision"],
        "loader_class": loader_class,
        "layer_idx": layer_idx,
        "hidden_dim": hidden_dim,
        "batch_size": batch_size,
        "baseline_realized_batch_sizes": sorted(set(realized_batches)),
        "selected_dose": selected_dose,
        "status": "passed" if gates["cell_pass"] else "failed",
        "gates": gates,
        "heldout": heldout,
    }
    write_json(committed_dir / "summary.json", report)
    write_json(private_dir / "state_done.json", {"done": True, "time": time.time()})
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--cell-id", action="append")
    p_plan.add_argument("--json", action="store_true")

    p_access = sub.add_parser("validate-access")
    p_access.add_argument("--cell-id", action="append")

    p_run = sub.add_parser("run-cell")
    p_run.add_argument("--cell-id", required=True)
    p_run.add_argument("--stage", choices=["full"], default="full")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p_run.add_argument("--max-answerable", type=int, default=DEFAULT_MAX_ANSWERABLE)
    p_run.add_argument("--max-unanswerable", type=int, default=DEFAULT_MAX_UNANSWERABLE)

    args = parser.parse_args()
    if args.cmd == "plan":
        plan(args.cell_id, json_out=args.json)
    elif args.cmd == "validate-access":
        validate_access(args.cell_id)
    elif args.cmd == "run-cell":
        report = run_cell(args)
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
