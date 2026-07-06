"""Example project render function for a tuner mechinterp cell.

NOT a registered instrument. Teaching companion to the example cell.

Contract (see synaptic-tuner/docs/MECH_INTERP_CELLS.md, "Plug-in points"):

    render(row: dict) -> str          # a prompt string; apply your chat template here

The steer and extract verbs call the render function per row to build the prompt
that is tokenized and generated over. Resolved via importlib against sys.path,
so keep the graders/renders dirs on PYTHONPATH:

    PYTHONPATH=experiment/phase1/probe/graders:experiment/phase1/probe/renders

A real render for this research line would apply the checkpoint's chat template
(the frozen harness does this in steering_common.py). This example keeps it to a
minimal user-turn wrap so the contract is legible.
"""

from __future__ import annotations


def render(row: dict) -> str:
    """Map one input row to a prompt string."""
    question = str(row.get("prompt", row.get("question", ""))).strip()
    # Minimal chat-style wrap. Replace with tokenizer.apply_chat_template(...) for
    # a real checkpoint so the rendered prompt matches training-time formatting.
    return f"User: {question}\nAssistant:"
