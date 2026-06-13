#!/usr/bin/env python3
"""End-to-end smoke test for run_eval.py on fixtures (no model, no real adapters).

Builds a self-contained temp workspace: an in-domain record set, a minimal gold,
and pre-recorded generations for two arms, then drives run_eval.run() and asserts
the full output contract (§6.7): metrics.json (provenance-stamped), bootstrap_ci.json,
comparisons/mcnemar.csv, comparisons/summary_table.csv.
"""

from __future__ import annotations

import csv
import json
import sys
import types
from pathlib import Path

import pytest
import yaml

import ood
import run_eval
import scorers


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _write_utf8_json(path: Path, payload):
    path.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _write_utf8_jsonl(path: Path, rows):
    path.write_bytes(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows).encode("utf-8")
        + b"\n"
    )


def test_end_to_end_fixture_run(tmp_path):
    # --- gold ---
    gold = tmp_path / "gold.jsonl"
    _write_jsonl(gold, [
        {"question_norm": "what is the capital of france?", "normalized_aliases": ["paris"]},
        {"question_norm": "how many moons does mars have?", "normalized_aliases": ["two"]},
    ])

    # --- in-domain records ---
    records = [
        {"id": "q1", "question": "What is the capital of France?", "label": "known"},
        {"id": "q2", "question": "How many moons does Mars have?", "label": "known"},
        {"id": "q3", "question": "What is the gold price next Tuesday?", "label": "unknown"},
    ]
    recs_path = tmp_path / "in_domain_records.json"
    recs_path.write_text(json.dumps(records), encoding="utf-8")

    results_dir = tmp_path / "results"

    # --- pre-recorded generations per arm (FixtureGenerator path) ---
    # arm "good": answers knowns correctly, refuses the unknown -> high truthful
    _write_jsonl(results_dir / "good__in_domain" / "generations.jsonl", [
        {"id": "q1", "generated_answer": "Paris."},
        {"id": "q2", "generated_answer": "Two."},
        {"id": "q3", "generated_answer": "I don't know the answer."},
    ])
    # arm "bad": over-refuses a known, hallucinates the unknown -> low truthful
    _write_jsonl(results_dir / "bad__in_domain" / "generations.jsonl", [
        {"id": "q1", "generated_answer": "I do not know the answer."},
        {"id": "q2", "generated_answer": "Two."},
        {"id": "q3", "generated_answer": "It will be 1999 dollars."},
    ])

    cfg = {
        "model_tag": "test-model",
        "gold_path": str(gold),
        "results_dir": str(results_dir),
        "confidence": {"signal": "self_consistency", "n_samples": 8},
        "bootstrap": {"n_resamples": 200, "level": 0.95, "seed": 42},
        "arms": [
            {"name": "good", "method": "sft", "model": "test-model"},
            {"name": "bad", "method": "dpo", "model": "test-model"},
        ],
        "eval_sets": {
            "in_domain": {"path": str(recs_path), "label_from_target": False},
        },
    }
    cfg_path = tmp_path / "eval.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    result = run_eval.run(cfg_path)

    # summary rows present for both arms
    assert len(result["summary_rows"]) == 2
    by_arm = {r["arm"]: r for r in result["summary_rows"]}
    assert by_arm["good"]["truthful_pct"] > by_arm["bad"]["truthful_pct"]

    # per-arm metrics.json with provenance
    good_metrics = json.loads(
        (results_dir / "good__in_domain" / "metrics.json").read_text(encoding="utf-8")
    )
    prov = good_metrics["provenance"]
    for k in ("source", "metric", "model", "method", "verified", "config_sha"):
        assert k in prov
    assert prov["verified"] is True
    assert prov["method"] == "sft"
    # AP confidence source + N-sample budget recorded per run (architect note)
    assert good_metrics["confidence_source"] == "self_consistency"
    assert good_metrics["confidence_n_samples"] == 8

    # bootstrap_ci.json
    boot = json.loads(
        (results_dir / "good__in_domain" / "bootstrap_ci.json").read_text(
            encoding="utf-8"
        )
    )
    assert "truthful_rate" in boot
    assert boot["truthful_rate"]["ci_lo"] <= boot["truthful_rate"]["point"]

    # comparisons
    mcnemar_csv = results_dir / "comparisons" / "mcnemar.csv"
    summary_csv = results_dir / "comparisons" / "summary_table.csv"
    assert mcnemar_csv.exists()
    assert summary_csv.exists()
    rows = list(csv.DictReader(summary_csv.open(encoding="utf-8")))
    assert len(rows) == 2
    mc_rows = list(csv.DictReader(mcnemar_csv.open(encoding="utf-8")))
    assert mc_rows and mc_rows[0]["arm_a"] == "good" and mc_rows[0]["arm_b"] == "bad"
    # MB4: a real comparison carries status='compared' and populated stat columns
    assert mc_rows[0]["status"] == "compared"
    assert mc_rows[0]["statistic"] != ""
    # FB2: equal-length arms scored via the Cheng-validated truthful_rate scorer
    # stamp verified=True (conditioned on VALIDATED_METRICS, not hardcoded)
    assert good_metrics["provenance"]["metric"] == "truthful_rate"
    assert good_metrics["provenance"]["verified"] is True


def test_fixture_generator_missing_generation_raises(tmp_path):
    gen = run_eval.FixtureGenerator(tmp_path, "in_domain")
    try:
        gen.generate("missing_arm", {"id": "nope"})
        assert False, "expected KeyError for missing fixture"
    except KeyError:
        pass


class _CleanTokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return "<|im_start|>assistant\n<think>\n\n</think>\n\n"


class _DirectRejectingTokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        if "enable_thinking" in kwargs:
            raise TypeError("unexpected keyword argument 'enable_thinking'")
        return "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def _install_fake_vllm(monkeypatch, *, tokenizer=None, generated_text="Paris."):
    class FakeSamplingParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeLoRARequest:
        def __init__(self, lora_name, lora_int_id, lora_path):
            self.lora_name = lora_name
            self.lora_int_id = lora_int_id
            self.lora_path = lora_path

    class FakeLLM:
        instances = []

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.tokenizer = tokenizer or _CleanTokenizer()
            self.generate_calls = []
            FakeLLM.instances.append(self)

        def get_tokenizer(self):
            return self.tokenizer

        def generate(self, prompts, sampling_params, **kwargs):
            self.generate_calls.append(
                {
                    "prompts": prompts,
                    "sampling_params": sampling_params,
                    "kwargs": kwargs,
                }
            )
            output = types.SimpleNamespace(text=generated_text)
            return [types.SimpleNamespace(outputs=[output])]

    fake_vllm = types.ModuleType("vllm")
    fake_vllm.LLM = FakeLLM
    fake_vllm.SamplingParams = FakeSamplingParams
    fake_lora = types.ModuleType("vllm.lora")
    fake_lora_request = types.ModuleType("vllm.lora.request")
    fake_lora_request.LoRARequest = FakeLoRARequest
    monkeypatch.setitem(sys.modules, "vllm", fake_vllm)
    monkeypatch.setitem(sys.modules, "vllm.lora", fake_lora)
    monkeypatch.setitem(sys.modules, "vllm.lora.request", fake_lora_request)
    return FakeLLM, FakeLoRARequest


def _vllm_cfg(tmp_path):
    return {
        "model_tag": "fake-qwen3",
        "model_name": "hf/fake-qwen3",
        "generation": {
            "enable_thinking": False,
            "seed": 123,
            "temperature": 0.0,
            "max_new_tokens": 17,
        },
        "arms": [
            {"name": "base", "method": "base", "model": "fake-qwen3", "adapter": None},
            {
                "name": "sft",
                "method": "sft",
                "model": "fake-qwen3",
                "adapter": str(tmp_path / "sft_adapter"),
            },
        ],
    }


def test_vllm_generator_constructor_lazy_imports_and_enables_lora(monkeypatch, tmp_path):
    FakeLLM, _ = _install_fake_vllm(monkeypatch)

    gen = run_eval.VLLMGenerator(_vllm_cfg(tmp_path))

    assert gen is not None
    assert len(FakeLLM.instances) == 1
    assert FakeLLM.instances[0].kwargs == {
        "model": "hf/fake-qwen3",
        "enable_lora": True,
    }


def test_vllm_generator_requires_explicit_live_model_name(monkeypatch, tmp_path):
    _install_fake_vllm(monkeypatch)
    cfg = _vllm_cfg(tmp_path)
    del cfg["model_name"]

    with pytest.raises(KeyError, match="model_name"):
        run_eval.VLLMGenerator(cfg)


def test_vllm_generator_selects_base_vs_lora_requests(monkeypatch, tmp_path):
    FakeLLM, _ = _install_fake_vllm(monkeypatch)
    gen = run_eval.VLLMGenerator(_vllm_cfg(tmp_path))

    base = gen.generate("base", {"id": "q1", "question": "Capital?"})
    sft = gen.generate("sft", {"id": "q1", "question": "Capital?"})

    assert base["generated_answer"] == "Paris."
    assert sft["generated_answer"] == "Paris."
    calls = FakeLLM.instances[0].generate_calls
    assert calls[0]["kwargs"] == {}
    lora_request = calls[1]["kwargs"]["lora_request"]
    assert lora_request.lora_name == "sft"
    assert lora_request.lora_int_id == 1
    assert lora_request.lora_path == str((tmp_path / "sft_adapter").resolve())
    assert calls[0]["sampling_params"].kwargs == {
        "n": 1,
        "temperature": 0.0,
        "max_tokens": 17,
        "seed": 123,
        "stop": ["<think>", "</think>"],
    }


def test_vllm_sampling_params_stop_thinking_markers_when_disabled(
    monkeypatch, tmp_path
):
    _install_fake_vllm(monkeypatch)

    gen = run_eval.VLLMGenerator(_vllm_cfg(tmp_path))

    assert gen._sampling_params.kwargs["stop"] == ["<think>", "</think>"]


def test_vllm_sampling_params_preserves_configured_stop_strings(
    monkeypatch, tmp_path
):
    _install_fake_vllm(monkeypatch)
    cfg = _vllm_cfg(tmp_path)
    cfg["generation"]["stop"] = ["<|endoftext|>", "</think>"]

    gen = run_eval.VLLMGenerator(cfg)

    assert gen._sampling_params.kwargs["stop"] == [
        "<|endoftext|>",
        "</think>",
        "<think>",
    ]


def test_vllm_generator_falls_back_to_chat_template_kwargs(monkeypatch, tmp_path):
    tokenizer = _DirectRejectingTokenizer()
    _install_fake_vllm(monkeypatch, tokenizer=tokenizer)
    gen = run_eval.VLLMGenerator(_vllm_cfg(tmp_path))

    gen.generate("base", {"id": "q1", "question": "Capital?"})

    assert [call["kwargs"] for call in tokenizer.calls] == [
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "enable_thinking": False,
        },
        {
            "tokenize": False,
            "add_generation_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    ]


def test_vllm_generator_rejects_generated_thinking(monkeypatch, tmp_path):
    _install_fake_vllm(monkeypatch, generated_text="<think>private</think> Paris.")
    gen = run_eval.VLLMGenerator(_vllm_cfg(tmp_path))

    with pytest.raises(RuntimeError, match="thinking marker"):
        gen.generate("base", {"id": "q1", "question": "Capital?"})


def test_eval_loaders_read_utf8_not_windows_locale_default(tmp_path):
    gold_path = tmp_path / "gold.jsonl"
    _write_utf8_jsonl(
        gold_path,
        [
            {
                "question_norm": "where is 東京?",
                "normalized_aliases": ["日本"],
            }
        ],
    )
    assert scorers.load_gold(gold_path)["where is 東京?"] == ["日本"]

    in_domain_path = tmp_path / "in_domain.json"
    _write_utf8_json(
        in_domain_path,
        [{"question": "Where is 東京?", "label": "known"}],
    )
    records = run_eval._load_eval_records(
        "in_domain", {"path": str(in_domain_path)}, {}
    )
    assert records[0]["question"] == "Where is 東京?"

    selfaware_path = tmp_path / "SelfAware.json"
    _write_utf8_json(
        selfaware_path,
        {
            "example": [
                {
                    "question_id": "utf8",
                    "question": "Where is 東京?",
                    "answer": ["日本"],
                    "answerable": True,
                }
            ]
        },
    )
    ood_records = ood.load_selfaware(selfaware_path)
    assert ood_records[0]["question"] == "Where is 東京?"


def test_eval_record_loader_no_limit_preserves_all_records(tmp_path):
    records_path = tmp_path / "records.json"
    records = [
        {"question_id": "q1", "question": "Question 1?", "label": "known"},
        {"question_id": "q2", "question": "Question 2?", "label": "known"},
        {"question_id": "q3", "question": "Question 3?", "label": "unknown"},
    ]
    records_path.write_text(json.dumps(records), encoding="utf-8")

    loaded = run_eval._load_eval_records(
        "in_domain", {"path": str(records_path)}, {}
    )

    assert [record["id"] for record in loaded] == ["q1", "q2", "q3"]
    assert [record["question"] for record in loaded] == [
        "Question 1?",
        "Question 2?",
        "Question 3?",
    ]


def test_eval_record_loader_limit_offset_is_ordered_and_deterministic(tmp_path):
    records_path = tmp_path / "records.jsonl"
    _write_jsonl(
        records_path,
        [
            {"id": "q0", "question": "Question 0?", "label": "known"},
            {"id": "q1", "question": "Question 1?", "label": "known"},
            {"id": "q2", "question": "Question 2?", "label": "unknown"},
            {"id": "q3", "question": "Question 3?", "label": "unknown"},
        ],
    )
    set_cfg = {"path": str(records_path), "offset": 1, "limit": 2}

    first = run_eval._load_eval_records("in_domain", set_cfg, {})
    second = run_eval._load_eval_records("in_domain", set_cfg, {})

    assert [record["id"] for record in first] == ["q1", "q2"]
    assert second == first


def test_eval_record_loader_limit_applies_after_ood_normalization(
    monkeypatch, tmp_path
):
    normalized = [
        {"id": "ood-0", "question": "OOD 0?", "label": "known", "source": "fake"},
        {"id": "ood-1", "question": "OOD 1?", "label": "unknown", "source": "fake"},
        {"id": "ood-2", "question": "OOD 2?", "label": "known", "source": "fake"},
    ]

    def fake_load_ood_set(eval_set, path):
        assert eval_set == "selfaware"
        assert path == tmp_path / "SelfAware.json"
        return list(normalized)

    monkeypatch.setattr(ood, "load_ood_set", fake_load_ood_set)

    loaded = run_eval._load_eval_records(
        "selfaware",
        {
            "type": "ood",
            "path": str(tmp_path / "SelfAware.json"),
            "offset": 1,
            "limit": 1,
        },
        {},
    )

    assert loaded == [normalized[1]]


def test_eval_record_loader_rejects_invalid_limit(tmp_path):
    records_path = tmp_path / "records.json"
    records_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="eval_sets.in_domain.limit"):
        run_eval._load_eval_records(
            "in_domain", {"path": str(records_path), "limit": -1}, {}
        )


def test_eval_record_loader_rejects_fractional_limit(tmp_path):
    records_path = tmp_path / "records.json"
    records_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="eval_sets.in_domain.limit"):
        run_eval._load_eval_records(
            "in_domain", {"path": str(records_path), "limit": 1.5}, {}
        )


def test_local_4b_smoke_config_is_bounded_to_completed_adapters():
    repo = run_eval.EVAL_DIR.parents[2]
    cfg_path = run_eval.EVAL_DIR / "config" / "eval_smoke_local_4b.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    sft_record = json.loads(
        (
            repo / "experiment" / "phase1" / "run_records"
            / "sft__4b__headline__seed1.json"
        ).read_text(encoding="utf-8")
    )
    dpo_record = json.loads(
        (
            repo / "experiment" / "phase1" / "run_records"
            / "dpo__4b__headline__seed1.json"
        ).read_text(encoding="utf-8")
    )

    assert cfg["model_tag"] == "qwen3-4b-instruct"
    assert cfg["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    assert cfg["gold_path"] == "fixtures/gold_min.jsonl"
    assert cfg["eval_sets"] == {
        "in_domain": {
            "path": "fixtures/in_domain_records.json",
            "label_from_target": False,
        }
    }

    arms = {arm["name"]: arm for arm in cfg["arms"]}
    assert list(arms) == ["base", "sft", "dpo"]
    assert arms["base"]["adapter"] is None
    assert arms["sft"]["adapter"] == sft_record["outcome"]["adapter_path"]
    assert arms["dpo"]["adapter"] == dpo_record["outcome"]["adapter_path"]
    assert {arm["model"] for arm in arms.values()} == {"qwen3-4b-instruct"}


def test_local_4b_ood_slice_config_is_diagnostic_bounded_base_sft_dpo_only():
    cfg_path = run_eval.EVAL_DIR / "config" / "eval_ood_slice_local_4b.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    assert cfg["model_tag"] == "qwen3-4b-instruct"
    assert cfg["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    assert cfg["gold_path"] == (
        "../../../datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl"
    )
    assert cfg["results_dir"] == "results_ood_slice_local_4b"
    assert cfg["generation"]["n_samples"] == 1
    assert cfg["confidence"]["n_samples"] == 1
    assert cfg["bootstrap"]["n_resamples"] == 200
    assert cfg["vllm"]["max_lora_rank"] == 32

    arms = {arm["name"]: arm for arm in cfg["arms"]}
    assert list(arms) == ["base", "sft", "dpo"]
    assert {arm["method"] for arm in arms.values()} == {"base", "sft", "dpo"}
    assert all("kto" not in arm_name for arm_name in arms)
    assert all("bridge" not in arm_name for arm_name in arms)

    assert set(cfg["eval_sets"]) == {"coconot", "truthfulqa", "selfaware"}
    for set_cfg in cfg["eval_sets"].values():
        assert set_cfg["type"] == "ood"
        assert set_cfg["offset"] == 0
        assert set_cfg["limit"] == 64


def test_local_4b_selfaware_mixed_slice_config_is_diagnostic_bounded_base_sft_dpo_only():
    cfg_path = (
        run_eval.EVAL_DIR / "config" / "eval_selfaware_mixed_slice_local_4b.yaml"
    )
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    assert cfg["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    assert cfg["results_dir"] == "results_selfaware_mixed_slice_local_4b"
    assert cfg["vllm"]["max_lora_rank"] == 32

    arms = {arm["name"]: arm for arm in cfg["arms"]}
    assert list(arms) == ["base", "sft", "dpo"]
    assert {arm["method"] for arm in arms.values()} == {"base", "sft", "dpo"}

    assert set(cfg["eval_sets"]) == {"selfaware"}
    selfaware = cfg["eval_sets"]["selfaware"]
    assert selfaware["offset"] == 2300
    assert selfaware["limit"] == 64


def test_local_4b_selfaware_evidence_slice_config_is_bounded_base_sft_dpo_only():
    cfg_path = (
        run_eval.EVAL_DIR
        / "config"
        / "eval_selfaware_evidence_2240_192_local_4b.yaml"
    )
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    assert cfg["model_tag"] == "qwen3-4b-instruct"
    assert cfg["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    assert cfg["gold_path"] == (
        "../../../datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl"
    )
    assert cfg["results_dir"] == "results_selfaware_evidence_2240_192_local_4b"
    assert cfg["generation"]["enable_thinking"] is False
    assert cfg["generation"]["n_samples"] == 1
    assert cfg["confidence"]["n_samples"] == 1
    assert cfg["bootstrap"]["n_resamples"] == 200
    assert cfg["vllm"]["max_lora_rank"] == 32

    arms = {arm["name"]: arm for arm in cfg["arms"]}
    assert list(arms) == ["base", "sft", "dpo"]
    assert {arm["method"] for arm in arms.values()} == {"base", "sft", "dpo"}
    assert all("kto" not in arm_name for arm_name in arms)
    assert all("bridge" not in arm_name for arm_name in arms)
    assert all("cloud" not in arm_name for arm_name in arms)
    assert {arm["model"] for arm in arms.values()} == {"qwen3-4b-instruct"}

    assert set(cfg["eval_sets"]) == {"selfaware"}
    selfaware = cfg["eval_sets"]["selfaware"]
    assert selfaware == {
        "type": "ood",
        "path": "../../../datasets/selfaware/SelfAware.json",
        "offset": 2240,
        "limit": 192,
    }


# --- MB4: McNemar mismatched-length pairs are recorded, not silently skipped ---


def test_mcnemar_length_mismatch_records_skip_row_and_warns(tmp_path):
    """An arm pair with mismatched truthful-vector lengths must appear in
    mcnemar.csv as a status='skipped_length_mismatch' row carrying both lengths,
    AND raise a warning — never vanish silently (reviewer M4 / MB4).
    """
    import warnings

    results_dir = tmp_path / "results"
    cfg = {
        "arms": [
            {"name": "arm_a"},
            {"name": "arm_b"},  # mismatched length vs arm_a
            {"name": "arm_c"},  # equal length to arm_a -> a real comparison
        ],
    }
    truthful_vectors = {
        ("arm_a", "in_domain"): [1, 0, 1, 1],
        ("arm_b", "in_domain"): [1, 0, 1],       # length 3 != 4
        ("arm_c", "in_domain"): [0, 1, 0, 1],    # length 4 == 4
    }
    summary_rows = [{"arm": "arm_a", "eval_set": "in_domain", "truthful_pct": 75.0}]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        run_eval._write_comparisons(results_dir, cfg, truthful_vectors, summary_rows)

    # a warning fired for the mismatched pair
    assert any("McNemar skipped" in str(w.message) for w in caught)

    rows = list(
        csv.DictReader(
            (results_dir / "comparisons" / "mcnemar.csv").open(encoding="utf-8")
        )
    )
    by_pair = {(r["arm_a"], r["arm_b"]): r for r in rows}

    # arm_a vs arm_b: skip row, both lengths recorded, stat columns empty
    skip = by_pair[("arm_a", "arm_b")]
    assert skip["status"] == "skipped_length_mismatch"
    assert "arm_a=4" in skip["note"] and "arm_b=3" in skip["note"]
    assert skip["statistic"] == "" and skip["p_value"] == ""

    # arm_a vs arm_c: real comparison still produced alongside the skip
    compared = by_pair[("arm_a", "arm_c")]
    assert compared["status"] == "compared"
    assert compared["statistic"] != ""


def test_mcnemar_missing_vector_records_skip_row(tmp_path):
    """A pair where one arm's vector is absent (e.g. arm not scored on that set)
    is also recorded as a skip with note='missing', not dropped.
    """
    results_dir = tmp_path / "results"
    cfg = {"arms": [{"name": "arm_a"}, {"name": "arm_b"}]}
    truthful_vectors = {
        ("arm_a", "in_domain"): [1, 0, 1],
        # arm_b absent on in_domain
    }
    run_eval._write_comparisons(results_dir, cfg, truthful_vectors, [])
    rows = list(
        csv.DictReader(
            (results_dir / "comparisons" / "mcnemar.csv").open(encoding="utf-8")
        )
    )
    assert len(rows) == 1
    assert rows[0]["status"] == "skipped_length_mismatch"
    assert "missing" in rows[0]["note"]


# --- FB2: verified flag is conditioned on the scorer path, not hardcoded ------


def test_validated_metric_registry_drives_verified():
    """truthful_rate is a Cheng-regression-validated scorer path -> True;
    a synthetic non-validated metric -> False. Conditioning, not a literal.
    """
    assert run_eval.is_validated_metric("truthful_rate") is True
    assert run_eval.is_validated_metric("some_future_unvalidated_metric") is False


def test_provenance_non_validated_metric_stamps_verified_false():
    """A Provenance for a metric outside VALIDATED_METRICS must carry
    verified=False, preserving the HANDOFF §5 contract that the flag means
    'produced by a regression-validated scorer path'.
    """
    metric = "experimental_unvalidated_score"
    prov = run_eval.Provenance(
        source="in_domain",
        metric=metric,
        model="test-model",
        method="sft",
        verified=run_eval.is_validated_metric(metric),
        config_sha="deadbeef",
    )
    assert prov.verified is False
    assert prov.as_dict()["verified"] is False
