"""Inference backends for the Phase 1 knowledge probe (WS-1).

Location: experiment/phase1/probe/backends.py
Used by:  experiment/phase1/probe/probe.py

Two backends behind one tiny interface (`generate_batch`):

  - VLLMBackend: the real GPU backend. vLLM is imported LAZILY inside
    __init__ so this module loads on a machine without vLLM/CUDA (the CODE
    phase is fixture-only; the real probe run is post-sign-off). It applies
    the Qwen3 chat template with enable_thinking pinned per config and runs a
    runtime self-check that the rendered prompt carries no populated thinking
    block, so a template that silently ignores the kwarg fails LOUDLY on the
    first real run instead of contaminating probe outputs.

  - StubBackend: a deterministic, dependency-free backend for smoke tests. It
    fabricates answers from a per-question alias table with a fixed seed so
    the probe's scoring/labeling/resumability logic can be exercised end to
    end with no GPU and no network.

enable_thinking verification (done offline, CODE phase), what was checked:
  Per the Qwen3 docs (qwenlm/qwen3): apply_chat_template(enable_thinking=False)
  is the documented hard switch that skips thinking content. Because this
  backend renders text with the tokenizer and then calls LLM.generate(), the
  direct tokenizer kwarg is the primary path. We also try vLLM's chat API
  chat_template_kwargs={"enable_thinking": False} surface defensively for
  compatibility, then assert the rendered prompt and generated answers are
  clean. The *-Instruct-2507 variant is ALWAYS non-thinking (the kwarg is a
  no-op there); the hybrid Qwen3-4B/8B base models honor the kwarg.
  DEFERRED to the first real GPU run (no weights/template cached this phase):
  confirming the *specific pinned* tokenizer actually accepts the kwarg
  without raising and renders no populated thinking block. The runtime
  self-check below is exactly that confirmation; it is wired to run on the
  first prompt render.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol


# Markers that indicate Qwen3 thinking scaffolding leaked into a rendered
# prompt despite enable_thinking=False. The </think> close token is 151668;
# its text form plus the open tag are the textual tripwires.
THINK_TAG_MARKERS = ("<think>", "</think>")
EMPTY_THINK_OFF_MARKER_RE = re.compile(r"<think>\s*</think>")


class ProbeBackend(Protocol):
    """Minimal generation interface the probe depends on."""

    def generate_batch(
        self, question: str, n_samples: int, temperature: float, top_p: float,
        max_new_tokens: int, seed: int,
    ) -> list[str]:
        """Return n_samples generations for one question (greedy handled by caller)."""
        ...

    def generate_greedy(self, question: str, max_new_tokens: int) -> str:
        """Return one greedy (temperature 0) decode for one question."""
        ...


def assert_no_think_scaffolding(rendered_prompt: str) -> None:
    """Fail loudly if Qwen3 thinking content leaked into a rendered prompt.

    This is the runtime self-check the team-lead required: it turns a silent
    template-honoring failure into a hard error on the first real generation.

    Qwen3's live template may include an empty ``<think>\n\n</think>`` marker at
    the generation prompt when thinking is disabled. That marker is the
    thinking-off signature; populated or unclosed thinking scaffolding is not.
    """
    rendered_without_empty_off_markers = EMPTY_THINK_OFF_MARKER_RE.sub(
        "", rendered_prompt
    )
    for marker in THINK_TAG_MARKERS:
        if marker in rendered_without_empty_off_markers:
            raise RuntimeError(
                f"enable_thinking=False was requested but the rendered prompt "
                f"contains non-empty or unbalanced thinking marker {marker!r}. "
                f"The Qwen3 chat template is NOT honoring the thinking-off pin; "
                f"aborting before probe outputs are contaminated. Verify the "
                f"tokenizer chat template and the chat_template_kwargs wiring "
                f"(see backends.py header)."
            )


def assert_no_generated_thinking(text: str, *, question: str, generation_kind: str) -> None:
    """Fail if a model generation contains Qwen3 thinking tags.

    Prompt rendering may contain Qwen3's empty thinking-off marker, but output
    rows must never contain generated reasoning tags. Do not strip and proceed:
    a tag means the runtime/model combination is unsafe for this probe output.
    """
    for marker in THINK_TAG_MARKERS:
        if marker in text:
            question_preview = question.replace("\n", " ")[:120]
            raise RuntimeError(
                f"Qwen3 generated {generation_kind} output containing thinking "
                f"marker {marker!r} for question {question_preview!r}. "
                "Aborting before writing probe rows; do not reuse this partial "
                "run. Verify that tokenizer.apply_chat_template receives "
                "enable_thinking=False for the pinned model, or switch to a "
                "non-thinking Qwen3 instruct variant/vLLM-tokenizer combination."
            )


def assert_no_generated_thinking_batch(
    texts: list[str], *, question: str, generation_kind: str
) -> None:
    for idx, text in enumerate(texts):
        assert_no_generated_thinking(
            text,
            question=question,
            generation_kind=f"{generation_kind}[{idx}]",
        )


class VLLMBackend:
    """Real GPU backend. vLLM imported lazily so this file loads without it."""

    def __init__(self, model_name: str, enable_thinking: bool, system_prompt: str,
                 vllm_opts: dict | None = None):
        # Lazy import: keeps the module importable on CPU-only / no-vLLM hosts.
        from vllm import LLM  # noqa: PLC0415

        self.model_name = model_name
        self.enable_thinking = enable_thinking
        self.system_prompt = system_prompt
        self._chat_template_mode: str | None = None
        opts = vllm_opts or {}
        self.llm = LLM(
            model=model_name,
            dtype=opts.get("dtype", "auto"),
            gpu_memory_utilization=opts.get("gpu_memory_utilization", 0.90),
            max_model_len=opts.get("max_model_len", 2048),
        )
        self.tokenizer = self.llm.get_tokenizer()
        # Verify-on-construct: render one probe-shaped prompt and assert the
        # thinking-off pin holds. First real run fails here if the template
        # ignores enable_thinking, before any question is probed.
        self._self_check_thinking_off()

    def _apply_chat_template(self, messages: list[dict[str, str]], mode: str) -> str:
        template_kwargs = {
            "tokenize": False,
            "add_generation_prompt": True,
        }
        if mode == "chat_template_kwargs":
            template_kwargs["chat_template_kwargs"] = {
                "enable_thinking": self.enable_thinking
            }
        elif mode == "direct":
            template_kwargs["enable_thinking"] = self.enable_thinking
        else:
            raise ValueError(f"unknown chat template mode: {mode!r}")
        return self.tokenizer.apply_chat_template(messages, **template_kwargs)

    def _render_prompt(self, question: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
        ]
        if self.enable_thinking:
            return self._apply_chat_template(messages, "direct")
        if self._chat_template_mode is not None:
            return self._apply_chat_template(messages, self._chat_template_mode)

        failures: list[str] = []
        # We render with the tokenizer and call LLM.generate() on raw prompts,
        # so prefer the direct HF/Jinja kwarg. vLLM's chat_template_kwargs is
        # still tried as a compatibility fallback.
        for mode in ("direct", "chat_template_kwargs"):
            try:
                rendered = self._apply_chat_template(messages, mode)
                assert_no_think_scaffolding(rendered)
            except TypeError as exc:
                failures.append(f"{mode}: tokenizer rejected kwargs ({exc})")
                continue
            except RuntimeError as exc:
                failures.append(f"{mode}: {exc}")
                continue
            self._chat_template_mode = mode
            return rendered

        detail = "; ".join(failures) if failures else "no render attempts made"
        raise RuntimeError(
            "Unable to render a Qwen3 prompt with thinking disabled. Tried both "
            "vLLM chat_template_kwargs={'enable_thinking': False} and direct "
            "enable_thinking=False tokenizer surfaces, but neither produced a "
            f"self-check-clean prompt. Details: {detail}. Install a tokenizer/"
            "vLLM version whose Qwen3 chat template supports thinking-off, or "
            "update the configured model/tokenizer to a non-thinking variant."
        )

    def _self_check_thinking_off(self) -> None:
        if self.enable_thinking:
            return
        rendered = self._render_prompt("Who wrote Paradise Lost?")
        assert_no_think_scaffolding(rendered)

    def _sampling_params(self, n: int, temperature: float, top_p: float,
                         max_new_tokens: int, seed: int):
        from vllm import SamplingParams  # noqa: PLC0415

        return SamplingParams(
            n=n, temperature=temperature, top_p=top_p,
            max_tokens=max_new_tokens, seed=seed,
        )

    def generate_batch(self, question, n_samples, temperature, top_p,
                       max_new_tokens, seed):
        rendered = self._render_prompt(question)
        assert_no_think_scaffolding(rendered)
        params = self._sampling_params(
            n_samples, temperature, top_p, max_new_tokens, seed)
        out = self.llm.generate([rendered], params)
        texts = [o.text for o in out[0].outputs]
        assert_no_generated_thinking_batch(
            texts, question=question, generation_kind="sampled"
        )
        return texts

    def generate_greedy(self, question, max_new_tokens):
        rendered = self._render_prompt(question)
        assert_no_think_scaffolding(rendered)
        params = self._sampling_params(
            1, 0.0, 1.0, max_new_tokens, seed=0)
        out = self.llm.generate([rendered], params)
        text = out[0].outputs[0].text
        assert_no_generated_thinking(
            text, question=question, generation_kind="greedy"
        )
        return text


class StubBackend:
    """Deterministic, GPU-free backend for smoke tests.

    Fabricates generations from a per-question alias table so the probe's
    scoring, labeling, sensitivity, and resumability paths run end to end
    without a model. Determinism comes from hashing (question, sample index,
    seed) into a choice; the same inputs always produce the same outputs, so a
    resumed run reproduces skipped questions exactly.

    The alias table lets a test stage questions the stub will mostly get right
    (-> known), never get right (-> unknown), or sometimes get right
    (-> discard), exercising every band.
    """

    def __init__(self, alias_table: dict[str, list[str]], correct_rate: dict[str, float],
                 wrong_answer: str = "Atlantis", seed: int = 0):
        # alias_table: question -> gold aliases the stub may emit when "correct".
        # correct_rate: question -> probability a given sample is correct.
        self.alias_table = alias_table
        self.correct_rate = correct_rate
        self.wrong_answer = wrong_answer
        self.seed = seed

    def _unit(self, question: str, idx: int) -> float:
        key = f"{self.seed}|{question}|{idx}".encode()
        h = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        return (h % 10_000) / 10_000.0

    def _answer(self, question: str, idx: int) -> str:
        rate = self.correct_rate.get(question, 0.0)
        if self._unit(question, idx) < rate:
            aliases = self.alias_table.get(question, [])
            return aliases[0] if aliases else self.wrong_answer
        return self.wrong_answer

    def generate_batch(self, question, n_samples, temperature, top_p,
                       max_new_tokens, seed):
        return [self._answer(question, i) for i in range(n_samples)]

    def generate_greedy(self, question, max_new_tokens):
        # Greedy is the deterministic "best" decode: correct iff the question's
        # correct_rate is above 0.5 (the stub's notion of a confident answer).
        rate = self.correct_rate.get(question, 0.0)
        if rate >= 0.5:
            aliases = self.alias_table.get(question, [])
            return aliases[0] if aliases else self.wrong_answer
        return self.wrong_answer


def build_backend(config: dict, system_prompt: str) -> ProbeBackend:
    """Construct the configured backend. Stub backends are built by tests."""
    backend = config["runtime"]["backend"]
    if backend == "vllm":
        return VLLMBackend(
            model_name=config["model"]["model_name"],
            enable_thinking=config["model"]["enable_thinking"],
            system_prompt=system_prompt,
            vllm_opts=config["runtime"].get("vllm", {}),
        )
    if backend == "stub":
        raise ValueError(
            "the stub backend is constructed directly by tests with an alias "
            "table, not via build_backend; set runtime.backend=vllm for real runs"
        )
    raise ValueError(f"unknown probe backend: {backend!r}")
