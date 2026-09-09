"""Single lazy Modal SDK import boundary for native Host consumers."""

from __future__ import annotations

import importlib


def load_modal_sdk() -> object:
    """Load the SDK only when a consumer has admitted its operation."""
    return importlib.import_module("modal")
