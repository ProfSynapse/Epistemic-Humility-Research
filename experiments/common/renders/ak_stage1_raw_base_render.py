"""Render function for the AK Stage-1 raw-base surface (checkpoint_tag
"raw-base", unsloth/Qwen3-4B-bnb-4bit, no adapter).

The AK Stage-1 raw-base capture (experiment/phase1/probe/
amendment_ak_gentime_positions_extract.py) deliberately excludes question text
from its per-row output ("NO question text -> NO-LICENSE safe", see that
script's docstring): the committed and gitignored `rows.jsonl` this project's
`dark-actuator-screen` reads (`analysis/rows_pool.jsonl`, staged from
`$HOME/ak_census_data/ak-stage1-raw-base-r1/data/rows.jsonl`) carries no
`question`/`prompt` field at all. A steer cell needs a live prompt string per
row (it calls `model.generate()`), so this render function reconstructs the
EXACT prompt used at capture time from the row's `row_key` alone, by joining
against the same upstream question-text pools the AH Stage-0 pipeline produced
(source-tagged `kuq_ku_unknown`, `kuq_ku_unknown_x`, `selfaware_unanswerable`
-- no FalseQA rows in this surface) and re-applying the capture's own system
prompt and chat template.

Verified byte/token-identical to the original capture: retokenizing the
reconstructed prompt for every one of the 1,338 raw-base pool rows reproduces
that row's recorded `prompt_len` exactly (0 mismatches, 0 missing questions;
see dark-actuator-screen NOTEBOOK.md build entry). This is the correctness
check to rerun if either question-pool source or the manifest's system prompt
ever changes.

Contract (see synaptic-tuner MechInterp docs, "Plug-in points"):
    render(row: dict) -> str

Sources (both OUTSIDE this experiment's own tree; canonical-checkout-only,
gitignored analysis data on the ext4 checkout -- never committed, matching the
licensing posture of the AK capture itself, which excluded this same text for
the same reason):
  - question text: two AH Stage-0 pool files, keyed by row_key --
      experiment/phase1/probe/analysis/ah_stage0/candidates.jsonl
        (row_key prefix "ah::", the AH "mined" pass)
      experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl
        (row_key prefix "ahx::", the AH "expansion" pass)
  - system prompt: the AK Stage-1 raw-base capture manifest
      $HOME/ak_census_data/ak-stage1-raw-base-r1/data/manifest.json
      (`baseline_system_prompt` field; also names the exact model tag and
      `enable_thinking` used at capture time).

Env overrides (matching the DARK_ACTUATOR_ROWS_POOL pattern in
dark_actuator_grader.py -- set these if the canonical checkout moves, or to
point at a different checkpoint's capture manifest):
  AK_STAGE1_QUESTION_POOLS   colon-separated question-pool JSONL paths
                             (default: the two ah_stage0 files above)
  AK_STAGE1_MANIFEST_PATH    path to the capture manifest.json
                             (default: $HOME/ak_census_data/
                             ak-stage1-raw-base-r1/data/manifest.json)
  AK_STAGE1_MODEL_NAME       tokenizer/model repo id for apply_chat_template
                             (default: unsloth/Qwen3-4B-bnb-4bit, matching the
                             manifest's base_model)

CPU-only to import and to call: this module loads a tokenizer (no model
weights), which downloads/caches only vocab+template files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]

# The AH Stage-0 question pools are canonical-checkout-only gitignored
# analysis data (never staged into any experiment tree, per this module's own
# docstring). They do not necessarily exist under REPO_ROOT if this module is
# imported from a worktree checkout (e.g. an `ehr-worktrees/<slug>` clone) --
# only the canonical checkout ever ran the AH Stage-0 build scripts. Default
# to the canonical checkout's absolute path, matching the same hardcoded
# convention `amendment_ah_stage0_candidates.py` already uses for this exact
# data (its `CANONICAL` constant); override with AK_STAGE1_QUESTION_POOLS if
# running from, or with a copy staged into, a different checkout.
_CANONICAL_CHECKOUT = Path("/home/profsynapse/code/Epistemic-Humility-Research")
_DEFAULT_QUESTION_POOLS = [
    _CANONICAL_CHECKOUT / "experiment" / "phase1" / "probe" / "analysis"
    / "ah_stage0" / "candidates.jsonl",
    _CANONICAL_CHECKOUT / "experiment" / "phase1" / "probe" / "analysis"
    / "ah_stage0" / "expansion" / "expansion_candidates.jsonl",
]
_DEFAULT_MANIFEST_PATH = (
    Path.home() / "ak_census_data" / "ak-stage1-raw-base-r1" / "data"
    / "manifest.json"
)
_DEFAULT_MODEL_NAME = "unsloth/Qwen3-4B-bnb-4bit"

_QUESTION_MAP: Optional[dict[str, str]] = None
_SYSTEM_PROMPT: Optional[str] = None
_TOKENIZER = None


def _question_pool_paths() -> list[Path]:
    override = os.environ.get("AK_STAGE1_QUESTION_POOLS")
    if override:
        return [Path(p) for p in override.split(":") if p]
    return list(_DEFAULT_QUESTION_POOLS)


def _manifest_path() -> Path:
    override = os.environ.get("AK_STAGE1_MANIFEST_PATH")
    return Path(override) if override else _DEFAULT_MANIFEST_PATH


def _model_name() -> str:
    return os.environ.get("AK_STAGE1_MODEL_NAME", _DEFAULT_MODEL_NAME)


def _load_question_map() -> dict[str, str]:
    qmap: dict[str, str] = {}
    for pool_path in _question_pool_paths():
        if not pool_path.is_file():
            raise FileNotFoundError(
                f"ak_stage1_raw_base_render: question pool not found at "
                f"{pool_path}. This file lives in the canonical checkout's "
                "gitignored analysis/ tree, not this worktree -- copy it over "
                "or set AK_STAGE1_QUESTION_POOLS."
            )
        with pool_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                rk = row.get("row_key")
                q = row.get("question")
                if rk is None or q is None:
                    continue
                qmap[str(rk)] = str(q)
    return qmap


def _question_map() -> dict[str, str]:
    global _QUESTION_MAP
    if _QUESTION_MAP is None:
        _QUESTION_MAP = _load_question_map()
    return _QUESTION_MAP


def _system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        mpath = _manifest_path()
        if not mpath.is_file():
            raise FileNotFoundError(
                f"ak_stage1_raw_base_render: capture manifest not found at "
                f"{mpath}. Set AK_STAGE1_MANIFEST_PATH."
            )
        manifest = json.loads(mpath.read_text())
        _SYSTEM_PROMPT = manifest["baseline_system_prompt"]
    return _SYSTEM_PROMPT


def _tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained(_model_name())
    return _TOKENIZER


def render(row: dict) -> str:
    """Map one AK Stage-1 raw-base pool row to its original capture-time
    prompt string, reconstructed from row_key via the AH Stage-0 question
    pools and the capture manifest's system prompt."""
    row_key = None
    for k in ("row_key", "id", "key"):
        if k in row:
            row_key = str(row[k])
            break
    if row_key is None:
        raise KeyError("row has no row_key / id / key field")

    question = _question_map().get(row_key)
    if question is None:
        raise KeyError(
            f"ak_stage1_raw_base_render: no question text found for row_key "
            f"{row_key!r} in {[str(p) for p in _question_pool_paths()]}"
        )

    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": question},
    ]
    return _tokenizer().apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
