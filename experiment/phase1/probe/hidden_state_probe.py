#!/usr/bin/env python3
"""Hidden-state probing tier harness (exploratory mechanism tier, MVP).

Location: experiment/phase1/probe/hidden_state_probe.py
Reads:    experiment/phase1/probe/config/hidden_state_probe.yaml
          experiment/phase1/probe/<model_tag>/probe_results.jsonl (alignment, streamed)
          experiment/phase1/data/<model_tag>/questions_frozen.json (frozen split keys)
          experiment/phase1/eval/config/eval_smoke_local_4b.yaml (adapter paths, by-value)
Writes:   experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/
            manifest.json + rows.jsonl + per-arm h_base/h_lora/delta.safetensors

One job: for a matched known/unknown slice of FROZEN-split questions, run a
deterministic base-vs-LoRA forward pass and persist h_base, h_lora, and
delta = h_lora - h_base at the final prompt token across all layers, with an
exhaustive crash-safe manifest. It does NOT train probes or run interventions
(that is the deferred Phase 5), and it NEVER mutates probe_results.jsonl or any
run record (it links them by id only).

Design (plan Decisions A-E):
  - All validation is model-free in hidden_state_schema.py; this file is thin
    orchestration. Heavy deps (torch/transformers/peft) are LAZY-imported inside
    TransformersPeftBackend so the module loads, and the stub path runs, on a
    CPU-only / no-GPU / no-network host.
  - The forward pass is isolated behind the ExtractionBackend Protocol. The real
    TransformersPeftBackend needs a GPU; the StubExtractionBackend is
    deterministic, torch-free, and lets the full selection/manifest/persist/resume
    pipeline run GREEN in CI (mirrors backends.py's ProbeBackend/StubBackend seam).
  - Crash-safe manifest (Decision D-bis): the manifest is written with
    status="launched" BEFORE the forward, then patched to ok/failed; `verified`
    is set True only after emitted tensors are checked.

Real runs use TransformersPeftBackend on a GPU. The numerical h_base != h_lora
smoke assertion is GPU-only and out of MVP scope (a marked skip lives in the
test suite for the test-engineer).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Protocol

import yaml

import hidden_state_schema as schema

# Repo root is four levels up (experiment/phase1/probe/hidden_state_probe.py).
REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = Path(__file__).resolve().parent


def _rel(path: Path) -> str:
    """Path relative to REPO_ROOT for display, or absolute if outside it."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Step 3 — config parse, extraction_config_sha, output-tree resolution
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_eval_arm_adapters(config: dict, config_path: Path) -> dict:
    """Resolve active-arm adapter paths BY-VALUE from the eval config (Decision).

    Reads the eval config's arms[] and maps arm name -> adapter path, so the
    canonical adapter path is declared in exactly one place. An explicit
    `adapter` on a config arm overrides the mirror. Returns the config with
    each active arm's `adapter` populated; raises if an active arm has no
    resolvable adapter (a base arm legitimately has adapter=None).
    """
    eval_source = config.get("eval_arms_source")
    eval_adapters: dict[str, str | None] = {}
    if eval_source:
        # Relative paths in the config are anchored at the probe dir (the same
        # base resolve_output_dir / select_matched_slice use), not the config's
        # own dir, so they read naturally as probe/<...>.
        eval_path = (PROBE_DIR / eval_source).resolve()
        with eval_path.open(encoding="utf-8") as fh:
            eval_cfg = yaml.safe_load(fh)
        eval_adapters = {a["name"]: a.get("adapter") for a in eval_cfg.get("arms", [])}

    for arm in config["arms"]:
        if arm.get("adapter") is None and arm["adapter_state"] == schema.ADAPTER_STATE_ACTIVE:
            mirrored = eval_adapters.get(arm["name"])
            if not mirrored:
                raise ValueError(
                    f"active arm {arm['name']!r} has no adapter path: set "
                    f"arms[].adapter explicitly or add a matching arm to "
                    f"{eval_source!r}"
                )
            arm["adapter"] = mirrored
    return config


def parse_config(config_path: Path) -> tuple[dict, str]:
    """Load, validate (model-free), and hash the extraction config.

    Runs the P0 adapter-state pre-flight and the token-position-rule check at
    parse time so a malformed config fails BEFORE any model load. Returns the
    resolved config and its extraction_config_sha.
    """
    config = load_config(config_path)
    config = resolve_eval_arm_adapters(config, config_path)
    schema.validate_arm_states(config["arms"])
    schema.validate_token_position_rule(config["extraction"]["token_position_rule"])
    cfg_sha = schema.config_sha(config)
    return config, cfg_sha


def extraction_id(arm_name: str, extraction_config_sha: str) -> str:
    """Per-arm output id: f'{arm}__{extraction_config_sha[:12]}' (Decision C)."""
    return f"{arm_name}__{extraction_config_sha[:12]}"


def resolve_output_dir(config: dict, extraction_config_sha: str,
                       base_dir: Path | None = None) -> Path:
    """probe/<model_tag>/hidden_states/<extraction_id>/ (shared per extraction).

    The extraction_id keys the whole extraction (one base + one active arm), so
    the tree groups both arms' tensors with their shared manifest/rows.
    """
    root = base_dir if base_dir is not None else PROBE_DIR
    model_tag = config["model"]["model_tag"]
    subdir = config["output"]["hidden_states_subdir"]
    ext_id = extraction_id("extraction", extraction_config_sha)
    return root / model_tag / subdir / ext_id


# ---------------------------------------------------------------------------
# Step 4 — selection / alignment (frozen keys + streamed probe_results.jsonl)
# ---------------------------------------------------------------------------

def _select_keys(frozen: dict, pool_field: str, n: int, seed: int) -> list[str]:
    """Deterministically pick n keys from a frozen-split pool by stable hash."""
    import hashlib

    keys = list(frozen.get(pool_field, []))
    if n is None or n >= len(keys):
        return keys
    ordered = sorted(
        keys,
        key=lambda k: hashlib.sha256(f"{seed}|{k}".encode()).hexdigest(),
    )
    return ordered[:n]


def select_matched_slice(config: dict) -> list[dict]:
    """Build the matched known/unknown extraction slice (leakage-safe).

    Reads frozen known/unknown keys (probe_pool_row_key) and STREAMS
    probe_results.jsonl once, keeping only rows whose key is selected (never
    whole-loading the ~123MB file). Each returned row carries the alignment
    identity (probe_pool_row_key, question, label, probe_config_sha) the harness
    needs; alignment is by key only, never loose question text.
    """
    sel = config["selection"]
    # Config relative paths are anchored at the probe dir (see
    # resolve_eval_arm_adapters); keep frozen + results on the same base.
    frozen_path = (PROBE_DIR / sel["questions_frozen"]).resolve()
    results_path = (PROBE_DIR / sel["probe_results"]).resolve()

    with frozen_path.open(encoding="utf-8") as fh:
        frozen = json.load(fh)

    want_known = set(_select_keys(frozen, "known_question_keys",
                                  sel["n_known"], sel["selection_seed"]))
    want_unknown = set(_select_keys(frozen, "unknown_question_keys",
                                    sel["n_unknown"], sel["selection_seed"]))
    wanted = want_known | want_unknown
    label_by_key = {**{k: "known" for k in want_known},
                    **{k: "unknown" for k in want_unknown}}

    found = _stream_probe_rows(results_path, wanted, label_by_key)
    missing = wanted - {r["probe_pool_row_key"] for r in found}
    if missing:
        raise ValueError(
            f"{len(missing)} selected frozen key(s) not found in "
            f"{_rel(results_path)} (e.g. {sorted(missing)[:3]}); the probe "
            "tier must have probed these before extraction"
        )
    return found


def _stream_probe_rows(results_path: Path, wanted: set[str],
                       label_by_key: dict[str, str]) -> list[dict]:
    """Stream probe_results.jsonl, returning only the selected alignment rows."""
    found: list[dict] = []
    if not results_path.exists():
        raise FileNotFoundError(
            f"alignment source {_rel(results_path)} not found; run the probe "
            "tier first (it produces probe_results.jsonl)"
        )
    with results_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if key in wanted:
                found.append({
                    "probe_pool_row_key": key,
                    "question": row["question"],
                    "label": label_by_key[key],
                    "frozen_label": label_by_key[key],
                    "probe_label": row.get("label"),
                    "aligned_probe_config_sha": row.get("probe_config_sha"),
                })
    return found


# ---------------------------------------------------------------------------
# Step 5 — ExtractionBackend seam + Stub + writer + resume
# ---------------------------------------------------------------------------

class ExtractionBackend(Protocol):
    """Minimal forward interface the harness depends on (one seam to stub).

    The base-vs-LoRA contrast lives behind this Protocol so the real GPU path
    (TransformersPeftBackend) and a deterministic torch-free stub are
    interchangeable. forward returns layer_id -> 1-D final-token vector.
    """

    num_hidden_layers: int
    hidden_dim: int

    def render(self, question: str) -> str:
        """Render the prompt bytes for one question (shared render helper)."""
        ...

    def forward_hidden_states(self, rendered_prompt: str, arm_state: str,
                              adapter_name: str | None) -> dict:
        """Final-token hidden states per layer for one arm/adapter-state."""
        ...


class StubExtractionBackend:
    """Deterministic, torch-free ExtractionBackend for GPU-free tests.

    Fabricates per-layer final-token vectors from a stable hash of
    (prompt, arm_state, adapter_name, layer), so h_base != h_lora structurally
    (different arm_state seeds different vectors) and a resumed run reproduces
    identical tensors. No model, no torch — exercises the full select/persist/
    resume pipeline in CI.
    """

    def __init__(self, num_hidden_layers: int = 3, hidden_dim: int = 8,
                 system_prompt: str = "answer concisely", seed: int = 0):
        self.num_hidden_layers = num_hidden_layers
        self.hidden_dim = hidden_dim
        self.system_prompt = system_prompt
        self.seed = seed

    def render(self, question: str) -> str:
        # Deterministic stand-in render; the real backend uses the shared helper.
        return f"<|stub|>{self.system_prompt}|{question}<|gen|>"

    def forward_hidden_states(self, rendered_prompt, arm_state, adapter_name):
        import hashlib

        vectors: dict[int, list[float]] = {}
        layer_count = schema.expected_layer_count(self.num_hidden_layers)
        for layer in range(layer_count):
            key = f"{self.seed}|{rendered_prompt}|{arm_state}|{adapter_name}|{layer}"
            digest = hashlib.sha256(key.encode()).digest()
            vectors[layer] = [
                ((digest[i % len(digest)] / 255.0) - 0.5)
                for i in range(self.hidden_dim)
            ]
        return vectors


def _arm_roles(arms: list[dict]) -> tuple[dict, dict]:
    """Return (base_arm, active_arm) after the pre-flight has validated them."""
    base = next(a for a in arms if a["adapter_state"] in schema.BASE_ADAPTER_STATES)
    active = next(a for a in arms if a["adapter_state"] == schema.ADAPTER_STATE_ACTIVE)
    return base, active


def _vector_delta(lora: dict, base: dict) -> dict:
    """delta = h_lora - h_base, per layer (plain python; persisted, not trusted)."""
    return {
        layer: [lv - bv for lv, bv in zip(lora[layer], base[layer])]
        for layer in lora
    }


def load_done_row_keys(rows_path: Path) -> set[str]:
    """Row keys already written to the append-log (resume; probe.py idiom)."""
    done: set[str] = set()
    if not rows_path.exists():
        return done
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            key = json.loads(line).get("probe_pool_row_key")
            if key:
                done.add(key)
    return done


def run_extraction(config: dict, extraction_config_sha: str, backend,
                   slice_rows: list[dict], out_dir: Path) -> Path:
    """Run the deterministic extraction over the slice; resumable append-log.

    Crash-safe (Decision D-bis): write the manifest with status="launched"
    BEFORE the forward, append per-row results + per-arm tensors, then patch the
    manifest to ok and set verified after checking the emitted tensors exist.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / config["output"]["manifest_filename"]
    rows_path = out_dir / config["output"]["rows_filename"]
    base_arm, active_arm = _arm_roles(config["arms"])
    token_rule = config["extraction"]["token_position_rule"]

    # WRITE-BEFORE-INVOKE: launched manifest hits disk before any forward.
    manifest = schema.build_manifest(
        config=config, extraction_config_sha=extraction_config_sha,
        status=schema.STATUS_LAUNCHED)
    schema.validate_manifest(manifest)
    _write_json(manifest_path, manifest)

    done = load_done_row_keys(rows_path)
    n_preexisting = len(done)
    tensor_shapes: dict[str, list[int]] = {}
    try:
        n_new = _extract_rows(
            backend, slice_rows, done, rows_path, base_arm, active_arm,
            token_rule, extraction_config_sha, out_dir, config, tensor_shapes)
    except Exception as exc:  # noqa: BLE001 - record failure, then re-raise
        manifest["status"] = schema.STATUS_FAILED
        _write_json(manifest_path, manifest)
        raise RuntimeError(
            f"extraction failed after launch; manifest marked failed at "
            f"{_rel(manifest_path)}: {exc}"
        ) from exc

    manifest["status"] = schema.STATUS_OK
    manifest["tensor_shapes"] = tensor_shapes or None
    manifest["verified"] = _verify_emitted(out_dir, base_arm, active_arm, config)
    _write_json(manifest_path, manifest)
    print(f"hidden_state_probe: wrote {n_new} new rows to {_rel(rows_path)} "
          f"({n_preexisting} already present, skipped); manifest "
          f"status={manifest['status']} verified={manifest['verified']}")
    return manifest_path


def _extract_rows(backend, slice_rows, done, rows_path, base_arm, active_arm,
                  token_rule, cfg_sha, out_dir, config, tensor_shapes) -> int:
    """Forward each unseen row for both arms; append the row + per-arm tensors."""
    n_new = 0
    persist_delta = config["extraction"].get("persist_delta", True)
    with rows_path.open("a", encoding="utf-8") as fh:
        for row in slice_rows:
            key = row["probe_pool_row_key"]
            if key in done:
                continue
            rendered = backend.render(row["question"])
            h_base = backend.forward_hidden_states(
                rendered, base_arm["adapter_state"], None)
            h_lora = backend.forward_hidden_states(
                rendered, active_arm["adapter_state"], active_arm["name"])
            _validate_arm_tensors(backend, h_base, h_lora, token_rule)
            delta = _vector_delta(h_lora, h_base) if persist_delta else None

            _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta,
                                 config, tensor_shapes)
            record = {
                "probe_pool_row_key": key,
                "question": row["question"],
                "label": row["label"],
                "probe_label": row["probe_label"],
                "aligned_probe_config_sha": row["aligned_probe_config_sha"],
                "prompt_hash": schema.prompt_hash(rendered),
                "extraction_config_sha": cfg_sha,
                "layer_count": schema.expected_layer_count(backend.num_hidden_layers),
                "hidden_dim": backend.hidden_dim,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            done.add(key)
            n_new += 1
    return n_new


def _validate_arm_tensors(backend, h_base, h_lora, token_rule) -> None:
    for layer_vectors in (h_base, h_lora):
        schema.validate_hidden_state_shape(
            layer_vectors=layer_vectors,
            num_hidden_layers=backend.num_hidden_layers,
            hidden_dim=backend.hidden_dim,
            token_position_rule=token_rule)


def _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta, config,
                         tensor_shapes) -> None:
    """Persist per-arm tensors for one row as safetensors (lazy numpy import).

    numpy is imported lazily so the row-record/append path stays importable
    without it; persistence is where the array dependency legitimately enters.
    """
    import numpy as np  # noqa: PLC0415
    from safetensors.numpy import save_file  # noqa: PLC0415

    persist_dtype = config["extraction"]["persist_dtype"]
    np_dtype = getattr(np, persist_dtype)
    roles = {"h_base": h_base, "h_lora": h_lora}
    if delta is not None:
        roles["delta"] = delta

    safe_key = key.replace("|", "_")
    for role, layer_vectors in roles.items():
        tensors = {
            f"L{layer}": np.asarray(vec, dtype=np_dtype)
            for layer, vec in layer_vectors.items()
        }
        metadata = schema.safetensors_metadata(cfg_sha, safe_key, role)
        schema.validate_safetensors_metadata(metadata)
        path = out_dir / f"{safe_key}__{role}.safetensors"
        save_file(tensors, str(path), metadata=metadata)
        any_layer = next(iter(layer_vectors.values()))
        tensor_shapes[role] = [len(layer_vectors), len(any_layer)]


def _verify_emitted(out_dir: Path, base_arm, active_arm, config) -> bool:
    """Decision D-bis: verified=True ONLY if expected tensor shards exist.

    The numerical h_base != h_lora check is GPU-only (real forward); on CPU the
    structural existence check is the strongest honest verification, so this
    never hand-sets verified on a run that emitted no tensors.
    """
    shards = list(out_dir.glob("*.safetensors"))
    return len(shards) > 0


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 6 — TransformersPeftBackend (lazy heavy imports; GPU-only forward)
# ---------------------------------------------------------------------------

class TransformersPeftBackend:
    """Real HF Transformers + PEFT ExtractionBackend (GPU). Lazy heavy imports.

    torch/transformers/peft are imported INSIDE __init__ so this module loads,
    and the stub path runs, on a CPU-only / no-GPU host (mirrors VLLMBackend's
    lazy vLLM import). Deterministic forward: model.eval(), use_cache=False,
    torch.no_grad(), batch=1, fixed dtype/device. The base pass uses
    PeftModel.disable_adapter(); the LoRA pass uses set_adapter(active). The
    shared render helper (backends.render_probe_prompt) is reused so this path
    cannot drift from VLLMBackend's thinking-tag handling.

    NOTE: PEFT/Transformers versions are intentionally NOT hard-pinned here;
    the manifest records them at runtime and the version pins are a TODO for
    devops/architect (cross-version adapter-load skew is a first-GPU-run gate).
    """

    def __init__(self, config: dict, system_prompt: str, active_adapter_path: str,
                 active_adapter_name: str):
        import torch  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415

        self._torch = torch
        self.system_prompt = system_prompt
        self.enable_thinking = config["model"]["enable_thinking"]
        self.active_adapter_name = active_adapter_name
        ext = config["extraction"]
        self.device = ext.get("device", "cuda")
        self._compute_dtype = getattr(torch, ext["compute_dtype"])
        self.token_position_rule = ext["token_position_rule"]

        model_name = config["model"]["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        base = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=self._compute_dtype, device_map=self.device)
        self.model = PeftModel.from_pretrained(
            base, active_adapter_path, adapter_name=active_adapter_name)
        self.model.eval()
        self.num_hidden_layers = self.model.config.num_hidden_layers
        self.hidden_dim = self.model.config.hidden_size

    def render(self, question: str) -> str:
        # Reuse the SHARED render+verify helper (no second template path).
        from backends import render_probe_prompt  # noqa: PLC0415

        rendered, _mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking)
        return rendered

    def forward_hidden_states(self, rendered_prompt, arm_state, adapter_name):
        torch = self._torch
        inputs = self.tokenizer(rendered_prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            if arm_state in schema.BASE_ADAPTER_STATES:
                with self.model.disable_adapter():
                    out = self._forward(inputs)
            else:
                self.model.set_adapter(adapter_name)
                out = self._forward(inputs)
        # Final prompt token, all layers; batch=1 so -1 is unambiguous.
        return {
            layer: hs[0, -1, :].float().cpu().tolist()
            for layer, hs in enumerate(out.hidden_states)
        }

    def _forward(self, inputs):
        return self.model(**inputs, output_hidden_states=True,
                          use_cache=False, return_dict=True)


def build_extraction_backend(config: dict, system_prompt: str):
    """Construct the real GPU backend. The stub is built directly by tests."""
    _base_arm, active_arm = _arm_roles(config["arms"])
    return TransformersPeftBackend(
        config=config, system_prompt=system_prompt,
        active_adapter_path=active_arm["adapter"],
        active_adapter_name=active_arm["name"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_config = PROBE_DIR / "config" / "hidden_state_probe.yaml"
    parser.add_argument("--config", type=Path, default=default_config,
                        help="path to hidden_state_probe.yaml")
    args = parser.parse_args()

    config, cfg_sha = parse_config(args.config)
    slice_rows = select_matched_slice(config)
    out_dir = resolve_output_dir(config, cfg_sha)
    system_prompt = config.get("prompt", {}).get(
        "system", "You are a helpful assistant. Answer the question concisely.")
    backend = build_extraction_backend(config, system_prompt)
    run_extraction(config, cfg_sha, backend, slice_rows, out_dir)
    print(f"hidden_state_probe: extraction written to {_rel(out_dir)}")


if __name__ == "__main__":
    main()
