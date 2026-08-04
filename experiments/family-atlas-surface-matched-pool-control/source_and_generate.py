#!/usr/bin/env python3
"""Materialize UMWP and run resumable baseline generation inside the pinned container."""

from __future__ import annotations

import argparse
import json
import shutil
import string
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any, Callable

import numpy as np

from grader_port import grade_generation

from instrument_common import (
    ANALYSIS, ROOT, append_jsonl_fsync, atomic_json, atomic_jsonl, load_jsonl,
    load_yaml, require_pinned_container, sha256_file,
)

def normalize_question(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _source_name(row: dict[str, Any]) -> str:
    for key in ("source", "dataset", "dataset_name", "original_dataset"):
        if row.get(key):
            return str(row[key])
    raise ValueError(f"UMWP row {row.get('id')} has no native source")


def _original_pair_id(row: dict[str, Any]) -> str:
    value = row.get("id") if bool(row["answerable"]) else row.get("relevant_ids")
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError(f"row {row.get('id')} must have exactly one relevant_ids value")
        value = value[0]
    if value is None:
        raise ValueError(f"row {row.get('id')} has no original-pair id")
    return str(value)


def canonical_answer_aliases(value: Any) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = [value]
    out: list[str] = []
    for item in values:
        if item is None or isinstance(item, bool):
            continue
        if isinstance(item, (int, float)):
            out.append(format(float(item), ".15g"))
        else:
            candidate = str(item).strip()
            if candidate:
                out.append(candidate)
    return sorted(set(out))


def materialize_source(source_path: Path, out_path: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    source_cfg = cfg["source"]
    if sha256_file(source_path) != source_cfg["raw_sha256"]:
        raise ValueError("UMWP source sha256 does not match cell.yaml")
    rows = load_jsonl(source_path)
    materialized: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {}
    answerable_ids: dict[str, dict[str, Any]] = {}
    for raw in rows:
        rid = str(raw["id"])
        answerable = bool(raw["answerable"])
        native = _source_name(raw)
        side = "answerable" if answerable else "unanswerable"
        counts.setdefault(native, {"answerable": 0, "unanswerable": 0})[side] += 1
        if answerable:
            aliases = canonical_answer_aliases(raw.get("answer"))
            if not aliases:
                raise ValueError(f"answerable row {rid} has no answer")
            answerable_ids[rid] = raw
        else:
            aliases = []
        materialized.append({
            "row_key": f"umwp:{rid}", "umwp_id": rid, "source": "umwp",
            "native_source": native, "original_pair_id": _original_pair_id(raw),
            "category_canon": None if raw.get("category") is None else str(raw["category"]),
            "answerable": answerable, "question": str(raw["question"]),
            "aliases": aliases,
        })
    by_key = {row["row_key"]: row for row in materialized}
    for row in materialized:
        if row["answerable"]:
            continue
        peer = by_key.get(f"umwp:{row['original_pair_id']}")
        if not peer or not peer["answerable"] or peer["native_source"] != row["native_source"]:
            raise ValueError(f"invalid same-source pair mapping for {row['row_key']}")
    expected_counts = source_cfg["native_source_counts"]
    checks = {
        "rows": len(rows), "answerable": sum(r["answerable"] for r in materialized),
        "unanswerable": sum(not r["answerable"] for r in materialized),
        "native_source_counts": counts,
    }
    if checks["rows"] != source_cfg["expected_rows"] or checks["answerable"] != source_cfg["expected_answerable"] or checks["unanswerable"] != source_cfg["expected_unanswerable"] or counts != expected_counts:
        raise ValueError(f"UMWP source counts differ from cell.yaml: {checks}")
    atomic_jsonl(out_path, materialized)
    audit = {**checks, "source_sha256": sha256_file(source_path), "pair_mapping_exact": True}
    atomic_json(out_path.parent / "source_audit.json", audit)
    return audit


def validate_source_materialization(cfg: dict[str, Any]) -> dict[str, Any]:
    """Revalidate the raw source and private materialization without trusting an audit file."""
    source_path = ANALYSIS / "source" / "StandardDataset.jsonl"
    rows_path = ANALYSIS / "source" / "rows.jsonl"
    source_cfg = cfg["source"]
    if not source_path.is_file() or not rows_path.is_file():
        raise ValueError("raw UMWP source or private materialization is missing")
    if sha256_file(source_path) != source_cfg["raw_sha256"]:
        raise ValueError("raw UMWP sha256 changed")
    raw_rows, rows = load_jsonl(source_path), load_jsonl(rows_path)
    if len(raw_rows) != source_cfg["expected_rows"] or len(rows) != source_cfg["expected_rows"]:
        raise ValueError("UMWP raw/materialized row coverage is not exactly 5200")
    raw_by_id = {str(r["id"]): r for r in raw_rows}
    row_by_key = {r["row_key"]: r for r in rows}
    if len(raw_by_id) != len(raw_rows) or len(row_by_key) != len(rows):
        raise ValueError("UMWP IDs are not unique")
    counts: dict[str, dict[str, int]] = {}
    for rid, raw in raw_by_id.items():
        key = f"umwp:{rid}"
        row = row_by_key.get(key)
        if row is None or row["question"] != str(raw["question"]):
            raise ValueError(f"materialized row mismatch for {key}")
        native = _source_name(raw)
        side = "answerable" if raw["answerable"] else "unanswerable"
        counts.setdefault(native, {"answerable": 0, "unanswerable": 0})[side] += 1
        if row["original_pair_id"] != _original_pair_id(raw) or row["native_source"] != native:
            raise ValueError(f"pair/source mapping mismatch for {key}")
        expected_category = None if raw.get("category") is None else str(raw["category"])
        if (
            row.get("umwp_id") != rid
            or row.get("source") != "umwp"
            or row.get("answerable") is not bool(raw["answerable"])
            or row.get("category_canon") != expected_category
        ):
            raise ValueError(f"materialized identity/class fields mismatch for {key}")
        if raw["answerable"]:
            if row["aliases"] != canonical_answer_aliases(raw.get("answer")):
                raise ValueError(f"answer aliases mismatch for {key}")
        elif row["aliases"] != []:
            raise ValueError(f"unanswerable aliases consumed for {key}")
    if counts != source_cfg["native_source_counts"]:
        raise ValueError("UMWP native-source counts changed")
    return {"source_sha256": source_cfg["raw_sha256"], "rows": len(rows), "native_source_counts": counts, "pair_mapping_exact": True}


def build_exclusion_manifest(model_id: str, rows: list[dict[str, Any]], cfg: dict[str, Any]) -> set[str]:
    prior_cfg = cfg["models"][model_id]["prior_atlas_pool"]
    path = Path(prior_cfg["local_artifact"])
    if not path.is_file() or sha256_file(path) != prior_cfg["sha256"]:
        raise ValueError("pinned model-specific prior-atlas artifact is missing or changed")
    prior: dict[str, list[str]] = {}
    for row in load_jsonl(path):
        if row.get("question"):
            prior.setdefault(normalize_question(str(row["question"])), []).append(prior_cfg["source_experiment"])
    excluded = []
    for row in rows:
        normalized = normalize_question(row["question"])
        if normalized in prior:
            excluded.append({
                "row_key": row["row_key"],
                "normalized_text_hash": __import__("hashlib").sha256(normalized.encode()).hexdigest(),
                "matched_prior_paths": sorted(set(prior[normalized])),
            })
    path = ANALYSIS / model_id / "prior_atlas_exclusions_private.jsonl"
    atomic_jsonl(path, excluded)
    atomic_json(ANALYSIS / model_id / "prior_atlas_exclusion_summary_private.json", {
        "model_id": model_id, "n_source_rows": len(rows), "n_excluded": len(excluded),
        "n_eligible": len(rows) - len(excluded),
        "prior_source_experiment": prior_cfg["source_experiment"],
        "prior_artifact_sha256": prior_cfg["sha256"],
    })
    return {r["row_key"] for r in excluded}


def surface_scalars(question: str, prompt_tokens: int) -> dict[str, float]:
    n = max(len(question), 1)
    return {
        "rendered_prompt_token_count": float(prompt_tokens),
        "question_char_count": float(len(question)),
        "question_word_count": float(len(question.split())),
        "question_line_count": float(question.count("\n") + 1),
        "digit_count": float(sum(c.isdigit() for c in question)),
        "digit_fraction": sum(c.isdigit() for c in question) / n,
        "punctuation_count": float(sum(c in string.punctuation for c in question)),
        "punctuation_fraction": sum(c in string.punctuation for c in question) / n,
        "newline_count": float(question.count("\n")),
        "newline_fraction": question.count("\n") / n,
        "uppercase_count": float(sum(c.isupper() for c in question)),
        "uppercase_fraction": sum(c.isupper() for c in question) / n,
    }


def render_prompt(model_id: str, tokenizer: Any, row: dict[str, Any]) -> str:
    if model_id == "gemma4_e4b_it":
        from render_gemma import render_with_tokenizer
    elif model_id == "qwen3_4b_raw_base":
        from render_qwen import render_with_tokenizer
    else:
        raise ValueError(f"unknown model renderer {model_id!r}")
    return render_with_tokenizer(tokenizer, row)


def resolve_eos_ids(tokenizer: Any) -> list[int]:
    ids: set[int] = set()
    raw = tokenizer.eos_token_id
    if isinstance(raw, (list, tuple, set)):
        ids.update(int(value) for value in raw if value is not None)
    elif raw is not None:
        ids.add(int(raw))
    for token in ("<|im_end|>", "<end_of_turn>"):
        value = tokenizer.convert_tokens_to_ids(token)
        if isinstance(value, int) and value >= 0 and value != tokenizer.unk_token_id:
            ids.add(value)
    if not ids:
        raise RuntimeError("tokenizer provides no valid EOS token id")
    return sorted(ids)


def assign_role(answerable: bool, grade: dict[str, Any]) -> str | None:
    g = grade["full_grader_dict"]
    if answerable:
        return "known_correct_answered" if g["well_formed_correct"] and not g["refused"] else None
    if g["clean_tighten"]:
        return "unknown_refused"
    if g["answered"] and not g["refused"]:
        return "confab"
    return None


class BaselineRunLog:
    STANDARD_GRADE_FIELDS = {
        "well_formed", "n_answer_keys", "single_answer_key", "trailing_clean",
        "answered", "correct", "well_formed_correct", "refused",
        "semantic_refuse", "degenerate", "clean_tighten", "confidence_valid",
        "terminated_naturally",
    }
    REQUIRED = {
        "row_key", "source", "native_source", "original_pair_id", "category_canon",
        "umwp_id", "answerable",
        "model", "model_revision", "renderer_id", "seed", "generation_text",
        "answer_value", "terminated_naturally", "n_new_tokens", "full_grader_dict",
        "role", "split", "triad_id", "cell_id", "layer", "arm",
        "dose_or_strength", "finish_reason", "last_completion_token_id",
        "eos_token_ids",
    } | STANDARD_GRADE_FIELDS

    def __init__(self, path: Path):
        self.path = path
        rows = load_jsonl(path)
        keys = [r["row_key"] for r in rows]
        if len(keys) != len(set(keys)):
            raise ValueError("run log has duplicate row keys")
        self.completed = set(keys)

    def append(self, row: dict[str, Any]) -> None:
        missing = self.REQUIRED - set(row)
        if missing:
            raise ValueError(f"run-log record missing {sorted(missing)}")
        full = row["full_grader_dict"]
        if not isinstance(full, dict) or not self.STANDARD_GRADE_FIELDS <= set(full):
            raise ValueError("run log requires the complete grader dictionary")
        if any(row[field] != full[field] for field in self.STANDARD_GRADE_FIELDS):
            raise ValueError("run log flattened grader fields differ from full_grader_dict")
        if row["row_key"] in self.completed:
            return
        append_jsonl_fsync(self.path, row)
        self.completed.add(row["row_key"])


def _fit_surface_basis(rows: list[dict[str, Any]], prompts: list[str], token_counts: list[int], model_id: str) -> None:
    from joblib import dump
    from scipy import sparse
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.preprocessing import StandardScaler

    cfg = load_yaml(ROOT / "cell.yaml")["surface_basis"]["lexical"]
    questions = [r["question"] for r in rows]
    word = HashingVectorizer(n_features=cfg["hash_features_word"], alternate_sign=False, ngram_range=tuple(cfg["word_ngram_range"]), norm=None)
    char = HashingVectorizer(analyzer="char", n_features=cfg["hash_features_char"], alternate_sign=False, ngram_range=tuple(cfg["char_ngram_range"]), norm=None)
    word_tf = TfidfTransformer(sublinear_tf=True).fit_transform(word.transform(questions))
    char_tf = TfidfTransformer(sublinear_tf=True).fit_transform(char.transform(questions))
    word_svd = TruncatedSVD(n_components=cfg["svd_components_word"], random_state=cfg["svd_seed"]).fit(word_tf)
    char_svd = TruncatedSVD(n_components=cfg["svd_components_char"], random_state=cfg["svd_seed"]).fit(char_tf)
    scalar_names = list(surface_scalars("x", 1))
    scalars = np.asarray([[surface_scalars(r["question"], n)[k] for k in scalar_names] for r, n in zip(rows, token_counts)], dtype=np.float64)
    projected = np.hstack([scalars, word_svd.transform(word_tf), char_svd.transform(char_tf)])
    scaler = StandardScaler().fit(projected)
    out = ANALYSIS / model_id / "surface"
    out.mkdir(parents=True, exist_ok=True)
    dump({"word": word, "char": char, "word_tfidf": TfidfTransformer(sublinear_tf=True).fit(word.transform(questions)), "char_tfidf": TfidfTransformer(sublinear_tf=True).fit(char.transform(questions)), "word_svd": word_svd, "char_svd": char_svd, "scaler": scaler, "scalar_names": scalar_names}, out / "basis.joblib")
    atomic_jsonl(out / "coordinates.jsonl", [
        {"row_key": r["row_key"], "scalars": dict(zip(scalar_names, scalars[i].tolist())), "matching_vector": scaler.transform(projected[i:i+1])[0].tolist()}
        for i, r in enumerate(rows)
    ])


def derive_finish_evidence(
    n_new_tokens: int, max_new_tokens: int, last_token_id: int | None,
    eos_token_ids: list[int],
) -> tuple[str, bool]:
    if n_new_tokens < 0 or n_new_tokens > max_new_tokens:
        raise ValueError("completion token count is outside the generation cap")
    if last_token_id is not None and last_token_id in eos_token_ids:
        return "eos_token", True
    if n_new_tokens >= max_new_tokens:
        return "length", False
    return "stopping_criteria", True


def run_generation(model_id: str, rows_path: Path) -> None:
    require_pinned_container()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    cfg = load_yaml(ROOT / "cell.yaml")
    validate_source_materialization(cfg)
    model_cfg = cfg["models"][model_id]
    source_rows = load_jsonl(rows_path)
    excluded = build_exclusion_manifest(model_id, source_rows, cfg)
    rows = [row for row in source_rows if row["row_key"] not in excluded]
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["repo"], revision=model_cfg["revision"], token=None, trust_remote_code=True)
    prompts = [render_prompt(model_id, tokenizer, row) for row in rows]
    token_counts = [len(tokenizer(p, add_special_tokens=True)["input_ids"]) for p in prompts]
    _fit_surface_basis(rows, prompts, token_counts, model_id)
    model = AutoModelForCausalLM.from_pretrained(model_cfg["repo"], revision=model_cfg["revision"], torch_dtype=torch.bfloat16, trust_remote_code=True).to("cuda:0").eval()
    log = BaselineRunLog(ANALYSIS / model_id / "generation_rows.jsonl")
    if log.completed & excluded:
        raise RuntimeError("an excluded prior-atlas row is present in the generation log")
    renderer_id = model_cfg["render_contract"]
    max_new_tokens = int(cfg["generation"]["max_new_tokens"])
    min_new_tokens = int(cfg["generation"]["min_new_tokens"])
    eos_ids = resolve_eos_ids(tokenizer)
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_ids[0]
    for row, prompt in zip(rows, prompts):
        if row["row_key"] in log.completed:
            continue
        enc = tokenizer(prompt, return_tensors="pt", add_special_tokens=True).to("cuda:0")
        with torch.inference_mode():
            output = model.generate(
                **enc,
                do_sample=False,
                num_beams=int(cfg["generation"]["num_beams"]),
                min_new_tokens=min_new_tokens,
                max_new_tokens=max_new_tokens,
                eos_token_id=eos_ids,
                pad_token_id=pad_token_id,
                return_dict_in_generate=True,
            )
        new_ids = output.sequences[0, enc["input_ids"].shape[1]:]
        text = tokenizer.decode(new_ids, skip_special_tokens=True)
        last_token_id = int(new_ids[-1]) if len(new_ids) else None
        finish_reason, terminated = derive_finish_evidence(
            int(len(new_ids)), max_new_tokens, last_token_id, eos_ids
        )
        aliases = row["aliases"] if row["answerable"] else None
        graded = grade_generation(text, aliases, terminated)
        role = assign_role(row["answerable"], graded)
        g = graded["full_grader_dict"]
        log.append({
            "row_key": row["row_key"], "source": "umwp", "native_source": row["native_source"],
            "original_pair_id": row["original_pair_id"], "category_canon": row["category_canon"],
            "umwp_id": row["umwp_id"], "answerable": row["answerable"],
            "model": model_cfg["repo"], "model_revision": model_cfg["revision"], "renderer_id": renderer_id,
            "seed": cfg["seed"], "generation_text": text, "answer_value": graded["answer_value"],
            "terminated_naturally": terminated, "n_new_tokens": int(len(new_ids)), "full_grader_dict": g,
            "finish_reason": finish_reason, "last_completion_token_id": last_token_id,
            "eos_token_ids": eos_ids,
            "role": role, "split": None, "triad_id": None, "cell_id": model_id,
            "layer": None, "arm": "baseline", "dose_or_strength": 0.0, **g,
        })
    final_keys = {r["row_key"] for r in load_jsonl(log.path)}
    eligible_keys = {r["row_key"] for r in rows}
    if final_keys != eligible_keys:
        raise RuntimeError(
            f"generation coverage mismatch: got {len(final_keys)}, expected {len(eligible_keys)} "
            f"eligible rows from {cfg['source']['expected_rows']} source rows"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("materialize")
    p.add_argument("--source", type=Path)
    p.add_argument("--download", action="store_true")
    g = sub.add_parser("generate")
    g.add_argument("--model-id", choices=["gemma4_e4b_it", "qwen3_4b_raw_base"], required=True)
    g.add_argument("--rows", type=Path, default=ANALYSIS / "source" / "rows.jsonl")
    args = parser.parse_args()
    if args.command == "materialize":
        cfg = load_yaml(ROOT / "cell.yaml")
        canonical_source = ANALYSIS / "source" / "StandardDataset.jsonl"
        source = args.source or canonical_source
        if args.download:
            source.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(cfg["source"]["official_url"], source)
        if source.resolve() != canonical_source.resolve():
            if sha256_file(source) != cfg["source"]["raw_sha256"]:
                raise ValueError("UMWP source sha256 does not match cell.yaml")
            canonical_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, canonical_source)
        print(json.dumps(materialize_source(canonical_source, ANALYSIS / "source" / "rows.jsonl", cfg), indent=2))
    else:
        run_generation(args.model_id, args.rows)


if __name__ == "__main__":
    main()
