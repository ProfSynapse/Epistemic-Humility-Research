"""Engine configs and the registry of generation jobs.

Every generation is a ``steer`` (activation arms and plain forward) or
``dose-calibrate`` (u_d clamps) config, written under the private artifact tree
with ``artifact://`` / ``project://`` references only.  The base model is
referenced for the engine CLI as a plain local path (``--model`` is not
path-reference-resolved by engine 1.1.0rc1; see report).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Cell, Layout
from .util import HarnessError, read_jsonl, sha256_file, write_yaml

RENDER_FN = "hs20_nwe.render:render"


def direction_ref(cell: Cell, name: str) -> str:
    return f"{cell.cell['writer']['direction_root'].rstrip('/')}/{name}.json"


def generation_block(cell: Cell) -> dict:
    g = cell.cell["generation"]
    if g["do_sample"] or g["num_beams"] != 1 or g["thinking"]:
        raise HarnessError("GENERATION", "cell.yaml generation law must be greedy, single beam, thinking off")
    return {"max_new_tokens": int(g["max_new_tokens"]), "min_new_tokens": int(g["min_new_tokens"]),
            "do_sample": False, "seed": 0, "extra_eos_tokens": ["<|im_end|>"]}


def law_block(cell: Cell, readout: str) -> dict:
    if cell.cell["writer"]["reference_position"] != "anchor_onward":
        raise HarnessError("LAW", "reference position must be anchor_onward")
    return {"kind": "erase_write", "readout": readout, "layer": int(cell.cell["sensor"]["decoder_block"]),
            "position": "anchor_onward", "generation_mode": "gen_stream"}


def extract_config(cell: Cell, layout: Layout, *, rows_rel: str, out_rel: str, with_sites: bool) -> dict:
    cfg = {
        "rows_path": layout.ref(rows_rel, shared=True), "output_dir": layout.ref(out_rel),
        "families": ["anchor"], "layers": [int(cell.cell["sensor"]["hidden_state"])],
        "render_fn": RENDER_FN, "use_cache": bool(cell.cell["generation"]["use_cache"]),
        "forward_only": True, "resume": True,
    }
    if with_sites:
        cfg["capture_sites"] = [{"layer": int(b), "module": "mlp.down_proj", "tensor": "input"}
                                for b in cell.cell["candidates"]["blocks"]]
    return cfg


@dataclass
class Job:
    job_id: str
    kind: str                      # steer | dose-calibrate
    config_rel: str
    output_rel: str
    rows_rel: str
    n_rows: int
    n_passes: int = 1              # arms (steer) or doses (dose-calibrate)
    patch_rel: str | None = None   # spec path (relative artifact path) when a weight patch is applied
    patch_sha256: str | None = None
    meta: dict = field(default_factory=dict)

    @property
    def planned_rows(self) -> int:
        return self.n_rows * self.n_passes


def _surface(cell: Cell, layout: Layout, rows_rel: str, patch: dict | None) -> dict:
    surface = {"rows_path": layout.ref(rows_rel, shared=True), "generation": generation_block(cell), "seed": 0}
    if patch:
        surface["weight_patch"] = patch
    return surface


def _execution(cell: Cell, layout: Layout, output_rel: str, *, summary_rel: str | None = None,
               batch_size: int | None = None) -> dict:
    ex = {"output_path": layout.ref(output_rel), "resume": True, "render_fn": RENDER_FN,
          "batch_size": int(batch_size or cell.cell["generation"]["batch_size"])}
    if summary_rel:
        ex["summary_path"] = layout.ref(summary_rel)
    return ex


def steer_config(cell: Cell, layout: Layout, *, rows_rel: str, output_rel: str, arm: dict,
                 readout: str, patch: dict | None, batch_size: int | None = None) -> dict:
    return {
        "surface": _surface(cell, layout, rows_rel, patch),
        "readouts": [{"name": readout, "path": direction_ref(cell, readout)}],
        "law": law_block(cell, readout),
        "arms": [arm],
        "execution": _execution(cell, layout, output_rel, batch_size=batch_size),
    }


def dose_config(cell: Cell, layout: Layout, *, rows_rel: str, output_rel: str, summary_rel: str,
                setpoint: float, patch: dict | None) -> dict:
    return {
        "surface": _surface(cell, layout, rows_rel, patch),
        "readouts": [{"name": "u_d", "path": direction_ref(cell, "u_d")}],
        "law": law_block(cell, "u_d"),
        "calibration": {"doses": [float(setpoint)], "dose_kind": "setpoint", "selection": {}},
        "execution": _execution(cell, layout, output_rel, summary_rel=summary_rel),
    }


ZERO_ARM = {"name": "baseline", "strength": 0.0}


def controller_arm(cell: Cell) -> dict:
    return {"name": "controller", "strength": cell.controller_strength, "flag_field": "fire"}


def make_job(cell: Cell, layout: Layout, job_id: str, *, rows_rel: str, n_rows: int, patch_rel: str | None = None,
             kind: str = "steer", arm: dict | None = None, readout: str = "c_hat",
             setpoint: float | None = None, meta: dict | None = None, batch_size: int | None = None) -> Job:
    """Write the config for one job and return its registry entry."""
    patch = None
    patch_sha = None
    if patch_rel:
        patch_sha = sha256_file(layout.local(patch_rel, shared=True))
        patch = {"path": layout.ref(patch_rel, shared=True), "sha256": patch_sha}
    output_rel = f"runlog/{job_id}.jsonl"
    config_rel = f"configs/{job_id}.yaml"
    if kind == "steer":
        cfg = steer_config(cell, layout, rows_rel=rows_rel, output_rel=output_rel, arm=arm or ZERO_ARM,
                           readout=readout, patch=patch, batch_size=batch_size)
    else:
        cfg = dose_config(cell, layout, rows_rel=rows_rel, output_rel=output_rel,
                          summary_rel=f"runlog/{job_id}.summary.json", setpoint=float(setpoint), patch=patch)
    write_yaml(layout.local(config_rel), cfg)
    return Job(job_id, kind, config_rel, output_rel, rows_rel, n_rows, 1, patch_rel, patch_sha, meta or {})


def _n(layout: Layout, rows_rel: str) -> int:
    return len(read_jsonl(layout.local(rows_rel, shared=True)))


def static_jobs(cell: Cell, layout: Layout) -> list[Job]:
    """Decoy and FIT-screen baseline jobs: need only the materialized rows."""
    return [
        make_job(cell, layout, "decoy_baseline", rows_rel="materialize/decoy.jsonl",
                 n_rows=_n(layout, "materialize/decoy.jsonl"), meta={"role": "decoy"}),
        make_job(cell, layout, "screen_baseline", rows_rel="materialize/fit_screen.jsonl",
                 n_rows=_n(layout, "materialize/fit_screen.jsonl"), meta={"role": "screen"}),
    ]


def screen_candidate_job(cell: Cell, layout: Layout, cand_id: str) -> Job:
    return make_job(cell, layout, f"screen_{cand_id}", rows_rel="materialize/fit_screen.jsonl",
                    n_rows=_n(layout, "materialize/fit_screen.jsonl"),
                    patch_rel=f"patches/{cand_id}/spec.yaml", meta={"role": "screen", "candidate": cand_id})


HELDOUT_ROWS = "materialize/heldout_sensor.jsonl"
HELDOUT_CONFAB_ROWS = "materialize/heldout_sensor_confab.jsonl"
HELDOUT_KNOWN_ROWS = "materialize/heldout_sensor_known.jsonl"


def heldout_jobs(cell: Cell, layout: Layout, *, selected_spec_rel: str,
                 control_spec_rels: dict[int, str]) -> list[Job]:
    n = _n(layout, HELDOUT_ROWS)
    jobs = [
        make_job(cell, layout, "heldout_untouched", rows_rel=HELDOUT_ROWS, n_rows=n, meta={"arm": "untouched"}),
        make_job(cell, layout, "heldout_native", rows_rel=HELDOUT_ROWS, n_rows=n, patch_rel=selected_spec_rel,
                 meta={"arm": "native"}),
        make_job(cell, layout, "heldout_controller", rows_rel=HELDOUT_ROWS, n_rows=n, arm=controller_arm(cell),
                 meta={"arm": "controller"}),
    ]
    for seed, rel in sorted(control_spec_rels.items()):
        jobs.append(make_job(cell, layout, f"heldout_random_{seed}", rows_rel=HELDOUT_ROWS, n_rows=n,
                             patch_rel=rel, meta={"arm": f"random_{seed}", "seed": seed}))
    return jobs


def clamp_jobs(cell: Cell, layout: Layout, *, selected_spec_rel: str) -> list[Job]:
    nc, nk = _n(layout, HELDOUT_CONFAB_ROWS), _n(layout, HELDOUT_KNOWN_ROWS)
    jobs = []
    for weight, patch in (("untouched", None), ("native", selected_spec_rel)):
        for clamp, rows_rel, n in (("known", HELDOUT_CONFAB_ROWS, nc), ("unknown", HELDOUT_KNOWN_ROWS, nk)):
            jobs.append(make_job(cell, layout, f"clamp_{clamp}_{weight}", rows_rel=rows_rel, n_rows=n,
                                 patch_rel=patch, kind="dose-calibrate", readout="u_d",
                                 setpoint=cell.clamp_setpoint(clamp),
                                 meta={"arm": f"clamp_{clamp}", "weight": weight, "clamp": clamp}))
    return jobs


def engine_args(job: Job, layout: Layout, model_path_: str, revision: str) -> list[str]:
    verb = "steer" if job.kind == "steer" else "dose-calibrate"
    model_path_ = job.meta.get("model_path") or model_path_
    return [verb, "--mi-config", layout.ref(job.config_rel), "--model", model_path_, "--model-revision", revision]


def model_path(layout: Layout) -> str:
    """Absolute local path of the staged base model, strictly inside the artifact tree."""
    return str(layout.local("base_model", shared=True))
