#!/usr/bin/env python3
"""ExtractionBackend seam + Stub/Transformers backends for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). Owns the forward-pass seam:
the ExtractionBackend Protocol, the deterministic torch-free StubExtractionBackend,
the GPU TransformersPeftBackend (lazy heavy imports), the build_extraction_backend
factory, and the arm-role / vector-delta helpers the run-loop shares. None of
these read PROBE_DIR. Heavy deps (torch/transformers/peft) and the shared render
helper are LAZY-imported so this module loads on a CPU-only / no-GPU host.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

import hidden_state_schema as schema
from hs_provenance import _file_sha256, _local_model_dir_sha256


class ExtractionBackend(Protocol):
    """Minimal forward interface the harness depends on (one seam to stub).

    The base-vs-LoRA contrast lives behind this Protocol so the real GPU path
    (TransformersPeftBackend) and a deterministic torch-free stub are
    interchangeable. forward returns layer_id -> 1-D final-token vector.
    """

    num_hidden_layers: int
    hidden_dim: int
    # Per-head (attention_head granularity) layout; populated by backends that
    # implement forward_head_states. num_attention_heads * head_dim is the
    # o_proj-input width.
    num_attention_heads: int
    head_dim: int

    def render(self, question: str) -> str:
        """Render the prompt bytes for one question (shared render helper)."""
        ...

    def forward_hidden_states(self, rendered_prompt: str, arm_state: str,
                              adapter_name: str | None) -> dict:
        """Final-token hidden states per layer for one arm/adapter-state."""
        ...

    def forward_head_states(self, rendered_prompt: str, arm_state: str,
                            adapter_name: str | None) -> dict:
        """Final-token per-head o_proj-input stack for one arm/adapter-state.

        Returns ``{block_id: flat_vector}`` for block_id 0..N-1, where each
        flat_vector is length ``num_attention_heads * head_dim`` (the concatenated
        per-head context feeding that block's attention output projection). This
        is the ITI-style per-head surface; backends exposing it must also set
        `num_attention_heads` and `head_dim` so the harness/manifest can reshape.
        """
        ...

    def provenance(self) -> dict:
        """Backend-derived (post-load) manifest provenance fields.

        Returns the manifest fields that can only be known once the model is
        loaded: base_model_id/revision/hash, adapter_hash, tokenizer_revision,
        and the library versions (peft_version/transformers_version). The harness
        merges this into the manifest (after collect_static_provenance, so these
        win) before the finalize gate, so the REAL backend supplies real values
        and the stub supplies deterministic stand-ins (keeping the
        require_populated gate exercisable GPU-free).

        Seam note for the lora_* fields: on the REAL path they come from the
        adapter dir's adapter_config.json (read GPU-free by
        collect_static_provenance), so the real backend OMITS them here to let
        those values stand; the STUB has no adapter dir, so it INCLUDES lora_*
        stand-ins so the GPU-free pipeline still finalizes.
        """
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
                 system_prompt: str = "answer concisely", seed: int = 0,
                 num_attention_heads: int = 4, head_dim: int = 2):
        self.num_hidden_layers = num_hidden_layers
        self.hidden_dim = hidden_dim
        self.system_prompt = system_prompt
        self.seed = seed
        # Per-head layout for the attention_head granularity stub path; defaults
        # are tiny so tests stay fast. Independent of hidden_dim (under GQA the
        # o_proj-input width num_attention_heads*head_dim need not equal hidden).
        self.num_attention_heads = num_attention_heads
        self.head_dim = head_dim

    def render(self, question: str) -> str:
        # Deterministic stand-in render; the real backend uses the shared helper.
        return f"<|stub|>{self.system_prompt}|{question}<|gen|>"

    def _hashed_vector(self, *parts, width: int) -> list[float]:
        import hashlib

        key = "|".join(str(p) for p in parts)
        digest = hashlib.sha256(key.encode()).digest()
        return [((digest[i % len(digest)] / 255.0) - 0.5) for i in range(width)]

    def forward_hidden_states(self, rendered_prompt, arm_state, adapter_name):
        vectors: dict[int, list[float]] = {}
        layer_count = schema.expected_layer_count(self.num_hidden_layers)
        for layer in range(layer_count):
            vectors[layer] = self._hashed_vector(
                self.seed, rendered_prompt, arm_state, adapter_name, layer,
                width=self.hidden_dim,
            )
        return vectors

    def forward_head_states(self, rendered_prompt, arm_state, adapter_name):
        # Deterministic per-block o_proj-input stand-in: N attention blocks (no
        # embedding layer), each width num_attention_heads*head_dim. arm_state is
        # mixed into the hash so h_base != h_lora structurally, mirroring the
        # residual stub. A distinct "head" tag keeps these vectors from colliding
        # with the residual stub's per-layer vectors.
        width = self.num_attention_heads * self.head_dim
        return {
            block: self._hashed_vector(
                self.seed, "head", rendered_prompt, arm_state, adapter_name, block,
                width=width,
            )
            for block in range(schema.expected_attention_layer_count(
                self.num_hidden_layers))
        }

    def provenance(self) -> dict:
        """Deterministic stub stand-ins for the post-load provenance fields.

        These are clearly stub-marked (so a stub-produced manifest is never
        mistaken for a real extraction) but non-None, which lets the GPU-free
        pipeline produce a manifest that passes validate_manifest(
        require_populated=True) — i.e. the finalize gate is exercisable in CI.
        """
        return {
            "base_model_id": "stub/base-model",
            "base_model_revision": "stub-revision",
            "base_model_hash": "stub-base-hash",
            "adapter_hash": "stub-adapter-hash",
            "tokenizer_revision": "stub-tokenizer-revision",
            "peft_version": "stub-peft",
            "transformers_version": "stub-transformers",
            # LoRA hyperparams come from adapter_config.json on the real path
            # (GPU host has the adapter dir); the stub has no adapter dir, so it
            # supplies stand-ins here. The REAL backend OMITS these keys, letting
            # collect_static_provenance's adapter_config.json read stand.
            "lora_rank": -1,
            "lora_alpha": -1,
            "lora_dropout": 0.0,
            "lora_target_modules": ["stub-target"],
        }


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
        self._peft = __import__("peft")
        self._transformers = __import__("transformers")
        self.system_prompt = system_prompt
        self.enable_thinking = config["model"]["enable_thinking"]
        self.active_adapter_name = active_adapter_name
        self.active_adapter_path = active_adapter_path
        ext = config["extraction"]
        self.device = ext.get("device", "cuda")
        self._compute_dtype = getattr(torch, ext["compute_dtype"])
        self.token_position_rule = ext["token_position_rule"]

        self.model_name = config["model"]["model_name"]
        # Optional immutable revision pin (commit SHA / tag). Recorded as
        # base_model_revision and passed to from_pretrained so the load is
        # reproducible. None (default) loads the hub default branch — the
        # resolved snapshot SHA is still recovered post-load from
        # config._commit_hash below, so provenance stays a commit SHA, not a
        # mutable ref, whenever the hub returns one.
        self.model_revision = config["model"].get("revision")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, revision=self.model_revision)
        base = AutoModelForCausalLM.from_pretrained(
            self.model_name, revision=self.model_revision,
            torch_dtype=self._compute_dtype, device_map=self.device)
        self.model = PeftModel.from_pretrained(
            base, active_adapter_path, adapter_name=active_adapter_name)
        self.model.eval()
        self.num_hidden_layers = self.model.config.num_hidden_layers
        self.hidden_dim = self.model.config.hidden_size
        # Per-head layout for attention_head granularity. head_dim is read
        # explicitly from config when present (Qwen3 sets head_dim independently,
        # so hidden_size // num_attention_heads is WRONG under that config) and
        # only falls back to the even-split when the config omits it.
        self.num_attention_heads = self.model.config.num_attention_heads
        self.head_dim = getattr(
            self.model.config, "head_dim", None
        ) or (self.hidden_dim // self.num_attention_heads)

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

    def _o_proj_modules(self) -> dict:
        """Map attention-block id -> that block's o_proj module (PEFT-safe).

        Resolves by module-name suffix `self_attn.o_proj` over named_modules(),
        so it is robust to PEFT's wrapper nesting (the matched module is the
        possibly-LoRA-wrapped o_proj; hooking its INPUT captures the concatenated
        per-head context regardless of whether o_proj is a LoRA target). The
        block index is parsed from the `...layers.<i>...` segment of the name.
        Raises if the discovered ids are not exactly the N contiguous blocks, so
        a model whose attention module is named differently fails loudly instead
        of silently capturing a partial stack.
        """
        modules: dict[int, object] = {}
        for name, module in self.model.named_modules():
            if not name.endswith("self_attn.o_proj"):
                continue
            match = re.search(r"layers\.(\d+)\.", name)
            if match is None:
                raise RuntimeError(
                    f"found an o_proj module with no parseable block index: {name!r}"
                )
            modules[int(match.group(1))] = module
        expected = set(range(self.num_hidden_layers))
        if set(modules) != expected:
            raise RuntimeError(
                f"o_proj module discovery captured blocks {sorted(modules)}, "
                f"expected contiguous 0..{self.num_hidden_layers - 1}; the model's "
                "attention module naming is not the assumed `layers.<i>.self_attn."
                "o_proj` layout"
            )
        return modules

    def forward_head_states(self, rendered_prompt, arm_state, adapter_name):
        """Capture each block's final-token o_proj INPUT (per-head context).

        ITI-style per-head surface: a forward hook on every block's o_proj records
        the tensor fed INTO the output projection, whose last dim is
        num_attention_heads * head_dim (holds under GQA). We keep only the final
        prompt token ([0, -1, :]) per block and return ``{block_id: flat_list}``;
        the caller reshapes per head via schema.reshape_o_proj_input_to_heads.
        Deterministic like forward_hidden_states: eval / no_grad / use_cache=False,
        base vs active selected exactly as the residual path does. Hooks are always
        removed in a finally so a raising forward cannot leak handles across arms.
        """
        torch = self._torch
        captured: dict[int, list[float]] = {}
        modules = self._o_proj_modules()
        handles = []

        def _make_hook(block_id: int):
            def _hook(_module, inputs, _output):
                # inputs[0]: [batch, seq, num_attention_heads * head_dim]
                x = inputs[0]
                captured[block_id] = x[0, -1, :].float().cpu().tolist()
            return _hook

        inputs = self.tokenizer(rendered_prompt, return_tensors="pt").to(self.device)
        try:
            for block_id, module in modules.items():
                handles.append(module.register_forward_hook(_make_hook(block_id)))
            with torch.no_grad():
                if arm_state in schema.BASE_ADAPTER_STATES:
                    with self.model.disable_adapter():
                        self._forward(inputs)
                else:
                    self.model.set_adapter(adapter_name)
                    self._forward(inputs)
        finally:
            for handle in handles:
                handle.remove()

        expected_width = self.num_attention_heads * self.head_dim
        for block_id, vec in captured.items():
            if len(vec) != expected_width:
                raise RuntimeError(
                    f"block {block_id} o_proj-input width {len(vec)} != "
                    f"num_attention_heads * head_dim = {expected_width}; the "
                    "captured tensor does not match the configured head layout"
                )
        return captured

    def provenance(self) -> dict:
        """Post-load manifest provenance from the REAL loaded model + libraries.

        Supplies the fields that need the loaded backend: library versions, the
        base-model id/revision, and content hashes of the model + adapter dirs.
        Hub loads keep the resolved snapshot commit/configured revision behavior.
        Local merged-model directories have no hub commit, so they get an
        explicit local-sha256:<digest> identity over stable model files. Missing
        local provenance inputs fail explicitly; non-local unresolved hub ids
        still degrade to None so the strict finalize gate surfaces the gap.
        """
        base_cfg = getattr(self.model, "config", None)
        base_model_id = getattr(base_cfg, "_name_or_path", None) or self.model_name
        adapter_dir = Path(self.active_adapter_path) if self.active_adapter_path else None
        adapter_hash = (
            _file_sha256(adapter_dir / "adapter_config.json") if adapter_dir else None)
        # base_model_revision MUST be an IMMUTABLE pin, not a mutable ref or a
        # library version: prefer the resolved snapshot commit SHA the hub
        # returned (transformers sets config._commit_hash on a hub load), then
        # the operator-configured revision pin. Deliberately NOT
        # config.transformers_version (that is the library version the config was
        # saved with, not a model identity). None-safe: if neither is available
        # the field records None and the finalize gate surfaces the gap loudly
        # rather than attesting a non-immutable revision.
        base_model_revision = (
            getattr(base_cfg, "_commit_hash", None) or self.model_revision)
        local_model_hash = None
        if base_model_revision is None:
            local_model_hash = _local_model_dir_sha256(self.model_name)
            base_model_revision = local_model_hash
        return {
            "base_model_id": base_model_id,
            "base_model_revision": base_model_revision,
            "base_model_hash": local_model_hash or base_model_id,
            "adapter_hash": adapter_hash,
            "tokenizer_revision": getattr(self.tokenizer, "name_or_path", None),
            "peft_version": self._peft.__version__,
            "transformers_version": self._transformers.__version__,
        }


def build_extraction_backend(config: dict, system_prompt: str):
    """Construct the real GPU backend. The stub is built directly by tests."""
    _base_arm, active_arm = _arm_roles(config["arms"])
    return TransformersPeftBackend(
        config=config, system_prompt=system_prompt,
        active_adapter_path=active_arm["adapter"],
        active_adapter_name=active_arm["name"])
