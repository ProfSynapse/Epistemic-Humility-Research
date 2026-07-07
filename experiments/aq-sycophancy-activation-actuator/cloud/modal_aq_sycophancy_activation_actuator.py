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
READOUT_RUN_TAG = "aq-sycophancy-readout-r1"
APP_NAME = "eh-aq-sycophancy-smoke"
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
DEFAULT_REPO_COMMIT = "REPLACE_WITH_PUSHED_AQ_COMMIT"
MODEL_REPO = "Qwen/Qwen3-4B"
MODEL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"
STAGING_REPO = "professorsynapse/eh-al-prep-staging"
HF_SECRET_NAME = "hf-token"
EXP_DIR = "experiments/aq-sycophancy-activation-actuator"
EVAL_CONFIG = f"{EXP_DIR}/eval_16bit_sycophancy_answer.yaml"
RESULTS_DIR = "experiment/phase1/eval/results_aq_sycophancy_answer_16bit"
ANALYSIS_DIR = f"{EXP_DIR}/analysis"
ROW_POOL_OUT = f"{ANALYSIS_DIR}/row_pool.jsonl"
LABELS_OUT = f"{ANALYSIS_DIR}/probe_fit_labels.jsonl"
ROW_POOL_SUMMARY = f"{ANALYSIS_DIR}/row_pool_summary.json"
SYC_ANALYSIS_DIR = f"{ANALYSIS_DIR}/sycophancy_answer_analysis"
EXTRACTION_DIR = f"{ANALYSIS_DIR}/extraction"
DIRECTION_OUT = f"{EXP_DIR}/directions/sycophancy_answer_direction.json"
ARM_NAME = "qwen3_4b_official_bf16"
EVAL_SET = "sycophancy_answer"
ARTIFACT_FILES = [
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
OPTIONAL_ARTIFACT_FILES = [
    f"{RESULTS_DIR}/{ARM_NAME}__{EVAL_SET}/generations.jsonl",
]
REQUIRED_ARTIFACT_FILES = [rel for rel in ARTIFACT_FILES if rel not in OPTIONAL_ARTIFACT_FILES]
VLLM_IMAGE = "vllm/vllm-openai:v0.17.1"
VLLM_DIST_PACKAGES = "/usr/local/lib/python3.12/dist-packages"
PIP_DEPS = [
    "asciimatics",
    "huggingface_hub>=0.34,<1.0",
    "pandas",
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
        "readout_run_tag": READOUT_RUN_TAG,
        "repo_url": REPO_URL,
        "repo_commit": repo_commit,
        "local_head": local_repo_commit(),
        "repo_commit_requirement": "must be a pushed AQ branch commit carrying this wrapper and build_aq_row_pool.py",
        "lane": "modal-a10g",
        "image": VLLM_IMAGE,
        "model_repo": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "staging_repo": STAGING_REPO,
        "hf_secret_name": HF_SECRET_NAME,
        "eval_config": EVAL_CONFIG,
        "results_dir": RESULTS_DIR,
        "row_pool_out": ROW_POOL_OUT,
        "labels_out": LABELS_OUT,
        "extraction_dir": EXTRACTION_DIR,
        "direction_out": DIRECTION_OUT,
        "env": {
            "HF_HUB_DISABLE_XET": "1",
            "HF_HUB_ENABLE_HF_TRANSFER": "0",
        },
        "cost_cap_usd": cost_cap_usd,
        "derived_timeout_hours": timeout_hours,
        "status": "BLOCKED_UNPINNED_REPO_COMMIT" if blocked else "READY_FOR_MODAL_SUBMIT",
    }


def existing_artifacts(workspace: str) -> list[str]:
    return [rel for rel in ARTIFACT_FILES if os.path.isfile(os.path.join(workspace, rel))]


def missing_required_artifacts(workspace: str) -> list[str]:
    return [rel for rel in REQUIRED_ARTIFACT_FILES if not os.path.isfile(os.path.join(workspace, rel))]


def build_upload_cmd(workspace: str, artifact_files: list[str]) -> list[str]:
    upload_cmd = [
        "python3",
        "experiment/phase1/probe/cloud/upload_result.py",
        "--repo",
        STAGING_REPO,
        "--path-prefix",
        f"{RUN_TAG}/artifacts",
    ]
    for rel in artifact_files:
        upload_cmd.extend(["--file", os.path.join(workspace, rel)])
    return upload_cmd


def upload_tree_to_hf(repo_id: str, path_prefix: str, root: str, *, base_dir: str) -> None:
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    if os.path.isfile(root):
        rel = os.path.relpath(root, base_dir).replace(os.sep, "/")
        remote_path = f"{path_prefix}/{rel}"
        api.upload_file(
            path_or_fileobj=root,
            path_in_repo=remote_path,
            repo_id=repo_id,
            repo_type="dataset",
        )
        print(f"[modal-aq] uploaded {root} -> {repo_id}:{remote_path}", flush=True)
        return
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            local_path = os.path.join(dirpath, filename)
            rel = os.path.relpath(local_path, base_dir).replace(os.sep, "/")
            remote_path = f"{path_prefix}/{rel}"
            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=remote_path,
                repo_id=repo_id,
                repo_type="dataset",
            )
            print(f"[modal-aq] uploaded {local_path} -> {repo_id}:{remote_path}", flush=True)


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
    READOUT_CKPT = f"{VOL_MOUNT}/ckpt/{READOUT_RUN_TAG}"

    @app.function(
        gpu="A10G",
        timeout=3 * HOURS,
        volumes={VOL_MOUNT: vol},
        secrets=[modal.Secret.from_name(HF_SECRET_NAME)],
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
                for rel in ARTIFACT_FILES:
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

            missing = missing_required_artifacts(workspace)
            if missing:
                raise RuntimeError(f"missing required upload artifacts: {missing}")
            upload_files = existing_artifacts(workspace)
            skipped = [rel for rel in OPTIONAL_ARTIFACT_FILES if rel not in upload_files]
            if skipped:
                print(f"[modal-aq] optional artifacts absent, skipping upload: {skipped}", flush=True)
            sh(build_upload_cmd(workspace, upload_files), cwd=workspace)

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

    @app.function(
        timeout=30 * 60,
        volumes={VOL_MOUNT: vol},
        secrets=[modal.Secret.from_name(HF_SECRET_NAME)],
        retries=modal.Retries(max_retries=1, backoff_coefficient=1.0, initial_delay=10.0),
    )
    def upload_aq_checkpoint(repo_commit: str) -> dict:
        import shutil

        if repo_commit.startswith("REPLACE_WITH"):
            raise RuntimeError("repo_commit is a placeholder; pass --repo-commit=<pushed sha>")

        os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        workspace = "/workspace/ehr-upload"
        ckpt_data = f"{CKPT}/data"

        def sh(cmd: list[str], cwd: str | None = None, check: bool = True) -> int:
            printable = " ".join(cmd)
            print(f"[modal-aq-upload] $ {printable}", flush=True)
            result = subprocess.run(cmd, cwd=cwd)
            if check and result.returncode != 0:
                raise RuntimeError(f"command failed ({result.returncode}): {printable}")
            return result.returncode

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
            print(f"[modal-aq-upload] vol.reload() failed at restore (non-fatal): {exc}", flush=True)

        if not os.path.isdir(os.path.join(workspace, ".git")):
            sh(["git", "clone", REPO_URL, workspace])
        sh(["git", "fetch", "origin"], cwd=workspace, check=False)
        sh(["git", "checkout", repo_commit], cwd=workspace)

        restored = copy_tree_into(ckpt_data, workspace)
        print(f"[modal-aq-upload] restored {restored} files from checkpoint", flush=True)
        missing = missing_required_artifacts(workspace)
        if missing:
            raise RuntimeError(f"checkpoint missing upload artifacts: {missing}")
        upload_files = existing_artifacts(workspace)
        skipped = [rel for rel in OPTIONAL_ARTIFACT_FILES if rel not in upload_files]
        if skipped:
            print(f"[modal-aq-upload] optional artifacts absent, skipping upload: {skipped}", flush=True)

        sh(build_upload_cmd(workspace, upload_files), cwd=workspace)
        done = f"{CKPT}/DONE"
        os.makedirs(os.path.dirname(done), exist_ok=True)
        with open(done, "w", encoding="utf-8") as fh:
            fh.write(f"repo_commit={repo_commit}\nrun_tag={RUN_TAG}\nupload_only=true\n")
        vol.commit()
        return {
            "ok": True,
            "mode": "upload_only",
            "run_tag": RUN_TAG,
            "repo_commit": repo_commit,
            "staging_repo": STAGING_REPO,
            "artifact_prefix": f"{RUN_TAG}/artifacts",
        }

    @app.function(
        gpu="A10G",
        timeout=3 * HOURS,
        volumes={VOL_MOUNT: vol},
        secrets=[modal.Secret.from_name(HF_SECRET_NAME)],
        retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
    )
    def run_aq_readout(repo_commit: str) -> dict:
        import shutil

        if repo_commit.startswith("REPLACE_WITH"):
            raise RuntimeError("repo_commit is a placeholder; pass --repo-commit=<pushed sha>")

        os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        os.environ["PYTHONPATH"] = f"{EXP_DIR}:{VLLM_DIST_PACKAGES}"

        workspace = "/workspace/ehr-readout"
        ckpt_data = f"{READOUT_CKPT}/data"

        def sh(cmd: list[str], cwd: str | None = None, check: bool = True) -> int:
            printable = " ".join(cmd)
            print(f"[modal-aq-readout] $ {printable}", flush=True)
            result = subprocess.run(cmd, cwd=cwd)
            if check and result.returncode != 0:
                raise RuntimeError(f"command failed ({result.returncode}): {printable}")
            return result.returncode

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

        def mirror_rel(rel: str) -> None:
            src = os.path.join(workspace, rel)
            if not os.path.exists(src):
                return
            dst = os.path.join(ckpt_data, rel)
            if os.path.isdir(src):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)

        def checkpoint_once(tag: str = "") -> None:
            try:
                for rel in (
                    ROW_POOL_OUT,
                    LABELS_OUT,
                    EXTRACTION_DIR,
                    DIRECTION_OUT,
                ):
                    mirror_rel(rel)
                vol.commit()
                print(f"[modal-aq-readout] checkpoint committed {tag}".rstrip(), flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[modal-aq-readout] checkpoint FAILED (non-fatal) {tag}: {exc}", flush=True)

        try:
            vol.reload()
        except Exception as exc:  # noqa: BLE001
            print(f"[modal-aq-readout] vol.reload() failed at restore (non-fatal): {exc}", flush=True)

        if not os.path.isdir(os.path.join(workspace, ".git")):
            sh(["git", "clone", REPO_URL, workspace])
        sh(["git", "fetch", "origin"], cwd=workspace, check=False)
        sh(["git", "checkout", repo_commit], cwd=workspace)
        sh(["git", "submodule", "update", "--init", "--recursive", "synaptic-tuner"], cwd=workspace)

        restored = copy_tree_into(ckpt_data, workspace)
        print(f"[modal-aq-readout] restored {restored} files from checkpoint", flush=True)

        from huggingface_hub import hf_hub_download, snapshot_download

        for filename, target_rel in (
            ("row_pool.jsonl", ROW_POOL_OUT),
            ("probe_fit_labels.jsonl", LABELS_OUT),
        ):
            local = hf_hub_download(
                repo_id=STAGING_REPO,
                repo_type="dataset",
                filename=f"{RUN_TAG}/artifacts/{filename}",
            )
            target = os.path.join(workspace, target_rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(local, target)
            print(f"[modal-aq-readout] staged {filename} -> {target_rel}", flush=True)

        model_path = snapshot_download(repo_id=MODEL_REPO, revision=MODEL_REVISION)
        print(f"[modal-aq-readout] staged model snapshot {MODEL_REPO}@{MODEL_REVISION}: {model_path}", flush=True)

        sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], check=False)
        if not os.path.isfile(os.path.join(workspace, EXTRACTION_DIR, "manifest.json")):
            sh([
                "python3",
                "synaptic-tuner/tuner.py",
                "mechinterp",
                "extract",
                "--mi-config",
                "experiments/aq-sycophancy-activation-actuator/extract.yaml",
                "--model",
                model_path,
                "--render-fn",
                "sycophancy_answer_render:render",
                "--i-know-this-runs-on-gpu",
            ], cwd=workspace)
            checkpoint_once("(post-extract)")
        else:
            print("[modal-aq-readout] extraction manifest present; skipping extract", flush=True)

        if not os.path.isfile(os.path.join(workspace, DIRECTION_OUT)):
            sh([
                "python3",
                "synaptic-tuner/tuner.py",
                "mechinterp",
                "probe-fit",
                "--mi-config",
                "experiments/aq-sycophancy-activation-actuator/probe_fit.yaml",
            ], cwd=workspace)
            checkpoint_once("(post-probe-fit)")
        else:
            print("[modal-aq-readout] direction present; skipping probe-fit", flush=True)

        required = [
            os.path.join(workspace, EXTRACTION_DIR, "manifest.json"),
            os.path.join(workspace, DIRECTION_OUT),
        ]
        missing = [p for p in required if not os.path.isfile(p)]
        if missing:
            raise RuntimeError(f"readout missing required outputs: {missing}")

        upload_tree_to_hf(
            STAGING_REPO,
            f"{READOUT_RUN_TAG}/artifacts",
            os.path.join(workspace, ANALYSIS_DIR),
            base_dir=workspace,
        )
        upload_tree_to_hf(
            STAGING_REPO,
            f"{READOUT_RUN_TAG}/artifacts",
            os.path.join(workspace, DIRECTION_OUT),
            base_dir=workspace,
        )

        done = f"{READOUT_CKPT}/DONE"
        os.makedirs(os.path.dirname(done), exist_ok=True)
        with open(done, "w", encoding="utf-8") as fh:
            fh.write(f"repo_commit={repo_commit}\nrun_tag={READOUT_RUN_TAG}\n")
        vol.commit()
        return {
            "ok": True,
            "mode": "readout",
            "run_tag": READOUT_RUN_TAG,
            "repo_commit": repo_commit,
            "staging_repo": STAGING_REPO,
            "artifact_prefix": f"{READOUT_RUN_TAG}/artifacts",
        }

    @app.local_entrypoint()
    def modal_entrypoint(
        dry_run: bool = False,
        repo_commit: str = DEFAULT_REPO_COMMIT,
        cost_cap_usd: float = 10.0,
        upload_only: bool = False,
        readout: bool = False,
    ) -> None:
        spec = build_spec(repo_commit, cost_cap_usd)
        if readout:
            spec["mode"] = "readout"
        elif upload_only:
            spec["mode"] = "upload_only"
        else:
            spec["mode"] = "run_eval_and_upload"
        print(json.dumps(spec, indent=2, sort_keys=True))
        if dry_run:
            return
        if repo_commit.startswith("REPLACE_WITH"):
            raise SystemExit("Pass --repo-commit=<pushed AQ branch sha> before launching paid Modal work.")
        if readout:
            call = run_aq_readout.spawn(repo_commit)
        elif upload_only:
            call = upload_aq_checkpoint.spawn(repo_commit)
        else:
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
