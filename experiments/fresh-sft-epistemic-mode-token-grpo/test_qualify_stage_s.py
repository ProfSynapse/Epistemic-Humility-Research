from __future__ import annotations

import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import yaml
import pytest

MODULE_PATH = Path(__file__).with_name("qualify_stage_s.py")
SPEC = importlib.util.spec_from_file_location("qualify_stage_s", MODULE_PATH)
assert SPEC and SPEC.loader
qualify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualify)


class FakeTokenizer:
    token_ids = {"<ONE>": 101, "<TWO>": 102, "<THREE>": 103}
    all_special_tokens = list(token_ids)
    all_special_ids = list(token_ids.values())

    def convert_tokens_to_ids(self, token):
        return self.token_ids[token]

    def encode(self, token, add_special_tokens=False):
        assert add_special_tokens is False
        return [self.token_ids[token]]

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == {
            "tokenize": False,
            "add_generation_prompt": True,
            "enable_thinking": False,
        }
        return "\n".join(f"{row['role']}:{row['content']}" for row in messages) + "\nassistant:"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    experiment = repo / "experiments" / "fresh-sft-epistemic-mode-token-grpo"
    dataset = experiment / "analysis" / "dataset"
    rows = []
    for mode in qualify.MODE_NAMES:
        for index in range(2):
            rows.append(
                {
                    "conversations": [
                        {"role": "system", "content": "help"},
                        {"role": "user", "content": f"question {mode} {index}"},
                        {"role": "assistant", "content": "target"},
                    ],
                    "metadata": {
                        "row_key": f"row-{mode}-{index}",
                        "mode_label": mode,
                        "split": "dev",
                        "gold_aliases": ["alpha"],
                    },
                }
            )
    dev = dataset / "dev.jsonl"
    _write_jsonl(dev, rows)
    scorer = repo / "experiments" / "common" / "knowledge_probe" / "scoring.py"
    scorer.parent.mkdir(parents=True)
    scorer.write_text(
        "def is_correct(text, aliases):\n"
        "    return any(alias.lower() in text.lower() for alias in aliases)\n",
        encoding="utf-8",
    )
    stage = {
        "model": {"tokenizer": {"additional_special_tokens": ["<ONE>", "<TWO>", "<THREE>"]}}
    }
    (experiment / "stage_s.yaml").write_text(yaml.safe_dump(stage), encoding="utf-8")
    lineage = {
        "configured_tokens": [
            {"token": "<ONE>", "token_id": 101},
            {"token": "<TWO>", "token_id": 102},
            {"token": "<THREE>", "token_id": 103},
        ],
        "base_model_provenance": {
            "requested_repo": "base/repo",
            "requested_revision": "a" * 40,
            "resolved_commit": "a" * 40,
        },
    }
    model = experiment / "adapter"
    model.mkdir()
    (model / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    lineage_path = model / "special_tokens_lineage.json"
    lineage_path.write_text(json.dumps(lineage), encoding="utf-8")
    tuner = tmp_path / "tuner"
    tuner.mkdir()
    fake = '''
import argparse, hashlib, json, os, time
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument("command"); p.add_argument("--prompts"); p.add_argument("--model"); p.add_argument("--out-dir"); p.add_argument("--resume",action="store_true"); a,_=p.parse_known_args()
out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True); target=out/"completions.jsonl"; checkpoint=out/"checkpoint.json"
done=set()
if target.exists():
    if not a.resume: raise SystemExit(3)
    done={json.loads(x)["id"] for x in target.read_text().splitlines() if x.strip()}
ids={"ANSWER":101,"QUALIFY":102,"ABSTAIN":103}; tokens={"ANSWER":"<ONE>","QUALIFY":"<TWO>","ABSTAIN":"<THREE>"}
with target.open("a") as h:
  for line in Path(a.prompts).read_text().splitlines():
    row=json.loads(line); rid=row["id"]
    if rid in done: continue
    mode=next(x for x in ids if x in rid)
    forced="::forced::" in rid
    if "generation_base" in str(out): text="alpha"; toks=[9]
    elif forced:
      fm=rid.rsplit("::",1)[1]
      answer={"ANSWER":"alpha","QUALIFY":"My best answer is alpha, but I am not certain.","ABSTAIN":"I don't know reliably."}[fm]
      text=json.dumps({"answer":answer,"answer_confidence":{"ANSWER":.8,"QUALIFY":.5,"ABSTAIN":.1}[fm]}); toks=[8]
    else: text=json.dumps({"answer":"alpha","answer_confidence":{"ANSWER":.8,"QUALIFY":.5,"ABSTAIN":.1}[mode]}); toks=[ids[mode],8]
    h.write(json.dumps({"id":rid,"completion_text":text,"completion_token_ids":toks,"finish_reason":"length"})+"\\n"); h.flush(); os.fsync(h.fileno()); done.add(rid)
    checkpoint.write_text(json.dumps({"version":1,"config_hash":"fixture","done_ids":sorted(done),"count":len(done)})+"\\n")
    time.sleep(.08)
'''
    (tuner / "tuner.py").write_text(fake, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tuner, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tuner, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tuner, check=True)
    subprocess.run(["git", "add", "tuner.py"], cwd=tuner, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=tuner, check=True)
    tuner_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tuner, check=True, capture_output=True, text=True
    ).stdout.strip()
    config = {
        "schema_version": 1,
        "experiment": experiment.name,
        "stage_s_config": "stage_s.yaml",
        "dev": {
            "path": "analysis/dataset/dev.jsonl",
            "sha256": qualify.sha256_file(dev),
            "rows": 6,
            "rows_by_mode": {mode: 2 for mode in qualify.MODE_NAMES},
        },
        "heldout": {
            "access": "hash_only_outside_qualification_runner",
            "path_forbidden_in_runner": "analysis/dataset/heldout.jsonl",
        },
        "canonical_scorer": {
            "path": str(scorer.relative_to(repo)),
            "sha256": qualify.sha256_file(scorer),
        },
        "models": {"base": {"repo": "base/repo", "revision": "a" * 40}},
        "tuner": {"expected_commit": tuner_commit, "require_clean_worktree": True},
        "generation": {
            "public_tuner_verb": "batch-generate",
            "engine": "hf-batched",
            "batch_size": 1,
            "max_new_tokens": 32,
            "min_new_tokens": 1,
            "do_sample": False,
            "seed": 7,
            "enable_thinking": False,
        },
        "posture_contract": {
            "ANSWER": {
                "require_nonempty_substantive_answer": True,
                "forbidden_phrases_casefold": ["i don't know", "not certain", "no idea"],
            },
            "QUALIFY": {
                "exact_shape": {
                    "prefix": "My best answer is ",
                    "suffix": ", but I am not certain.",
                    "require_nonempty_substantive_candidate": True,
                }
            },
            "ABSTAIN": {"exact_answers": ["I don't know reliably."]},
        },
        "gates": {
            "configured_first_token_rate_min": 0.95,
            "valid_json_after_mode_token_rate_min": 0.95,
            "exact_required_fields_rate_min": 0.95,
            "confidence_parse_and_range_rate_min": 0.95,
            "confidence_population_sd_min": 0.05,
            "deterministic_forced_token_posture_compliance_min": 0.95,
            "visible_special_token_stripping_rate_min": 1.0,
            "per_mode_recall": {"lower_bound_gt": 0.3},
            "max_single_mode_share": {"numerator_max": 4, "denominator": 6},
            "answer_quality_noninferiority": {
                "metric": "paired_correctness_difference_stage_s_minus_base",
                "ci": "two_sided_95pct_paired_percentile_bootstrap",
                "seed": 7,
                "resamples": 100,
                "lower_bound_gt": -0.10,
            },
        },
        "output": {
            "root": "analysis/qualification",
            "prompt_files": {
                "base_native": "prompts_base.jsonl",
                "stage_s_native": "prompts_native.jsonl",
                "stage_s_forced": "prompts_forced.jsonl",
            },
            "generation_directories": {
                "base_native": "generation_base",
                "stage_s_native": "generation_native",
                "stage_s_forced": "generation_forced",
            },
            "scored_rows": "scored.jsonl",
            "run_manifest": "manifest.json",
            "summary": "summary.json",
        },
    }
    config_path = experiment / "qualification.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return {"config": config_path, "lineage": lineage_path, "model": model, "tuner": tuner, "experiment": experiment}


def test_interruption_resume_and_complete_exhaust(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    qualify.prepare_run(fx["config"], "kill-resume", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    argv = [
        sys.executable,
        str(MODULE_PATH),
        "generate",
        "--config", str(fx["config"]),
        "--run-id", "kill-resume",
        "--stage-s-model", str(fx["model"]),
        "--tuner-worktree", str(fx["tuner"]),
    ]
    process = subprocess.Popen(argv, start_new_session=True)
    partial = fx["experiment"] / "analysis/qualification/kill-resume/generation_base/completions.jsonl"
    deadline = time.time() + 5
    while time.time() < deadline and (not partial.exists() or not partial.read_text().strip()):
        time.sleep(0.02)
    assert partial.exists() and partial.read_text().strip()
    os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=5)
    resumed = subprocess.run(argv + ["--resume"], check=False, capture_output=True, text=True)
    assert resumed.returncode == 0, resumed.stderr
    summary = qualify.score(fx["config"], "kill-resume", resume=False)
    assert summary["heldout_rows_accessed"] == 0
    assert summary["all_pass"] is True
    assert summary["dev_rows"] == 6
    scored = fx["experiment"] / "analysis/qualification/kill-resume/scored.jsonl"
    assert len(scored.read_text().splitlines()) == 6
    assert not (fx["experiment"] / "analysis/dataset/heldout.jsonl").exists()


def test_fixed_token_ids_are_rejected_as_a_source_of_truth(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    stage = yaml.safe_load((fx["experiment"] / "stage_s.yaml").read_text())
    stage["model"]["tokenizer"]["additional_special_tokens"] = ["<RENAMED>", "<TWO>", "<THREE>"]
    (fx["experiment"] / "stage_s.yaml").write_text(yaml.safe_dump(stage), encoding="utf-8")
    try:
        qualify.prepare_run(fx["config"], "bad", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    except qualify.QualificationError as exc:
        assert "strings/order" in str(exc)
    else:
        raise AssertionError("lineage/config token mismatch was accepted")


def test_forced_posture_is_structural_semantics_not_gold_correctness() -> None:
    parsed = {"json_parse": True, "exact_fields": True, "confidence_valid": True}
    payload = {"answer": "a plausible but incorrect answer", "answer_confidence": 0.7}
    contract = {
        "ANSWER": {
            "require_nonempty_substantive_answer": True,
            "forbidden_phrases_casefold": ["i don't know", "not certain", "no idea"],
        }
    }
    passed, checks = qualify._posture_ok("ANSWER", payload, parsed, contract)
    assert passed is True
    assert "correct" not in checks
    for broken in (
        {"json_parse": False, "exact_fields": True, "confidence_valid": True},
        {"json_parse": True, "exact_fields": False, "confidence_valid": True},
        {"json_parse": True, "exact_fields": True, "confidence_valid": False},
    ):
        assert qualify._posture_ok("ANSWER", payload, broken, contract)[0] is False
    assert qualify._posture_ok(
        "ANSWER", {"answer": 1, "answer_confidence": 0.7}, parsed, contract
    )[0] is False
    assert qualify._posture_ok(
        "ANSWER", {"answer": "Paris", "answer_confidence": 0.7}, parsed, contract
    )[0] is True
    for weak in ("", "...", "I don't know", "This is not certain", "I have no idea."):
        assert qualify._posture_ok(
            "ANSWER", {"answer": weak, "answer_confidence": 0.7}, parsed, contract
        )[0] is False
    qualify_contract = {
        "QUALIFY": {
            "exact_shape": {
                "prefix": "My best answer is ",
                "suffix": ", but I am not certain.",
                "require_nonempty_substantive_candidate": True,
            }
        }
    }
    assert qualify._posture_ok(
        "QUALIFY",
        {"answer": "My best answer is Paris, but I am not certain.", "answer_confidence": 0.4},
        parsed,
        qualify_contract,
    )[0] is True
    for malformed in (
        "Paris, but I am not certain.",
        "My best answer is , but I am not certain.",
        "My best answer is Paris but I am not certain.",
    ):
        assert qualify._posture_ok(
            "QUALIFY", {"answer": malformed, "answer_confidence": 0.4}, parsed,
            qualify_contract,
        )[0] is False


def test_configured_tokens_must_be_registered_specials_with_lineage_ids(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)

    class MissingRegistrationTokenizer(FakeTokenizer):
        all_special_tokens = ["<ONE>", "<TWO>"]
        all_special_ids = [101, 102]

    with pytest.raises(qualify.QualificationError, match="not registered special"):
        qualify.prepare_run(
            fx["config"], "unregistered", fx["model"], fx["lineage"],
            tokenizer=MissingRegistrationTokenizer()
        )


def test_resume_rejects_manifest_drift_before_mutating_prompts(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    qualify.prepare_run(fx["config"], "resume-guard", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    run = fx["experiment"] / "analysis/qualification/resume-guard"
    before = {path.name: path.read_bytes() for path in run.glob("prompts*.jsonl")}
    config = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    config["generation"]["seed"] = 999
    fx["config"].write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(qualify.QualificationError, match="resume manifest differs"):
        qualify.prepare_run(
            fx["config"], "resume-guard", fx["model"], fx["lineage"],
            tokenizer=FakeTokenizer(), resume=True
        )
    assert {path.name: path.read_bytes() for path in run.glob("prompts*.jsonl")} == before


def test_generation_rejects_artifact_prompt_and_tuner_drift(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    qualify.prepare_run(fx["config"], "artifact-drift", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    (fx["model"] / "drift.bin").write_bytes(b"drift")
    with pytest.raises(qualify.QualificationError, match="artifact tree changed"):
        qualify.generate(fx["config"], "artifact-drift", fx["model"], fx["tuner"], resume=False)

    fx = _fixture(tmp_path / "prompt")
    qualify.prepare_run(fx["config"], "prompt-drift", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    prompt = fx["experiment"] / "analysis/qualification/prompt-drift/prompts_base.jsonl"
    prompt.write_bytes(prompt.read_bytes() + b"\n")
    with pytest.raises(qualify.QualificationError, match="prompt hash mismatch"):
        qualify.generate(fx["config"], "prompt-drift", fx["model"], fx["tuner"], resume=False)

    fx = _fixture(tmp_path / "tuner")
    qualify.prepare_run(fx["config"], "tuner-drift", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    (fx["tuner"] / "untracked.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(qualify.QualificationError, match="exactly clean"):
        qualify.generate(fx["config"], "tuner-drift", fx["model"], fx["tuner"], resume=False)


def test_visible_token_leak_and_generation_hash_are_fail_closed(tmp_path: Path) -> None:
    visible, stripped = qualify._forced_visible_text(
        '{"answer":"leak <ONE>","answer_confidence":0.5}',
        {"ANSWER": "<ONE>", "QUALIFY": "<TWO>", "ABSTAIN": "<THREE>"},
    )
    assert "<ONE>" in visible and stripped is False
    fx = _fixture(tmp_path)
    qualify.prepare_run(fx["config"], "hash-guard", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    qualify.generate(fx["config"], "hash-guard", fx["model"], fx["tuner"], resume=False)
    completion = fx["experiment"] / "analysis/qualification/hash-guard/generation_native/completions.jsonl"
    completion.write_bytes(completion.read_bytes() + b"\n")
    with pytest.raises(qualify.QualificationError, match="generation output hash mismatch"):
        qualify.score(fx["config"], "hash-guard", resume=False)


def test_scoring_resume_recomputes_every_existing_row_before_skip(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    qualify.prepare_run(fx["config"], "score-resume", fx["model"], fx["lineage"], tokenizer=FakeTokenizer())
    qualify.generate(fx["config"], "score-resume", fx["model"], fx["tuner"], resume=False)
    summary = qualify.score(fx["config"], "score-resume", resume=False)
    assert summary["all_pass"] is True
    scored = fx["experiment"] / "analysis/qualification/score-resume/scored.jsonl"
    original_rows = [json.loads(line) for line in scored.read_text().splitlines()]
    scored.write_bytes(qualify._jsonl_bytes(original_rows[:2]))
    resumed = qualify.score(fx["config"], "score-resume", resume=True)
    assert resumed["all_pass"] is True
    assert len(scored.read_text().splitlines()) == 6

    rows = [json.loads(line) for line in scored.read_text().splitlines()]
    rows[0]["stage_s_native"]["correct"] = not rows[0]["stage_s_native"]["correct"]
    scored.write_bytes(qualify._jsonl_bytes(rows))
    with pytest.raises(qualify.QualificationError, match="hash-bound recomputation"):
        qualify.score(fx["config"], "score-resume", resume=True)

    scored.write_bytes(qualify._jsonl_bytes(original_rows))
    scored.write_text(scored.read_text().replace(":", ": ", 1), encoding="utf-8")
    with pytest.raises(qualify.QualificationError, match="canonical byte-for-byte"):
        qualify.score(fx["config"], "score-resume", resume=True)
