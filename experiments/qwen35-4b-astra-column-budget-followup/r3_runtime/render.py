"""Frozen thinking-scaffold guard; no legacy renderer fallback."""
import re
THINK_TAG_MARKERS = ("<think>", "</think>")
EMPTY_THINK_OFF_MARKER_RE = re.compile(r"<think>\s*</think>")

def assert_no_think_scaffolding(rendered_prompt: str, *, model: str) -> None:
    """Fail if a rendered prompt contains populated/unbalanced thinking
    (enable_thinking=False pin, cell.yaml write.generation.enable_thinking)."""
    without_empty_off_markers = EMPTY_THINK_OFF_MARKER_RE.sub("", rendered_prompt)
    for marker in THINK_TAG_MARKERS:
        if marker in without_empty_off_markers:
            raise RuntimeError(
                f"enable_thinking=False was requested but the prompt rendered "
                f"for model {model!r} contains a non-empty or unbalanced "
                f"thinking marker {marker!r}. The chat template is NOT "
                f"honoring the thinking-off pin; aborting before this cell's "
                f"rows are contaminated."
            )

