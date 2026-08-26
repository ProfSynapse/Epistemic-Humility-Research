"""Bootstrap the exact host runtime before importing engine-dependent CLI code."""

from __future__ import annotations

import sys
from pathlib import Path

from .launcher import ensure_and_reexec


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    project_root = Path(__file__).resolve().parents[1]
    engine_root = project_root / "synaptic-tuner"
    child = ensure_and_reexec(
        project_root=project_root,
        engine_root=engine_root,
        argv=arguments,
    )
    if child is not None:
        return child

    from .cli import main as cli_main

    return cli_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
