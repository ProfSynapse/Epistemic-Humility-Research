#!/usr/bin/env python3
"""CPU-only surface residualization control for existing family-atlas captures.

This module contains the frozen analysis primitives and real-data driver. It
never imports torch, transformers, or a model. Private row text,
token IDs, row-level matrices, and activation caches may only live below this
experiment's gitignored analysis directory or the read-only source atlas roots.

Use ``synthetic-check`` for the non-evidence validation path. Running the real
control still requires a signed instrument and separate PI approval.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import yaml
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS_ROOT = (HERE / "analysis").resolve()
DEFAULT_CONFIG = HERE / "cell.yaml"
DEFAULT_GATES = HERE / "gates.yaml"

AGGREGATE_TOP_LEVEL_KEYS = {
    "schema_version",
    "report_kind",
    "experiment",
    "config_fingerprint",
    "substrates",
    "gates",
    "decision",
}

SCALAR_COLUMNS = (
    "rendered_prompt_token_count",
    "question_character_count",
    "question_whitespace_word_count",
    "question_line_count",
    "digit_count",
    "digit_fraction",
    "punctuation_count",
    "punctuation_fraction",
    "newline_count",
    "newline_fraction",
    "uppercase_count",
    "uppercase_fraction",
)


class ControlError(RuntimeError):
    """Fail-closed instrument error."""


@dataclass(frozen=True)
class SurfaceFeatures:
    low: np.ndarray
    lexical: np.ndarray
    combined: np.ndarray
    scalar_raw: np.ndarray
    scalar_names: tuple[str, ...]
    sources: np.ndarray
    categories: np.ndarray


@dataclass
class SourceData:
    name: str
    spec: dict[str, Any]
    root: Path
    committed_dir: Path
    capture_dir: Path
    rows: list[dict[str, Any]]
    roles: np.ndarray
    splits: np.ndarray
    sources: np.ndarray
    capture_files: list[Path]
    estimator: Any
    committed_profile: list[float]
    private_texts: set[str]
    provenance: dict[str, Any]
    fit_splits: tuple[str, ...] = ("fit", "fit_only")

    @property
    def fit_indices(self) -> np.ndarray:
        return np.where(np.isin(self.splits, self.fit_splits))[0]


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControlError(f"expected mapping in {path}")
    return payload


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def config_fingerprint(config_path: Path, gates_path: Path) -> str:
    h = hashlib.sha256()
    for path in (config_path, gates_path, Path(__file__)):
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def source_fingerprint(data: SourceData, instrument_fingerprint: str) -> str:
    h = hashlib.sha256(instrument_fingerprint.encode("ascii"))
    for label, record in sorted(data.provenance["files"].items()):
        h.update(label.encode("utf-8"))
        h.update(record["file_sha256"].encode("ascii"))
    h.update(data.provenance["activation_content_sha256"].encode("ascii"))
    return h.hexdigest()


def registered_layer_seed(cfg: dict[str, Any], layer: int) -> int:
    return int(cfg["seed"]) + int(layer)


def registered_planted_seed(cfg: dict[str, Any]) -> int:
    return registered_layer_seed(cfg, int(cfg["planted_signal"]["hs_index"]))


def paired_profile_deviation(
    controlled_unplanted: Sequence[float], controlled_planted: Sequence[float]
) -> float:
    unplanted = np.asarray(controlled_unplanted, dtype=np.float64)
    planted = np.asarray(controlled_planted, dtype=np.float64)
    if unplanted.shape != planted.shape or unplanted.ndim != 1:
        raise ControlError("paired controlled profiles must be aligned vectors")
    return float(
        np.max(np.abs(planted - unplanted) / np.maximum(np.abs(unplanted), 1e-30))
    )


def require_beneath_analysis(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ANALYSIS_ROOT)
    except ValueError as exc:
        raise ControlError(
            f"refusing output outside experiment analysis root: {resolved}"
        ) from exc
    return resolved


def _walk_private_text(value: Any, private_texts: set[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _walk_private_text(item, private_texts)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _walk_private_text(item, private_texts)
    elif isinstance(value, str):
        if value in private_texts:
            raise ControlError("aggregate output contains an exact private text value")
        for text in private_texts:
            if len(text) >= 16 and text in value:
                raise ControlError("aggregate output contains private text")


def _exact_keys(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControlError(f"aggregate {where} must be an object")
    if set(value) != expected:
        raise ControlError(
            f"aggregate {where} keys differ from positive schema: "
            f"expected={sorted(expected)} observed={sorted(value)}"
        )
    return value


def _numeric_array(value: Any, where: str) -> None:
    if not isinstance(value, list) or any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v)
        for v in value
    ):
        raise ControlError(f"aggregate {where} must be a finite numeric array")


def _finite_number(value: Any, where: str, allow_none: bool = False) -> None:
    if allow_none and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ControlError(f"aggregate {where} must be a finite number")


def _validate_peak(value: Any, where: str) -> None:
    peak = _exact_keys(
        value,
        {
            "peak_hs_index",
            "peak_depth",
            "classification",
            "peak_value",
            "runner_up_hs_index",
            "peak_to_runner_up_ratio",
        },
        where,
    )
    if peak["classification"] not in {"early-exterior", "beyond-early-exterior"}:
        raise ControlError(f"aggregate {where} has invalid classification")
    for key in (
        "peak_hs_index",
        "peak_depth",
        "peak_value",
        "runner_up_hs_index",
        "peak_to_runner_up_ratio",
    ):
        _finite_number(peak[key], f"{where}.{key}")


def _validate_provenance(value: Any, where: str) -> None:
    prov = _exact_keys(
        value,
        {
            "model_revision_match",
            "capture_coverage",
            "n_hidden_states",
            "hidden_size",
            "activation_content_sha256",
            "activation_file_count",
            "files",
            "counts",
            "fit_role_counts",
            "required_field_coverage",
            "missing_counts",
        },
        where,
    )
    files = _exact_keys(
        prov["files"],
        {"capture_manifest", "split_manifest", "atlas_summary", "capture_index", "capture_input", "private_rows", "estimator_module"},
        f"{where}.files",
    )
    for label, record in files.items():
        _exact_keys(record, {"path_sha256", "file_sha256", "record_count"}, f"{where}.files.{label}")
        if not isinstance(record["path_sha256"], str) or not isinstance(record["file_sha256"], str):
            raise ControlError(f"aggregate {where}.files.{label} hashes must be strings")
        _finite_number(record["record_count"], f"{where}.files.{label}.record_count")
    _exact_keys(
        prov["counts"],
        {"split_rows", "capture_index", "capture_input", "private_rows", "joined_rows", "fit_rows"},
        f"{where}.counts",
    )
    _exact_keys(
        prov["fit_role_counts"],
        {"confab", "known_correct_answered", "unknown_refused"},
        f"{where}.fit_role_counts",
    )
    _exact_keys(
        prov["required_field_coverage"],
        {"role", "split", "question", "source", "category", "render_template_id", "prompt_token_count"},
        f"{where}.required_field_coverage",
    )
    _exact_keys(
        prov["missing_counts"],
        {"capture_index", "capture_input", "private_rows", "capture_files", "question", "token_count", "activation_rows"},
        f"{where}.missing_counts",
    )
    if not isinstance(prov["model_revision_match"], bool):
        raise ControlError(f"aggregate {where}.model_revision_match must be boolean")
    for key in ("capture_coverage", "n_hidden_states", "hidden_size"):
        _finite_number(prov[key], f"{where}.{key}")
    if not isinstance(prov["activation_content_sha256"], str):
        raise ControlError(f"aggregate {where}.activation_content_sha256 must be a string")
    _finite_number(prov["activation_file_count"], f"{where}.activation_file_count")
    for section in ("counts", "fit_role_counts", "required_field_coverage", "missing_counts"):
        for key, item in prov[section].items():
            _finite_number(item, f"{where}.{section}.{key}")


PROFILE_KEYS = {
    "baseline",
    "low_dimensional_residual",
    "lexical_residual",
    "full_fit_combined_residual",
    "surface_explained",
    "full_fit_combined_residual_seeded_50pct",
}


def validate_aggregate(payload: dict[str, Any], allowed_substrates: set[str]) -> None:
    top = _exact_keys(payload, AGGREGATE_TOP_LEVEL_KEYS, "root")
    if top["report_kind"] not in {"preflight", "result"}:
        raise ControlError("aggregate report_kind must be preflight or result")
    if not isinstance(top["experiment"], str) or not isinstance(top["config_fingerprint"], str):
        raise ControlError("aggregate experiment and fingerprint must be strings")
    if set(top["substrates"]) - allowed_substrates:
        raise ControlError("aggregate contains an unregistered substrate")
    gate_summary = _exact_keys(top["gates"], {"G0", "G1", "G2", "G3", "G4", "G5"}, "gates")
    if any(not isinstance(value, (str, bool)) for value in gate_summary.values()):
        raise ControlError("aggregate gate summaries must be scalar strings or booleans")
    decision = _exact_keys(top["decision"], {"status", "reason"}, "decision")
    if not isinstance(decision["status"], str) or not isinstance(decision["reason"], str):
        raise ControlError("aggregate decision leaves must be strings")
    for name, report in top["substrates"].items():
        if top["report_kind"] == "preflight":
            _exact_keys(report, {"provenance"}, f"substrates.{name}")
            _validate_provenance(report["provenance"], f"substrates.{name}.provenance")
            continue
        result = _exact_keys(
            report,
            {"provenance", "profiles", "peaks", "data_exhaust", "planted", "permutations", "subsamples", "r2_profiles", "gates"},
            f"substrates.{name}",
        )
        _validate_provenance(result["provenance"], f"substrates.{name}.provenance")
        _exact_keys(result["profiles"], PROFILE_KEYS, f"substrates.{name}.profiles")
        _exact_keys(result["peaks"], PROFILE_KEYS, f"substrates.{name}.peaks")
        for key in PROFILE_KEYS:
            _numeric_array(result["profiles"][key], f"substrates.{name}.profiles.{key}")
            if result["profiles"][key]:
                _validate_peak(result["peaks"][key], f"substrates.{name}.peaks.{key}")
            elif result["peaks"][key] is not None:
                raise ControlError(f"aggregate empty profile {key} must have null peak")
        exhaust = _exact_keys(
            result["data_exhaust"],
            {
                "fit_row_count",
                "fit_manifest_sha256",
                "surface_matrix_sha256",
                "oof_prediction_content_sha256",
                "oof_prediction_file_count",
                "surface_shapes",
                "oof_prediction_blocks",
                "residual_reconstruction",
            },
            f"substrates.{name}.data_exhaust",
        )
        _finite_number(exhaust["fit_row_count"], f"substrates.{name}.data_exhaust.fit_row_count")
        if not isinstance(exhaust["fit_manifest_sha256"], str) or not isinstance(
            exhaust["surface_matrix_sha256"], str
        ):
            raise ControlError("aggregate data-exhaust hashes must be strings")
        if not isinstance(exhaust["oof_prediction_content_sha256"], str):
            raise ControlError("aggregate OOF prediction digest must be a string")
        _finite_number(
            exhaust["oof_prediction_file_count"],
            f"substrates.{name}.data_exhaust.oof_prediction_file_count",
        )
        shapes = _exact_keys(
            exhaust["surface_shapes"],
            {"low_dimensional", "lexical", "combined", "scalar_raw"},
            f"substrates.{name}.data_exhaust.surface_shapes",
        )
        for key, shape in shapes.items():
            _numeric_array(shape, f"substrates.{name}.data_exhaust.surface_shapes.{key}")
        if exhaust["oof_prediction_blocks"] != [
            "low_dimensional",
            "lexical",
            "combined",
        ]:
            raise ControlError("aggregate data-exhaust OOF blocks differ from registration")
        if exhaust["residual_reconstruction"] != "source_activation_minus_oof_prediction":
            raise ControlError("aggregate data-exhaust reconstruction rule differs")
        planted = _exact_keys(result["planted"], {"alpha", "raw_peak", "controlled_peak", "max_normalized_deviation", "pass"}, f"substrates.{name}.planted")
        if planted["raw_peak"] is not None:
            _validate_peak(planted["raw_peak"], f"substrates.{name}.planted.raw_peak")
            _validate_peak(planted["controlled_peak"], f"substrates.{name}.planted.controlled_peak")
        _finite_number(planted["alpha"], f"substrates.{name}.planted.alpha", allow_none=True)
        _finite_number(planted["max_normalized_deviation"], f"substrates.{name}.planted.max_normalized_deviation", allow_none=True)
        if not isinstance(planted["pass"], bool):
            raise ControlError("aggregate planted pass must be boolean")
        perm = _exact_keys(result["permutations"], {"n", "early_count", "median_abs_peak_shift", "peak_hs_indices", "max_early_r2", "pass"}, f"substrates.{name}.permutations")
        _numeric_array(perm["peak_hs_indices"], f"substrates.{name}.permutations.peak_hs_indices")
        _numeric_array(perm["max_early_r2"], f"substrates.{name}.permutations.max_early_r2")
        for key in ("n", "early_count", "median_abs_peak_shift"):
            _finite_number(perm[key], f"substrates.{name}.permutations.{key}")
        if not isinstance(perm["pass"], bool):
            raise ControlError("aggregate permutation pass must be boolean")
        subsamples = _exact_keys(result["subsamples"], {"full"}, f"substrates.{name}.subsamples")
        _exact_keys(subsamples["full"], {"n_rows", "profile", "peak", "support_pass"}, f"substrates.{name}.subsamples.full")
        for label, sub in subsamples.items():
            _numeric_array(sub["profile"], f"substrates.{name}.subsamples.{label}.profile")
            if sub["profile"]:
                _validate_peak(sub["peak"], f"substrates.{name}.subsamples.{label}.peak")
            if not isinstance(sub["support_pass"], bool):
                raise ControlError("aggregate subsample support flag must be boolean")
        _finite_number(subsamples["full"]["n_rows"], f"substrates.{name}.subsamples.full.n_rows")
        r2 = _exact_keys(result["r2_profiles"], {"observed", "permutations", "observed_early_max", "permutation_p95_early_max", "excess_over_p95"}, f"substrates.{name}.r2_profiles")
        _numeric_array(r2["observed"], f"substrates.{name}.r2_profiles.observed")
        if not isinstance(r2["permutations"], list):
            raise ControlError("aggregate permutation R2 profiles must be a list")
        for idx, profile in enumerate(r2["permutations"]):
            _numeric_array(profile, f"substrates.{name}.r2_profiles.permutations.{idx}")
        for key in ("observed_early_max", "permutation_p95_early_max", "excess_over_p95"):
            _finite_number(r2[key], f"substrates.{name}.r2_profiles.{key}")
        substrate_gates = _exact_keys(result["gates"], {"G0", "G1", "G2", "G3", "G4", "G5"}, f"substrates.{name}.gates")
        if any(not isinstance(value, bool) for value in substrate_gates.values()):
            raise ControlError("aggregate substrate gates must be booleans")


def write_aggregate(
    path: Path,
    payload: dict[str, Any],
    private_texts: Iterable[str],
    allowed_substrates: set[str] | None = None,
) -> None:
    target = require_beneath_analysis(path)
    validate_aggregate(payload, allowed_substrates or set(payload.get("substrates", {})))
    text_set = {t for t in private_texts if t}
    _walk_private_text(payload, text_set)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(target)


def write_checkpoint(path: Path, fingerprint: str, unit: str, payload: dict[str, Any]) -> None:
    target = require_beneath_analysis(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {"config_fingerprint": fingerprint, "unit": unit, "payload": payload}
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    tmp.replace(target)


def read_checkpoint(path: Path, fingerprint: str, unit: str) -> dict[str, Any] | None:
    target = require_beneath_analysis(path)
    if not target.exists():
        return None
    record = json.loads(target.read_text(encoding="utf-8"))
    if record.get("config_fingerprint") != fingerprint:
        raise ControlError(f"checkpoint fingerprint mismatch: {target}")
    if record.get("unit") != unit:
        raise ControlError(f"checkpoint unit mismatch: {target}")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise ControlError(f"malformed checkpoint payload: {target}")
    return payload


def write_surface_data_exhaust(
    data: SourceData,
    fit: np.ndarray,
    features: SurfaceFeatures,
) -> dict[str, Any]:
    """Persist row-aligned surface inputs needed to reuse OOF predictions."""
    if features.combined.shape[0] != fit.size:
        raise ControlError("surface exhaust must align one-to-one with fit rows")
    root = require_beneath_analysis(ANALYSIS_ROOT / "exhaust" / data.name)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "fit_rows_private.jsonl"
    manifest_tmp = manifest_path.with_suffix(".jsonl.tmp")
    with manifest_tmp.open("w", encoding="utf-8") as fh:
        for source_index in fit:
            row = data.rows[int(source_index)]
            fh.write(
                json.dumps(
                    {
                        "row_id": row["row_key"],
                        "role": row["role"],
                        "source": row["source"],
                        "category": row["category_canon"],
                        "split": row["split"],
                        "source_row_index": int(source_index),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    manifest_tmp.replace(manifest_path)

    matrices = {
        "low_dimensional": np.asarray(features.low, dtype=np.float32),
        "lexical": np.asarray(features.lexical, dtype=np.float32),
        "combined": np.asarray(features.combined, dtype=np.float32),
        "scalar_raw": np.asarray(features.scalar_raw, dtype=np.float32),
    }
    matrix_path = root / "surface_matrices.npz"
    matrix_tmp = matrix_path.with_suffix(".npz.tmp")
    with matrix_tmp.open("wb") as fh:
        np.savez_compressed(fh, **matrices)
    matrix_tmp.replace(matrix_path)
    return {
        "fit_row_count": int(fit.size),
        "fit_manifest_sha256": sha256_file(manifest_path),
        "surface_matrix_sha256": sha256_file(matrix_path),
        "oof_prediction_content_sha256": "",
        "oof_prediction_file_count": 0,
        "surface_shapes": {
            key: [int(value.shape[0]), int(value.shape[1])]
            for key, value in matrices.items()
        },
        "oof_prediction_blocks": ["low_dimensional", "lexical", "combined"],
        "residual_reconstruction": "source_activation_minus_oof_prediction",
    }


def finalize_oof_data_exhaust(
    data_exhaust: dict[str, Any],
    model_name: str,
    expected_layer_count: int | None = None,
) -> dict[str, Any]:
    """Bind aggregate provenance to the retained row-aligned OOF predictions."""
    checkpoint_root = require_beneath_analysis(ANALYSIS_ROOT / "checkpoints" / model_name)
    records: list[tuple[str, str]] = []
    for block in data_exhaust["oof_prediction_blocks"]:
        block_root = checkpoint_root / block
        for path in sorted(block_root.glob("hs*.npz")):
            records.append((path.relative_to(checkpoint_root).as_posix(), sha256_file(path)))
    if expected_layer_count is not None:
        expected_files = len(data_exhaust["oof_prediction_blocks"]) * expected_layer_count
        if len(records) != expected_files:
            raise ControlError(
                "OOF prediction exhaust is incomplete: "
                f"expected {expected_files} files, found {len(records)}"
            )
    digest = hashlib.sha256()
    for record in records:
        digest.update(json.dumps(record, separators=(",", ":")).encode("ascii"))
        digest.update(b"\n")
    updated = dict(data_exhaust)
    updated["oof_prediction_content_sha256"] = digest.hexdigest()
    updated["oof_prediction_file_count"] = len(records)
    return updated


def infer_source(row: dict[str, Any]) -> str:
    explicit = row.get("source")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()
    key = str(row.get("row_key", "")).lower()
    if "triviaqa" in key:
        return "triviaqa"
    if "popqa" in key:
        return "popqa"
    if "selfaware" in key:
        return "selfaware"
    if "kuq" in key:
        return "kuq"
    return "unknown"


def question_scalars(question: str, prompt_token_count: int) -> np.ndarray:
    n_chars = len(question)
    denom = max(n_chars, 1)
    digit = sum(ch.isdigit() for ch in question)
    punctuation = sum(ch in string.punctuation for ch in question)
    newline = question.count("\n")
    uppercase = sum(ch.isupper() for ch in question)
    return np.asarray(
        [
            prompt_token_count,
            n_chars,
            len(question.split()),
            question.count("\n") + 1,
            digit,
            digit / denom,
            punctuation,
            punctuation / denom,
            newline,
            newline / denom,
            uppercase,
            uppercase / denom,
        ],
        dtype=np.float64,
    )


def build_surface_features(rows: Sequence[dict[str, Any]], cfg: dict[str, Any]) -> SurfaceFeatures:
    """Build Z without consulting role or any model behavior field."""
    if not rows:
        raise ControlError("cannot build surface features from zero rows")
    lexical_cfg = cfg["surface_covariates"]["lexical"]
    questions: list[str] = []
    scalars: list[np.ndarray] = []
    categorical: list[list[str]] = []
    sources: list[str] = []
    categories: list[str] = []
    for row in rows:
        question = row.get("question")
        if not isinstance(question, str) or not question:
            raise ControlError("private row is missing non-empty question text")
        token_count = row.get("rendered_prompt_token_count")
        if not isinstance(token_count, int) or token_count <= 0:
            raise ControlError("row is missing positive rendered_prompt_token_count")
        source = infer_source(row)
        category = str(row.get("category_canon") or row.get("category") or "unknown")
        render_id = str(row.get("render_template_id") or "unknown")
        questions.append(question)
        scalars.append(question_scalars(question, token_count))
        categorical.append([render_id, source, category])
        sources.append(source)
        categories.append(category)

    scalar_raw = np.stack(scalars)
    scalar_z = StandardScaler().fit_transform(scalar_raw)
    one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float64)
    category_z = one_hot.fit_transform(categorical)
    low = np.concatenate([scalar_z, category_z], axis=1)

    word_hash = HashingVectorizer(
        n_features=int(lexical_cfg["word_hash_features"]),
        alternate_sign=bool(lexical_cfg["alternate_sign"]),
        analyzer="word",
        ngram_range=tuple(lexical_cfg["word_ngram_range"]),
        norm=None,
        lowercase=True,
    ).transform(questions)
    char_hash = HashingVectorizer(
        n_features=int(lexical_cfg["char_hash_features"]),
        alternate_sign=bool(lexical_cfg["alternate_sign"]),
        analyzer="char",
        ngram_range=tuple(lexical_cfg["char_ngram_range"]),
        norm=None,
        lowercase=True,
    ).transform(questions)
    word_tfidf = TfidfTransformer(
        sublinear_tf=bool(lexical_cfg["sublinear_tf"])
    ).fit_transform(word_hash)
    char_tfidf = TfidfTransformer(
        sublinear_tf=bool(lexical_cfg["sublinear_tf"])
    ).fit_transform(char_hash)
    max_rank = max(1, min(len(rows) - 1, word_tfidf.shape[1] - 1))
    word_rank = min(int(lexical_cfg["word_svd_components"]), max_rank)
    char_rank = min(int(lexical_cfg["char_svd_components"]), max_rank)
    seed = int(cfg["seed"])
    word_svd = TruncatedSVD(n_components=word_rank, random_state=seed).fit_transform(word_tfidf)
    char_svd = TruncatedSVD(n_components=char_rank, random_state=seed + 1).fit_transform(char_tfidf)
    lexical = StandardScaler().fit_transform(np.concatenate([word_svd, char_svd], axis=1))
    combined = np.concatenate([low, lexical], axis=1)
    return SurfaceFeatures(
        low=low,
        lexical=lexical,
        combined=combined,
        scalar_raw=scalar_raw,
        scalar_names=SCALAR_COLUMNS,
        sources=np.asarray(sources),
        categories=np.asarray(categories),
    )


def _make_strata(values: Sequence[str], n_splits: int) -> np.ndarray:
    labels = np.asarray([str(v) for v in values])
    unique, counts = np.unique(labels, return_counts=True)
    rare = set(unique[counts < n_splits])
    if rare:
        labels = np.asarray(["__rare__" if v in rare else v for v in labels])
    _, counts = np.unique(labels, return_counts=True)
    if counts.size == 0 or counts.min() < n_splits:
        labels = np.zeros(len(labels), dtype=int).astype(str)
    return labels


def crossfit_ridge(
    h: np.ndarray,
    z: np.ndarray,
    strata: Sequence[str],
    alpha_grid: Sequence[float],
    outer_folds: int,
    inner_folds: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    if h.ndim != 2 or z.ndim != 2 or h.shape[0] != z.shape[0]:
        raise ControlError("crossfit inputs must be aligned 2D matrices")
    yhat = np.empty_like(h, dtype=np.float64)
    chosen: list[float] = []
    outer_labels = _make_strata(strata, outer_folds)
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed)
    for fold, (train, test) in enumerate(outer.split(z, outer_labels)):
        inner_labels = _make_strata(np.asarray(strata)[train], inner_folds)
        inner = StratifiedKFold(
            n_splits=inner_folds, shuffle=True, random_state=seed + 100 + fold
        )
        losses: dict[float, list[float]] = {float(a): [] for a in alpha_grid}
        for inner_train, inner_valid in inner.split(z[train], inner_labels):
            tr = train[inner_train]
            va = train[inner_valid]
            for alpha in losses:
                model = Ridge(alpha=alpha, fit_intercept=True)
                model.fit(z[tr], h[tr])
                pred = model.predict(z[va])
                losses[alpha].append(mean_squared_error(h[va], pred))
        alpha = min(losses, key=lambda a: (float(np.mean(losses[a])), a))
        chosen.append(alpha)
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(z[train], h[train])
        yhat[test] = model.predict(z[test])
    return h.astype(np.float64) - yhat, yhat, chosen


def activation_oof_r2(h: np.ndarray, residual: np.ndarray) -> float:
    centered = h.astype(np.float64) - h.mean(axis=0, keepdims=True)
    total = float(np.sum(centered**2))
    if total <= 1e-30:
        return 0.0
    return float(1.0 - np.sum(residual.astype(np.float64) ** 2) / total)


def stratified_subsample_indices(
    strata: Sequence[str], fraction: float, seed: int
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    strata_array = np.asarray(strata)
    selected: list[int] = []
    for value in sorted(set(strata_array)):
        idx = np.where(strata_array == value)[0]
        take = max(1, int(np.floor(idx.size * fraction)))
        chosen = rng.choice(idx, size=take, replace=False)
        selected.extend(chosen.tolist())
    return np.asarray(sorted(selected), dtype=int)


def peak_summary(profile: Sequence[float], early_max_depth: float = 0.20) -> dict[str, Any]:
    values = np.asarray(profile, dtype=np.float64)
    if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)):
        raise ControlError("profile must be finite and contain at least two layers")
    order = np.argsort(values)[::-1]
    peak = int(order[0])
    runner = int(order[1])
    depth = peak / float(values.size - 1)
    return {
        "peak_hs_index": peak,
        "peak_depth": depth,
        "classification": "early-exterior" if depth <= early_max_depth else "beyond-early-exterior",
        "peak_value": float(values[peak]),
        "runner_up_hs_index": runner,
        "peak_to_runner_up_ratio": float(values[peak] / max(values[runner], 1e-30)),
    }


def standardized_surface_plant(
    z: np.ndarray, hidden_width: int, target_h: np.ndarray, seed: int
) -> np.ndarray:
    z_std = StandardScaler().fit_transform(z)
    rng = np.random.default_rng(seed)
    projection = rng.normal(size=(z_std.shape[1], hidden_width)) / np.sqrt(z_std.shape[1])
    surface = z_std @ projection
    surface -= surface.mean(axis=0, keepdims=True)
    target_centered = target_h - target_h.mean(axis=0, keepdims=True)
    source_rms = float(np.sqrt(np.mean(surface**2)))
    target_rms = float(np.sqrt(np.mean(target_centered**2)))
    if source_rms <= 1e-30 or target_rms <= 1e-30:
        raise ControlError("planted-signal RMS scaling is degenerate")
    return surface * (target_rms / source_rms)


def permute_within_strata(z: np.ndarray, strata: Sequence[str], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.empty_like(z)
    strata_array = np.asarray(strata)
    for value in np.unique(strata_array):
        idx = np.where(strata_array == value)[0]
        perm = idx.copy()
        rng.shuffle(perm)
        out[idx] = z[perm]
    return out


def import_pinned_estimator(path: Path):
    if not path.is_file():
        raise ControlError(f"pinned estimator module not found: {path}")
    spec = importlib.util.spec_from_file_location("source_atlas_panel", path)
    if spec is None or spec.loader is None:
        raise ControlError(f"cannot import estimator module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, "eff_dim_frac", None)):
        raise ControlError(f"source module does not expose eff_dim_frac: {path}")
    return module.eff_dim_frac


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControlError(f"expected JSON object: {path}")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ControlError(f"expected object at {path}:{line_no}")
            rows.append(value)
    return rows


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()


def _file_record(path: Path, count: int) -> dict[str, Any]:
    return {
        "path_sha256": _path_sha256(path),
        "file_sha256": sha256_file(path),
        "record_count": int(count),
    }


def activation_content_digest(
    capture_rows: Sequence[dict[str, Any]], capture_dir: Path
) -> tuple[str, int]:
    records: list[tuple[str, str, str]] = []
    root = capture_dir.resolve()
    for row in capture_rows:
        row_id = row.get("id")
        rel_file = row.get("file")
        if not isinstance(row_id, str) or not row_id:
            raise ControlError("capture index has a missing row identifier")
        if not isinstance(rel_file, str) or not rel_file:
            raise ControlError("capture index has a missing relative filename")
        normalized = Path(rel_file).as_posix()
        tensor_path = (root / normalized).resolve()
        try:
            tensor_path.relative_to(root)
        except ValueError as exc:
            raise ControlError("capture index file escapes capture directory") from exc
        if not tensor_path.is_file():
            raise ControlError("capture index references a missing activation file")
        records.append((row_id, normalized, sha256_file(tensor_path)))
    digest = hashlib.sha256()
    for record in sorted(records):
        digest.update(
            json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest(), len(records)


def load_source_data(
    name: str, spec: dict[str, Any], population_cfg: dict[str, Any] | None = None
) -> SourceData:
    root_value = os.environ.get(str(spec["atlas_root_env"]))
    rows_value = os.environ.get(str(spec["private_rows_env"]))
    if not root_value or not rows_value:
        raise ControlError(
            f"{name}: set {spec['atlas_root_env']} and {spec['private_rows_env']}"
        )
    root = Path(root_value).resolve()
    private_rows_path = Path(rows_value).resolve()
    committed = root / spec["committed_dir"]
    capture_dir = root / spec["capture_dir"]
    capture_input = root / spec["capture_input"]
    estimator = root / spec["estimator_module"]
    required = [
        root,
        private_rows_path,
        committed / "capture_manifest.json",
        committed / "split_manifest.json",
        committed / "atlas_summary.json",
        capture_dir / "capture.jsonl",
        capture_input,
        estimator,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ControlError(f"{name}: missing required private/source inputs: {missing}")
    manifest = _load_json(committed / "capture_manifest.json")
    expected = {
        "model": spec["model"],
        "revision": spec["revision"],
        "n_rows_captured": int(spec["expected_rows"]),
        "n_hidden_states": int(spec["n_hidden_states"]),
        "hidden_size": int(spec["hidden_size"]),
    }
    mismatches = {
        key: {"expected": value, "observed": manifest.get(key)}
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise ControlError(f"{name}: capture manifest mismatch: {mismatches}")
    if float(manifest.get("coverage_frac", 0.0)) != 1.0:
        raise ControlError(f"{name}: capture coverage must equal 1.0")

    split_path = committed / "split_manifest.json"
    summary_path = committed / "atlas_summary.json"
    index_path = capture_dir / "capture.jsonl"
    split_payload = _load_json(split_path)
    split_rows = split_payload.get("rows")
    if not isinstance(split_rows, list):
        raise ControlError(f"{name}: split manifest has no rows list")
    capture_rows = load_jsonl(index_path)
    capture_inputs = load_jsonl(capture_input)
    private_rows = load_jsonl(private_rows_path)
    activation_digest, activation_file_count = activation_content_digest(
        capture_rows, capture_dir
    )
    if manifest.get("capture_index_sha256") not in (None, sha256_file(index_path)):
        raise ControlError(f"{name}: capture index checksum differs from capture manifest")
    expected_hashes = spec.get("expected_sha256", {})
    actual_hashes = {
        "atlas_summary": sha256_file(summary_path),
        "capture_index": sha256_file(index_path),
        "capture_input": sha256_file(capture_input),
        "capture_manifest": sha256_file(committed / "capture_manifest.json"),
        "estimator_module": sha256_file(estimator),
        "private_rows": sha256_file(private_rows_path),
        "split_manifest": sha256_file(split_path),
    }
    for label, expected_hash in expected_hashes.items():
        if actual_hashes.get(label) != expected_hash:
            raise ControlError(f"{name}: pinned source checksum mismatch for {label}")
    expected_activation_digest = spec.get("expected_activation_content_sha256")
    if (
        expected_activation_digest is not None
        and activation_digest != expected_activation_digest
    ):
        raise ControlError(f"{name}: pinned activation-content digest mismatch")

    def indexed(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            value = row.get(key)
            if not isinstance(value, str) or not value:
                raise ControlError(f"{name}: {label} row lacks string {key}")
            if value in out:
                raise ControlError(f"{name}: duplicate identifier in {label}")
            out[value] = row
        return out

    split_by_id = indexed(split_rows, "row_key", "split manifest")
    index_by_id = indexed(capture_rows, "id", "capture index")
    input_by_id = indexed(capture_inputs, "id", "capture input")
    private_by_id = indexed(private_rows, "row_key", "private rows")
    expected_ids = set(split_by_id)
    missing_counts = {
        "capture_index": len(expected_ids - set(index_by_id)),
        "capture_input": len(expected_ids - set(input_by_id)),
        "private_rows": len(expected_ids - set(private_by_id)),
        "capture_files": 0,
        "question": 0,
        "token_count": 0,
        "activation_rows": 0,
    }
    extras = {
        "capture_index": len(set(index_by_id) - expected_ids),
        "capture_input": len(set(input_by_id) - expected_ids),
        "private_rows": len(set(private_by_id) - expected_ids),
    }
    if any(missing_counts[k] or extras[k] for k in extras):
        raise ControlError(f"{name}: source identifier joins are incomplete")

    joined_rows: list[dict[str, Any]] = []
    capture_files: list[Path] = []
    private_texts: set[str] = set()
    bad_meta = 0
    for row_id, split_row in split_by_id.items():
        index_row = index_by_id[row_id]
        input_row = input_by_id[row_id]
        private_row = private_by_id[row_id]
        question = private_row.get("question")
        if not isinstance(question, str) or not question:
            missing_counts["question"] += 1
            question = ""
        else:
            private_texts.add(question)
        token_ids = input_row.get("token_ids")
        if not isinstance(token_ids, list) or not token_ids:
            missing_counts["token_count"] += 1
            token_count = 0
        else:
            token_count = len(token_ids)
            positions = input_row.get("positions")
            if not isinstance(positions, dict) or positions.get("anchor") != token_count - 1:
                raise ControlError(f"{name}: capture-input anchor does not match token count")
        rel_file = index_row.get("file")
        if not isinstance(rel_file, str) or not rel_file:
            raise ControlError(f"{name}: capture index lacks file")
        tensor_path = (capture_dir / rel_file).resolve()
        try:
            tensor_path.relative_to(capture_dir.resolve())
        except ValueError as exc:
            raise ControlError(f"{name}: capture index file escapes capture directory") from exc
        if not tensor_path.is_file():
            missing_counts["capture_files"] += 1
        capture_files.append(tensor_path)
        if index_row.get("hidden_dim") != int(spec["hidden_size"]):
            bad_meta += 1
        if index_row.get("n_layers") != int(spec["n_hidden_states"]):
            bad_meta += 1
        source = infer_source({**private_row, **split_row})
        role = split_row.get("role")
        split = split_row.get("split")
        allowed_roles = set(
            (population_cfg or {}).get(
                "roles", ["confab", "known_correct_answered", "unknown_refused"]
            )
        )
        allowed_splits = set(
            (population_cfg or {}).get(
                "full_fit_splits", ["fit", "fit_only"]
            )
        ) | {"held_out"}
        if role not in allowed_roles:
            raise ControlError(f"{name}: split manifest contains an unregistered role")
        if split not in allowed_splits:
            raise ControlError(f"{name}: split manifest contains an unregistered split")
        if source == "unknown":
            raise ControlError(f"{name}: source inference left an unknown-origin row")
        category = str(
            split_row.get("category_canon")
            or private_row.get("category_canon")
            or "unknown"
        )
        joined_rows.append(
            {
                "row_key": row_id,
                "role": role,
                "split": split,
                "source": source,
                "category_canon": category,
                "question": question,
                "rendered_prompt_token_count": token_count,
                "render_template_id": str(spec.get("logical_experiment") or name),
            }
        )
    missing_counts["activation_rows"] = bad_meta
    if any(missing_counts.values()):
        raise ControlError(f"{name}: required source coverage is incomplete: {missing_counts}")
    if len(joined_rows) != int(spec["expected_rows"]):
        raise ControlError(f"{name}: joined row count differs from config")

    roles = np.asarray([str(row["role"]) for row in joined_rows])
    splits = np.asarray([str(row["split"]) for row in joined_rows])
    sources = np.asarray([str(row["source"]) for row in joined_rows])
    configured_fit_splits = tuple(
        (population_cfg or {}).get("full_fit_splits", ["fit", "fit_only"])
    )
    fit_mask = np.isin(splits, configured_fit_splits)
    if int(fit_mask.sum()) != int(spec["expected_fit_rows"]):
        raise ControlError(f"{name}: fit row count differs from config")
    role_names = ("confab", "known_correct_answered", "unknown_refused")
    fit_role_counts = {role: int(np.sum(fit_mask & (roles == role))) for role in role_names}
    required_coverage = {
        "role": int(sum(bool(row["role"]) for row in joined_rows)),
        "split": int(sum(bool(row["split"]) for row in joined_rows)),
        "question": int(sum(bool(row["question"]) for row in joined_rows)),
        "source": int(sum(bool(row["source"]) for row in joined_rows)),
        "category": int(sum(bool(row["category_canon"]) for row in joined_rows)),
        "render_template_id": len(joined_rows),
        "prompt_token_count": int(sum(row["rendered_prompt_token_count"] > 0 for row in joined_rows)),
    }
    atlas_summary = _load_json(summary_path)
    per_layer = atlas_summary.get("per_layer")
    if not isinstance(per_layer, dict):
        raise ControlError(f"{name}: atlas summary lacks per_layer")
    committed_profile = [
        float(per_layer[str(layer)]["profile"]["eff_dim_frac"])
        for layer in range(int(spec["n_hidden_states"]))
    ]
    provenance = {
        "model_revision_match": True,
        "capture_coverage": 1.0,
        "n_hidden_states": int(spec["n_hidden_states"]),
        "hidden_size": int(spec["hidden_size"]),
        "activation_content_sha256": activation_digest,
        "activation_file_count": activation_file_count,
        "files": {
            "capture_manifest": _file_record(committed / "capture_manifest.json", 1),
            "split_manifest": _file_record(split_path, len(split_rows)),
            "atlas_summary": _file_record(summary_path, 1),
            "capture_index": _file_record(index_path, len(capture_rows)),
            "capture_input": _file_record(capture_input, len(capture_inputs)),
            "private_rows": _file_record(private_rows_path, len(private_rows)),
            "estimator_module": _file_record(estimator, 1),
        },
        "counts": {
            "split_rows": len(split_rows),
            "capture_index": len(capture_rows),
            "capture_input": len(capture_inputs),
            "private_rows": len(private_rows),
            "joined_rows": len(joined_rows),
            "fit_rows": int(fit_mask.sum()),
        },
        "fit_role_counts": fit_role_counts,
        "required_field_coverage": required_coverage,
        "missing_counts": missing_counts,
    }
    return SourceData(
        name=name,
        spec=spec,
        root=root,
        committed_dir=committed,
        capture_dir=capture_dir,
        rows=joined_rows,
        roles=roles,
        splits=splits,
        sources=sources,
        capture_files=capture_files,
        estimator=import_pinned_estimator(estimator),
        committed_profile=committed_profile,
        private_texts=private_texts,
        provenance=provenance,
        fit_splits=configured_fit_splits,
    )


def load_activation_layer(data: SourceData, layer: int) -> np.ndarray:
    from safetensors.numpy import load_file

    key = f"anchor__L{layer}"
    matrix = np.empty(
        (len(data.rows), int(data.spec["hidden_size"])), dtype=np.float64
    )
    for idx, path in enumerate(data.capture_files):
        tensors = load_file(str(path))
        if key not in tensors:
            raise ControlError(f"{data.name}: activation file missing registered layer")
        vector = np.asarray(tensors[key], dtype=np.float64)
        if vector.shape != (int(data.spec["hidden_size"]),):
            raise ControlError(f"{data.name}: activation vector width mismatch")
        matrix[idx] = vector
    return matrix


def crossfit_ridge_incremental(
    h: np.ndarray,
    z: np.ndarray,
    strata: Sequence[str],
    alpha_grid: Sequence[float],
    outer_folds: int,
    inner_folds: int,
    seed: int,
    checkpoint_base: Path,
    fingerprint: str,
    unit: str,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    checkpoint_base = require_beneath_analysis(checkpoint_base)
    state_path = checkpoint_base.with_suffix(".npz")
    meta_path = checkpoint_base.with_suffix(".json")
    checkpoint_base.parent.mkdir(parents=True, exist_ok=True)
    outer_labels = _make_strata(strata, outer_folds)
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed)
    folds = list(outer.split(z, outer_labels))
    yhat = np.full_like(h, np.nan, dtype=np.float64)
    chosen: list[float] = []
    completed = 0
    meta = read_checkpoint(meta_path, fingerprint, unit)
    if meta is not None and state_path.exists():
        state = np.load(state_path)
        yhat = state["yhat"]
        completed = int(meta["completed_folds"])
        chosen = [float(v) for v in meta["chosen_alphas"]]
        if yhat.shape != h.shape or completed != len(chosen):
            raise ControlError(f"checkpoint state shape mismatch for {unit}")
    for fold, (train, test) in enumerate(folds):
        if fold < completed:
            continue
        inner_labels = _make_strata(np.asarray(strata)[train], inner_folds)
        inner = StratifiedKFold(
            n_splits=inner_folds, shuffle=True, random_state=seed + 100 + fold
        )
        losses: dict[float, list[float]] = {float(a): [] for a in alpha_grid}
        for inner_train, inner_valid in inner.split(z[train], inner_labels):
            tr = train[inner_train]
            va = train[inner_valid]
            for alpha in losses:
                model = Ridge(alpha=alpha, fit_intercept=True)
                model.fit(z[tr], h[tr])
                losses[alpha].append(mean_squared_error(h[va], model.predict(z[va])))
        alpha = min(losses, key=lambda a: (float(np.mean(losses[a])), a))
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(z[train], h[train])
        yhat[test] = model.predict(z[test])
        chosen.append(alpha)
        tmp_state = state_path.with_suffix(".npz.tmp")
        with tmp_state.open("wb") as fh:
            np.savez_compressed(fh, yhat=yhat)
        tmp_state.replace(state_path)
        write_checkpoint(
            meta_path,
            fingerprint,
            unit,
            {"completed_folds": fold + 1, "chosen_alphas": chosen},
        )
    if np.isnan(yhat).any():
        raise ControlError(f"crossfit checkpoint incomplete for {unit}")
    return h.astype(np.float64) - yhat, yhat, chosen


def _empty_profiles() -> dict[str, list[float]]:
    return {key: [] for key in PROFILE_KEYS}


def _empty_result(
    data: SourceData,
    gates: dict[str, bool],
    data_exhaust: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profiles = _empty_profiles()
    return {
        "provenance": data.provenance,
        "profiles": profiles,
        "peaks": {key: None for key in PROFILE_KEYS},
        "data_exhaust": data_exhaust
        or {
            "fit_row_count": 0,
            "fit_manifest_sha256": "",
            "surface_matrix_sha256": "",
            "oof_prediction_content_sha256": "",
            "oof_prediction_file_count": 0,
            "surface_shapes": {
                "low_dimensional": [0, 0],
                "lexical": [0, 0],
                "combined": [0, 0],
                "scalar_raw": [0, 0],
            },
            "oof_prediction_blocks": ["low_dimensional", "lexical", "combined"],
            "residual_reconstruction": "source_activation_minus_oof_prediction",
        },
        "planted": {
            "alpha": None,
            "raw_peak": None,
            "controlled_peak": None,
            "max_normalized_deviation": None,
            "pass": False,
        },
        "permutations": {
            "n": 0,
            "early_count": 0,
            "median_abs_peak_shift": 0.0,
            "peak_hs_indices": [],
            "max_early_r2": [],
            "pass": False,
        },
        "subsamples": {
            "full": {"n_rows": 0, "profile": [], "peak": None, "support_pass": False},
        },
        "r2_profiles": {
            "observed": [],
            "permutations": [],
            "observed_early_max": 0.0,
            "permutation_p95_early_max": 0.0,
            "excess_over_p95": 0.0,
        },
        "gates": {key: bool(gates.get(key, False)) for key in ("G0", "G1", "G2", "G3", "G4", "G5")},
    }


def run_substrate(
    data: SourceData, cfg: dict[str, Any], fingerprint: str
) -> dict[str, Any]:
    gates = {key: False for key in ("G0", "G1", "G2", "G3", "G4", "G5")}
    gates["G0"] = True
    fit = data.fit_indices
    fit_roles = data.roles[fit]
    fit_sources = data.sources[fit]
    strata_fit = np.asarray(
        [f"{source}|{role}" for source, role in zip(fit_sources, fit_roles)]
    )

    # G1 is completed before any controlled analysis.
    reproduced: list[float] = []
    max_dev = 0.0
    for layer in range(int(data.spec["n_hidden_states"])):
        h = load_activation_layer(data, layer)[fit]
        value = float(data.estimator(h))
        reproduced.append(value)
        max_dev = max(max_dev, abs(value - data.committed_profile[layer]))
        write_checkpoint(
            ANALYSIS_ROOT / "checkpoints" / data.name / "baseline" / f"hs{layer}.json",
            fingerprint,
            f"{data.name}:baseline:hs{layer}",
            {"eff_dim_frac": value, "abs_deviation": abs(value - data.committed_profile[layer])},
        )
    gates["G1"] = max_dev <= 1e-6
    if not gates["G1"]:
        return _empty_result(data, gates)

    features = build_surface_features([data.rows[int(index)] for index in fit], cfg)
    z_low = features.low
    z_lexical = features.lexical
    z_combined = features.combined
    data_exhaust = write_surface_data_exhaust(data, fit, features)

    profiles = _empty_profiles()
    profiles["baseline"] = reproduced
    observed_r2: list[float] = []
    residual_by_layer: list[np.ndarray] = []
    outer = int(cfg["residualization"]["outer_folds"])
    inner = int(cfg["residualization"]["inner_folds"])
    alpha_grid = cfg["residualization"]["alpha_grid"]
    for layer in range(int(data.spec["n_hidden_states"])):
        h = load_activation_layer(data, layer)[fit]
        layer_outputs: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for variant, z in (
            ("low_dimensional", z_low),
            ("lexical", z_lexical),
            ("combined", z_combined),
        ):
            residual, explained, _ = crossfit_ridge_incremental(
                h,
                z,
                strata_fit,
                alpha_grid,
                outer,
                inner,
                registered_layer_seed(cfg, layer),
                ANALYSIS_ROOT / "checkpoints" / data.name / variant / f"hs{layer}",
                fingerprint,
                f"{data.name}:{variant}:hs{layer}",
            )
            layer_outputs[variant] = (residual, explained)
        low_residual = layer_outputs["low_dimensional"][0]
        lexical_residual = layer_outputs["lexical"][0]
        combined_residual, combined_explained = layer_outputs["combined"]
        residual_by_layer.append(combined_residual)
        profiles["low_dimensional_residual"].append(float(data.estimator(low_residual)))
        profiles["lexical_residual"].append(float(data.estimator(lexical_residual)))
        profiles["full_fit_combined_residual"].append(float(data.estimator(combined_residual)))
        profiles["surface_explained"].append(float(data.estimator(combined_explained)))
        observed_r2.append(activation_oof_r2(h, combined_residual))
    data_exhaust = finalize_oof_data_exhaust(
        data_exhaust, data.name, int(data.spec["n_hidden_states"])
    )

    # G3: fixed hs2 planted surface peak.
    plant_cfg = cfg["planted_signal"]
    plant_layer = int(plant_cfg["hs_index"])
    h_plant = load_activation_layer(data, plant_layer)[fit]
    surface = standardized_surface_plant(
        z_combined,
        h_plant.shape[1],
        h_plant,
        seed=int(plant_cfg["projection_seed"]),
    )
    selected_alpha: float | None = None
    planted_raw_profile: list[float] | None = None
    for alpha in plant_cfg["alpha_grid"]:
        candidate = list(profiles["baseline"])
        candidate[plant_layer] = float(data.estimator(h_plant + float(alpha) * surface))
        summary = peak_summary(candidate)
        if (
            summary["peak_hs_index"] == plant_layer
            and summary["peak_to_runner_up_ratio"]
            >= float(plant_cfg["min_peak_to_runner_up_ratio"])
        ):
            selected_alpha = float(alpha)
            planted_raw_profile = candidate
            break
    planted = {
        "alpha": selected_alpha,
        "raw_peak": None,
        "controlled_peak": None,
        "max_normalized_deviation": None,
        "pass": False,
    }
    if selected_alpha is not None and planted_raw_profile is not None:
        planted_residual, _, _ = crossfit_ridge_incremental(
            h_plant + selected_alpha * surface,
            z_combined,
            strata_fit,
            alpha_grid,
            outer,
            inner,
            registered_planted_seed(cfg),
            ANALYSIS_ROOT / "checkpoints" / data.name / "planted" / f"hs{plant_layer}",
            fingerprint,
            f"{data.name}:planted:hs{plant_layer}:alpha{selected_alpha}",
        )
        controlled = list(profiles["full_fit_combined_residual"])
        controlled[plant_layer] = float(data.estimator(planted_residual))
        deviation = paired_profile_deviation(
            profiles["full_fit_combined_residual"], controlled
        )
        raw_peak = peak_summary(planted_raw_profile)
        controlled_peak = peak_summary(controlled)
        plant_pass = bool(
            controlled_peak["peak_hs_index"] != plant_layer
            and deviation
            <= float(plant_cfg["max_controlled_normalized_profile_deviation"])
        )
        planted = {
            "alpha": selected_alpha,
            "raw_peak": raw_peak,
            "controlled_peak": controlled_peak,
            "max_normalized_deviation": deviation,
            "pass": plant_pass,
        }
    gates["G3"] = bool(planted["pass"])
    if not gates["G3"]:
        peaks = {key: peak_summary(value) if value else None for key, value in profiles.items()}
        result = _empty_result(data, gates, data_exhaust)
        result.update(
            {
                "profiles": profiles,
                "peaks": peaks,
                "data_exhaust": data_exhaust,
                "planted": planted,
                "r2_profiles": {
                    "observed": observed_r2,
                    "permutations": [],
                    "observed_early_max": 0.0,
                    "permutation_p95_early_max": 0.0,
                    "excess_over_p95": 0.0,
                },
                "gates": gates,
            }
        )
        return result

    # G4 permutation bank, also used by G2's treatment-strength null.
    perm_cfg = cfg["permutation_control"]
    permutation_profiles: list[list[float]] = []
    permutation_r2: list[list[float]] = []
    permutation_peaks: list[int] = []
    early_limit = int(
        np.floor(
            float(cfg["peak_location"]["early_exterior_max_depth"])
            * (int(data.spec["n_hidden_states"]) - 1)
        )
    )
    for perm_no in range(int(perm_cfg["n_permutations"])):
        seed = int(perm_cfg["seed_start"]) + perm_no
        perm_z = permute_within_strata(z_combined, strata_fit, seed)
        profile: list[float] = []
        r2_profile: list[float] = []
        for layer in range(int(data.spec["n_hidden_states"])):
            h = load_activation_layer(data, layer)[fit]
            residual, _, _ = crossfit_ridge_incremental(
                h,
                perm_z,
                strata_fit,
                alpha_grid,
                outer,
                inner,
                int(cfg["seed"]) + 10000 + perm_no * 100 + layer,
                ANALYSIS_ROOT
                / "checkpoints"
                / data.name
                / "permutations"
                / f"perm{perm_no}"
                / f"hs{layer}",
                fingerprint,
                f"{data.name}:perm{perm_no}:hs{layer}",
            )
            profile.append(float(data.estimator(residual)))
            r2_profile.append(activation_oof_r2(h, residual))
        permutation_profiles.append(profile)
        permutation_r2.append(r2_profile)
        permutation_peaks.append(int(peak_summary(profile)["peak_hs_index"]))
    baseline_peak = int(peak_summary(profiles["baseline"])["peak_hs_index"])
    early_count = sum(
        peak / float(int(data.spec["n_hidden_states"]) - 1)
        <= float(cfg["peak_location"]["early_exterior_max_depth"])
        for peak in permutation_peaks
    )
    median_shift = float(
        np.median(np.abs(np.asarray(permutation_peaks) - baseline_peak))
    )
    max_early_r2 = [float(max(profile[1 : early_limit + 1])) for profile in permutation_r2]
    permutation_pass = bool(
        early_count >= int(perm_cfg["min_early_exterior"])
        and median_shift <= float(perm_cfg["max_median_abs_peak_shift_hs"])
    )
    gates["G4"] = permutation_pass

    treatment_cfg = cfg["treatment_strength"]
    observed_early_max = float(max(observed_r2[1 : early_limit + 1]))
    permutation_p95 = float(
        np.quantile(max_early_r2, float(treatment_cfg["permutation_null_quantile"]))
    )
    excess = observed_early_max - permutation_p95
    treatment_pass = bool(
        observed_early_max
        >= float(treatment_cfg["min_observed_max_activation_oof_r2"])
        and excess >= float(treatment_cfg["min_above_permutation_quantile"])
    )
    gates["G2"] = treatment_pass

    if not gates["G2"] or not gates["G4"]:
        peaks = {key: peak_summary(value) if value else None for key, value in profiles.items()}
        result = _empty_result(data, gates, data_exhaust)
        result.update(
            {
                "profiles": profiles,
                "peaks": peaks,
                "data_exhaust": data_exhaust,
                "planted": planted,
                "permutations": {
                    "n": int(perm_cfg["n_permutations"]),
                    "early_count": int(early_count),
                    "median_abs_peak_shift": median_shift,
                    "peak_hs_indices": permutation_peaks,
                    "max_early_r2": max_early_r2,
                    "pass": permutation_pass,
                },
                "r2_profiles": {
                    "observed": observed_r2,
                    "permutations": permutation_r2,
                    "observed_early_max": observed_early_max,
                    "permutation_p95_early_max": permutation_p95,
                    "excess_over_p95": excess,
                },
                "gates": gates,
            }
        )
        return result

    # Fixed-seed full-population stability guard.
    sub_cfg = cfg["subsample_guard"]
    full_sub = stratified_subsample_indices(
        strata_fit, float(sub_cfg["fraction"]), int(sub_cfg["seed"])
    )
    full_sub_profile = [
        float(data.estimator(residual[full_sub])) for residual in residual_by_layer
    ]
    profiles["full_fit_combined_residual_seeded_50pct"] = full_sub_profile
    peaks = {key: peak_summary(value) if value else None for key, value in profiles.items()}
    decisive = (
        "full_fit_combined_residual",
        "full_fit_combined_residual_seeded_50pct",
    )
    gates["G5"] = all(
        peaks[key]["classification"] == "early-exterior" for key in decisive
    )
    return {
        "provenance": data.provenance,
        "profiles": profiles,
        "peaks": peaks,
        "data_exhaust": data_exhaust,
        "planted": planted,
        "permutations": {
            "n": int(perm_cfg["n_permutations"]),
            "early_count": int(early_count),
            "median_abs_peak_shift": median_shift,
            "peak_hs_indices": permutation_peaks,
            "max_early_r2": max_early_r2,
            "pass": permutation_pass,
        },
        "subsamples": {
            "full": {
                "n_rows": int(full_sub.size),
                "profile": full_sub_profile,
                "peak": peak_summary(full_sub_profile),
                "support_pass": True,
            },
        },
        "r2_profiles": {
            "observed": observed_r2,
            "permutations": permutation_r2,
            "observed_early_max": observed_early_max,
            "permutation_p95_early_max": permutation_p95,
            "excess_over_p95": excess,
        },
        "gates": gates,
    }


def adjudicate_results(substrates: dict[str, dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    gate_summary = {
        gate: ("pass" if all(report["gates"][gate] for report in substrates.values()) else "fail")
        for gate in ("G0", "G1", "G2", "G3", "G4", "G5")
    }
    if any(gate_summary[gate] != "pass" for gate in ("G0", "G1", "G2", "G3", "G4")):
        return gate_summary, {
            "status": "indeterminate",
            "reason": "one or more integrity, treatment-strength, reachability, or negative-control gates failed",
        }
    invalid_stability_support = any(
        report.get("subsamples", {}).get("full", {}).get("support_pass") is False
        for report in substrates.values()
    )
    if invalid_stability_support:
        return gate_summary, {
            "status": "indeterminate",
            "reason": "a registered stability subsample failed its support recheck; no location verdict",
        }
    if gate_summary["G5"] == "pass":
        return gate_summary, {
            "status": "pass",
            "reason": "all registered primary and stability peaks remain early-exterior",
        }
    return gate_summary, {
        "status": "falsified",
        "reason": "at least one valid primary or registered stability peak moved beyond depth 0.20",
    }


def synthetic_check(cfg: dict[str, Any]) -> dict[str, Any]:
    rng = np.random.default_rng(int(cfg["seed"]))
    n, p, d = 160, 8, 24
    z = rng.normal(size=(n, p))
    h = rng.normal(scale=0.25, size=(n, d)) + z @ rng.normal(size=(p, d))
    strata = np.asarray([f"s{i % 4}" for i in range(n)])
    residual, explained, _ = crossfit_ridge(
        h,
        z,
        strata,
        cfg["residualization"]["alpha_grid"],
        outer_folds=5,
        inner_folds=3,
        seed=int(cfg["seed"]),
    )
    baseline_mse = float(np.mean(h**2))
    residual_mse = float(np.mean(residual**2))
    if not residual_mse < baseline_mse * 0.30:
        raise ControlError("synthetic ridge reachability failed")
    plant = standardized_surface_plant(z, d, h, seed=20260722)
    planted_residual, _, _ = crossfit_ridge(
        h + 2.0 * plant,
        z,
        strata,
        cfg["residualization"]["alpha_grid"],
        outer_folds=5,
        inner_folds=3,
        seed=int(cfg["seed"]),
    )
    if float(np.mean(planted_residual**2)) >= float(np.mean((h + 2.0 * plant) ** 2)) * 0.30:
        raise ControlError("synthetic planted control was not removable")
    permuted = permute_within_strata(z, strata, seed=5)
    if np.array_equal(permuted, z):
        raise ControlError("synthetic permutation did not change Z")

    def synthetic_eff_dim_frac(mat: np.ndarray) -> float:
        x = mat.astype(np.float64) - mat.mean(axis=0, keepdims=True)
        eigvals = np.clip(
            np.linalg.eigvalsh((x @ x.T) / max(x.shape[0] - 1, 1)), 0.0, None
        )
        return float(
            (eigvals.sum() ** 2 / max(float(np.sum(eigvals**2)), 1e-30))
            / x.shape[0]
        )

    profile_rng = np.random.default_rng(1)
    profile_n, profile_p, profile_d, n_layers = 120, 10, 30, 8
    profile_z = profile_rng.normal(size=(profile_n, profile_p))
    profile_strata = np.asarray([f"s{i % 4}" for i in range(profile_n)])
    layers: list[np.ndarray] = []
    for layer_no in range(n_layers):
        rank = 3 if layer_no == 1 else 1
        row_scalar = profile_rng.normal(size=(profile_n, rank))
        direction = profile_rng.normal(size=(rank, profile_d))
        layers.append(
            row_scalar @ direction
            + 0.01 * profile_rng.normal(size=(profile_n, profile_d))
        )
    raw_profile = [synthetic_eff_dim_frac(layer) for layer in layers]
    plant_layer = int(cfg["planted_signal"]["hs_index"])
    profile_surface = standardized_surface_plant(
        profile_z,
        profile_d,
        layers[plant_layer],
        int(cfg["planted_signal"]["projection_seed"]),
    )
    planted_alpha = None
    planted_raw_profile = None
    for alpha in cfg["planted_signal"]["alpha_grid"]:
        candidate = list(raw_profile)
        candidate[plant_layer] = synthetic_eff_dim_frac(
            layers[plant_layer] + float(alpha) * profile_surface
        )
        candidate_peak = peak_summary(candidate)
        if (
            candidate_peak["peak_hs_index"] == plant_layer
            and candidate_peak["peak_to_runner_up_ratio"]
            >= float(cfg["planted_signal"]["min_peak_to_runner_up_ratio"])
        ):
            planted_alpha = float(alpha)
            planted_raw_profile = candidate
            break
    if planted_alpha is None or planted_raw_profile is None:
        raise ControlError("synthetic registered hs2 peak was unreachable")
    controlled_profile = []
    for layer_no, layer in enumerate(layers):
        residual_layer, _, _ = crossfit_ridge(
            layer,
            profile_z,
            profile_strata,
            cfg["residualization"]["alpha_grid"],
            5,
            3,
            registered_layer_seed(cfg, layer_no),
        )
        controlled_profile.append(synthetic_eff_dim_frac(residual_layer))
    planted_residual_layer, _, _ = crossfit_ridge(
        layers[plant_layer] + planted_alpha * profile_surface,
        profile_z,
        profile_strata,
        cfg["residualization"]["alpha_grid"],
        5,
        3,
        registered_planted_seed(cfg),
    )
    controlled_planted = list(controlled_profile)
    controlled_planted[plant_layer] = synthetic_eff_dim_frac(planted_residual_layer)
    normalized_deviation = paired_profile_deviation(
        controlled_profile, controlled_planted
    )
    planted_relocated = peak_summary(controlled_planted)["peak_hs_index"] != plant_layer
    planted_tolerance = normalized_deviation <= float(
        cfg["planted_signal"]["max_controlled_normalized_profile_deviation"]
    )
    if not planted_relocated or not planted_tolerance:
        raise ControlError("synthetic registered planted endpoint failed")
    return {
        "ridge_reachability": True,
        "planted_removal_reachability": True,
        "permutation_changes_alignment": True,
        "registered_hs2_unique_peak": True,
        "registered_hs2_relocated": planted_relocated,
        "registered_profile_tolerance": planted_tolerance,
        "registered_profile_normalized_deviation": normalized_deviation,
        "baseline_mse": baseline_mse,
        "residual_mse": residual_mse,
        "explained_mse": float(np.mean(explained**2)),
    }


def cmd_preflight(args: argparse.Namespace) -> int:
    cfg = load_yaml(args.config)
    selected = args.substrates or list(cfg["source_roots"])
    data = [
        load_source_data(name, cfg["source_roots"][name], cfg["population"])
        for name in selected
    ]
    fingerprint = config_fingerprint(args.config, args.gates)
    payload = {
        "schema_version": 1,
        "report_kind": "preflight",
        "experiment": "family-atlas-surface-residualization-control",
        "config_fingerprint": fingerprint,
        "substrates": {item.name: {"provenance": item.provenance} for item in data},
        "gates": {
            "G0": "pass",
            "G1": "not_run",
            "G2": "not_run",
            "G3": "not_run",
            "G4": "not_run",
            "G5": "not_run",
        },
        "decision": {
            "status": "preflight_only",
            "reason": "source coverage and containment inputs validated; no profile computed",
        },
    }
    private_texts = set().union(*(item.private_texts for item in data))
    validate_aggregate(payload, set(cfg["source_roots"]))
    _walk_private_text(payload, private_texts)
    if args.report:
        report_path = ANALYSIS_ROOT / "preflight_report.json"
        write_aggregate(
            report_path, payload, private_texts, allowed_substrates=set(cfg["source_roots"])
        )
        print(json.dumps({"preflight": "pass", "report": str(report_path)}, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_yaml(args.config)
    selected = args.substrates or list(cfg["source_roots"])
    if set(selected) != set(cfg["source_roots"]) or len(selected) != len(cfg["source_roots"]):
        raise ControlError(
            "real run requires the exact registered substrate set; use preflight for partial checks"
        )
    fingerprint = config_fingerprint(args.config, args.gates)
    data = [
        load_source_data(name, cfg["source_roots"][name], cfg["population"])
        for name in selected
    ]
    reports: dict[str, dict[str, Any]] = {}
    for item in data:
        reports[item.name] = run_substrate(
            item, cfg, source_fingerprint(item, fingerprint)
        )
    gate_summary, decision = adjudicate_results(reports)
    payload = {
        "schema_version": 1,
        "report_kind": "result",
        "experiment": "family-atlas-surface-residualization-control",
        "config_fingerprint": fingerprint,
        "substrates": reports,
        "gates": gate_summary,
        "decision": decision,
    }
    private_texts = set().union(*(item.private_texts for item in data))
    output = ANALYSIS_ROOT / cfg["execution"]["aggregate_filename"]
    write_aggregate(
        output, payload, private_texts, allowed_substrates=set(cfg["source_roots"])
    )
    print(json.dumps({"status": decision["status"], "output": str(output)}, sort_keys=True))
    return 0


def cmd_synthetic(args: argparse.Namespace) -> int:
    cfg = load_yaml(args.config)
    report = synthetic_check(cfg)
    print(json.dumps({"synthetic_check": report}, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--gates", type=Path, default=DEFAULT_GATES)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn in (("preflight", cmd_preflight), ("run", cmd_run)):
        command = sub.add_parser(name)
        command.add_argument("--substrates", nargs="*", default=[])
        if name == "preflight":
            command.add_argument(
                "--report", action="store_true", help="write aggregate-only preflight report"
            )
        command.set_defaults(func=fn)
    synthetic = sub.add_parser("synthetic-check")
    synthetic.set_defaults(func=cmd_synthetic)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ControlError as exc:
        print(f"[STOP] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
