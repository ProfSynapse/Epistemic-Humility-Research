"""Canonical training inputs and planning through the public v1 API only."""

from __future__ import annotations

from pathlib import Path
from synaptic_tuner.api.v1 import ProviderRef, TrainingAPI, TrainingInputV1


def load_training_input(path: Path) -> TrainingInputV1:
    """Validate the actual engine contract; do not translate historical recipes."""
    path = Path(path)
    if path.stat().st_size > 65536:
        raise ValueError("training input exceeds the public contract byte limit")
    return TrainingInputV1.from_json(path.read_text(encoding="utf-8"))


def plan_training(api: TrainingAPI, request: TrainingInputV1, provider: ProviderRef):
    """Plan using caller-composed operations; never start or grant a run here."""
    if type(api) is not TrainingAPI or type(request) is not TrainingInputV1:
        raise TypeError("exact public TrainingAPI and TrainingInputV1 required")
    if type(provider) is not ProviderRef:
        raise TypeError("exact public ProviderRef required")
    loaded = api.load(request.canonical_json())
    resolved = api.resolve(loaded)
    return api.plan(resolved, provider)
