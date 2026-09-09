"""Read the selected local Modal login without constructing a provider client."""

from __future__ import annotations

import contextlib
import importlib
import io
import unicodedata
from collections.abc import Mapping

from . import modal_sdk


def _valid_pair(pair: tuple[object, object]) -> bool:
    try:
        return all(
            type(value) is str and value.strip() and len(value.encode("utf-8")) <= 4096
            and not any(unicodedata.category(char).startswith("C") for char in value)
            for value in pair
        )
    except (UnicodeError, ValueError):
        return False


def select_modal_credentials(
    environment: Mapping[str, str], *, allow_saved: bool,
) -> tuple[str, str] | None:
    """Prefer explicit credentials; never fall back from any explicit name.

    The parent launcher disables saved-login access. Verified native consumers
    may enable it; selection itself never constructs a provider client.
    """
    names = ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET")
    if any(name in environment for name in names):
        pair = (environment.get(names[0]), environment.get(names[1]))
        return pair if _valid_pair(pair) else None
    return saved_modal_credentials() if allow_saved else None


def saved_modal_credentials() -> tuple[str, str] | None:
    """Return one complete saved-profile pair, or a closed refusal.

    Called only after the isolated runtime proof is validated. Never called
    when the operator supplied either credential environment variable: an
    incomplete explicit pair must not silently select another account.
    No token setup, workspace lookup, credential file write or client creation.
    """
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sdk = modal_sdk.load_modal_sdk()
            if sdk.__version__ != "1.5.4":
                return None
            config = importlib.import_module("modal.config").config
            pair = tuple(config.get(key, use_env=False) for key in ("token_id", "token_secret"))
            if not _valid_pair(pair):
                return None
            return pair
    except Exception:
        return None
