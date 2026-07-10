"""Render function for the AO propensity-regulated-caution steer cells (both
Stage-1 candidate cells and the Stage-2 cell), on the AI-TRUE checkpoint /
prop_z pool surface.

Contract (synaptic-tuner docs/MECH_INTERP_CELLS.md, "Plug-in points"):

    render(row: dict) -> str

`MechInterp/cli.py::run_steer` calls this with ONE row dict and nothing else
(no tokenizer is injected -- see `_run_one_pass`'s `prompt = render_fn(row)`),
so this module loads its own tokenizer, lazily and once, cached at module
scope.

This is NOT a new prompt convention: it faithfully reproduces the byte-pinned
render this exact AI-TRUE / A0 surface already uses at
`archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py` (see its
`run_extract`/`run_generate`, both of which call
``render_probe_prompt(tokenizer, baseline_system, item["question"],
enable_thinking=False)``) and
`archive/experiment/phase1/probe/amendments/amendment_an_steer_generate.py` (the sibling AN
steer script for the SAME checkpoint and SAME caution-direction lineage).
Both of those import ``render_probe_prompt`` from
``archive/experiment/phase1/probe/backends.py`` and ``load_baseline_system_prompt``
through the ``archive/experiment/phase1/probe/amendment_ah_stage0_extract.py``
compatibility wrapper for the archived AH implementation; this module imports
the exact same two functions rather than re-deriving the prompt string, so a
future change to either source stays in sync automatically.

``load_baseline_system_prompt`` reads the system prompt from
``experiments/doubt-regulated-caution/phase3_ac_doubt_coupled_intervention.yaml``'s
``prompt.system`` key -- the "Answer the user's question... Return only a
JSON object with exactly two keys: 'answer' and 'response_confidence'..."
text -- the same baseline system prompt every AL/AN/AI script in this
research line uses (see that config's own header comment for its Amendment
AC provenance; it is reused unprimed here, matching the AL/AN/AI convention
of "baseline unprimed system prompt").

Tokenizer resolution: the checkpoint this experiment steers
(``professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora`` per
``experiment.yaml``'s ``checkpoint`` block) is the AI-TRUE GRPO LoRA adapter
applied on top of the clean-SFT merged 16-bit base -- the SAME base
AN's ``amendment_an_steer_generate.py`` hardcodes as ``BASE_MODEL`` (see that
script's docstring: "Byte-identical load path, prompt render, and decode to
the AL A0 baseline"). The base model and the AI-TRUE adapter share one
tokenizer (the adapter does not retrain tokenization), so this module loads
the tokenizer from that same local canonical path by default. Override with
the ``AO_RENDER_TOKENIZER_PATH`` environment variable if a run environment
does not have that exact local path staged (e.g. a fresh cloud box) --- point
it at any local path or HF repo id carrying the identical Qwen3-4B tokenizer
and chat template.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "archive" / "archive" / "archive" / "archive" / "experiment" / "phase1" / "probe" / "backends.py").exists()
            and (candidate / "experiments").is_dir()
        ):
            return candidate
    raise RuntimeError(f"Could not locate repository root from {here}")


CANONICAL = _repo_root()
PROBE_DIR = CANONICAL / "archive" / "archive" / "archive" / "archive" / "experiment" / "phase1" / "probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from backends import render_probe_prompt  # noqa: E402  (exact prompt render this surface uses)
from amendment_ah_stage0_extract import load_baseline_system_prompt  # noqa: E402

DEFAULT_TOKENIZER_PATH = str(
    CANONICAL / "scratch/schema_response_confidence/runs/"
    "sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit"
)

_tokenizer = None
_baseline_system = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer

        path = os.environ.get("AO_RENDER_TOKENIZER_PATH", DEFAULT_TOKENIZER_PATH)
        _tokenizer = AutoTokenizer.from_pretrained(path)
    return _tokenizer


def _get_baseline_system() -> str:
    global _baseline_system
    if _baseline_system is None:
        _baseline_system = load_baseline_system_prompt()
    return _baseline_system


def render(row: dict) -> str:
    """Map one prop_z-pool row to the AI-TRUE / A0 baseline prompt string.

    `row["question"]` is the raw question text (prop_z_gain_map_rows.jsonl
    schema, see build_rows_pool.py); enable_thinking=False matches every
    generation script in this research line for this checkpoint.
    """
    tokenizer = _get_tokenizer()
    baseline_system = _get_baseline_system()
    question = str(row.get("question", "")).strip()
    rendered, _mode = render_probe_prompt(
        tokenizer, baseline_system, question, enable_thinking=False
    )
    return rendered
