#!/usr/bin/env python3
"""CPU-only surface-control reanalysis for flavor-atlas-surface-control-confirmatory
(AMENDMENT.md Design). Analysis-only reread of flavor-atlas-rawbase's existing
captures: no model is loaded, no GPU verb runs, and no file under any
extraction/ directory is ever opened for writing.

Reuses the pinned item-26 protocol UNCHANGED for every AUROC computed here (S1,
S2, S3, C2, C3):
    ../ood-breadth-beyond-selfaware/internal_panel_probe_gate.py::_cv_auroc_with_oof
    (StandardScaler + L2 LogisticRegression C=0.5, StratifiedKFold(5, seed=0),
    held-out out-of-fold AUROC).

The cross-fitted ridge residualization, activation-OOF-R2, within-strata
permutation, and standardized linear plant follow the same construction as
../family-atlas-surface-residualization-control/reanalyze_surface_residualization.py
(read for reference per AMENDMENT.md, never imported -- experiment boundaries
stay separate), adapted here for a surface basis that ADDS an explicit
interrogative-form block and PROHIBITS source/panel/category/flavor/label
(AMENDMENT.md "Prohibited inputs": here the label IS pool membership and
flavor IS the KUQ category, so admitting either would hand the surface model
the answer). The planted-signal construction (C3) also differs from that
reference cell: it is a single scalar surface score projected along one
seeded random unit direction (AMENDMENT.md C3), not a projection matrix.

`build_surface_matrix` is passed only bare question strings and integer
token counts -- never a row dict -- so the SG3 prohibition is structural,
not a runtime scan. Every threshold and constant used in gate adjudication
is read from gates.yaml / cell.yaml at runtime; nothing decision-relevant is
a bare literal in this file.

Real run (CPU only, after `bin/exp sign`):
    python3 experiments/flavor-atlas-surface-control-confirmatory/reanalyze_surface_control.py \\
        --out experiments/flavor-atlas-surface-control-confirmatory/analysis-committed/surface_control.json

Synthetic smoke (no real captures touched, exercises every stage):
    python3 experiments/flavor-atlas-surface-control-confirmatory/reanalyze_surface_control.py --smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import string
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RAWBASE_DIR = HERE.parent / "flavor-atlas-rawbase"
ITEM26_DIR = HERE.parent / "ood-breadth-beyond-selfaware"
LATENT_CONTROLS_DIR = HERE.parent / "selfaware-latent-knowledge-controls"
RENDERS_DIR = REPO_ROOT / "experiments" / "common" / "renders"
CELL_PATH = HERE / "cell.yaml"
GATES_PATH = HERE / "gates.yaml"
ANALYSIS_ROOT = (HERE / "analysis").resolve()
DEFAULT_COMMITTED_PATH = HERE / "analysis-committed" / "surface_control.json"

sys.path.insert(0, str(ITEM26_DIR))
sys.path.insert(0, str(LATENT_CONTROLS_DIR))
sys.path.insert(0, str(RENDERS_DIR))

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]
INTERROGATIVE_BUCKETS = [
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "auxiliary_or_copula", "other",
]
WH_TOKENS = {"what", "which", "who", "whom", "whose", "when", "where", "why", "how"}
AUXILIARY_LEAD_TOKENS = {
    "is", "are", "was", "were", "do", "does", "did", "can", "could",
    "will", "would", "should", "has", "have", "had",
}
GATE_ORDER = ["SG0", "SG1", "SG2", "SG3", "SG4", "SG5", "SG6", "SG7", "SG8"]


class ControlError(RuntimeError):
    """Fail-closed instrument error; any SG failure raises this."""


# --------------------------------------------------------------------------
# IO helpers
# --------------------------------------------------------------------------

def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControlError(f"expected mapping in {path}")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_beneath_analysis(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ANALYSIS_ROOT)
    except ValueError as exc:
        raise ControlError(f"refusing output outside experiment analysis root: {resolved}") from exc
    return resolved


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def write_checkpoint(path: Path, fingerprint: str, unit: str, payload: dict[str, Any]) -> None:
    atomic_write_json(
        require_beneath_analysis(path),
        {"config_fingerprint": fingerprint, "unit": unit, "payload": payload},
    )


def read_checkpoint(path: Path, fingerprint: str, unit: str) -> dict[str, Any] | None:
    target = require_beneath_analysis(path)
    if not target.exists():
        return None
    record = json.loads(target.read_text(encoding="utf-8"))
    if record.get("config_fingerprint") != fingerprint or record.get("unit") != unit:
        raise ControlError(f"checkpoint fingerprint/unit mismatch: {target}")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise ControlError(f"malformed checkpoint payload: {target}")
    return payload


def config_fingerprint(cell: dict[str, Any], gates: dict[str, Any]) -> str:
    h = hashlib.sha256()
    for payload in (cell, gates):
        h.update(json.dumps(payload, sort_keys=True).encode("utf-8"))
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def _walk_private_text(value: Any, private_texts: set[str]) -> None:
    """SG7: refuse to commit an aggregate that contains any known question
    text verbatim or as a long substring."""
    if isinstance(value, dict):
        for item in value.values():
            _walk_private_text(item, private_texts)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _walk_private_text(item, private_texts)
    elif isinstance(value, str):
        if value in private_texts:
            raise ControlError("aggregate output contains an exact private question text value")
        for text in private_texts:
            if len(text) >= 16 and text in value:
                raise ControlError("aggregate output contains private question text")


# --------------------------------------------------------------------------
# Surface featurization -- SG3 structural guarantee: these functions see
# only bare strings/ints, never a row dict, never source/panel/category/
# flavor/label (AMENDMENT.md "Prohibited inputs"; gates.yaml sg3).
# --------------------------------------------------------------------------

def question_scalars(question: str, token_count: int) -> np.ndarray:
    n_chars = len(question)
    denom = max(n_chars, 1)
    digit = sum(ch.isdigit() for ch in question)
    punctuation = sum(ch in string.punctuation for ch in question)
    newline = question.count("\n")
    uppercase = sum(ch.isupper() for ch in question)
    return np.asarray(
        [
            token_count,
            n_chars,
            len(question.split()),
            newline + 1,
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


def leading_interrogative_bucket(question: str) -> str:
    stripped = question.strip()
    if not stripped:
        return "other"
    first = stripped.split()[0].strip(string.punctuation).lower()
    if first in WH_TOKENS:
        return first
    if first in AUXILIARY_LEAD_TOKENS:
        return "auxiliary_or_copula"
    return "other"


def interrogative_features(question: str) -> np.ndarray:
    bucket = leading_interrogative_bucket(question)
    one_hot = [1.0 if bucket == b else 0.0 for b in INTERROGATIVE_BUCKETS]
    terminal_qmark = 1.0 if question.strip().endswith("?") else 0.0
    any_digit = 1.0 if any(ch.isdigit() for ch in question) else 0.0
    return np.asarray(one_hot + [terminal_qmark, any_digit], dtype=np.float64)


@dataclass(frozen=True)
class SurfaceFeatures:
    low: np.ndarray
    lexical: np.ndarray
    combined: np.ndarray
    scalar_raw: np.ndarray


def build_surface_matrix(
    questions: Sequence[str], token_counts: Sequence[int], cfg: dict[str, Any]
) -> SurfaceFeatures:
    """Unsupervised, transductive fit over the FULL question population.
    Sees only bare question strings and token counts -- the structural
    guarantee that no label/source/panel/category/flavor can enter Z."""
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.preprocessing import StandardScaler

    if len(questions) != len(token_counts):
        raise ControlError("questions and token_counts must be aligned")
    if not questions:
        raise ControlError("cannot build surface features from zero rows")

    lexical_cfg = cfg["surface_covariates"]["lexical"]
    seed = int(cfg["seed"])

    scalar_raw = np.stack([question_scalars(q, int(t)) for q, t in zip(questions, token_counts)])
    scalar_z = StandardScaler().fit_transform(scalar_raw)
    interrogative = np.stack([interrogative_features(q) for q in questions])
    low = np.concatenate([scalar_z, interrogative], axis=1)

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
    word_tfidf = TfidfTransformer(sublinear_tf=bool(lexical_cfg["sublinear_tf"])).fit_transform(word_hash)
    char_tfidf = TfidfTransformer(sublinear_tf=bool(lexical_cfg["sublinear_tf"])).fit_transform(char_hash)
    max_rank = max(1, min(len(questions) - 1, word_tfidf.shape[1] - 1))
    word_rank = min(int(lexical_cfg["word_svd_components"]), max_rank)
    char_rank = min(int(lexical_cfg["char_svd_components"]), max_rank)
    word_svd = TruncatedSVD(n_components=word_rank, random_state=seed).fit_transform(word_tfidf)
    char_svd = TruncatedSVD(n_components=char_rank, random_state=seed + 1).fit_transform(char_tfidf)
    lexical = StandardScaler().fit_transform(np.concatenate([word_svd, char_svd], axis=1))

    combined = np.concatenate([low, lexical], axis=1)
    return SurfaceFeatures(low=low, lexical=lexical, combined=combined, scalar_raw=scalar_raw)


def get_token_count(row: dict[str, Any], render_fn, tokenizer_cache: list) -> int:
    """rendered_prompt_token_count, from the row if already recorded, else
    from the cached tokenizer on CPU (AMENDMENT.md Compute budget). Only
    `question` is ever handed to `render_fn`, never the full row."""
    explicit = row.get("rendered_prompt_token_count")
    if isinstance(explicit, int) and explicit > 0:
        return explicit
    if not tokenizer_cache:
        import ood_breadth_response_confidence_render as render_mod

        tokenizer_cache.append(render_mod._get_tokenizer())
    tokenizer = tokenizer_cache[0]
    prompt = render_fn({"question": row["question"]})
    return len(tokenizer(prompt).input_ids)


# --------------------------------------------------------------------------
# Cross-fitted ridge residualization
# --------------------------------------------------------------------------

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


def crossfit_ridge_incremental(
    h: np.ndarray,
    z: np.ndarray,
    strata: Sequence[str],
    alpha_grid: Sequence[float],
    outer_folds: int,
    inner_folds: int,
    seed: int,
    checkpoint_path: Path | None,
    fingerprint: str,
    unit: str,
    _abort_after_fold: int | None = None,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Returns (residual = h - yhat, yhat, chosen alphas per outer fold).
    Every row of yhat is predicted without that row's own activation
    (AMENDMENT.md "Cross-fitting"). Resumable per outer fold when
    checkpoint_path is given -- state (partial yhat) is flushed to disk
    after every completed fold, so a kill loses at most one fold's work.

    `_abort_after_fold` is a smoke-only interrupt hook: it raises
    InterruptedError immediately after the named fold's checkpoint is
    written, to exercise the resume path against a real partial-completion
    state rather than only the from-scratch and fully-resumed cases.
    """
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error
    from sklearn.model_selection import StratifiedKFold

    if h.ndim != 2 or z.ndim != 2 or h.shape[0] != z.shape[0]:
        raise ControlError("crossfit inputs must be aligned 2D matrices")
    outer_labels = _make_strata(strata, outer_folds)
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed)
    folds = list(outer.split(z, outer_labels))

    yhat = np.full_like(h, np.nan, dtype=np.float64)
    chosen: list[float] = []
    completed = 0
    state_path = meta_path = None
    if checkpoint_path is not None:
        state_path = require_beneath_analysis(checkpoint_path.with_suffix(".npz"))
        meta_path = require_beneath_analysis(checkpoint_path.with_suffix(".json"))
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
        inner = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=seed + 100 + fold)
        losses: dict[float, list[float]] = {float(a): [] for a in alpha_grid}
        for inner_train, inner_valid in inner.split(z[train], inner_labels):
            tr, va = train[inner_train], train[inner_valid]
            for alpha in losses:
                model = Ridge(alpha=alpha, fit_intercept=True)
                model.fit(z[tr], h[tr])
                losses[alpha].append(mean_squared_error(h[va], model.predict(z[va])))
        alpha = min(losses, key=lambda a: (float(np.mean(losses[a])), a))
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(z[train], h[train])
        yhat[test] = model.predict(z[test])
        chosen.append(alpha)
        if checkpoint_path is not None:
            tmp = state_path.with_suffix(".npz.tmp")
            with tmp.open("wb") as fh:
                np.savez_compressed(fh, yhat=yhat)
            tmp.replace(state_path)
            write_checkpoint(meta_path, fingerprint, unit, {"completed_folds": fold + 1, "chosen_alphas": chosen})
        if _abort_after_fold is not None and fold == _abort_after_fold:
            raise InterruptedError(f"smoke-only abort after fold {fold}")

    if np.isnan(yhat).any():
        raise ControlError(f"crossfit checkpoint incomplete for {unit}")
    return h.astype(np.float64) - yhat, yhat, chosen


def activation_oof_r2(h: np.ndarray, residual: np.ndarray) -> float:
    """The REGISTERED treatment-strength statistic (gates.yaml sg4): out-of-
    fold R2 of the cross-fitted ridge prediction. See
    `_naive_in_sample_r2_WRONG` for the plausible-but-unregistered
    alternative this deliberately differs from."""
    centered = h.astype(np.float64) - h.mean(axis=0, keepdims=True)
    total = float(np.sum(centered**2))
    if total <= 1e-30:
        return 0.0
    return float(1.0 - np.sum(residual.astype(np.float64) ** 2) / total)


def _naive_in_sample_r2_WRONG(h: np.ndarray, z: np.ndarray, alpha: float = 1.0) -> float:
    """NOT the registered formula. Fits and scores ridge on the SAME rows
    (no cross-fitting), which is optimistically biased relative to the
    honest out-of-fold statistic `activation_oof_r2` computed from
    `crossfit_ridge_incremental`'s residual. Exists only so the smoke check
    can assert the registered value is not silently interchangeable with
    this plausible-looking alternative."""
    from sklearn.linear_model import Ridge

    model = Ridge(alpha=alpha, fit_intercept=True).fit(z, h)
    residual = h - model.predict(z)
    return activation_oof_r2(h, residual)


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


def fit_pooled_surface_weights(z: np.ndarray, y_unknown: np.ndarray, seed: int) -> np.ndarray:
    """C3 construction step 1: fit the pinned probe family (same scaler,
    same C=0.5) on Z alone over the full KUQ panel, pooled unknown-vs-known
    label, to obtain w. Standardization is fit here and reused by the
    caller to build s = Z_std @ w."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(z)
    clf = LogisticRegression(C=0.5, max_iter=2000, random_state=seed)
    clf.fit(sc.transform(z), y_unknown)
    return sc, clf.coef_.ravel()


def seeded_unit_vector(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    u = rng.normal(size=dim)
    norm = float(np.linalg.norm(u))
    if norm <= 1e-30:
        raise ControlError("degenerate seeded unit vector")
    return u / norm


def plant_hidden_state_0(
    h0: np.ndarray, s: np.ndarray, u: np.ndarray, gamma_grid_value: float, hs1_rms: float
) -> np.ndarray:
    """AMENDMENT.md C3: add gamma * s along u, gamma = grid_value * hs1_rms."""
    gamma = gamma_grid_value * hs1_rms
    return h0 + gamma * np.outer(s, u)


def hidden_state_1_centered_rms(h1: np.ndarray) -> float:
    centered = h1 - h1.mean(axis=0, keepdims=True)
    return float(np.sqrt(np.mean(centered**2)))


# --------------------------------------------------------------------------
# Panel / activation loading (real-run only; never touched by --smoke)
# --------------------------------------------------------------------------

@dataclass
class Panel:
    name: str
    rows: list[dict[str, Any]]
    row_keys: list[str]
    y_known: np.ndarray  # 1 known, 0 unknown
    flavor: np.ndarray
    extraction_dir: Path


def squeeze_singleton(x: np.ndarray) -> np.ndarray:
    if x.ndim == 3:
        if x.shape[1] != 1:
            raise ControlError(f"expected exactly 1 captured position per row, got {x.shape[1]}")
        x = x[:, 0, :]
    return x


def load_layer_matrix(extraction_dir: Path, row_keys: list[str], layer: int) -> np.ndarray:
    import latent_knowledge_probe as lkp

    mats = lkp.load_layers(extraction_dir, row_keys, [layer], source="anchor")
    return squeeze_singleton(mats[layer])


def m1_flavor_mask(panel: Panel, flavor_name: str | None) -> np.ndarray:
    known_mask = panel.y_known == 1
    unknown_mask = (panel.y_known == 0) if flavor_name is None else (panel.flavor == flavor_name)
    return known_mask | unknown_mask


# --------------------------------------------------------------------------
# SG0 / SG1: integrity
# --------------------------------------------------------------------------

def verify_sg0(cell: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    from safetensors import safe_open

    checks = gates["sg0_input_integrity"]["checks"]
    problems: list[str] = []

    def check_file(rel: str, expected_sha: str, label: str) -> Path:
        path = (HERE / rel).resolve()
        if not path.is_file():
            problems.append(f"{label} missing: {rel}")
            return path
        actual = sha256_file(path)
        if actual != expected_sha:
            problems.append(f"{label} sha256 mismatch: {rel} actual={actual[:12]} expected={expected_sha[:12]}")
        return path

    panels_cfg = cell["source_panels"]
    check_file(panels_cfg["kuq"]["panel_file"], checks["kuq_panel_sha256_must_equal"], "kuq panel")
    check_file(panels_cfg["ambigqa"]["panel_file"], checks["ambigqa_panel_sha256_must_equal"], "ambigqa panel")
    check_file(panels_cfg["selfaware"]["panel_file"], checks["selfaware_panel_sha256_must_equal"], "selfaware panel")
    check_file(cell["panels_manifest"]["path"], checks["panels_manifest_sha256_must_equal"], "panels manifest")
    check_file(
        str(Path(panels_cfg["kuq"]["extraction_dir"]) / "manifest.json"),
        checks["kuq_extraction_manifest_sha256_must_equal"],
        "kuq extraction manifest",
    )
    check_file(
        str(Path(panels_cfg["ambigqa"]["extraction_dir"]) / "manifest.json"),
        checks["ambigqa_extraction_manifest_sha256_must_equal"],
        "ambigqa extraction manifest",
    )
    check_file(
        str(Path(panels_cfg["selfaware"]["extraction_dir"]) / "manifest.json"),
        checks["selfaware_extraction_manifest_sha256_must_equal"],
        "selfaware extraction manifest",
    )
    check_file(cell["baseline_atlas_sweep"]["path"], checks["atlas_sweep_sha256_must_equal"], "atlas sweep")
    check_file(cell["probe_protocol"]["module"], checks["probe_module_sha256_must_equal"], "probe module")

    for name, expected in (
        ("kuq_rows_must_equal", panels_cfg["kuq"]["n_rows"]),
        ("kuq_known_must_equal", panels_cfg["kuq"]["n_known"]),
        ("kuq_unknown_must_equal", panels_cfg["kuq"]["n_unknown"]),
        ("ambigqa_rows_must_equal", panels_cfg["ambigqa"]["n_rows"]),
        ("selfaware_rows_must_equal", panels_cfg["selfaware"]["n_rows"]),
        ("n_hidden_states_present_must_equal", cell["n_hidden_states"]),
        ("hidden_dim_must_equal", cell["hidden_dim"]),
    ):
        if checks[name] != expected:
            problems.append(f"{name}: cell.yaml={expected} gates.yaml={checks[name]}")
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        got = panels_cfg["kuq"]["flavor_counts"].get(cat)
        if got != expected:
            problems.append(f"kuq flavor '{cat}' count mismatch: cell.yaml={got} gates.yaml={expected}")

    status = "PASS" if not problems else "STOP"
    return {"status": status, "problems": problems}


def verify_sg0_row_coverage(panel: Panel, expected_n_hidden_states: int) -> list[str]:
    """Every panel row_key has exactly one anchor safetensors file with
    n_hidden_states keys L0..L{n-1}. Reads only the safetensors header
    (safe_open), never loads tensor data."""
    from safetensors import safe_open

    from latent_knowledge_probe import row_key_to_tensor_file

    expected_keys = {f"L{i}" for i in range(expected_n_hidden_states)}
    problems: list[str] = []
    for rk in panel.row_keys:
        path = row_key_to_tensor_file(panel.extraction_dir, rk, source="anchor")
        if not path.is_file():
            problems.append(f"{panel.name}: missing anchor file for {rk}")
            continue
        with safe_open(str(path), "pt") as fh:
            keys = set(fh.keys())
        if keys != expected_keys:
            problems.append(f"{panel.name}: {rk} has {len(keys)} keys, expected {expected_n_hidden_states}")
    return problems


def extraction_tree_digest(extraction_dir: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(extraction_dir.rglob("*")):
        if path.is_file():
            h.update(path.relative_to(extraction_dir).as_posix().encode("utf-8"))
            h.update(sha256_file(path).encode("ascii"))
    return h.hexdigest()


# --------------------------------------------------------------------------
# Gate adjudication (SG8)
# --------------------------------------------------------------------------

def adjudicate(
    residualized_primary: dict[str, dict[int, float]],
    reference_readout: dict[str, dict[int, float]],
    s2_surface_only: dict[str, float],
    gates: dict[str, Any],
) -> dict[str, Any]:
    bands = gates["s_bands"]
    p1_floor = float(bands["p1_survival_floor_heldout_auroc"])
    p2_ceiling = float(bands["p2_ambigqa_ceiling"])
    p3_floor = float(bands["p3_surface_only_carrier_floor"])

    per_flavor: dict[str, dict[str, Any]] = {}
    all_primary_hold = True
    all_at_or_below_75 = True
    for flavor, layers in bands["primary_cells"].items():
        values = residualized_primary[flavor]
        cell_pass = all(values[layer] >= p1_floor for layer in layers)
        cell_falls_to_75 = all(values[layer] <= p2_ceiling for layer in layers)
        zone = "survival" if cell_pass else ("collapse" if cell_falls_to_75 else "ambiguous")
        per_flavor[flavor] = {"layers": {str(l): values[layer] for l, layer in zip(layers, layers)}, "zone": zone}
        all_primary_hold = all_primary_hold and cell_pass
        all_at_or_below_75 = all_at_or_below_75 and cell_falls_to_75

    p1 = all_primary_hold
    selfaware_ref = reference_readout.get("selfaware", {})
    ambigqa_ref = reference_readout.get("ambigqa", {})
    p2 = (
        all(selfaware_ref.get(l, 0.0) >= p1_floor for l in bands["reference_cells"]["selfaware"])
        and all(ambigqa_ref.get(l, 1.0) <= p2_ceiling for l in bands["reference_cells"]["ambigqa"])
    )
    p3 = any(s2_surface_only.get(f, 0.0) >= p3_floor for f in KUQ_CATEGORIES)

    f1 = all_at_or_below_75
    f2 = not p1

    if f1:
        pattern = "F1_style_artifact_confirmed"
    elif f2:
        pattern = "F2_partial_style_dependence_blocks_promotion"
    else:
        pattern = "P1_survival"

    return {
        "per_flavor": per_flavor,
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "F1": f1,
        "F2": f2,
        "pattern": pattern,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_COMMITTED_PATH)
    ap.add_argument("--smoke", action="store_true", help="run the synthetic self-check; touches no real captures")
    args = ap.parse_args(argv)

    if args.smoke:
        return run_smoke()

    print(
        "REFUSING TO RUN: the real-data path is not exercised by this scaffold task "
        "(no GPU/extraction verb, no signed instrument in hand). Use --smoke for the "
        "CPU self-check, or run the signed instrument after `bin/exp sign`.",
        file=sys.stderr,
    )
    return 1


# --------------------------------------------------------------------------
# Synthetic smoke: exercises every stage and the gate math on tiny
# in-memory arrays. Never opens a path under source_panels; never imports
# torch/transformers/safetensors for real activation IO.
# --------------------------------------------------------------------------

def run_smoke() -> int:
    rng = np.random.default_rng(2026081099)
    n_per_flavor = 8
    hidden_dim = 6
    n_flavors = 3  # smaller than the real 6, still exercises per-flavor looping
    flavors = KUQ_CATEGORIES[:n_flavors]

    smoke_cfg = {
        "seed": 999,
        "surface_covariates": {
            "lexical": {
                "word_hash_features": 64,
                "char_hash_features": 64,
                "word_svd_components": 4,
                "char_svd_components": 4,
                "word_ngram_range": [1, 2],
                "char_ngram_range": [3, 5],
                "alternate_sign": False,
                "sublinear_tf": True,
            }
        },
    }

    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        status = "ok" if cond else "FAIL"
        print(f"  [{status}] {name}", file=sys.stderr)
        if not cond:
            failures.append(name)

    print("== smoke: surface featurization ==", file=sys.stderr)
    stems = {
        "known": "what is the capital of France",
        "ambiguous": "which one did they mean when they said that thing",
        "controversial": "is it true that this policy works",
        "counterfactual": "what would have happened if the war never started",
    }
    questions: list[str] = []
    flavor_labels: list[str] = []
    y_known: list[int] = []
    for flavor in flavors:
        for i in range(n_per_flavor):
            questions.append(f"{stems[flavor]} number {i}?")
            flavor_labels.append(flavor)
            y_known.append(0)
    for i in range(n_per_flavor * n_flavors):
        questions.append(f"{stems['known']} variant {i}?")
        flavor_labels.append("known")
        y_known.append(1)
    y_known = np.asarray(y_known)
    flavor_labels_arr = np.asarray(flavor_labels)
    token_counts = [len(q.split()) + 10 for q in questions]

    features = build_surface_matrix(questions, token_counts, smoke_cfg)
    check("combined surface matrix has finite values", bool(np.all(np.isfinite(features.combined))))
    check(
        "low block excludes any obviously label-shaped column count blowup "
        "(scalar 12 + interrogative 13 = 25 dims)",
        features.low.shape[1] == 25,
    )
    check(
        "featurizer signature takes only strings/ints (structural SG3 guarantee)",
        build_surface_matrix.__code__.co_varnames[:2] == ("questions", "token_counts"),
    )

    print("== smoke: interrogative bucket + scalar block ==", file=sys.stderr)
    check("wh-word leading token buckets correctly", leading_interrogative_bucket("What is X?") == "what")
    check("auxiliary lead buckets to auxiliary_or_copula (not a wh token)", leading_interrogative_bucket("Is this true?") == "auxiliary_or_copula")
    check("other bucket for non-wh non-aux", leading_interrogative_bucket("Tell me about X.") == "other")
    check("empty question buckets to other without crashing", leading_interrogative_bucket("") == "other")

    print("== smoke: registered vs plausible-wrong R2 formula ==", file=sys.stderr)
    n_rows, z_dim = 40, 8
    z_signal = rng.normal(size=(n_rows, z_dim))
    true_w = rng.normal(size=(z_dim, hidden_dim))
    h_synthetic = z_signal @ true_w + 0.05 * rng.normal(size=(n_rows, hidden_dim))
    strata_synth = ["a" if i % 2 == 0 else "b" for i in range(n_rows)]
    alpha_grid = [0.01, 0.1, 1.0, 10.0]
    residual, yhat, chosen_alphas = crossfit_ridge_incremental(
        h_synthetic, z_signal, strata_synth, alpha_grid,
        outer_folds=4, inner_folds=2, seed=101,
        checkpoint_path=None, fingerprint="smoke", unit="r2-formula-check",
    )
    registered_r2 = activation_oof_r2(h_synthetic, residual)
    naive_r2 = _naive_in_sample_r2_WRONG(h_synthetic, z_signal, alpha=chosen_alphas[0] if chosen_alphas else 1.0)
    check(
        "registered out-of-fold R2 and naive in-sample R2 DISAGREE (naive is optimistically inflated)",
        naive_r2 > registered_r2,
    )
    check("registered R2 is what SG4 treatment-strength gating consumes (not the naive one)", 0.0 <= registered_r2 <= 1.0)

    print("== smoke: crossfit resume (real kill/resume, not just idempotence) ==", file=sys.stderr)
    smoke_ckpt_dir = ANALYSIS_ROOT / "smoke" / "checkpoints"
    smoke_ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = smoke_ckpt_dir / "resume_test"
    for p in (ckpt_path.with_suffix(".npz"), ckpt_path.with_suffix(".json")):
        p.unlink(missing_ok=True)

    residual_from_scratch, _, _ = crossfit_ridge_incremental(
        h_synthetic, z_signal, strata_synth, alpha_grid,
        outer_folds=4, inner_folds=2, seed=101,
        checkpoint_path=None, fingerprint="smoke-resume", unit="resume-baseline",
    )

    interrupted = False
    try:
        crossfit_ridge_incremental(
            h_synthetic, z_signal, strata_synth, alpha_grid,
            outer_folds=4, inner_folds=2, seed=101,
            checkpoint_path=ckpt_path, fingerprint="smoke-resume", unit="resume-baseline",
            _abort_after_fold=0,
        )
    except InterruptedError:
        interrupted = True
    check("simulated kill actually interrupted after fold 0", interrupted)

    meta = json.loads(ckpt_path.with_suffix(".json").read_text(encoding="utf-8"))
    check("checkpoint recorded exactly 1 completed fold before the kill", meta["payload"]["completed_folds"] == 1)

    residual_resumed, _, _ = crossfit_ridge_incremental(
        h_synthetic, z_signal, strata_synth, alpha_grid,
        outer_folds=4, inner_folds=2, seed=101,
        checkpoint_path=ckpt_path, fingerprint="smoke-resume", unit="resume-baseline",
    )
    check(
        "resumed-after-kill residual is bit-identical to a from-scratch run",
        np.allclose(residual_from_scratch, residual_resumed, atol=1e-10),
    )

    t0 = time.monotonic()
    residual_rerun, _, _ = crossfit_ridge_incremental(
        h_synthetic, z_signal, strata_synth, alpha_grid,
        outer_folds=4, inner_folds=2, seed=101,
        checkpoint_path=ckpt_path, fingerprint="smoke-resume", unit="resume-baseline",
    )
    rerun_wall = time.monotonic() - t0
    check("fully-completed checkpoint short-circuits (no refit) on a second call", rerun_wall < 0.05)
    check("short-circuited rerun still matches the from-scratch residual", np.allclose(residual_from_scratch, residual_rerun, atol=1e-10))

    print("== smoke: permutation control ==", file=sys.stderr)
    permuted = permute_within_strata(z_signal, strata_synth, seed=202)
    check("permutation preserves shape", permuted.shape == z_signal.shape)
    check("permutation actually changes row order (not a no-op)", not np.allclose(permuted, z_signal))
    check(
        "permutation preserves the strata-conditional row SET (row-level alignment destroyed within strata only)",
        all(
            sorted(np.where(np.asarray(strata_synth) == v)[0].tolist())
            == sorted(np.where(np.asarray(strata_synth) == v)[0].tolist())
            for v in set(strata_synth)
        ),
    )

    print("== smoke: planted linear channel (C3 construction) ==", file=sys.stderr)
    y_pool = np.concatenate([np.zeros(n_per_flavor * n_flavors, dtype=int), np.ones(n_per_flavor * n_flavors, dtype=int)])
    sc, w = fit_pooled_surface_weights(features.combined, y_pool, seed=303)
    z_std = sc.transform(features.combined)
    s = z_std @ w
    check("planted scalar s has one value per row", s.shape == (features.combined.shape[0],))

    h0_dim = 5
    h0 = 0.01 * rng.normal(size=(features.combined.shape[0], h0_dim))  # near-null baseline, mirrors real hs0
    h1 = rng.normal(size=(features.combined.shape[0], h0_dim)) + 3.0
    hs1_rms = hidden_state_1_centered_rms(h1)
    u = seeded_unit_vector(h0_dim, seed=404)
    check("seeded unit vector has unit norm", abs(float(np.linalg.norm(u)) - 1.0) < 1e-9)

    reachable = False
    for gamma_grid_value in (0.25, 0.5, 1.0, 2.0, 4.0, 8.0):
        h0_planted = plant_hidden_state_0(h0, s, u, gamma_grid_value, hs1_rms)
        mean_auc, _std, _oof = ipg_cv_auroc_with_oof(h0_planted, y_pool)
        if mean_auc >= 0.90:
            reachable = True
            break
    check("planted channel reaches >= 0.90 pooled AUROC on the gamma grid", reachable)

    residual_planted, _, _ = crossfit_ridge_incremental(
        h0_planted, features.combined, [f"{a}|{b}" for a, b in zip(y_pool.astype(str), flavor_labels_arr)],
        [0.01, 0.1, 1.0, 10.0], outer_folds=4, inner_folds=2, seed=505,
        checkpoint_path=None, fingerprint="smoke-plant", unit="hs0-planted",
    )
    controlled_auc, _std, _oof = ipg_cv_auroc_with_oof(residual_planted, y_pool)
    check("residualization pulls the planted channel back down (below its raw planted reading)", controlled_auc < mean_auc)

    print("== smoke: gate adjudication logic (pass case and fail case) ==", file=sys.stderr)
    gates_smoke = {
        "s_bands": {
            "primary_cells": {flavors[0]: [0, 1], flavors[1]: [0, 1], flavors[2]: [0, 1]},
            "reference_cells": {"selfaware": [0, 1], "ambigqa": [0, 1]},
            "p1_survival_floor_heldout_auroc": 0.90,
            "p2_ambigqa_ceiling": 0.75,
            "p3_surface_only_carrier_floor": 0.75,
        }
    }
    survival_case = adjudicate(
        residualized_primary={f: {0: 0.95, 1: 0.93} for f in flavors},
        reference_readout={"selfaware": {0: 0.95, 1: 0.94}, "ambigqa": {0: 0.60, 1: 0.55}},
        s2_surface_only={f: 0.60 for f in flavors},
        gates=gates_smoke,
    )
    check("all-survive synthetic case adjudicates P1=True, F1=False, F2=False", survival_case["P1"] and not survival_case["F1"] and not survival_case["F2"])

    collapse_case = adjudicate(
        residualized_primary={f: {0: 0.55, 1: 0.60} for f in flavors},
        reference_readout={"selfaware": {0: 0.95, 1: 0.94}, "ambigqa": {0: 0.60, 1: 0.55}},
        s2_surface_only={f: 0.85 for f in flavors},
        gates=gates_smoke,
    )
    check("all-collapse synthetic case adjudicates F1=True (style artifact confirmed)", collapse_case["F1"])
    check("all-collapse case also implies F2 (nested by construction)", collapse_case["F2"])

    mixed_case = adjudicate(
        residualized_primary={flavors[0]: {0: 0.95, 1: 0.93}, flavors[1]: {0: 0.55, 1: 0.50}, flavors[2]: {0: 0.82, 1: 0.80}},
        reference_readout={"selfaware": {0: 0.95, 1: 0.94}, "ambigqa": {0: 0.60, 1: 0.55}},
        s2_surface_only={f: 0.80 for f in flavors},
        gates=gates_smoke,
    )
    check("mixed synthetic case is neither a clean survival nor a full F1 collapse", not mixed_case["P1"] and not mixed_case["F1"])
    check("mixed case per-flavor zones distinguish survival/collapse/ambiguous", {v["zone"] for v in mixed_case["per_flavor"].values()} == {"survival", "collapse", "ambiguous"})

    print("== smoke: containment scan (SG7) ==", file=sys.stderr)
    committed_ok = {"aurocs": {"ambiguous": 0.95}, "n": {"ambiguous": 32}}
    committed_bad = {"aurocs": {"ambiguous": 0.95}, "leak": questions[0]}
    private_texts = set(questions)
    leaked = False
    try:
        _walk_private_text(committed_bad, private_texts)
    except ControlError:
        leaked = True
    check("containment scan raises on a payload that leaks question text", leaked)
    no_false_positive = True
    try:
        _walk_private_text(committed_ok, private_texts)
    except ControlError:
        no_false_positive = False
    check("containment scan does not false-positive on a clean counts-only payload", no_false_positive)

    for p in (ckpt_path.with_suffix(".npz"), ckpt_path.with_suffix(".json"), ckpt_path.with_suffix(".npz.tmp")):
        p.unlink(missing_ok=True)

    print(f"\nsmoke: {len(failures)} failing check(s)" if failures else "\nsmoke: ALL CHECKS PASSED", file=sys.stderr)
    if failures:
        for name in failures:
            print(f"  FAILED: {name}", file=sys.stderr)
        return 1
    return 0


def ipg_cv_auroc_with_oof(x: np.ndarray, y: np.ndarray):
    """Thin wrapper resolving the pinned protocol lazily, so smoke mode
    (which never touches real captures) still exercises the SAME imported,
    unmodified function real runs use."""
    import internal_panel_probe_gate as ipg

    return ipg._cv_auroc_with_oof(x, y, folds=5, C=0.5, seed=0)


if __name__ == "__main__":
    raise SystemExit(main())
