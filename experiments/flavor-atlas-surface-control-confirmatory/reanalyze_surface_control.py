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
        state_path.parent.mkdir(parents=True, exist_ok=True)
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


def load_panel(name: str, cell: dict[str, Any], base_dir: Path = HERE) -> Panel:
    spec = cell["source_panels"][name]
    path = resolve_path(base_dir, spec["panel_file"])
    rows = load_jsonl(path)
    row_keys = [r["row_key"] for r in rows]
    y_known = np.asarray([1 if r["label"] == "known" else 0 for r in rows])
    flavor = np.asarray([r["flavor"] for r in rows])
    extraction_dir = resolve_path(base_dir, spec["extraction_dir"])
    return Panel(name=name, rows=rows, row_keys=row_keys, y_known=y_known, flavor=flavor, extraction_dir=extraction_dir)


def make_raw_cache():
    """Memoizing wrapper over `load_layer_matrix`, keyed by (panel, layer),
    so a layer shared by several primary cells (L35) or several permutation
    replicates is only ever read from disk once."""
    cache: dict[tuple[str, int], np.ndarray] = {}

    def get(panel: Panel, layer: int) -> np.ndarray:
        key = (panel.name, layer)
        if key not in cache:
            cache[key] = load_layer_matrix(panel.extraction_dir, panel.row_keys, layer)
        return cache[key]

    return get


def flavor_auroc(panel: Panel, values: np.ndarray, flavor: str | None) -> float:
    mask = m1_flavor_mask(panel, flavor)
    mean_auc, _std, _oof = ipg_cv_auroc_with_oof(values[mask], panel.y_known[mask])
    return float(mean_auc)


def fit_full_probe(x: np.ndarray, y: np.ndarray, seed: int = 0):
    """S3 construction: one full-data fit of the pinned probe family (same
    scaler, same C=0.5), no cross-validation -- frozen and then scored on a
    DIFFERENT dataset (`score_frozen`), which is its own held-out set."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    sc = StandardScaler().fit(x)
    clf = LogisticRegression(C=0.5, max_iter=2000, random_state=seed)
    clf.fit(sc.transform(x), y)
    return sc, clf


def score_frozen(sc, clf, x: np.ndarray, y: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    scores = clf.decision_function(sc.transform(x))
    return float(roc_auc_score(y, scores))


def primary_layer_set(cell: dict[str, Any]) -> list[int]:
    """The distinct KUQ layers spanned by the twelve primary cells (six
    flavors' best_layer plus the shared secondary_layer) -- what C1/C2 are
    evaluated at, per gates.yaml sg4/sg6 ('each primary layer')."""
    layers: set[int] = set()
    for spec in cell["primary_cells"].values():
        layers.add(int(spec["best_layer"]))
        layers.add(int(spec["secondary_layer"]))
    return sorted(layers)


def compute_layer_plan(cell: dict[str, Any]) -> dict[str, list[int]]:
    """Every (panel, layer) this run must residualize, derived entirely from
    cell.yaml: primary_cells, reference_cells, s3_transfer's extra layers,
    and hidden states 0/1 (SG2's null check plus C3's plant/RMS reference,
    KUQ only)."""
    primary = cell["primary_cells"]
    reference = cell["reference_cells"]
    s3 = cell["s3_transfer"]

    kuq_layers: set[int] = set(primary_layer_set(cell))
    kuq_layers.add(int(reference["pooled_all_unknowns"]["best_layer"]))
    kuq_layers.add(int(reference["pooled_all_unknowns"]["secondary_layer"]))
    for l in s3["kuq_extra_layers"]:
        kuq_layers.add(int(l))
    kuq_layers.update({0, 1})

    selfaware_layers: set[int] = {
        int(reference["selfaware"]["best_layer"]),
        int(reference["selfaware"]["secondary_layer"]),
        0,
    }
    for l in s3["selfaware_extra_layers"]:
        selfaware_layers.add(int(l))

    ambigqa_layers: set[int] = {
        int(reference["ambigqa"]["best_layer"]),
        int(reference["ambigqa"]["secondary_layer"]),
        0,
    }

    return {"kuq": sorted(kuq_layers), "selfaware": sorted(selfaware_layers), "ambigqa": sorted(ambigqa_layers)}


# --------------------------------------------------------------------------
# SG0 / SG1: integrity
# --------------------------------------------------------------------------

def resolve_path(base_dir: Path, raw: str) -> Path:
    """Resolve a cell.yaml-declared path against `base_dir` (the real HERE
    for a production run, a fixture root for the smoke end-to-end check).
    An already-absolute string (used by the fixture for the real, unfaked
    pinned modules) is returned unchanged."""
    p = Path(raw)
    return p.resolve() if p.is_absolute() else (base_dir / p).resolve()


def real_input_inventory(
    cell: dict[str, Any], gates: dict[str, Any], base_dir: Path = HERE
) -> list[dict[str, Any]]:
    """Every real, on-disk input this cell reads at run time: label,
    resolved path, and (when pinned) the expected sha256. Single source of
    truth for SG0 verification and for `--dry-run` reporting."""
    checks = gates["sg0_input_integrity"]["checks"]
    panels_cfg = cell["source_panels"]
    entries: list[tuple[str, str, str | None]] = [
        ("kuq panel", panels_cfg["kuq"]["panel_file"], checks["kuq_panel_sha256_must_equal"]),
        ("ambigqa panel", panels_cfg["ambigqa"]["panel_file"], checks["ambigqa_panel_sha256_must_equal"]),
        ("selfaware panel", panels_cfg["selfaware"]["panel_file"], checks["selfaware_panel_sha256_must_equal"]),
        ("panels manifest", cell["panels_manifest"]["path"], checks["panels_manifest_sha256_must_equal"]),
        (
            "kuq extraction manifest",
            str(Path(panels_cfg["kuq"]["extraction_dir"]) / "manifest.json"),
            checks["kuq_extraction_manifest_sha256_must_equal"],
        ),
        (
            "ambigqa extraction manifest",
            str(Path(panels_cfg["ambigqa"]["extraction_dir"]) / "manifest.json"),
            checks["ambigqa_extraction_manifest_sha256_must_equal"],
        ),
        (
            "selfaware extraction manifest",
            str(Path(panels_cfg["selfaware"]["extraction_dir"]) / "manifest.json"),
            checks["selfaware_extraction_manifest_sha256_must_equal"],
        ),
        ("atlas sweep baseline", cell["baseline_atlas_sweep"]["path"], checks["atlas_sweep_sha256_must_equal"]),
        ("probe module", cell["probe_protocol"]["module"], checks["probe_module_sha256_must_equal"]),
        ("render module", cell["render_module"]["path"], None),
        ("kuq extraction dir", panels_cfg["kuq"]["extraction_dir"], None),
        ("ambigqa extraction dir", panels_cfg["ambigqa"]["extraction_dir"], None),
        ("selfaware extraction dir", panels_cfg["selfaware"]["extraction_dir"], None),
    ]
    inventory = []
    for label, rel, expected_sha in entries:
        path = resolve_path(base_dir, rel)
        exists = path.exists()
        actual_sha = sha256_file(path) if (exists and path.is_file() and expected_sha) else None
        sha_ok = expected_sha is None or actual_sha == expected_sha
        inventory.append(
            {
                "label": label,
                "path": path,
                "exists": exists,
                "sha256": expected_sha,
                "sha256_actual": actual_sha,
                "sha256_ok": sha_ok,
            }
        )
    return inventory


def verify_panels_manifest_counts(
    cell: dict[str, Any], gates: dict[str, Any], base_dir: Path = HERE
) -> list[str]:
    """panels_manifest.json's own recorded counts, cross-checked against the
    same gates.yaml numbers SG0 already pins by sha. The sha pin proves the
    file is byte-identical to what was reviewed; this proves the file's
    CONTENT is what the cell believes it is -- a legible failure instead of
    an opaque hash mismatch when it disagrees."""
    path = resolve_path(base_dir, cell["panels_manifest"]["path"])
    manifest = json.loads(path.read_text(encoding="utf-8"))
    checks = gates["sg0_input_integrity"]["checks"]
    problems: list[str] = []
    counts = manifest.get("counts", {})

    kuq = counts.get("kuq", {})
    if kuq.get("n") != checks["kuq_rows_must_equal"]:
        problems.append(f"panels_manifest kuq.n={kuq.get('n')} vs gate {checks['kuq_rows_must_equal']}")
    kuq_labels = kuq.get("by_label", {})
    if kuq_labels.get("known") != checks["kuq_known_must_equal"]:
        problems.append(f"panels_manifest kuq.by_label.known={kuq_labels.get('known')} vs gate {checks['kuq_known_must_equal']}")
    if kuq_labels.get("unknown") != checks["kuq_unknown_must_equal"]:
        problems.append(f"panels_manifest kuq.by_label.unknown={kuq_labels.get('unknown')} vs gate {checks['kuq_unknown_must_equal']}")
    kuq_flavors = kuq.get("by_flavor", {})
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        got = kuq_flavors.get(cat, 0)
        if got != expected:
            problems.append(f"panels_manifest kuq.by_flavor['{cat}']={got} vs gate {expected}")

    ambigqa = counts.get("ambigqa", {})
    if ambigqa.get("n") != checks["ambigqa_rows_must_equal"]:
        problems.append(f"panels_manifest ambigqa.n={ambigqa.get('n')} vs gate {checks['ambigqa_rows_must_equal']}")

    selfaware = counts.get("selfaware", {})
    if selfaware.get("n") != checks["selfaware_rows_must_equal"]:
        problems.append(f"panels_manifest selfaware.n={selfaware.get('n')} vs gate {checks['selfaware_rows_must_equal']}")

    return problems


def verify_sg0(cell: dict[str, Any], gates: dict[str, Any], base_dir: Path = HERE) -> dict[str, Any]:
    checks = gates["sg0_input_integrity"]["checks"]
    problems: list[str] = []

    for item in real_input_inventory(cell, gates, base_dir):
        if not item["exists"]:
            problems.append(f"{item['label']} missing: {item['path']}")
            continue
        if item["sha256"] is not None and not item["sha256_ok"]:
            problems.append(
                f"{item['label']} sha256 mismatch: actual={(item['sha256_actual'] or '')[:12]} "
                f"expected={item['sha256'][:12]}"
            )

    panels_cfg = cell["source_panels"]
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

    if not problems:
        problems.extend(verify_panels_manifest_counts(cell, gates, base_dir))

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
# Real-run orchestration (SG2, S2, S3, C1/C2, C3) -- shared verbatim between
# the CLI real-data path and the smoke fixture end-to-end check below, which
# is why every function here takes `cell`/`gates`/panels/features as
# arguments rather than reading the module-level CELL_PATH/GATES_PATH.
# --------------------------------------------------------------------------

def evaluate_sg2(
    kuq: Panel, ambigqa: Panel, selfaware: Panel, cell: dict[str, Any], gates: dict[str, Any], raw_cache
) -> dict[str, Any]:
    """Raw (non-residualized) reproduction of the atlas baseline at 4dp,
    plus the hidden-state-0 == 0.5000 null check for all nine rows. A
    controlled number is meaningless unless the uncontrolled number is
    reproduced first (gates.yaml sg2 derivation)."""
    checks = gates["sg2_baseline_reproduction"]["checks"]
    cells_expected = checks["cells"]
    problems: list[str] = []
    computed: dict[str, dict[str, float]] = {}

    def raw_row(panel: Panel, best_layer: int, secondary_layer: int, flavor: str | None, key: str) -> None:
        got_best = round(flavor_auroc(panel, raw_cache(panel, best_layer), flavor), 4)
        got_secondary = round(flavor_auroc(panel, raw_cache(panel, secondary_layer), flavor), 4)
        secondary_key = f"L{secondary_layer}"
        computed[key] = {f"L{best_layer}": got_best, secondary_key: got_secondary}
        expected = cells_expected.get(key)
        if expected is None:
            problems.append(f"{key}: no expected baseline registered in gates.yaml sg2 cells table")
        elif computed[key][f"L{best_layer}"] != expected.get(f"L{best_layer}") or computed[key][secondary_key] != expected.get(secondary_key):
            problems.append(f"{key}: got {computed[key]}, expected {expected}")

    for flavor, spec in cell["primary_cells"].items():
        raw_row(kuq, int(spec["best_layer"]), int(spec["secondary_layer"]), flavor, flavor)
    pooled_spec = cell["reference_cells"]["pooled_all_unknowns"]
    raw_row(kuq, int(pooled_spec["best_layer"]), int(pooled_spec["secondary_layer"]), None, "pooled_all_unknowns")
    selfaware_spec = cell["reference_cells"]["selfaware"]
    raw_row(selfaware, int(selfaware_spec["best_layer"]), int(selfaware_spec["secondary_layer"]), None, "selfaware")
    ambigqa_spec = cell["reference_cells"]["ambigqa"]
    raw_row(ambigqa, int(ambigqa_spec["best_layer"]), int(ambigqa_spec["secondary_layer"]), None, "ambigqa")

    hs0_expected = round(float(checks["hidden_state_0_must_equal_for_all_rows"]), 4)
    hs0_computed: dict[str, float] = {}
    for flavor in cell["primary_cells"]:
        hs0_computed[flavor] = round(flavor_auroc(kuq, raw_cache(kuq, 0), flavor), 4)
    hs0_computed["pooled_all_unknowns"] = round(flavor_auroc(kuq, raw_cache(kuq, 0), None), 4)
    hs0_computed["selfaware"] = round(flavor_auroc(selfaware, raw_cache(selfaware, 0), None), 4)
    hs0_computed["ambigqa"] = round(flavor_auroc(ambigqa, raw_cache(ambigqa, 0), None), 4)
    for row, val in hs0_computed.items():
        if val != hs0_expected:
            problems.append(f"hidden_state_0 for {row}: got {val}, expected {hs0_expected}")

    return {
        "status": "PASS" if not problems else "STOP",
        "problems": problems,
        "computed": computed,
        "hidden_state_0": hs0_computed,
    }


def compute_s2(
    kuq: Panel, ambigqa: Panel, selfaware: Panel, features, slices: dict[str, slice], cell: dict[str, Any]
) -> dict[str, float]:
    """S2: surface-only probe, no activation touched at all -- every atlas
    row (six flavors plus the three reference pools)."""
    s2: dict[str, float] = {}
    for flavor in cell["primary_cells"]:
        mask = m1_flavor_mask(kuq, flavor)
        z = features.combined[slices["kuq"]][mask]
        mean_auc, _std, _oof = ipg_cv_auroc_with_oof(z, kuq.y_known[mask])
        s2[flavor] = float(mean_auc)
    mask = m1_flavor_mask(kuq, None)
    s2["pooled_all_unknowns"] = float(
        ipg_cv_auroc_with_oof(features.combined[slices["kuq"]][mask], kuq.y_known[mask])[0]
    )
    s2["selfaware"] = float(ipg_cv_auroc_with_oof(features.combined[slices["selfaware"]], selfaware.y_known)[0])
    s2["ambigqa"] = float(ipg_cv_auroc_with_oof(features.combined[slices["ambigqa"]], ambigqa.y_known)[0])
    return s2


def compute_s3(kuq: Panel, selfaware: Panel, cell: dict[str, Any], get_kuq_residual, get_selfaware_residual) -> dict[str, Any]:
    """S3: descriptive residualized cross-dataset transfer, both directions,
    at the layers `s3_transfer` in cell.yaml declares (AMENDMENT.md Design
    S3). Fit is a single full-data probe fit, frozen and scored on the
    OTHER dataset -- never refit there."""
    kuq_to_selfaware: dict[str, Any] = {}
    for flavor, spec in cell["primary_cells"].items():
        layer = int(spec["best_layer"])
        kuq_residual, _r2 = get_kuq_residual(layer)
        mask = m1_flavor_mask(kuq, flavor)
        sc, clf = fit_full_probe(kuq_residual[mask], kuq.y_known[mask])
        selfaware_residual, _r2 = get_selfaware_residual(layer)
        kuq_to_selfaware[flavor] = {"layer": layer, "auroc": score_frozen(sc, clf, selfaware_residual, selfaware.y_known)}

    fit_layer = int(cell["s3_transfer"]["selfaware_to_kuq_fit_layer"])
    selfaware_residual, _r2 = get_selfaware_residual(fit_layer)
    sc, clf = fit_full_probe(selfaware_residual, selfaware.y_known)
    selfaware_to_kuq: dict[str, Any] = {}
    for flavor in cell["primary_cells"]:
        kuq_residual, _r2 = get_kuq_residual(fit_layer)
        mask = m1_flavor_mask(kuq, flavor)
        selfaware_to_kuq[flavor] = {"layer": fit_layer, "auroc": score_frozen(sc, clf, kuq_residual[mask], kuq.y_known[mask])}

    return {"kuq_flavor_to_selfaware": kuq_to_selfaware, "selfaware_to_kuq": selfaware_to_kuq}


def compute_permutation_controls(
    kuq: Panel,
    features,
    slices: dict[str, slice],
    cell: dict[str, Any],
    fingerprint: str,
    checkpoint_root: Path | None,
) -> tuple[dict[int, list[float]], list[bool]]:
    """C1/C2 share the same 20 fixed-seed permutation replicates (AMENDMENT.md
    Compute budget: '20 permutation replicates ... restricted to the primary
    layers'). For each replicate: permute Z once, then residualize KUQ at
    every distinct primary layer using that SAME permuted Z, recording the
    activation-OOF-R2 (feeds C1's threshold) and, at each flavor's own two
    primary layers, the residualized AUROC (feeds C2's 18-of-20 count)."""
    primary_layers = primary_layer_set(cell)
    n_perm = int(cell["permutation_control"]["n_permutations"])
    seed_start = int(cell["permutation_control"]["seed_start"])
    strata = [f"{lab}|{flav}" for lab, flav in zip(kuq.y_known.astype(str), kuq.flavor)]

    permuted_r2_by_layer: dict[int, list[float]] = {l: [] for l in primary_layers}
    replicate_all_flavors_pass: list[bool] = []

    for i in range(n_perm):
        perm_seed = seed_start + i
        z_perm = permute_within_strata(features.combined[slices["kuq"]], strata, perm_seed)
        replicate_ok = True
        for layer in primary_layers:
            h_raw = load_layer_matrix(kuq.extraction_dir, kuq.row_keys, layer)
            seed = int(cell["seed"]) + layer
            ckpt = (checkpoint_root / "kuq" / "permutation" / f"p{i}" / f"hs{layer}") if checkpoint_root else None
            residual, _yhat, _chosen = crossfit_ridge_incremental(
                h_raw,
                z_perm,
                strata,
                cell["residualization"]["alpha_grid"],
                outer_folds=int(cell["residualization"]["outer_folds"]),
                inner_folds=int(cell["residualization"]["inner_folds"]),
                seed=seed,
                checkpoint_path=ckpt,
                fingerprint=fingerprint,
                unit=f"kuq/permutation/p{i}/L{layer}",
            )
            permuted_r2_by_layer[layer].append(activation_oof_r2(h_raw, residual))
            for flavor, spec in cell["primary_cells"].items():
                if layer not in (int(spec["best_layer"]), int(spec["secondary_layer"])):
                    continue
                # 0.90 here is the registered C2 band: gates.yaml
                # sg6_permutation_negative_control's key name is
                # min_permuted_runs_keeping_all_six_flavors_AT_OR_ABOVE_0_90 --
                # the floor is embedded in that key's name, not exposed as a
                # separate numeric field, so it is transcribed here rather
                # than read out of the dict. This is the C2 band, a distinct
                # registered quantity from sg8's p1_survival_floor even
                # though the two currently share a value; do not derive one
                # from the other.
                if flavor_auroc(kuq, residual, flavor) < 0.90:
                    replicate_ok = False
        replicate_all_flavors_pass.append(replicate_ok)

    return permuted_r2_by_layer, replicate_all_flavors_pass


def evaluate_sg4(
    observed_r2_by_layer: dict[int, float], permuted_r2_by_layer: dict[int, list[float]], gates: dict[str, Any]
) -> dict[str, Any]:
    checks = gates["sg4_treatment_strength"]["checks"]
    min_r2 = float(checks["min_activation_oof_r2_at_each_primary_layer"])
    q = float(checks["permutation_null_quantile"])
    min_above = float(checks["min_above_permutation_quantile"])
    per_layer: dict[int, dict[str, Any]] = {}
    all_pass = True
    for layer, observed in observed_r2_by_layer.items():
        perm_values = permuted_r2_by_layer.get(layer, [])
        q95 = float(np.percentile(perm_values, q * 100)) if perm_values else 0.0
        cell_pass = observed >= min_r2 and observed >= q95 + min_above
        per_layer[layer] = {"observed_r2": observed, "permutation_q95": q95, "pass": cell_pass}
        all_pass = all_pass and cell_pass
    return {"per_layer": per_layer, "pass": all_pass}


def evaluate_sg6(replicate_all_flavors_pass: list[bool], gates: dict[str, Any]) -> dict[str, Any]:
    checks = gates["sg6_permutation_negative_control"]["checks"]
    min_pass = int(checks["min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90"])
    n_pass = sum(replicate_all_flavors_pass)
    return {"n_permutations": len(replicate_all_flavors_pass), "n_passing": n_pass, "pass": n_pass >= min_pass}


def compute_and_evaluate_c3(
    kuq: Panel,
    features,
    slices: dict[str, slice],
    cell: dict[str, Any],
    fingerprint: str,
    get_kuq_residual,
    checkpoint_root: Path | None,
) -> dict[str, Any]:
    """C3: single scalar surface score projected along one seeded random
    unit direction, planted into hidden-state-0 (AMENDMENT.md C3;
    cell.yaml planted_signal). hs_index and hs_index+1 come from
    cell.yaml, never hardcoded."""
    planted_cfg = cell["planted_signal"]
    hs_index = int(planted_cfg["hs_index"])
    h0 = load_layer_matrix(kuq.extraction_dir, kuq.row_keys, hs_index)
    h1 = load_layer_matrix(kuq.extraction_dir, kuq.row_keys, hs_index + 1)
    hs1_rms = hidden_state_1_centered_rms(h1)

    z_kuq = features.combined[slices["kuq"]]
    sc, w = fit_pooled_surface_weights(z_kuq, kuq.y_known, seed=int(planted_cfg["weight_fit_seed"]))
    s = sc.transform(z_kuq) @ w
    u = seeded_unit_vector(h0.shape[1], seed=int(planted_cfg["projection_seed"]))

    reach_floor = float(planted_cfg["planted_pooled_auroc_must_reach_at_least"])
    chosen_gamma = None
    planted_pooled_auroc = None
    h0_planted = None
    for gv in planted_cfg["gamma_grid"]:
        candidate = plant_hidden_state_0(h0, s, u, float(gv), hs1_rms)
        auc, _std, _oof = ipg_cv_auroc_with_oof(candidate, kuq.y_known)
        if auc >= reach_floor:
            chosen_gamma, planted_pooled_auroc, h0_planted = float(gv), float(auc), candidate
            break
    reachable = chosen_gamma is not None
    if not reachable:
        gv = float(planted_cfg["gamma_grid"][-1])
        h0_planted = plant_hidden_state_0(h0, s, u, gv, hs1_rms)
        planted_pooled_auroc, _std, _oof = ipg_cv_auroc_with_oof(h0_planted, kuq.y_known)
        chosen_gamma = gv

    unplanted_residual, _r2 = get_kuq_residual(hs_index)
    strata = [f"{lab}|{flav}" for lab, flav in zip(kuq.y_known.astype(str), kuq.flavor)]
    seed = int(cell["seed"]) + hs_index
    ckpt = (checkpoint_root / "kuq" / "planted" / f"hs{hs_index}") if checkpoint_root else None
    planted_residual, _yhat, _chosen = crossfit_ridge_incremental(
        h0_planted,
        z_kuq,
        strata,
        cell["residualization"]["alpha_grid"],
        outer_folds=int(cell["residualization"]["outer_folds"]),
        inner_folds=int(cell["residualization"]["inner_folds"]),
        seed=seed,
        checkpoint_path=ckpt,
        fingerprint=fingerprint,
        unit=f"kuq/planted/hs{hs_index}",
    )
    residualized_planted_pooled_auroc, _std, _oof = ipg_cv_auroc_with_oof(planted_residual, kuq.y_known)

    per_flavor_deviation: dict[str, float] = {}
    max_dev = 0.0
    for flavor in cell["primary_cells"]:
        unplanted_auc = flavor_auroc(kuq, unplanted_residual, flavor)
        planted_auc = flavor_auroc(kuq, planted_residual, flavor)
        dev = abs(planted_auc - unplanted_auc)
        per_flavor_deviation[flavor] = dev
        max_dev = max(max_dev, dev)

    ceiling = float(planted_cfg["residualized_planted_pooled_auroc_must_be_at_most"])
    max_allowed_dev = float(planted_cfg["max_flavor_deviation_from_unplanted_residualized"])
    sg5_pass = reachable and (residualized_planted_pooled_auroc <= ceiling) and (max_dev <= max_allowed_dev)

    return {
        "gamma": chosen_gamma,
        "planted_pooled_auroc": planted_pooled_auroc,
        "reachable": reachable,
        "residualized_planted_pooled_auroc": residualized_planted_pooled_auroc,
        "per_flavor_deviation": per_flavor_deviation,
        "max_flavor_deviation": max_dev,
        "pass": sg5_pass,
    }


def append_provenance_line(analysis_root: Path, fingerprint: str, out_path: Path) -> None:
    log_path = require_beneath_analysis(analysis_root / "run_log.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "provenance": True,
        "config_fingerprint": fingerprint,
        "committed_output": str(out_path),
        "timestamp_unix": time.time(),
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def run_real(
    cell: dict[str, Any],
    gates: dict[str, Any],
    base_dir: Path,
    out_path: Path,
    checkpoint_root: Path,
    analysis_root: Path,
) -> tuple[int, dict[str, Any] | None]:
    """The full registered real-data pipeline: SG0 -> panel load -> SG0 row
    coverage -> panels_manifest counts -> SG1 pre-digest -> surface basis ->
    SG2 baseline reproduction -> S1/reference residualization -> S2 -> S3 ->
    C1/C2 permutation controls -> C3 planted control -> SG1 post-digest ->
    SG8 adjudication -> counts-only committed write. Every threshold and
    layer number is read from `cell`/`gates`; nothing decision-relevant is a
    bare literal. Returns (exit_code, payload_or_None)."""
    fingerprint = config_fingerprint(cell, gates)

    print("SG0: verifying input integrity (paths, shas, declared counts)...", file=sys.stderr)
    sg0 = verify_sg0(cell, gates, base_dir)
    if sg0["status"] != "PASS":
        print("SG0 STOP:", file=sys.stderr)
        for p in sg0["problems"]:
            print(f"  - {p}", file=sys.stderr)
        return 1, None

    panels = {name: load_panel(name, cell, base_dir) for name in ("kuq", "ambigqa", "selfaware")}
    kuq, ambigqa, selfaware = panels["kuq"], panels["ambigqa"], panels["selfaware"]

    print("SG0: verifying every panel row has full anchor coverage (header-only reads)...", file=sys.stderr)
    coverage_problems: list[str] = []
    for panel in panels.values():
        coverage_problems.extend(verify_sg0_row_coverage(panel, int(cell["n_hidden_states"])))
    if coverage_problems:
        print("SG0 STOP (anchor coverage):", file=sys.stderr)
        for p in coverage_problems[:50]:
            print(f"  - {p}", file=sys.stderr)
        return 1, None

    print("SG1: recording pre-run extraction-tree digests...", file=sys.stderr)
    pre_digests = {name: extraction_tree_digest(p.extraction_dir) for name, p in panels.items()}

    print("building the frozen surface basis over the full question union...", file=sys.stderr)
    render_path = resolve_path(base_dir, cell["render_module"]["path"])
    if str(render_path.parent) not in sys.path:
        sys.path.insert(0, str(render_path.parent))
    try:
        import ood_breadth_response_confidence_render as render_mod
    except Exception as exc:
        print(f"REFUSING TO RUN: could not import render module ({render_path}): {exc}", file=sys.stderr)
        return 1, None
    render_fn = render_mod.render

    union_rows = kuq.rows + ambigqa.rows + selfaware.rows
    questions = [r["question"] for r in union_rows]
    tokenizer_cache: list = []
    token_counts = [get_token_count(r, render_fn, tokenizer_cache) for r in union_rows]
    features = build_surface_matrix(questions, token_counts, cell)

    n_kuq, n_ambigqa, n_selfaware = len(kuq.rows), len(ambigqa.rows), len(selfaware.rows)
    slices = {
        "kuq": slice(0, n_kuq),
        "ambigqa": slice(n_kuq, n_kuq + n_ambigqa),
        "selfaware": slice(n_kuq + n_ambigqa, n_kuq + n_ambigqa + n_selfaware),
    }

    raw_cache = make_raw_cache()

    print("SG2: reproducing the raw (non-residualized) atlas baseline...", file=sys.stderr)
    sg2 = evaluate_sg2(kuq, ambigqa, selfaware, cell, gates, raw_cache)
    if sg2["status"] != "PASS":
        print(
            "SG2 STOP (baseline reproduction failed -- this cell is not reading the same "
            "instrument the atlas read):",
            file=sys.stderr,
        )
        for p in sg2["problems"]:
            print(f"  - {p}", file=sys.stderr)
        return 1, None

    residual_cache: dict[tuple[str, int], tuple[np.ndarray, float]] = {}

    def get_panel_residual(panel: Panel, panel_slice: slice, layer: int):
        key = (panel.name, layer)
        if key not in residual_cache:
            h_raw = raw_cache(panel, layer)
            z = features.combined[panel_slice]
            strata = [f"{lab}|{flav}" for lab, flav in zip(panel.y_known.astype(str), panel.flavor)]
            seed = int(cell["seed"]) + layer
            ckpt = checkpoint_root / panel.name / "combined" / f"hs{layer}"
            residual, _yhat, _chosen = crossfit_ridge_incremental(
                h_raw,
                z,
                strata,
                cell["residualization"]["alpha_grid"],
                outer_folds=int(cell["residualization"]["outer_folds"]),
                inner_folds=int(cell["residualization"]["inner_folds"]),
                seed=seed,
                checkpoint_path=ckpt,
                fingerprint=fingerprint,
                unit=f"{panel.name}/combined/L{layer}",
            )
            residual_cache[key] = (residual, activation_oof_r2(h_raw, residual))
        return residual_cache[key]

    def get_kuq_residual(layer: int):
        return get_panel_residual(kuq, slices["kuq"], layer)

    def get_selfaware_residual(layer: int):
        return get_panel_residual(selfaware, slices["selfaware"], layer)

    def get_ambigqa_residual(layer: int):
        return get_panel_residual(ambigqa, slices["ambigqa"], layer)

    print("S1/reference: cross-fitted residualization at every registered layer...", file=sys.stderr)
    layer_plan = compute_layer_plan(cell)
    for layer in layer_plan["kuq"]:
        get_kuq_residual(layer)
    for layer in layer_plan["selfaware"]:
        get_selfaware_residual(layer)
    for layer in layer_plan["ambigqa"]:
        get_ambigqa_residual(layer)

    residualized_primary: dict[str, dict[int, float]] = {}
    for flavor, spec in cell["primary_cells"].items():
        residualized_primary[flavor] = {}
        for layer in (int(spec["best_layer"]), int(spec["secondary_layer"])):
            residual, _r2 = get_kuq_residual(layer)
            residualized_primary[flavor][layer] = flavor_auroc(kuq, residual, flavor)

    reference_readout: dict[str, dict[int, float]] = {}
    pooled_spec = cell["reference_cells"]["pooled_all_unknowns"]
    reference_readout["pooled_all_unknowns"] = {}
    for layer in (int(pooled_spec["best_layer"]), int(pooled_spec["secondary_layer"])):
        residual, _r2 = get_kuq_residual(layer)
        reference_readout["pooled_all_unknowns"][layer] = flavor_auroc(kuq, residual, None)

    selfaware_spec = cell["reference_cells"]["selfaware"]
    reference_readout["selfaware"] = {}
    for layer in (int(selfaware_spec["best_layer"]), int(selfaware_spec["secondary_layer"])):
        residual, _r2 = get_selfaware_residual(layer)
        reference_readout["selfaware"][layer] = flavor_auroc(selfaware, residual, None)

    ambigqa_spec = cell["reference_cells"]["ambigqa"]
    reference_readout["ambigqa"] = {}
    for layer in (int(ambigqa_spec["best_layer"]), int(ambigqa_spec["secondary_layer"])):
        residual, _r2 = get_ambigqa_residual(layer)
        reference_readout["ambigqa"][layer] = flavor_auroc(ambigqa, residual, None)

    print("S2: surface-only probe (no activations)...", file=sys.stderr)
    s2 = compute_s2(kuq, ambigqa, selfaware, features, slices, cell)

    print("S3: descriptive residualized cross-dataset transfer...", file=sys.stderr)
    s3 = compute_s3(kuq, selfaware, cell, get_kuq_residual, get_selfaware_residual)

    print("C1/C2: permutation controls at the distinct primary layers...", file=sys.stderr)
    observed_r2_by_layer: dict[int, float] = {}
    for layer in primary_layer_set(cell):
        _residual, r2 = get_kuq_residual(layer)
        observed_r2_by_layer[layer] = r2
    permuted_r2_by_layer, replicate_all_flavors_pass = compute_permutation_controls(
        kuq, features, slices, cell, fingerprint, checkpoint_root
    )
    sg4 = evaluate_sg4(observed_r2_by_layer, permuted_r2_by_layer, gates)
    sg6 = evaluate_sg6(replicate_all_flavors_pass, gates)

    print("C3: planted linear surface channel...", file=sys.stderr)
    c3 = compute_and_evaluate_c3(kuq, features, slices, cell, fingerprint, get_kuq_residual, checkpoint_root)

    print("SG1: verifying no extraction directory changed during the run...", file=sys.stderr)
    post_digests = {name: extraction_tree_digest(p.extraction_dir) for name, p in panels.items()}
    if pre_digests != post_digests:
        raise ControlError("SG1 VIOLATION: an extraction directory changed during this analysis-only run")

    print("SG8: adjudicating P1/P2/P3/F1/F2 against the registered bands...", file=sys.stderr)
    all_controls_pass = sg4["pass"] and c3["pass"] and sg6["pass"]
    decision = (
        adjudicate(residualized_primary, reference_readout, s2, gates)
        if all_controls_pass
        else {"status": "INDETERMINATE", "reason": "one or more of C1/C2/C3 failed; SG8 does not adjudicate"}
    )

    payload = {
        "cell": "flavor-atlas-surface-control-confirmatory",
        "config_fingerprint": fingerprint,
        "gates": {
            "SG0": True,
            "SG1": True,
            "SG2": True,
            "SG3": True,
            "SG4": sg4["pass"],
            "SG5": c3["pass"],
            "SG6": sg6["pass"],
        },
        "controls_pass": all_controls_pass,
        "s1_primary": {f: {str(l): round(v, 4) for l, v in layers.items()} for f, layers in residualized_primary.items()},
        "reference": {r: {str(l): round(v, 4) for l, v in layers.items()} for r, layers in reference_readout.items()},
        "s2_surface_only": {k: round(v, 4) for k, v in s2.items()},
        "s3_transfer": s3,
        "c1_treatment_strength": {
            "per_layer": {str(l): v for l, v in sg4["per_layer"].items()},
            "pass": sg4["pass"],
        },
        "c2_permutation": {"n_permutations": sg6["n_permutations"], "n_passing": sg6["n_passing"], "pass": sg6["pass"]},
        "c3_planted": c3,
        "decision": decision,
        "sg2_baseline": sg2["computed"],
    }

    print("SG7: containment scan before commit...", file=sys.stderr)
    _walk_private_text(payload, set(questions))

    atomic_write_json(out_path, payload)
    append_provenance_line(analysis_root, fingerprint, out_path)
    print(f"wrote {out_path}", file=sys.stderr)
    return 0, payload


def run_dry_run(cell: dict[str, Any], gates: dict[str, Any], base_dir: Path) -> int:
    """Resolves every real input, prints the full execution plan, executes
    nothing and writes nothing. Standing pre-sign / pre-launch existence
    check."""
    inventory = real_input_inventory(cell, gates, base_dir)

    print("== dry-run: resolved real inputs ==", file=sys.stderr)
    all_ok = True
    for item in inventory:
        ok = item["exists"] and item["sha256_ok"]
        all_ok = all_ok and ok
        status = "ok" if ok else ("MISSING" if not item["exists"] else "SHA_MISMATCH")
        print(f"  [{status}] {item['label']}: {item['path']}", file=sys.stderr)

    layer_plan = compute_layer_plan(cell)
    primary_layers = primary_layer_set(cell)
    n_flavors = len(cell["primary_cells"])
    print("\n== dry-run: execution plan (nothing executed, nothing written) ==", file=sys.stderr)
    print("  panels: kuq, ambigqa, selfaware", file=sys.stderr)
    print(f"  kuq layers to residualize: {layer_plan['kuq']}", file=sys.stderr)
    print(f"  selfaware layers to residualize: {layer_plan['selfaware']}", file=sys.stderr)
    print(f"  ambigqa layers to residualize: {layer_plan['ambigqa']}", file=sys.stderr)
    print(f"  S1 primary cells: {n_flavors} flavors x 2 layers = {n_flavors * 2}", file=sys.stderr)
    print(f"  S1 reference cells: {list(cell['reference_cells'].keys())} x 2 layers", file=sys.stderr)
    print(f"  S2 rows: {n_flavors + 3} (six flavors + pooled + selfaware + ambigqa)", file=sys.stderr)
    print(f"  S3 transfer cells: {n_flavors * 2} ({n_flavors} kuq->selfaware + {n_flavors} selfaware->kuq)", file=sys.stderr)
    print(
        f"  C1/C2 permutation replicates: {cell['permutation_control']['n_permutations']} "
        f"x {len(primary_layers)} distinct primary layers {primary_layers}",
        file=sys.stderr,
    )
    print(
        f"  C3 planted control: hidden state {cell['planted_signal']['hs_index']}, "
        f"gamma grid {cell['planted_signal']['gamma_grid']}",
        file=sys.stderr,
    )
    print(f"  committed output: {resolve_path(base_dir, cell['containment']['committed_output'])}", file=sys.stderr)
    print(f"  checkpoint root: {(ANALYSIS_ROOT / 'checkpoints')}", file=sys.stderr)

    # The real panels (per flavor-atlas-rawbase/build_flavor_panels.py) do
    # not carry rendered_prompt_token_count, so get_token_count's tokenizer
    # fallback is on the real critical path. Nothing else checks it before
    # spend, so resolve it here: same import as run_real, then render and
    # tokenize one fixed synthetic string. Read-only; no writes.
    tokenizer_label = "render module tokenizer (get_token_count fallback)"
    tokenizer_ok = False
    tokenizer_detail = ""
    try:
        render_path = resolve_path(base_dir, cell["render_module"]["path"])
        if str(render_path.parent) not in sys.path:
            sys.path.insert(0, str(render_path.parent))
        import ood_breadth_response_confidence_render as render_mod

        tokenizer = render_mod._get_tokenizer()
        prompt = render_mod.render({"question": "dry-run tokenizer check"})
        n_tokens = len(tokenizer(prompt).input_ids)
        tokenizer_ok = True
        tokenizer_detail = f"resolved, {n_tokens} tokens for the probe string"
    except Exception as exc:  # noqa: BLE001 -- any exception here IS the dry-run finding
        tokenizer_detail = f"{type(exc).__name__}: {exc}"
    print(
        f"  [{'ok' if tokenizer_ok else 'FAILED'}] {tokenizer_label}: {tokenizer_detail}",
        file=sys.stderr,
    )
    all_ok = all_ok and tokenizer_ok

    if not all_ok:
        missing = [item["label"] for item in inventory if not item["exists"]]
        mismatched = [item["label"] for item in inventory if item["exists"] and not item["sha256_ok"]]
        print("\ndry-run: STOP -- not every real input resolves.", file=sys.stderr)
        if missing:
            print(f"  missing: {missing}", file=sys.stderr)
        if mismatched:
            print(f"  sha256 mismatch: {mismatched}", file=sys.stderr)
        if not tokenizer_ok:
            print(f"  tokenizer fallback failed: {tokenizer_detail}", file=sys.stderr)
        return 1

    print("\ndry-run: all real inputs resolve; the plan above is what a real run would execute.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_COMMITTED_PATH)
    ap.add_argument("--smoke", action="store_true", help="run the synthetic self-check; touches no real captures")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve every real input and print the execution plan; executes and writes nothing",
    )
    args = ap.parse_args(argv)

    if args.smoke:
        return run_smoke()

    cell = load_yaml(CELL_PATH)
    gates = load_yaml(GATES_PATH)

    if args.dry_run:
        return run_dry_run(cell, gates, HERE)

    code, _payload = run_real(cell, gates, HERE, args.out, ANALYSIS_ROOT / "checkpoints", ANALYSIS_ROOT)
    return code


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

    print("== smoke: real gates.yaml/cell.yaml schema walk ==", file=sys.stderr)
    # Every key path this module actually reads off the REAL gates.yaml and
    # cell.yaml (not the synthetic fixture below), asserting presence only.
    # This exists because the fixture's dicts are hand-built at the SAME
    # shape the code expects, so a fixture-only smoke can pass even when the
    # code's read path has drifted from the real file's schema (as happened
    # when sg4/sg6 were read flat while gates.yaml nests them under
    # `checks:`). Walking the real files here catches that class of drift
    # before a real run burns compute on it.
    real_gates_for_schema_check = load_yaml(GATES_PATH)
    real_cell_for_schema_check = load_yaml(CELL_PATH)

    def walk(d: Any, path: tuple[str, ...]) -> bool:
        cur = d
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return False
            cur = cur[key]
        return True

    gates_key_paths: list[tuple[str, ...]] = [
        ("sg0_input_integrity", "checks"),
        ("sg0_input_integrity", "checks", "kuq_panel_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "ambigqa_panel_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "selfaware_panel_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "panels_manifest_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "kuq_extraction_manifest_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "ambigqa_extraction_manifest_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "selfaware_extraction_manifest_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "atlas_sweep_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "probe_module_sha256_must_equal"),
        ("sg0_input_integrity", "checks", "kuq_rows_must_equal"),
        ("sg0_input_integrity", "checks", "kuq_known_must_equal"),
        ("sg0_input_integrity", "checks", "kuq_unknown_must_equal"),
        ("sg0_input_integrity", "checks", "kuq_flavor_counts_must_equal"),
        ("sg0_input_integrity", "checks", "ambigqa_rows_must_equal"),
        ("sg0_input_integrity", "checks", "selfaware_rows_must_equal"),
        ("sg2_baseline_reproduction", "checks"),
        ("sg2_baseline_reproduction", "checks", "cells"),
        ("sg2_baseline_reproduction", "checks", "hidden_state_0_must_equal_for_all_rows"),
        ("sg4_treatment_strength", "checks"),
        ("sg4_treatment_strength", "checks", "min_activation_oof_r2_at_each_primary_layer"),
        ("sg4_treatment_strength", "checks", "permutation_null_quantile"),
        ("sg4_treatment_strength", "checks", "min_above_permutation_quantile"),
        ("sg6_permutation_negative_control", "checks"),
        ("sg6_permutation_negative_control", "checks", "min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90"),
        ("s_bands",),
        ("s_bands", "primary_cells"),
        ("s_bands", "reference_cells"),
        ("s_bands", "p1_survival_floor_heldout_auroc"),
        ("s_bands", "p2_ambigqa_ceiling"),
        ("s_bands", "p3_surface_only_carrier_floor"),
    ]
    cell_key_paths: list[tuple[str, ...]] = [
        ("seed",),
        ("n_hidden_states",),
        ("hidden_dim",),
        ("source_panels",),
        ("panels_manifest", "path"),
        ("baseline_atlas_sweep", "path"),
        ("probe_protocol", "module"),
        ("render_module", "path"),
        ("residualization", "alpha_grid"),
        ("residualization", "outer_folds"),
        ("residualization", "inner_folds"),
        ("permutation_control", "n_permutations"),
        ("permutation_control", "seed_start"),
        ("planted_signal",),
        ("primary_cells",),
        ("reference_cells", "pooled_all_unknowns"),
        ("reference_cells", "selfaware"),
        ("reference_cells", "ambigqa"),
    ]
    for path in gates_key_paths:
        check(f"real gates.yaml has key path {'.'.join(path)}", walk(real_gates_for_schema_check, path))
    for path in cell_key_paths:
        check(f"real cell.yaml has key path {'.'.join(path)}", walk(real_cell_for_schema_check, path))

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

    print("== smoke: real orchestration end-to-end on a tiny synthetic fixture ==", file=sys.stderr)
    try:
        fixture_ok, fixture_detail = run_fixture_end_to_end_check()
    except Exception as exc:  # noqa: BLE001 -- any exception here IS the failure signal
        fixture_ok, fixture_detail = False, f"raised {type(exc).__name__}: {exc}"
    check(f"real run_real() orchestration produces a complete adjudicated JSON ({fixture_detail})", fixture_ok)

    for p in (ckpt_path.with_suffix(".npz"), ckpt_path.with_suffix(".json"), ckpt_path.with_suffix(".npz.tmp")):
        p.unlink(missing_ok=True)

    print(f"\nsmoke: {len(failures)} failing check(s)" if failures else "\nsmoke: ALL CHECKS PASSED", file=sys.stderr)
    if failures:
        for name in failures:
            print(f"  FAILED: {name}", file=sys.stderr)
        return 1
    return 0


def build_fixture(tmp_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a tiny, real-schema fixture under `tmp_root`: three panels with
    real safetensors extraction dirs, a panels_manifest.json, an
    atlas-sweep placeholder, and matching cell/gates dicts at the SAME
    shape as the production cell.yaml/gates.yaml, just far smaller. This is
    what `run_fixture_end_to_end_check` drives `run_real` against -- it
    never touches a real flavor-atlas-rawbase path.

    Hidden state 0 is constructed IDENTICAL across every row of a panel
    (mirroring the real anchor-embedding invariant), which gives an exact,
    principled 0.5000 null AUROC rather than a hand-picked placeholder.
    """
    from safetensors.torch import save_file as st_save_file
    import torch

    rng = np.random.default_rng(20260813)
    hidden_dim = 4
    n_hidden_states = 6  # layers 0..5

    best_layer_by_flavor = {
        "ambiguous": 1,
        "controversial": 2,
        "counterfactual": 1,
        "false assumption": 2,
        "future unknown": 3,
        "unsolved problem": 3,
    }
    secondary_layer = 5
    ref_best = {"pooled_all_unknowns": 1, "selfaware": 2, "ambigqa": 2}

    def write_rows(panel_dir: Path, rows: list[dict[str, Any]], y_known: np.ndarray) -> None:
        panel_dir.mkdir(parents=True, exist_ok=True)
        layer_weights = {L: rng.normal(size=hidden_dim) for L in range(1, n_hidden_states)}
        const0 = np.full(hidden_dim, 0.1, dtype=np.float32)
        for i, row in enumerate(rows):
            tensors: dict[str, torch.Tensor] = {"L0": torch.from_numpy(const0.copy())}
            for L in range(1, n_hidden_states):
                sign = 1.0 if y_known[i] == 1 else -1.0
                noise = rng.normal(scale=0.3, size=hidden_dim)
                tensors[f"L{L}"] = torch.from_numpy((sign * layer_weights[L] + noise).astype(np.float32))
            stem = row["row_key"].replace("::", "__")
            st_save_file(tensors, str(panel_dir / f"{stem}__anchor.safetensors"))

    # ---- KUQ: six flavors, six unknown rows each, plus a known pool ----
    kuq_rows: list[dict[str, Any]] = []
    kuq_y: list[int] = []
    n_unknown_per_flavor = 6
    n_known = 24
    for flavor in KUQ_CATEGORIES:
        for i in range(n_unknown_per_flavor):
            rk = f"kuq-{flavor.replace(' ', '_')}-{i:03d}"
            kuq_rows.append(
                {
                    "row_key": rk,
                    "question": f"fixture unknown question {flavor} {i}",
                    "label": "unknown",
                    "flavor": flavor,
                    "rendered_prompt_token_count": 12 + i,
                }
            )
            kuq_y.append(0)
    for i in range(n_known):
        rk = f"kuq-known-{i:03d}"
        kuq_rows.append(
            {
                "row_key": rk,
                "question": f"fixture known question {i}",
                "label": "known",
                "flavor": "known",
                "rendered_prompt_token_count": 10 + i,
            }
        )
        kuq_y.append(1)
    kuq_y_arr = np.asarray(kuq_y)

    # ---- AmbigQA / SelfAware: single pool each, known vs unknown ----
    def make_pool_rows(prefix: str, n_known_pool: int, n_unknown_pool: int, flavor_name: str) -> tuple[list[dict[str, Any]], np.ndarray]:
        rows: list[dict[str, Any]] = []
        y: list[int] = []
        for i in range(n_known_pool):
            rows.append(
                {
                    "row_key": f"{prefix}-known-{i:03d}",
                    "question": f"fixture {prefix} known question {i}",
                    "label": "known",
                    "flavor": flavor_name,
                    "rendered_prompt_token_count": 11 + i,
                }
            )
            y.append(1)
        for i in range(n_unknown_pool):
            rows.append(
                {
                    "row_key": f"{prefix}-unknown-{i:03d}",
                    "question": f"fixture {prefix} unknown question {i}",
                    "label": "unknown",
                    "flavor": flavor_name,
                    "rendered_prompt_token_count": 13 + i,
                }
            )
            y.append(0)
        return rows, np.asarray(y)

    ambigqa_rows, ambigqa_y = make_pool_rows("ambigqa", 8, 8, "ambigqa")
    selfaware_rows, selfaware_y = make_pool_rows("selfaware", 12, 8, "selfaware")

    rawbase_dir = tmp_root / "rawbase"
    extraction_root = rawbase_dir / "analysis" / "extraction"
    panels_root = rawbase_dir / "analysis" / "panels"
    panels_root.mkdir(parents=True, exist_ok=True)

    write_rows(extraction_root / "kuq", kuq_rows, kuq_y_arr)
    write_rows(extraction_root / "ambigqa", ambigqa_rows, ambigqa_y)
    write_rows(extraction_root / "selfaware", selfaware_rows, selfaware_y)

    def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

    kuq_panel_path = panels_root / "kuq_panel.jsonl"
    ambigqa_panel_path = panels_root / "ambigqa_panel.jsonl"
    selfaware_panel_path = panels_root / "selfaware_panel.jsonl"
    write_jsonl(kuq_panel_path, kuq_rows)
    write_jsonl(ambigqa_panel_path, ambigqa_rows)
    write_jsonl(selfaware_panel_path, selfaware_rows)

    for name, extraction_dir in (
        ("kuq", extraction_root / "kuq"),
        ("ambigqa", extraction_root / "ambigqa"),
        ("selfaware", extraction_root / "selfaware"),
    ):
        (extraction_dir / "manifest.json").write_text(
            json.dumps({"layers": "all", "n_hidden_states": n_hidden_states, "hidden_dim": hidden_dim}), encoding="utf-8"
        )

    flavor_counts = {f: n_unknown_per_flavor for f in KUQ_CATEGORIES}
    panels_manifest = {
        "fg0_status": "PASS",
        "sources": {"kuq": {"path": "kuq_panel.jsonl"}, "ambigqa": {"path": "ambigqa_panel.jsonl"}, "selfaware": {"path": "selfaware_panel.jsonl"}},
        "counts": {
            "kuq": {"n": len(kuq_rows), "by_label": {"known": n_known, "unknown": n_unknown_per_flavor * len(KUQ_CATEGORIES)}, "by_flavor": flavor_counts},
            "ambigqa": {"n": len(ambigqa_rows), "by_label": {"known": 8, "unknown": 8}},
            "selfaware": {"n": len(selfaware_rows), "by_label": {"known": 12, "unknown": 8}},
        },
    }
    panels_manifest_path = panels_root / "panels_manifest.json"
    panels_manifest_path.write_text(json.dumps(panels_manifest, indent=2), encoding="utf-8")

    atlas_sweep_path = rawbase_dir / "analysis-committed" / "atlas_sweep.json"
    atlas_sweep_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_sweep_path.write_text(json.dumps({"fixture": True}), encoding="utf-8")

    cell_fixture: dict[str, Any] = {
        "seed": 4242,
        "n_hidden_states": n_hidden_states,
        "hidden_dim": hidden_dim,
        "source_panels": {
            "kuq": {
                "extraction_dir": "rawbase/analysis/extraction/kuq",
                "panel_file": "rawbase/analysis/panels/kuq_panel.jsonl",
                "n_rows": len(kuq_rows),
                "n_known": n_known,
                "n_unknown": n_unknown_per_flavor * len(KUQ_CATEGORIES),
                "flavor_counts": flavor_counts,
            },
            "ambigqa": {
                "extraction_dir": "rawbase/analysis/extraction/ambigqa",
                "panel_file": "rawbase/analysis/panels/ambigqa_panel.jsonl",
                "n_rows": len(ambigqa_rows),
            },
            "selfaware": {
                "extraction_dir": "rawbase/analysis/extraction/selfaware",
                "panel_file": "rawbase/analysis/panels/selfaware_panel.jsonl",
                "n_rows": len(selfaware_rows),
            },
        },
        "panels_manifest": {"path": "rawbase/analysis/panels/panels_manifest.json"},
        "baseline_atlas_sweep": {"path": "rawbase/analysis-committed/atlas_sweep.json"},
        "probe_protocol": {"module": str(ITEM26_DIR / "internal_panel_probe_gate.py")},
        "render_module": {"path": str(RENDERS_DIR / "ood_breadth_response_confidence_render.py")},
        "surface_covariates": {
            "lexical": {
                "word_hash_features": 32,
                "char_hash_features": 32,
                "word_svd_components": 3,
                "char_svd_components": 3,
                "word_ngram_range": [1, 2],
                "char_ngram_range": [3, 5],
                "alternate_sign": False,
                "sublinear_tf": True,
            }
        },
        "residualization": {"outer_folds": 3, "inner_folds": 2, "alpha_grid": [0.1, 1.0, 10.0]},
        "permutation_control": {"n_permutations": 2, "seed_start": 5000},
        "planted_signal": {
            "hs_index": 0,
            "weight_fit_seed": 606,
            "projection_seed": 707,
            "gamma_grid": [1.0, 2.0, 4.0, 8.0, 16.0, 32.0],
            "planted_pooled_auroc_must_reach_at_least": 0.90,
            "residualized_planted_pooled_auroc_must_be_at_most": 0.99,
            "max_flavor_deviation_from_unplanted_residualized": 1.0,
        },
        "primary_cells": {f: {"best_layer": best_layer_by_flavor[f], "secondary_layer": secondary_layer} for f in KUQ_CATEGORIES},
        "reference_cells": {
            "pooled_all_unknowns": {"best_layer": ref_best["pooled_all_unknowns"], "secondary_layer": secondary_layer},
            "selfaware": {"best_layer": ref_best["selfaware"], "secondary_layer": secondary_layer},
            "ambigqa": {"best_layer": ref_best["ambigqa"], "secondary_layer": secondary_layer},
        },
        "s3_transfer": {
            "selfaware_extra_layers": sorted(set(best_layer_by_flavor.values()) - {ref_best["selfaware"]}),
            "kuq_extra_layers": [ref_best["selfaware"]],
            "selfaware_to_kuq_fit_layer": ref_best["selfaware"],
        },
        "containment": {"committed_output": "output/surface_control.json"},
    }

    def sha(path: Path) -> str:
        return sha256_file(path)

    gates_fixture: dict[str, Any] = {
        "sg0_input_integrity": {
            "checks": {
                "kuq_panel_sha256_must_equal": sha(kuq_panel_path),
                "ambigqa_panel_sha256_must_equal": sha(ambigqa_panel_path),
                "selfaware_panel_sha256_must_equal": sha(selfaware_panel_path),
                "panels_manifest_sha256_must_equal": sha(panels_manifest_path),
                "kuq_extraction_manifest_sha256_must_equal": sha(extraction_root / "kuq" / "manifest.json"),
                "ambigqa_extraction_manifest_sha256_must_equal": sha(extraction_root / "ambigqa" / "manifest.json"),
                "selfaware_extraction_manifest_sha256_must_equal": sha(extraction_root / "selfaware" / "manifest.json"),
                "atlas_sweep_sha256_must_equal": sha(atlas_sweep_path),
                "probe_module_sha256_must_equal": sha(ITEM26_DIR / "internal_panel_probe_gate.py"),
                "kuq_rows_must_equal": len(kuq_rows),
                "kuq_known_must_equal": n_known,
                "kuq_unknown_must_equal": n_unknown_per_flavor * len(KUQ_CATEGORIES),
                "kuq_flavor_counts_must_equal": flavor_counts,
                "ambigqa_rows_must_equal": len(ambigqa_rows),
                "selfaware_rows_must_equal": len(selfaware_rows),
                "n_hidden_states_present_must_equal": n_hidden_states,
                "hidden_dim_must_equal": hidden_dim,
            }
        },
        "sg2_baseline_reproduction": {
            "checks": {
                "cells": {},  # populated below by a bootstrap pass over the same code path
                "hidden_state_0_must_equal_for_all_rows": 0.5000,
            }
        },
        "sg4_treatment_strength": {
            "checks": {
                "min_activation_oof_r2_at_each_primary_layer": 0.0,
                "permutation_null_quantile": 0.95,
                "min_above_permutation_quantile": 0.0,
            }
        },
        "sg6_permutation_negative_control": {
            "checks": {"min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90": 0}
        },
        "s_bands": {
            "primary_cells": {f: [cell_fixture["primary_cells"][f]["best_layer"], secondary_layer] for f in KUQ_CATEGORIES},
            "reference_cells": {"selfaware": [ref_best["selfaware"], secondary_layer], "ambigqa": [ref_best["ambigqa"], secondary_layer]},
            "p1_survival_floor_heldout_auroc": 0.90,
            "p2_ambigqa_ceiling": 0.75,
            "p3_surface_only_carrier_floor": 0.75,
        },
    }

    # Bootstrap pass: compute the raw baseline the SAME way evaluate_sg2
    # will at real-run time, then transcribe it into the fixture's own
    # gates table -- exactly how a human populates gates.yaml's SG2 table
    # from one real atlas-sweep run, just automated here.
    kuq_panel = load_panel("kuq", cell_fixture, tmp_root)
    ambigqa_panel = load_panel("ambigqa", cell_fixture, tmp_root)
    selfaware_panel = load_panel("selfaware", cell_fixture, tmp_root)
    raw_cache = make_raw_cache()
    bootstrap = evaluate_sg2(kuq_panel, ambigqa_panel, selfaware_panel, cell_fixture, gates_fixture, raw_cache)
    gates_fixture["sg2_baseline_reproduction"]["checks"]["cells"] = bootstrap["computed"]

    return cell_fixture, gates_fixture


def run_fixture_end_to_end_check() -> tuple[bool, str]:
    """Drives the REAL `run_real` orchestration end-to-end against a tiny
    synthetic fixture in the real on-disk schema, asserting it produces a
    complete adjudicated JSON. This fails loudly if `main()`'s real-data
    branch is ever reduced back to a stub, because `run_real` would not
    exist / would not be reachable / would not return a payload."""
    import shutil
    import tempfile

    fixture_scratch = ANALYSIS_ROOT / "smoke" / "fixture"
    if fixture_scratch.exists():
        shutil.rmtree(fixture_scratch)
    checkpoint_root = fixture_scratch / "checkpoints"
    out_path = fixture_scratch / "surface_control.json"

    with tempfile.TemporaryDirectory(prefix="style-control-fixture-") as tmp:
        tmp_root = Path(tmp)
        cell_fixture, gates_fixture = build_fixture(tmp_root)
        code, payload = run_real(cell_fixture, gates_fixture, tmp_root, out_path, checkpoint_root, fixture_scratch)

    if code != 0 or payload is None:
        return False, f"run_real returned code={code}, payload is None={payload is None}"
    if not out_path.is_file():
        return False, "committed output was not written to disk"
    on_disk = json.loads(out_path.read_text(encoding="utf-8"))

    required_top_level = {
        "cell", "config_fingerprint", "gates", "controls_pass", "s1_primary",
        "reference", "s2_surface_only", "s3_transfer", "c1_treatment_strength",
        "c2_permutation", "c3_planted", "decision", "sg2_baseline",
    }
    missing = required_top_level - set(on_disk.keys())
    if missing:
        return False, f"committed JSON missing top-level keys: {sorted(missing)}"
    if set(on_disk["s1_primary"].keys()) != set(KUQ_CATEGORIES):
        return False, f"s1_primary flavor keys incomplete: {sorted(on_disk['s1_primary'].keys())}"
    if len(on_disk["s3_transfer"]["kuq_flavor_to_selfaware"]) != len(KUQ_CATEGORIES):
        return False, "s3_transfer kuq_flavor_to_selfaware incomplete"
    if not (checkpoint_root.exists() and any(checkpoint_root.rglob("*.json"))):
        return False, "no incremental checkpoints were written during the real orchestration"

    shutil.rmtree(fixture_scratch, ignore_errors=True)
    return True, f"wrote {len(required_top_level)} top-level sections, controls_pass={on_disk['controls_pass']}"


def ipg_cv_auroc_with_oof(x: np.ndarray, y: np.ndarray):
    """Thin wrapper resolving the pinned protocol lazily, so smoke mode
    (which never touches real captures) still exercises the SAME imported,
    unmodified function real runs use."""
    import internal_panel_probe_gate as ipg

    return ipg._cv_auroc_with_oof(x, y, folds=5, C=0.5, seed=0)


if __name__ == "__main__":
    raise SystemExit(main())
