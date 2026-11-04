"""Generate the ``mechinterp-pipeline/v1`` plan for this cell.

Default: every engine invocation is a ``command`` stage running this package's
CLI (which calls the engine through the host ``EngineCLI`` under budget and
hash gates). Native static execution is refused because it bypasses the ledger.

``--model`` is passed to the engine as a plain local path because engine
1.1.0rc1 does not resolve ``artifact://`` in ``--model``.
"""

from __future__ import annotations

from .config import Cell, Layout
from . import jobs as J
from .util import HarnessError

CLI = ["-m", "hs20_nwe"]


def _cmd(python: str, *args: str) -> list[str]:
    flags = [a for a in args if a == "--gpu-ack"]
    return [python, *CLI, *flags, *(a for a in args if a != "--gpu-ack")]


def build(cell: Cell, layout: Layout, *, python: str = "python", native_static: bool = False,
          gpu_ack_flag: bool = True) -> dict:
    gpu = ["--gpu-ack"] if gpu_ack_flag else []
    if native_static:
        raise HarnessError("BUDGET_BYPASS", "native static execution bypasses the registered ledger and is not admitted")
    model = J.model_path(layout)
    stages: list[dict] = []

    def command(name: str, *args: str) -> None:
        stages.append({"name": name, "kind": "command", "command": _cmd(python, *args)})

    command("materialize", "materialize")
    command("check_binding", "stage", "check-binding")
    command("emit_static", "stage", "emit-static")
    command("extract_fit_l", "stage", "extract-fit-l", *gpu)
    command("inspect", "stage", "inspect")
    command("localize", "stage", "localize")
    command("propose", "stage", "propose")
    command("gen_static", "stage", "gen-static", *gpu)
    command("gen_screen_candidates", "stage", "gen-screen-candidates", *gpu)
    command("select", "stage", "select")
    command("controls", "stage", "controls")
    command("export_selected", "stage", "export")
    command("verify_selected", "stage", "verify-selected", *gpu)
    command("extract_heldout", "stage", "extract-heldout", *gpu)
    command("gen_heldout", "stage", "gen-heldout", *gpu)
    command("build_pool", "stage", "build-pool")
    return {
        "schema_version": "mechinterp-pipeline/v1",
        "name": cell.slug,
        "model": model,
        "model_revision": cell.revision,
        "runtime": {"provider": "local", "python": python, "workdir": ".",
                    "pythonpath": [f"project://experiments/{cell.slug}"],
                    "env": {"HS20NWE_RENDER_MODEL": model, "PYTHONHASHSEED": "0"}},
        "stages": stages,
    }
