"""Capture provenance and prompt checks independent of weight selection."""
import json
from pathlib import Path

import numpy as np
import pytest
from hs20_nwe import astra_capture as ac
from hs20_nwe import astra_render as ar
from hs20_nwe.util import HarnessError
from test_astra_fixed import (
    bf16_weight,
    groups,
    keys,
    small_proposal,
    write_synthetic_capture,
)


def fixture(tmp_path):
    p = small_proposal()
    rng = np.random.default_rng(4)
    U, K = groups(rng)
    W = bf16_weight(rng, (6, 40))
    uk, kk = keys("u", 8), keys("k", 8)
    path = tmp_path / "cap"
    write_synthetic_capture(path, uk, kk, U, K, W=W, proposal=p)
    return p, path, uk + kk, W, U, K


@pytest.mark.parametrize("change", ["revision", "renderer", "shards", "adapter", "sites", "cache"])
def test_matching_fingerprint_cannot_bypass_registered_capture_settings(tmp_path, change):
    p, path, roster, *_ = fixture(tmp_path)
    request_path = tmp_path / "capture_request.json"
    doc = json.loads(request_path.read_text())
    identity = doc["identity"]
    if change == "revision": identity["run"]["revision"] = "0" * 40
    elif change == "renderer": identity["run"]["render"]["callable"] = "hs20_nwe.astra_render:render_prc"
    elif change == "shards": identity["run"]["model"]["files"] = {}
    elif change == "adapter": identity["run"]["adapter"] = "unexpected"
    elif change == "sites": identity["sites"] = identity["sites"][:1]
    else: identity["use_cache"] = not identity["use_cache"]
    doc["fingerprint"] = ac.fingerprint(identity)
    request_path.write_text(json.dumps(doc))
    (path / "capture.runlog.jsonl.meta.json").write_text(json.dumps({"complete": True, "fingerprint": doc["fingerprint"]}))
    with pytest.raises(HarnessError, match="capture request differs"):
        ac.verify_request(p, path, request_path, roster)


def test_capture_request_and_linear_readback_are_checked(tmp_path):
    p, path, roster, W, U, K = fixture(tmp_path)
    report = ac.verify_request(p, path, tmp_path / "capture_request.json", roster)
    assert report["fingerprint"]
    outputs = np.concatenate([U, K]) @ W.T
    assert ac.linear_consistency(U, K, outputs.astype(np.float32), W, p)["rows"] == 16
    with pytest.raises(HarnessError, match="does not agree"):
        ac.linear_consistency(U, K, outputs + 1, W, p)
    m = json.loads((path / "manifest.json").read_text())
    m["weight_patch"] = {"digest": "unexpected"}
    (path / "manifest.json").write_text(json.dumps(m))
    with pytest.raises(HarnessError, match="patched"):
        ac.verify_request(p, path, tmp_path / "capture_request.json", roster)


def test_target_prompts_preserve_existing_contract_and_question_only(monkeypatch):
    import yaml
    exp = Path(__file__).parents[1]
    proposal = yaml.safe_load((exp / "astra_r1.yaml").read_text())
    assert ar.PSTRUCT == proposal["prompts"]["P-struct"] and ar.PRC == proposal["prompts"]["P-rc"]
    calls = []
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls.append((messages, kwargs))
            return "synthetic prompt"
    monkeypatch.setattr(ar, "_tokenizer", lambda: Tokenizer())
    assert ar.render_pstruct({"question": "Q", "role": "unknown", "aliases": ["secret"]}) == "synthetic prompt"
    assert calls == [([{"role": "system", "content": ar.PSTRUCT}, {"role": "user", "content": "Q"}],
                      {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False})]
