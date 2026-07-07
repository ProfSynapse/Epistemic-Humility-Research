"""Modal wrapper for AQ answer-sycophancy row-pool smoke.

This first AQ cloud stage runs live vLLM generation/scoring for the small
official-Qwen answer-sycophancy slice, then builds:

  - experiments/aq-sycophancy-activation-actuator/analysis/row_pool.jsonl
  - experiments/aq-sycophancy-activation-actuator/analysis/probe_fit_labels.jsonl

Launch shape after the branch is pushed and a commit is supplied:

    modal run --detach experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py --repo-commit=<sha>

Dry-run remains import-light:

    python experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path


try:  # Keep local dry-run and py_compile usable before Modal is installed.
    import modal
except Exception:  # pragma: no cover - exercised on hosts without modal
    modal = None  # type: ignore[assignment]


RUN_TAG = "aq-sycophancy-actuator-smoke-r1"
APP_NAME = "eh-aq-sycophancy-smoke"
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
DEFAULT_REPO_COMMIT = "REPLACE_WITH_PUSHED_AQ_COMMIT"
MODEL_REPO = "Qwen/Qwen3-4B"
MODEL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
STAGING_REPO = "professorsynapse/eh-al-prep-staging"
EXP_DIR = "experiments/aq-sycophancy-activation-actuator"
EVAL_CONFIG = f"{EXP_DIR}/eval_16bit_sycophancy_answer.yaml"
RESULTS_DIR = "experiment/phase1/eval/results_aq_sycophancy_answer_16bit"
ANALYSIS_DIR = f"{EXP_DIR}/analysis"
ROW_POOL_OUT = f"{ANALYSIS_DIR}/row_pool.jsonl"
LABELS_OUT = f"{ANALYSIS_DIR}/probe_fit_labels.jsonl"
ROW_POOL_SUMMARY = f"{ANALYSIS_DIR}/row_pool_summary.json"
SYC_ANALYSIS_DIR = f"{ANALYSIS_DIR}/sycophancy_answer_analysis"
ARM_NAME = "qwen3_4b_official_bf16"
EVAL_SET = "sycophancy_answer"
VLLM_IMAGE = "vllm/vllm-openai:v0.17.1"
VLLM_DIST_PACKAGES = "/usr/local/lib/python3.12/dist-packages"
PIP_DEPS = [
    "huggingface_hub>=0.34,<1.0",
    "pyyaml",
    "scipy",
    "scikit-learn",
    "safetensors",
]
HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120
ASSUMED_A10G_USD_PER_HOUR = 1.10


def local_repo_commit() -> str:
    root = Path(__file__).resolve().parents[3]
    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={root.as_posix()}", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def build_spec(repo_commit: str, cost_cap_usd: float | None) -> dict:
    timeout_hours = None
    if cost_cap_usd is not None:
        timeout_hours = round(cost_cap_usd / ASSUMED_A10G_USD_PER_HOUR, 2)
    blocked = repo_commit.startswith("REPLACE_WITH")
    return {
        "app": APP_NAME,
        "run_tag": RUN_TAG,
        "repo_url": REPO_URL,
        "repo_commit": repo_commit,
        "local_head": local_repo_commit(),
        "repo_commit_requirement": "must be a pushed AQ branch commit carrying this wrapper and build_aq_row_pool.py",
        "lane": "modal-a10g",
        "image": VLLM_IMAGE,
        "model_repo": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "staging_repo": STAGING_REPO,
        "eval_config": EVAL_CONFIG,
        "results_dir": RESULTS_DIR,
        "row_pool_out": ROW_POOL_OUT,
        "labels_out": LABELS_OUT,
        "env": {
            "HF_HUB_DISABLE_XET": "1",
            "HF_HUB_ENABLE_HF_TRANSFER": "0",
        },
        "cost_cap_usd": cost_cap_usd,
        "derived_timeout_hours": timeout_hours,
        "status": "BLOCKED_UNPINNED_REPO_COMMIT" if blocked else "READY_FOR_MODAL_SUBMIT",
    }


if modal is not None:
    image = (
        modal.Image.from_registry(VLLM_IMAGE, add_python="3.12")
        .entrypoint([])
        .run_commands("python3 -m pip install " + " ".join(shlex.quote(dep) for dep in PIP_DEPS))
        .run_commands(f"PYTHONPATH={VLLM_DIST_PACKAGES} python3 -c 'import vllm; print(vllm.__version__)'")
        .apt_install("git")
        .env({
            "HF_HUB_DISABLE_XET": "1",
            "HF_HUB_ENABLE_HF_TRANSFER": "0",
            "PYTHONPATH": VLLM_DIST_PACKAGES,
        })
    )

    app = modal.App(APP_NAME, image=image)
    vol = modal.Volume.from_name("eh-aq-sycophancy-smoke-logs", create_if_missing=True)
    VOL_MOUNT = "/vol/aqlogs"
    CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"

    @app.function(
        gpu="A10G",
        timeout=3 * HOURS,
        volumes={VOL_MOUNT: vol},
        secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
        retries=modal.Retries(max_retries=3, backoff_coefficient=1.0, initial_delay=10.0),
    )
    def run_aq_smoke(repo_commit: str) -> dict:
        import shutil
        import threading
        import time

        if repo_commit.startswith("REPLACE_WITH"):
            raise RuntimeError("repo_commit is a placeholder; pass --repo-commit=<pushed sha>")

        os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        os.environ["PYTHONPATH"] = VLLM_DIST_PACKAGES
        workspace = "/workspace/ehr"

        def sh(cmd: list[str], cwd: str | None = None, check: bool = True) -> int:
            printable = " ".join(cmd)
            print(f"[modal-aq] $ {printable}", flush=True)
            result = subprocess.run(cmd, cwd=cwd)
            if check and result.returncode != 0:
                raise RuntimeError(f"command failed ({result.returncode}): {printable}")
            return result.returncode

        out = f"/tmp/{RUN_TAG}"
        os.makedirs(out, exist_ok=True)
        ckpt_data = f"{CKPT}/data"

        def copy_tree_into(src: str, dst: str) -> int:
            n = 0
            if not os.path.isdir(src):
                return 0
            for root, _dirs, files in os.walk(src):
                rel = os.path.relpath(root, src)
                target_dir = dst if rel == "." else os.path.join(dst, rel)
                os.makedirs(target_dir, exist_ok=True)
                for filename in files:
                    shutil.copyfile(os.path.join(root, filename), os.path.join(target_dir, filename))
                    n += 1
            return n

        try:
            vol.reload()
        except Exception as exc:  # noqa: BLE001
            print(f"[modal-aq] vol.reload() failed at restore (non-fatal): {exc}", flush=True)

        if not os.path.isdir(os.path.join(workspace, ".git")):
            sh(["git", "clone", REPO_URL, workspace])
        sh(["git", "fetch", "origin"], cwd=workspace, check=False)
        sh(["git", "checkout", repo_commit], cwd=workspace)

        restored = copy_tree_into(ckpt_data, workspace) if os.path.isdir(ckpt_data) else 0
        print(f"[modal-aq] restored {restored} files from checkpoint", flush=True)

        def mirror_file(src: str, dst_root: str) -> None:
            if not os.path.isfile(src):
                return
            rel = os.path.relpath(src, workspace)
            dst = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            tmp = dst + ".tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)

        def checkpoint_once(tag: str = "") -> None:
            try:
                for rel in (
                    f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/generations.jsonl",
                    f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/scored_rows.jsonl",
                    f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/metrics.json",
                    f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/bootstrap_ci.json",
                    f"{RESULTS_DIR}/comparisons/summary_table.csv",
                    f"{SYC_ANALYSIS_DIR}/summary.json",
                    f"{SYC_ANALYSIS_DIR}/sycophancy_answer_summary.csv",
                    f"{SYC_ANALYSIS_DIR}/sycophancy_answer_pairs.jsonl",
                    ROW_POOL_OUT,
                    LABELS_OUT,
                    ROW_POOL_SUMMARY,
                ):
                    mirror_file(os.path.join(workspace, rel), ckpt_data)
                vol.commit()
                print(f"[modal-aq] checkpoint committed {tag}".rstrip(), flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[modal-aq] checkpoint FAILED (non-fatal) {tag}: {exc}", flush=True)

        stop_ckpt = threading.Event()

        def checkpoint_loop() -> None:
            while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
                checkpoint_once("(periodic)")

        thread = threading.Thread(target=checkpoint_loop, daemon=True)
        thread.start()

        try:
            sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], check=False)
            sh([
                "python3",
                "experiment/phase1/eval/run_eval.py",
                "--config",
                EVAL_CONFIG,
                "--live-vllm",
            ], cwd=workspace)
            checkpoint_once("(post-eval)")

            sh([
                "python3",
                "experiment/phase1/eval/analysis/sycophancy_answer_analysis.py",
                "--results-dir",
                RESULTS_DIR,
                "--output-root",
                SYC_ANALYSIS_DIR,
            ], cwd=workspace)
            sh([
                "python3",
                f"{EXP_DIR}/build_aq_row_pool.py",
                "--results-dir",
                RESULTS_DIR,
                "--row-pool-out",
                ROW_POOL_OUT,
                "--labels-out",
                LABELS_OUT,
                "--summary-out",
                ROW_POOL_SUMMARY,
            ], cwd=workspace)
            checkpoint_once("(post-row-pool)")

            upload = "experiment/phase1/probe/cloud/upload_result.py"
            artifact_files = [
                f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/generations.jsonl",
                f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/scored_rows.jsonl",
                f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/metrics.json",
                f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/bootstrap_ci.json",
                f"{RESULTS_DIR}/comparisons/summary_table.csv",
                f"{SYC_ANALYSIS_DIR}/summary.json",
                f"{SYC_ANALYSIS_DIR}/sycophancy_answer_summary.csv",
                f"{SYC_ANALYSIS_DIR}/sycophancy_answer_pairs.jsonl",
                ROW_POOL_OUT,
                LABELS_OUT,
                ROW_POOL_SUMMARY,
            ]
            upload_cmd = [
                "python3",
                upload,
                "--repo",
                STAGING_REPO,
                "--path-prefix",
                f"{RUN_TAG}/artifacts",
            ]
            for rel in artifact_files:
                upload_cmd.extend(["--file", os.path.join(workspace, rel)])
            sh(upload_cmd, cwd=workspace)

            done = f"{CKPT}/DONE"
            os.makedirs(os.path.dirname(done), exist_ok=True)
            with open(done, "w", encoding="utf-8") as fh:
                fh.write(f"repo_commit={repo_commit}\nrun_tag={RUN_TAG}\n")
            vol.commit()
            return {
                "ok": True,
                "run_tag": RUN_TAG,
                "repo_commit": repo_commit,
                "staging_repo": STAGING_REPO,
                "artifact_prefix": f"{RUN_TAG}/artifacts",
            }
        finally:
            stop_ckpt.set()
            thread.join(timeout=30)
            checkpoint_once("(final)")

    @app.local_entrypoint()
    def modal_entrypoint(
        dry_run: bool = False,
        repo_commit: str = DEFAULT_REPO_COMMIT,
        cost_cap_usd: float = 10.0,
    ) -> None:
        spec = build_spec(repo_commit, cost_cap_usd)
        print(json.dumps(spec, indent=2, sort_keys=True))
        if dry_run:
            return
        if repo_commit.startswith("REPLACE_WITH"):
            raise SystemExit("Pass --repo-commit=<pushed AQ branch sha> before launching paid Modal work.")
        call = run_aq_smoke.spawn(repo_commit)
        print(f"spawned {call.object_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo-commit", default=DEFAULT_REPO_COMMIT)
    parser.add_argument("--cost-cap-usd", type=float, default=float(os.environ.get("MODAL_COST_CAP_USD", "10")))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build_spec(args.repo_commit, args.cost_cap_usd), indent=2, sort_keys=True))
    if args.dry_run:
        return 0
    raise SystemExit("Use `modal run --detach ... --repo-commit=<pushed sha>` for real submission.")


if __name__ == "__main__":
    raise SystemExit(main())
