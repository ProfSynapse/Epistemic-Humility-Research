"""Equivalence + wiring tests for the tuner-batched engine on the extractor.

Covers the throughput-plan §4 locked training-regimen addition to
amendment_x_cross_model_extract.py: the `--engine tuner-batched` path that
replaces ONLY the GPU inner loop with the synaptic-tuner batch-generate /
batch-capture public CLI verbs, plus `--scratch-dir` and the manifest
engine/batch_size fields.

Two tiers:
  * Pure-function tests (always run, CPU-only, no model): the conversion +
    position-building seam the batched path relies on — parse/grade parity with
    the sequential inline logic, and the pre/post safetensors key split.
  * A real mini end-to-end EQUIVALENCE test (sequential vs tuner-batched on
    hf-internal-testing/tiny-random-gpt2) gated on CUDA, because the sequential
    load path is `device_map="cuda"` (unchanged by this work — we do not weaken
    the default path to make a test run on CPU). It asserts identical rows.jsonl
    core fields, identical safetensors keys/shapes, near-identical tensor values,
    and the manifest engine/batch_size delta.

Run with an explicit file path (the rtk pytest directory-glob false negative):
  pytest experiments/common/knowledge_probe/tests/test_amendment_x_tuner_batched.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import amendment_x_cross_model_extract as m  # noqa: E402

TINY_MODEL = "hf-internal-testing/tiny-random-gpt2"
REPO_ROOT = PROBE_DIR.parents[2]
if REPO_ROOT.name == "experiments":
    REPO_ROOT = REPO_ROOT.parent


def _resolve_tuner_dir():
    """Locate a synaptic-tuner checkout that actually has tuner.py.

    In a git worktree the submodule may be uninitialized (empty); fall back to
    the primary checkout's submodule. Operators pass --tuner-dir for the same
    reason on the cloud lane.
    """
    local = REPO_ROOT / "synaptic-tuner"
    if (local / "tuner.py").exists():
        return local
    # .worktrees/<name> -> the main checkout is two parents up from REPO_ROOT.
    if REPO_ROOT.parent.name == ".worktrees":
        main = REPO_ROOT.parents[1] / "synaptic-tuner"
        if (main / "tuner.py").exists():
            return main
    return local


TUNER_DIR = _resolve_tuner_dir()

_has_torch = False
try:  # torch is optional for the pure-function tier
    import torch  # noqa: F401
    _has_torch = True
except Exception:  # pragma: no cover - torch always present in the run env
    pass

_cuda = _has_torch and torch.cuda.is_available()
_tuner_present = (TUNER_DIR / "tuner.py").exists()
_tuner_text = (
    (TUNER_DIR / "tuner.py").read_text(encoding="utf-8", errors="ignore")
    if _tuner_present else ""
)
_tuner_batch_verbs_present = "batch-generate" in _tuner_text and "batch-capture" in _tuner_text


# ---------------------------------------------------------------------------
# Pure-function tier: the render/parse/grade helpers are the single source of
# truth shared by BOTH engines. A stub tokenizer (token id -> literal string)
# exercises them without a model. This is the "smallest honest seam" the plan
# calls for when a full run is unavailable.
# ---------------------------------------------------------------------------
class StubTokenizer:
    def __init__(self, vocab, specials=None):
        self.vocab = vocab
        self.specials = specials or set()

    def decode(self, ids, skip_special_tokens=False):
        out = []
        for i in ids:
            if skip_special_tokens and int(i) in self.specials:
                continue
            out.append(self.vocab[int(i)])
        return "".join(out)


def test_parse_completion_chat_mode_matches_inline_logic():
    # chat-mode: decode the whole tail, trim trailing specials.
    vocab = {0: "sys", 1: "Q", 2: " Paris", 3: "<eos>"}
    tok = StubTokenizer(vocab, specials={3})
    full = [0, 1, 2, 3]  # prompt = [0,1]; gen = " Paris" then eos
    answer, end = m.parse_completion(tok, full, prompt_len=2,
                                     special_ids={3}, base_mode=False)
    assert answer == "Paris"
    assert end == 2  # last content token, eos trimmed


def test_parse_completion_base_mode_first_line():
    vocab = {0: "Q:", 1: " Paris", 2: "\n", 3: "Q:", 4: " next"}
    tok = StubTokenizer(vocab)
    full = [0, 1, 2, 3, 4]  # prompt = [0]; gen babbles past a newline
    answer, end = m.parse_completion(tok, full, prompt_len=1,
                                     special_ids=set(), base_mode=True)
    assert answer == "Paris"
    assert end == 1  # stops before the newline token


def test_grade_row_answerable_correct_wrong():
    it = {"source": "answerable", "aliases_norm": ["paris"]}
    # is_correct normalizes; "Paris" should match alias "paris".
    answered, refused, correct, outcome = m.grade_row(it, "Paris", content_end=5)
    assert answered and not refused and correct and outcome == "correct"
    answered, refused, correct, outcome = m.grade_row(it, "Berlin", content_end=5)
    assert answered and correct is False and outcome == "wrong"


def test_grade_row_selfaware_sources():
    known = {"source": "selfaware_known"}
    unknown = {"source": "selfaware_unknown"}
    assert m.grade_row(known, "something", 3)[3] == "known_answered"
    assert m.grade_row(unknown, "something", 3)[3] == "hallucination"


def test_grade_row_unanswered_when_no_content_end():
    it = {"source": "answerable", "aliases_norm": ["x"]}
    answered, refused, correct, outcome = m.grade_row(it, "", content_end=None)
    assert answered is False and correct is None and outcome is None


# ---------------------------------------------------------------------------
# Conversion seam: the tuner emits per-row safetensors keyed "<pos>__L<layer>";
# the extractor splits that into two files keyed "L0..Ln". Verify the split logic
# in isolation (no tuner, no model) by round-tripping a synthetic capture file.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_torch, reason="torch required")
def test_pre_post_key_split_from_tuner_layout(tmp_path):
    from safetensors.torch import save_file, load_file

    n_layers = 3  # -> hidden-state indices 0..3 (n_layers+1)
    src = {}
    for li in range(n_layers + 1):
        src[f"pre__L{li}"] = torch.arange(4, dtype=torch.float32) + li
        src[f"post__L{li}"] = torch.arange(4, dtype=torch.float32) + 100 + li
    cap_file = tmp_path / "row.safetensors"
    save_file(src, str(cap_file))

    loaded = load_file(str(cap_file))
    pre = {f"L{li}": loaded[f"pre__L{li}"].float().cpu().contiguous()
           for li in range(n_layers + 1)}
    post = {f"L{li}": loaded[f"post__L{li}"].float().cpu().contiguous()
            for li in range(n_layers + 1)}
    assert sorted(pre) == [f"L{i}" for i in range(n_layers + 1)]
    assert sorted(post) == [f"L{i}" for i in range(n_layers + 1)]
    assert torch.equal(pre["L2"], torch.tensor([2., 3., 4., 5.]))
    assert torch.equal(post["L0"], torch.tensor([100., 101., 102., 103.]))


# ---------------------------------------------------------------------------
# End-to-end equivalence: sequential vs tuner-batched on the tiny model.
# ---------------------------------------------------------------------------
def _stub_pool():
    """A tiny mixed pool with all three sources; no dataset files touched.

    Fields mirror what build_mixed_pool yields: row_key/dataset/question/source
    (+ aliases_norm for answerable). Questions are short so the tiny model emits
    a few tokens under base-mode.
    """
    return [
        {"row_key": "answerable::1", "dataset": "popqa",
         "question": "What is the capital of France?", "source": "answerable",
         "aliases_norm": ["paris"]},
        {"row_key": "answerable::2", "dataset": "triviaqa",
         "question": "What is the chemical symbol for gold?", "source": "answerable",
         "aliases_norm": ["au"]},
        {"row_key": "selfaware_known::1", "dataset": "selfaware",
         "question": "How many days are in a week?", "source": "selfaware_known"},
        {"row_key": "selfaware_unknown::1", "dataset": "selfaware",
         "question": "What did I eat for breakfast?", "source": "selfaware_unknown"},
    ]


def _run_extractor(tmp_path, engine, monkeypatch, scratch_dir=None):
    out_dir = tmp_path / f"out_{engine}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Stub the pool so no dataset/gate files are needed; base-mode so the tiny
    # (chat-template-less) gpt2 renders via the fixed k-shot completion block.
    monkeypatch.setattr(m, "build_mixed_pool",
                        lambda *a, **k: _stub_pool())
    argv = [
        "--out-dir", str(out_dir),
        "--base-model", TINY_MODEL,
        "--gate-rows", str(tmp_path / "unused_gate.jsonl"),
        "--datasets-root", str(tmp_path),
        "--base-mode",
        "--max-new-tokens", "6",
        "--max-attempts", "10",
        "--wrong-floor", "0", "--hallucination-floor", "0",
        "--seed", "0",
        "--engine", engine,
    ]
    if engine == "tuner-batched":
        argv += ["--batch-size", "2", "--tuner-dir", str(TUNER_DIR)]
    if scratch_dir is not None:
        argv += ["--scratch-dir", str(scratch_dir)]
    rc = m.run(m.parse_args(argv))
    assert rc == 0
    return out_dir


def _load_rows(out_dir):
    return [json.loads(l) for l in
            (out_dir / "rows.jsonl").read_text().splitlines() if l.strip()]


@pytest.mark.skipif(
    not (_cuda and _tuner_batch_verbs_present),
    reason="needs CUDA (sequential load is device_map=cuda) + tuner batch-generate/batch-capture verbs")
def test_sequential_vs_tuner_batched_equivalence(tmp_path, monkeypatch):
    from safetensors.torch import load_file

    seq_dir = _run_extractor(tmp_path, "sequential", monkeypatch)
    bat_dir = _run_extractor(tmp_path, "tuner-batched", monkeypatch)

    seq_rows = {r["row_key"]: r for r in _load_rows(seq_dir)}
    bat_rows = {r["row_key"]: r for r in _load_rows(bat_dir)}
    assert set(seq_rows) == set(bat_rows)

    for key, sr in seq_rows.items():
        br = bat_rows[key]
        for field in ("dataset", "question", "source", "answered",
                      "outcome", "correct", "answer_text"):
            assert sr[field] == br[field], (
                f"row {key} field {field}: seq={sr[field]!r} bat={br[field]!r}")

    # Safetensors: identical files, keys, shapes; near-identical values.
    for key, sr in seq_rows.items():
        if not sr["answered"]:
            continue
        safe = key.replace("::", "__").replace("|", "_")
        for pos in ("pre", "post"):
            sf = load_file(str(seq_dir / f"{safe}__{pos}.safetensors"))
            bf = load_file(str(bat_dir / f"{safe}__{pos}.safetensors"))
            assert set(sf) == set(bf)
            for lk in sf:
                assert sf[lk].shape == bf[lk].shape
                assert sf[lk].dtype == bf[lk].dtype == torch.float32
                # Both engines compute in bf16 on GPU; the batched forward's
                # right-padded reduction order can flip the LAST bf16 ULP vs the
                # single-sequence forward (observed max abs delta ~0.016 = one
                # bf16 ULP at the final-layer magnitude ~2-3, only at the top
                # layer). This is exactly the last-ulp allowance plan §5 names;
                # the answer_text / outcome fields (asserted above) match exactly.
                assert torch.allclose(sf[lk], bf[lk], atol=2e-2, rtol=1e-2), (
                    f"{key} {pos} {lk} values differ beyond bf16 last-ulp "
                    f"tolerance (max abs "
                    f"{float((sf[lk] - bf[lk]).abs().max()):.4g})")


@pytest.mark.skipif(
    not (_cuda and _tuner_batch_verbs_present),
    reason="needs CUDA + tuner batch-generate/batch-capture verbs")
def test_manifest_engine_batch_size_fields(tmp_path, monkeypatch):
    seq_dir = _run_extractor(tmp_path, "sequential", monkeypatch)
    bat_dir = _run_extractor(tmp_path, "tuner-batched", monkeypatch)

    seq_man = json.loads((seq_dir / "manifest.json").read_text())
    bat_man = json.loads((bat_dir / "manifest.json").read_text())

    # Sequential manifest gains NO engine/batch_size keys (byte-shape unchanged).
    assert "engine" not in seq_man
    assert "batch_size" not in seq_man
    # tuner-batched manifest adds them.
    assert bat_man["engine"] == "tuner-batched"
    assert bat_man["batch_size"] == 2


@pytest.mark.skipif(
    not (_cuda and _tuner_batch_verbs_present),
    reason="needs CUDA + tuner batch-generate/batch-capture verbs")
def test_scratch_dir_tensors_land_in_out_dir(tmp_path, monkeypatch):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    out_dir = _run_extractor(tmp_path, "tuner-batched", monkeypatch,
                             scratch_dir=scratch)

    # Final tensors are in out_dir; scratch holds no leftover tensor subdir.
    tensors = list(out_dir.glob("*.safetensors"))
    assert tensors, "expected safetensors moved into out_dir"
    leftover = list(scratch.glob("**/*.safetensors"))
    assert not leftover, f"scratch should be emptied, found {leftover}"
