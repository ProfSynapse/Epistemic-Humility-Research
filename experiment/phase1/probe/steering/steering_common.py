#!/usr/bin/env python3
"""Shared plumbing for the Amendment AA steering harnesses (run_arm_a / run_arm_b).

SPEC: experiment/protocol/AMENDMENT-AA-causal-confidence-steering.md (Tier-2,
DRAFT — NOT signed; NO GPU cell may launch without signature + explicit user
launch approval naming cells/lane).

CPU-ONLY AT IMPORT TIME. Everything in this module is unit-testable with
synthetic fixtures: no model loading, no GPU, no network. Model loading lives
exclusively inside the guarded main() paths of run_arm_a.py / run_arm_b.py.

What lives here (so the two runners stay thin):
  - eval-pool construction (SelfAware gate pool / PopQA+TriviaQA dial pool,
    plus a --pool-file JSONL override for CPU dry-runs and tests)
  - grading: abstention (Amendment-Z grader), correctness (Cheng scorer),
    degenerate-output detection (the amendment's coherence floor)
  - the unified two-pass protocol pieces (revision-instruction prompt builder,
    revised-flag computation)
  - per-item flat record construction + per-condition summaries (gate metric,
    dial metric = appropriate-revision discrimination)
  - paired bootstrap CIs (2000 resamples, Amendment-X convention)
  - GenerationHookController: cache-aware gating of confidence_steer.SteeringHook
    across the forward calls of one generate() (prefill vs decode steps)
  - cell-JSON writing

Reused modules (imported, not reimplemented):
  - confidence_steer.py  (SteeringHook, load_direction, compute_proportional_alpha)
  - cot_inject.py        (InjectionConfig, build_think_prompt)
  - eval/scorers.py      (is_correct, is_stated_confidence_refusal — Cheng port)
  - amendment_s_correctness_probe_extract.py (SYSTEM_PROMPT, build_pool,
    _content_end_index, _config_sha — the Amendment-X answerable pool source)

Vendored (small, with source named):
  - load_selfaware_pool  (from amendment_u_unified_extract.py — imported, it is
    import-light; kept as an import, see below)
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Path setup: steering/ -> probe/ (backends, amendment_*) and eval/ (scorers)
# ---------------------------------------------------------------------------

STEERING_DIR = Path(__file__).resolve().parent
PROBE_DIR = STEERING_DIR.parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for _p in (str(STEERING_DIR), str(PROBE_DIR), str(EVAL_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scorers  # noqa: E402  (eval/scorers.py — Cheng-validated grader port)
# Answerable-pool builder + prompt/scan helpers VERBATIM from Amendment S
# (the same functions Amendment X composes its mixed pool from).
from amendment_s_correctness_probe_extract import (  # noqa: E402
    SYSTEM_PROMPT,
    _config_sha,
    _content_end_index,
    build_pool,
)
# SelfAware pool loader VERBATIM from Amendment U (same import Amendment X uses).
from amendment_u_unified_extract import load_selfaware_pool  # noqa: E402

from confidence_steer import (  # noqa: E402
    SteeringHook,
    compute_proportional_alpha,
    load_direction,
)

__all__ = [
    "SYSTEM_PROMPT",
    "REVISION_INSTRUCTION",
    "COHERENCE_FLOOR",
    "N_BOOT_DEFAULT",
    "load_direction",
    "compute_proportional_alpha",
    "SteeringHook",
    "GenerationHookController",
    "parse_alpha_list",
    "text_hash",
    "truncate_text",
    "is_degenerate",
    "grade_output",
    "compute_revised",
    "make_flat_record",
    "load_pool_file",
    "build_eval_pool",
    "build_initial_messages",
    "build_revision_messages",
    "probe_score_from_hidden",
    "metric_abstention_unknown",
    "metric_answer_rate_known",
    "metric_accuracy_known",
    "metric_accuracy_answerable",
    "metric_revision_discrimination",
    "metric_degenerate_rate",
    "summarize_condition",
    "paired_bootstrap_diff_ci",
    "compare_conditions",
    "adequacy_check",
    "write_cell_json",
]

# ---------------------------------------------------------------------------
# Constants (Amendment AA §"Unified protocol" / coherence floor / CI convention)
# ---------------------------------------------------------------------------

REVISION_INSTRUCTION = (
    "Double-check your answer above. If you are not confident it is correct, "
    "say so or revise it."
)

# Amendment AA coherence floor: degenerate-output rate must be <= 5% per cell.
COHERENCE_FLOOR = 0.05

# Bootstrap resamples (Amendment X / amendment_x_cross_model_score.py convention).
N_BOOT_DEFAULT = 2000

# Truncation length for stored per-item texts (full text is hashed).
TEXT_TRUNCATE = 240


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def parse_alpha_list(spec: str) -> list[float]:
    """Parse a comma-separated alpha list, e.g. '-4,-2,-1,0,1,2,4'."""
    vals = [float(tok) for tok in spec.split(",") if tok.strip() != ""]
    if not vals:
        raise ValueError(f"empty alpha list: {spec!r}")
    return vals


def text_hash(text: str) -> str:
    """Stable sha256 (hex, 16 chars) of a generated text for provenance."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def truncate_text(text: str, limit: int = TEXT_TRUNCATE) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "…"


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Degenerate-output detection (the amendment's coherence floor definition:
# "empty, a single repeated n-gram, or unparseable by the same
#  answer/abstention grader used in Amendment Z")
# ---------------------------------------------------------------------------

_MAX_NGRAM = 5
_MIN_REPEATS = 3


def _is_repeated_ngram(tokens: list[str]) -> bool:
    """True if the token list is one n-gram (n<=_MAX_NGRAM) repeated >=_MIN_REPEATS
    times, covering the whole output (a trailing partial repeat is allowed)."""
    n_tok = len(tokens)
    for n in range(1, _MAX_NGRAM + 1):
        if n_tok < n * _MIN_REPEATS:
            continue
        unit = tokens[:n]
        reps = n_tok // n
        if reps < _MIN_REPEATS:
            continue
        if all(tokens[i * n:(i + 1) * n] == unit for i in range(reps)) and \
                tokens[reps * n:] == unit[: n_tok - reps * n]:
            return True
    return False


def is_degenerate(text: str) -> bool:
    """Coherence-floor flag for one generated output.

    Degenerate iff: empty (after stripping), no alphanumeric content (nothing
    the substring-based Amendment-Z grader can parse), or a single repeated
    n-gram (n<=5, >=3 repetitions covering the whole output).
    """
    stripped = (text or "").strip()
    if not stripped:
        return True
    if not re.search(r"[a-zA-Z0-9]", stripped):
        return True
    tokens = stripped.split()
    return _is_repeated_ngram(tokens)


# ---------------------------------------------------------------------------
# Grading (Amendment-Z grader: scorers.is_stated_confidence_refusal for the
# gate / abstention side, scorers.is_correct vs gold aliases for the dial)
# ---------------------------------------------------------------------------

def grade_output(text: str, aliases_norm: Optional[Sequence[str]]) -> dict:
    """Grade one generated output.

    Returns
    -------
    dict with:
      degenerate : coherence-floor flag
      abstained  : Amendment-Z abstention detection (gate metric input)
      answered   : non-degenerate and not abstained
      correct    : bool if aliases_norm is a non-empty list (dial metric input);
                   None when the row carries no gold aliases (SelfAware rows)
    """
    degenerate = is_degenerate(text)
    abstained = (not degenerate) and scorers.is_stated_confidence_refusal(text)
    answered = (not degenerate) and (not abstained)
    correct: Optional[bool] = None
    if answered and aliases_norm:
        correct = bool(scorers.is_correct(text, list(aliases_norm)))
    return {
        "degenerate": degenerate,
        "abstained": abstained,
        "answered": answered,
        "correct": correct,
    }


def compute_revised(
    initial_text: str,
    final_text: str,
    initial_grade: dict,
    final_grade: dict,
) -> bool:
    """Did the model revise between the initial and final pass?

    Revised iff the final pass abstains where the initial answered, OR the
    normalized answer content changed (scorers.normalize space — the same
    normalizer the correctness grader keys on).
    """
    if final_grade["abstained"] and initial_grade["answered"]:
        return True
    return scorers.normalize(initial_text or "") != scorers.normalize(final_text or "")


def make_flat_record(
    item: dict,
    initial_text: str,
    final_text: str,
    extra: Optional[dict] = None,
) -> dict:
    """Build the flat per-item record every summary/bootstrap function consumes."""
    initial_grade = grade_output(initial_text, item.get("aliases_norm"))
    final_grade = grade_output(final_text, item.get("aliases_norm"))
    rec = {
        "row_key": item["row_key"],
        "source": item["source"],
        "initial_text": truncate_text(initial_text),
        "initial_hash": text_hash(initial_text),
        "final_text": truncate_text(final_text),
        "final_hash": text_hash(final_text),
        "initial_grade": initial_grade,
        "final_grade": final_grade,
        "revised": compute_revised(initial_text, final_text, initial_grade, final_grade),
        "degenerate": bool(initial_grade["degenerate"] or final_grade["degenerate"]),
    }
    if extra:
        rec.update(extra)
    return rec


# ---------------------------------------------------------------------------
# Eval-pool construction (Amendment AA §Inputs: SelfAware known/unknown rows
# for gate cells; PopQA+TriviaQA answerable pool for dial cells).
# ---------------------------------------------------------------------------

def load_pool_file(path: Path) -> list[dict]:
    """Load a JSONL pool override (CPU dry-runs / unit tests).

    Each row must carry: row_key, question, source in
    {selfaware_known, selfaware_unknown, answerable}; aliases_norm optional
    (defaults to [] — required in practice for answerable rows to grade the dial).
    """
    items = []
    with Path(path).open(encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            for key in ("row_key", "question", "source"):
                if key not in r:
                    raise ValueError(f"pool-file row missing {key!r}: {r}")
            if r["source"] not in ("selfaware_known", "selfaware_unknown", "answerable"):
                raise ValueError(f"pool-file row has bad source {r['source']!r}")
            r.setdefault("aliases_norm", [])
            items.append(r)
    if not items:
        raise ValueError(f"pool file {path} is empty")
    return items


def _take_by_source(items: list[dict], source: str, n: int) -> list[dict]:
    picked = [it for it in items if it["source"] == source][:n]
    if len(picked) < n:
        raise ValueError(
            f"pool has only {len(picked)} items with source={source!r}, need {n}"
        )
    return picked


def build_eval_pool(
    eval_pool: str,
    n_unknown: int,
    n_known: int,
    n_answerable: int,
    seed: int,
    pool_file: Optional[Path] = None,
    datasets_root: Optional[Path] = None,
    gate_rows: Optional[Path] = None,
) -> list[dict]:
    """Build the per-cell item pool.

    eval_pool='gate' -> n_unknown SelfAware-unknown + n_known SelfAware-known
    eval_pool='dial' -> n_answerable PopQA+TriviaQA graded rows

    A --pool-file JSONL overrides the dataset sources entirely (CPU dry-run /
    test path). Otherwise the real sources are the Amendment-Z item sets:
    load_selfaware_pool(gate_rows) and build_pool(datasets_root, popqa+triviaqa).
    """
    if eval_pool not in ("gate", "dial"):
        raise ValueError(f"eval_pool must be 'gate' or 'dial', got {eval_pool!r}")

    if pool_file is not None:
        base = load_pool_file(pool_file)
    elif eval_pool == "gate":
        if gate_rows is None:
            raise ValueError("gate pool requires --gate-rows (or --pool-file)")
        sa = load_selfaware_pool(Path(gate_rows), seed)
        base = [{
            "row_key": it["row_key"],
            "dataset": it["dataset"],
            "question": it["question"],
            "source": ("selfaware_known" if it["label"] == "known"
                       else "selfaware_unknown"),
            "aliases_norm": it.get("aliases_norm", []),
        } for it in sa]
    else:
        if datasets_root is None:
            raise ValueError("dial pool requires --datasets-root (or --pool-file)")
        answerable = build_pool(Path(datasets_root), ["popqa", "triviaqa"], None, seed)
        base = []
        for it in answerable:
            it = dict(it)
            it["source"] = "answerable"
            base.append(it)

    if eval_pool == "gate":
        pool = (_take_by_source(base, "selfaware_unknown", n_unknown)
                + _take_by_source(base, "selfaware_known", n_known))
    else:
        pool = _take_by_source(base, "answerable", n_answerable)

    random.Random(seed).shuffle(pool)
    return pool


# ---------------------------------------------------------------------------
# Two-pass prompt construction (chat-message level; rendering with the model's
# own tokenizer happens in the runners' guarded main() paths)
# ---------------------------------------------------------------------------

def build_initial_messages(question: str, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]


def build_revision_messages(
    question: str,
    initial_answer: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> list[dict]:
    """Revision pass: the initial answer goes back as an assistant turn and the
    fixed revision instruction (Amendment AA unified protocol) follows."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
        {"role": "assistant", "content": initial_answer},
        {"role": "user", "content": REVISION_INSTRUCTION},
    ]


# ---------------------------------------------------------------------------
# Probe scoring from a hidden state (confidence_steer.py mechanics: score =
# logistic(dot(h, d)); calibration stats then drive compute_proportional_alpha)
# ---------------------------------------------------------------------------

def probe_score_from_hidden(h: np.ndarray, d: np.ndarray) -> float:
    """P(positive)-style score for one hidden-state vector against a unit-norm
    direction: logistic(dot(h, d)) — the mapping named in confidence_steer.py's
    alpha-proportional recipe."""
    z = float(np.dot(np.asarray(h, dtype=np.float64),
                     np.asarray(d, dtype=np.float64)))
    return float(1.0 / (1.0 + math.exp(-z)))


# ---------------------------------------------------------------------------
# GenerationHookController: cache-aware gating of the SteeringHook within one
# generate() call. HuggingFace generate() with KV cache calls the hooked layer
# once for the prefill (seq_len == prompt_len) and once per decode step
# (seq_len == 1). The controller maps the amendment's positions onto that:
#   mode='anchor'     — steer ONLY the prefill call, at the LAST prompt token
#                       (the pre-answer anchor; propagates via the KV cache)
#   mode='gen_stream' — steer ONLY decode-step calls (every generated token;
#                       the amendment's END/all-post write)
#   mode='off'        — never steer (the alpha=0 control / the inactive pass)
# ---------------------------------------------------------------------------

class GenerationHookController:
    """Register THIS callable (not the raw hook) as the layer forward hook.

    The runner calls begin_pass(mode, alpha) before each generate() so the
    underlying SteeringHook is active only in the correct pass and only at the
    correct forward calls within that pass.
    """

    MODES = ("anchor", "gen_stream", "off")

    def __init__(self, hook: SteeringHook) -> None:
        self.hook = hook
        self.mode = "off"
        self._nth_call = 0
        self.pass_log: list[dict] = []  # (mode, alpha) per begin_pass, for provenance

    def begin_pass(self, mode: str, alpha: float) -> None:
        if mode not in self.MODES:
            raise ValueError(f"mode must be one of {self.MODES}, got {mode!r}")
        self.mode = mode
        self.hook.alpha = float(alpha)
        self._nth_call = 0
        self.pass_log.append({"mode": mode, "alpha": float(alpha)})

    def __call__(self, module, inputs, output):
        self._nth_call += 1
        if self.mode == "off" or self.hook.alpha == 0.0:
            return output
        if self.mode == "anchor":
            if self._nth_call == 1:  # prefill only
                self.hook.position = "anchor"
                self.hook.anchor_token_idx = None  # last prompt token
                return self.hook(module, inputs, output)
            return output
        # gen_stream: skip the prefill (no generated tokens yet), steer every
        # decode step (seq_len == 1 under KV cache -> steer that one position).
        if self._nth_call == 1:
            return output
        self.hook.position = "all_post"
        self.hook.anchor_start = 0
        return self.hook(module, inputs, output)


# ---------------------------------------------------------------------------
# Metrics over flat records. Each metric returns float or None (undefined on
# this record subset — e.g. no unknown rows, no graded rows, empty class).
# Degenerate-final records are EXCLUDED from rate denominators; the degenerate
# rate itself is reported separately against the 5% coherence floor.
# ---------------------------------------------------------------------------

def _clean(records: list[dict]) -> list[dict]:
    return [r for r in records if not r["final_grade"]["degenerate"]]


def metric_abstention_unknown(records: list[dict]) -> Optional[float]:
    """Gate metric: final abstention rate on unknown questions."""
    sub = [r for r in _clean(records) if r["source"] == "selfaware_unknown"]
    if not sub:
        return None
    return float(np.mean([r["final_grade"]["abstained"] for r in sub]))


def metric_answer_rate_known(records: list[dict]) -> Optional[float]:
    """No-regression proxy on SelfAware-known rows (ungraded: no gold aliases),
    final answer rate = 1 - abstention."""
    sub = [r for r in _clean(records) if r["source"] == "selfaware_known"]
    if not sub:
        return None
    return float(np.mean([r["final_grade"]["answered"] for r in sub]))


def metric_accuracy_known(records: list[dict]) -> Optional[float]:
    """Final accuracy on known rows, only when the pool carries gold aliases."""
    sub = [r for r in _clean(records)
           if r["source"] == "selfaware_known"
           and r["final_grade"]["correct"] is not None]
    if not sub:
        return None
    return float(np.mean([r["final_grade"]["correct"] for r in sub]))


def metric_accuracy_answerable(records: list[dict]) -> Optional[float]:
    """Final accuracy on graded answerable rows (dial cells' no-regression floor)."""
    sub = [r for r in _clean(records) if r["source"] == "answerable"]
    if not sub:
        return None
    vals = [bool(r["final_grade"]["correct"]) for r in sub]
    return float(np.mean(vals))


def metric_revision_discrimination(records: list[dict]) -> Optional[float]:
    """Dial metric: P(revise | initial wrong) - P(revise | initial correct),
    over records whose initial pass produced a GRADED answer."""
    wrong, correct = [], []
    for r in _clean(records):
        c = r["initial_grade"]["correct"]
        if c is None:
            continue
        (correct if c else wrong).append(bool(r["revised"]))
    if not wrong or not correct:
        return None
    return float(np.mean(wrong) - np.mean(correct))


def metric_degenerate_rate(records: list[dict]) -> Optional[float]:
    """Fraction of records whose initial OR final output is degenerate
    (checked against the 5% coherence floor)."""
    if not records:
        return None
    return float(np.mean([r["degenerate"] for r in records]))


_METRICS: dict[str, Callable[[list[dict]], Optional[float]]] = {
    "abstention_unknown": metric_abstention_unknown,
    "answer_rate_known": metric_answer_rate_known,
    "accuracy_known": metric_accuracy_known,
    "accuracy_answerable": metric_accuracy_answerable,
    "revision_discrimination": metric_revision_discrimination,
    "degenerate_rate": metric_degenerate_rate,
}


def summarize_condition(records: list[dict]) -> dict:
    """All defined metrics + counts for one condition (one alpha / one variant)."""
    out: dict = {"n_items": len(records)}
    for name, fn in _METRICS.items():
        v = fn(records)
        out[name] = round(v, 4) if v is not None else None
    n_wrong = sum(1 for r in _clean(records) if r["initial_grade"]["correct"] is False)
    n_correct = sum(1 for r in _clean(records) if r["initial_grade"]["correct"] is True)
    out["n_initial_wrong"] = n_wrong
    out["n_initial_correct"] = n_correct
    dr = out["degenerate_rate"]
    out["coherence_floor_ok"] = (dr is not None and dr <= COHERENCE_FLOOR)
    return out


# ---------------------------------------------------------------------------
# Paired bootstrap (2000 resamples — Amendment X CI convention, adapted from
# amendment_u_two_signal_score.boot_auroc_ci's resample-and-percentile shape
# to paired condition contrasts on the same item set)
# ---------------------------------------------------------------------------

def paired_bootstrap_diff_ci(
    stat_fn: Callable[[list[dict]], Optional[float]],
    records_a: list[dict],
    records_b: list[dict],
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = 20260701,
) -> Optional[dict]:
    """95% CI for stat_fn(a) - stat_fn(b) with items resampled IN PAIRS.

    records_a and records_b must be aligned item-for-item (same row_key order);
    resampling draws the same indices from both, preserving the pairing.
    Resamples where the statistic is undefined on either side are skipped
    (mirrors boot_auroc_ci's degenerate-resample skip).
    Returns None when the point statistic is undefined.
    """
    if len(records_a) != len(records_b):
        raise ValueError("paired bootstrap requires equal-length record lists")
    for ra, rb in zip(records_a, records_b):
        if ra["row_key"] != rb["row_key"]:
            raise ValueError("paired bootstrap requires row_key-aligned records")
    sa, sb = stat_fn(records_a), stat_fn(records_b)
    if sa is None or sb is None:
        return None
    rng = np.random.default_rng(seed)
    n = len(records_a)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        ba = [records_a[i] for i in idx]
        bb = [records_b[i] for i in idx]
        da, db = stat_fn(ba), stat_fn(bb)
        if da is None or db is None:
            continue
        diffs.append(da - db)
    diffs = np.asarray(diffs)
    if len(diffs) == 0:
        return None
    return {
        "delta": round(float(sa - sb), 4),
        "ci_lo": round(float(np.percentile(diffs, 2.5)), 4),
        "ci_hi": round(float(np.percentile(diffs, 97.5)), 4),
        "n_boot": int(len(diffs)),
        "ci_excludes_zero": bool(
            float(np.percentile(diffs, 2.5)) > 0.0
            or float(np.percentile(diffs, 97.5)) < 0.0
        ),
    }


def compare_conditions(
    records_test: list[dict],
    records_control: list[dict],
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = 20260701,
) -> dict:
    """Paired bootstrap contrasts (test - control) for every defined metric.

    'Control' is the alpha=0 sweep point for Arm A and the placebo variant for
    Arm B (Amendment AA: never a no-injection baseline)."""
    out = {}
    for name, fn in _METRICS.items():
        if name == "degenerate_rate":
            continue  # floor is per-condition, not a contrast
        ci = paired_bootstrap_diff_ci(fn, records_test, records_control,
                                      n_boot=n_boot, seed=seed)
        if ci is not None:
            out[name] = ci
    return out


def adequacy_check(control_records: list[dict]) -> dict:
    """Amendment AA adequacy floors, evaluated on the control condition:
    >=40 wrong AND >=40 correct initial answers (dial cells);
    >=100 unknown items ANSWERED under control (gate cells)."""
    clean = _clean(control_records)
    n_wrong = sum(1 for r in clean if r["initial_grade"]["correct"] is False)
    n_correct = sum(1 for r in clean if r["initial_grade"]["correct"] is True)
    n_unknown_answered = sum(
        1 for r in clean
        if r["source"] == "selfaware_unknown" and r["initial_grade"]["answered"])
    return {
        "n_initial_wrong": n_wrong,
        "n_initial_correct": n_correct,
        "n_unknown_answered_control": n_unknown_answered,
        "dial_adequate_ge_40_40": bool(n_wrong >= 40 and n_correct >= 40),
        "gate_adequate_ge_100_unknown_answered": bool(n_unknown_answered >= 100),
    }


# ---------------------------------------------------------------------------
# Cell-JSON output
# ---------------------------------------------------------------------------

def write_cell_json(out_path: Path, payload: dict) -> Path:
    """Write one per-cell result JSON (mkdir -p on the parent)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return out_path


def base_cell_payload(
    *,
    arm: str,
    cell: Optional[str],
    signal: str,
    position: str,
    model: str,
    direction_meta: Optional[dict],
    eval_pool: str,
    seed: int,
    n_items: int,
    config_extra: Optional[dict] = None,
) -> dict:
    """Common header block for both runners' cell JSONs."""
    header = {
        "amendment": "AA",
        "arm": arm,
        "cell": cell,
        "signal": signal,
        "position": position,
        "model": model,
        "eval_pool": eval_pool,
        "seed": seed,
        "n_items": n_items,
        "coherence_floor": COHERENCE_FLOOR,
        "revision_instruction": REVISION_INSTRUCTION,
        "created_utc": utc_now_iso(),
    }
    if direction_meta is not None:
        header["direction"] = {
            "signal": direction_meta.get("signal"),
            "best_layer": direction_meta.get("best_layer"),
            "auroc_at_best_layer": direction_meta.get("auroc_at_best_layer"),
            "provenance": direction_meta.get("provenance"),
        }
    if config_extra:
        header["config"] = config_extra
        header["config_sha"] = _config_sha(config_extra)
    return header
