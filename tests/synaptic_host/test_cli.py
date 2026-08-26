from __future__ import annotations

from synaptic_host.__main__ import _intent, _parser
from synaptic_host.modal_provider import ModalHostConfigV1


def config():
    return ModalHostConfigV1(
        "main", "modal-a10-v1", "1", "control", "artifacts", "runtime",
        ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        {"PATH": "/opt/conda/bin:/usr/bin"}, 3600, 100, "USD",
    )


def test_cli_exposes_clean_provider_and_training_verbs_only() -> None:
    parser = _parser()
    assert parser.parse_args(["provider", "deploy"]).provider_command == "deploy"
    assert parser.parse_args(["provider", "preflight"]).provider_command == "preflight"
    assert parser.parse_args(["training", "start", "--config", "x.json"]).training_command == "start"
    assert parser.parse_args(["training", "preflight", "--config", "x.json"]).training_command == "preflight"
    assert parser.parse_args(["training", "outcome", "--run-id", "run-1"]).training_command == "outcome"


def test_generated_training_intent_is_unique_and_budget_bounded() -> None:
    first = _intent(config())
    second = _intent(config())
    assert first.run_id != second.run_id
    assert first.effect_id != second.effect_id
    assert first.maximum_cost_minor_units == 100
    assert first.currency == "USD"
    assert first.effect_id.startswith("effect-")
