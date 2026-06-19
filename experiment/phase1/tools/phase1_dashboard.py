#!/usr/bin/env python
"""Local Phase 1 run dashboard.

Serves a small dependency-free dashboard for monitoring existing run records,
queue logs, and host-visible training artifacts. It is intentionally read-only
except for optional server host logs/PID written by the launch command.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCRIPT = Path(__file__).resolve()
PHASE1_DIR = SCRIPT.parents[1]
REPO_ROOT = PHASE1_DIR.parents[1]
RUN_RECORDS_DIR = PHASE1_DIR / "run_records"
RUN_LOGS_DIR = RUN_RECORDS_DIR / "logs"
ARTIFACT_RUNS_DIR = REPO_ROOT / "synaptic-tuner" / "toolset-training-artifacts" / "runs"

QUEUE_LOGS = [
    RUN_LOGS_DIR / "queue_remaining_4b_headline.log",
    RUN_LOGS_DIR / "queue_remaining_4b_headline.out.log",
    RUN_LOGS_DIR / "queue_remaining_4b_headline.err.log",
    RUN_LOGS_DIR / "queue_amendment_a_after_headline.log",
    RUN_LOGS_DIR / "queue_amendment_a_after_headline.out.log",
    RUN_LOGS_DIR / "queue_amendment_a_after_headline.err.log",
]

KNOWN_MONITORS = {
    "active_seed2_pid": "34252",
    "headline_queue_pid": "39164",
    "amendment_a_queue_pid": "36436",
    "active_container": "local-run-sft-4b-headline-seed2-20260615-090734",
}

METRIC_STALE_SECONDS = 10 * 60
QUEUE_STALE_SECONDS = 10 * 60

TABLE_RE = re.compile(
    r"^\s*(?P<step>\d+)\s*/\s*(?P<total>\d+)\s*\|\s*"
    r"(?P<loss>[-+0-9.eE]+)\s*\|\s*"
    r"(?P<learning_rate>[-+0-9.eE]+)\s*\|\s*"
    r"(?P<grad_norm>[-+0-9.eE]+)\s*\|\s*"
    r"(?P<epoch>[-+0-9.eE]+)\s*\|\s*"
    r"(?P<gpu_mem>[^|]+?)\s*\|\s*"
    r"(?P<time_per_5_steps>[^|]+?)\s*\|\s*"
    r"(?P<samples_per_sec>[-+0-9.eE]+)\s*\|\s*"
    r"(?P<eta>.+?)\s*$"
)
PROGRESS_RE = re.compile(r"(?P<step>\d+)\s*/\s*(?P<total>\d+)")
STDERR_TQDM_RE = re.compile(
    r"^\s*(?:(?P<percent>\d+(?:\.\d+)?)%\|[^|]*\|)?\s*"
    r"(?P<step>\d+)\s*/\s*(?P<total>\d+)\s*"
    r"\[(?P<elapsed>[^<,\]]+)"
    r"(?:<(?P<eta>[^,\]]+))?"
    r"(?:,\s*(?P<rate>[^\]]+))?\]\s*$"
)


def hidden_subprocess_kwargs() -> dict[str, Any]:
    if os.name != "nt":
        return {}
    kwargs: dict[str, Any] = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "STARTUPINFO") and hasattr(subprocess, "STARTF_USESHOWWINDOW"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    return kwargs


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def file_meta(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
        return {
            "path": rel(path),
            "exists": True,
            "size": stat.st_size,
            "mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat(timespec="seconds"),
            "mtime_epoch": stat.st_mtime,
            "age_seconds": max(0, int(time.time() - stat.st_mtime)),
        }
    except OSError as exc:
        return {"path": rel(path), "exists": False, "error": str(exc)}


def read_text(path: Path, limit_bytes: int = 256_000) -> tuple[str | None, str | None]:
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > limit_bytes:
                fh.seek(max(0, size - limit_bytes))
            data = fh.read()
        return data.decode("utf-8", errors="replace"), None
    except OSError as exc:
        return None, str(exc)


def tail_lines(path: Path, max_lines: int = 60) -> dict[str, Any]:
    text, err = read_text(path)
    meta = file_meta(path)
    if err:
        meta["tail"] = []
        meta["error"] = err
        return meta
    lines = text.splitlines()[-max_lines:] if text else []
    meta["tail"] = lines
    return meta


def parse_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            value = json.load(fh)
        return value if isinstance(value, dict) else {"value": value}, None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def read_pid_file(path: Path) -> dict[str, Any]:
    text, err = read_text(path, limit_bytes=2048)
    pid = text.strip() if text and text.strip() else None
    return {
        **file_meta(path),
        "pid": pid,
        "pid_alive": is_pid_alive(pid),
        "read_error": err,
    }


def is_pid_alive(pid: str | int | None) -> bool | None:
    if pid is None:
        return None
    try:
        pid_int = int(str(pid).strip())
    except ValueError:
        return None
    if pid_int <= 0:
        return False
    if os.name == "nt":
        try:
            proc = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid_int}", "/FO", "CSV", "/NH"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
                check=False,
                **hidden_subprocess_kwargs(),
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return str(pid_int) in proc.stdout
    try:
        os.kill(pid_int, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OSError, SystemError):
        return False
    return True


def run_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not RUN_RECORDS_DIR.exists():
        return records
    for path in sorted(RUN_RECORDS_DIR.glob("*.json")):
        data, err = parse_json(path)
        item: dict[str, Any] = {
            "path": rel(path),
            "mtime": file_meta(path).get("mtime"),
            "read_error": err,
        }
        if data:
            item.update(
                {
                    "run_id": data.get("run_id") or path.stem,
                    "method": data.get("method") or data.get("coordinate", {}).get("arm"),
                    "model": data.get("model"),
                    "lane": data.get("lane"),
                    "launched_at": data.get("launched_at"),
                    "status": data.get("outcome", {}).get("status"),
                    "verified": data.get("outcome", {}).get("verified"),
                    "adapter_path": data.get("outcome", {}).get("adapter_path"),
                    "metrics_path": data.get("outcome", {}).get("metrics_path"),
                    "materialized_recipe": data.get("materialized_recipe"),
                    "coordinate": data.get("coordinate"),
                }
            )
        else:
            item["run_id"] = path.stem
        records.append(item)
    records.sort(key=lambda item: item.get("launched_at") or item.get("mtime") or "", reverse=True)
    return records


def parse_literal_metric(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not (line.startswith("{") and line.endswith("}")):
        return None
    try:
        value = ast.literal_eval(line)
    except (SyntaxError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def parse_metric_line(line: str) -> dict[str, Any] | None:
    match = TABLE_RE.match(line)
    if match:
        item: dict[str, Any] = match.groupdict()
        for key in ["step", "total"]:
            item[key] = int(item[key])
        for key in ["loss", "learning_rate", "grad_norm", "epoch", "samples_per_sec"]:
            item[key] = float(item[key])
        item["source_format"] = "stdout_table"
        return item

    metric = parse_literal_metric(line)
    if metric:
        metric["source_format"] = "stdout_dict"
        return metric
    return None


def parse_tqdm_stderr_line(line: str) -> dict[str, Any] | None:
    match = STDERR_TQDM_RE.match(line.strip().lstrip("\r"))
    if not match:
        return None
    item: dict[str, Any] = {
        "step": int(match.group("step")),
        "total": int(match.group("total")),
        "elapsed": match.group("elapsed").strip(),
        "source_format": "stderr_tqdm",
    }
    percent = match.group("percent")
    eta = match.group("eta")
    rate = match.group("rate")
    if percent is not None:
        item["percent"] = float(percent)
    if eta:
        item["eta"] = eta.strip()
    if rate:
        item["rate"] = rate.strip()
    return item


def annotate_metric_source(metric: dict[str, Any], path: Path, source_kind: str) -> dict[str, Any]:
    meta = file_meta(path)
    metric["source_kind"] = source_kind
    metric["source_path"] = rel(path)
    metric["source_mtime"] = meta.get("mtime")
    metric["source_mtime_epoch"] = meta.get("mtime_epoch")
    metric["source_age_seconds"] = meta.get("age_seconds")
    metric["source_stale"] = bool((meta.get("age_seconds") or 0) > METRIC_STALE_SECONDS)
    if "total" not in metric and "total_steps" in metric:
        metric["total"] = metric.get("total_steps")
    if metric.get("event") == "train_end":
        metric["completion_evidence"] = "train_end"
    return metric


def latest_jsonl_metric(path: Path) -> dict[str, Any] | None:
    text, _err = read_text(path)
    if not text:
        return None
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            value["source_format"] = "jsonl"
            return annotate_metric_source(value, path, "artifact_jsonl")
    return None


def latest_stdout_metric(path: Path) -> dict[str, Any] | None:
    text, _err = read_text(path)
    if not text:
        return None
    last_metric: dict[str, Any] | None = None
    last_table: dict[str, Any] | None = None
    for line in text.splitlines():
        parsed = parse_metric_line(line)
        if not parsed:
            continue
        if parsed.get("source_format") == "stdout_table":
            last_table = parsed
        last_metric = parsed
    if last_table and last_metric and last_metric.get("source_format") == "stdout_dict":
        merged = {**last_metric}
        for key in ["step", "total", "gpu_mem", "time_per_5_steps", "samples_per_sec", "eta"]:
            if key in last_table:
                merged[key] = last_table[key]
        merged["source_format"] = "stdout_table+dict"
        last_metric = merged
    return annotate_metric_source(last_metric, path, "stdout_log") if last_metric else None


def latest_stderr_tqdm_metric(path: Path) -> dict[str, Any] | None:
    text, _err = read_text(path)
    if not text:
        return None
    last_metric: dict[str, Any] | None = None
    for line in text.splitlines():
        parsed = parse_tqdm_stderr_line(line)
        if parsed:
            last_metric = parsed
    return annotate_metric_source(last_metric, path, "stderr_log") if last_metric else None


def metric_sort_key(metric: dict[str, Any]) -> tuple[int, int, int, float]:
    completion = 1 if metric.get("completion_evidence") else 0
    source_priority = {"artifact_jsonl": 2, "stdout_log": 1, "stderr_log": 0}.get(str(metric.get("source_kind")), 0)
    progress = 1 if metric.get("step") is not None and metric.get("total") is not None else 0
    return completion, progress, source_priority, float(metric.get("source_mtime_epoch") or 0)


def find_files_named(root: Path, filename: str) -> list[Path]:
    matches: list[Path] = []
    if not root.exists():
        return matches
    for dirpath, _dirnames, filenames in os.walk(root, onerror=lambda _exc: None):
        if filename in filenames:
            matches.append(Path(dirpath) / filename)
    return matches


def discover_metrics() -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for path in find_files_named(ARTIFACT_RUNS_DIR, "training_latest.jsonl"):
        metric = latest_jsonl_metric(path)
        if metric:
            metric["run_id"] = infer_run_id_from_artifact_path(path)
            metrics.append(metric)
    if RUN_LOGS_DIR.exists():
        for path in RUN_LOGS_DIR.glob("*.out.log"):
            metric = latest_stdout_metric(path)
            if metric:
                metric["run_id"] = path.name.removesuffix(".out.log")
                metrics.append(metric)
        for path in RUN_LOGS_DIR.glob("*.err.log"):
            metric = latest_stderr_tqdm_metric(path)
            if metric:
                metric["run_id"] = path.name.removesuffix(".err.log")
                metrics.append(metric)
    metrics.sort(key=metric_sort_key, reverse=True)
    return metrics


def infer_run_id_from_artifact_path(path: Path) -> str | None:
    parts = list(path.parts)
    for idx, part in enumerate(parts):
        if "__4b__" in part or "__8b__" in part:
            return part
        if idx > 0 and part == "logs" and idx >= 2:
            return parts[idx - 2]
    return None


def discover_artifact_evidence() -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for lineage_path in find_files_named(ARTIFACT_RUNS_DIR, "training_lineage.json"):
        run_id = infer_run_id_from_artifact_path(lineage_path)
        if not run_id:
            continue
        run_dir = lineage_path.parent
        lineage, err = parse_json(lineage_path)
        runtime = lineage.get("runtime", {}) if lineage else {}
        results = lineage.get("results", {}) if lineage else {}
        final_model = run_dir / "final_model"
        adapter_model = final_model / "adapter_model.safetensors"
        latest_log = run_dir / "logs" / "training_latest.jsonl"
        latest_metric = latest_jsonl_metric(latest_log)
        adapter_meta = file_meta(adapter_model)
        latest_log_meta = file_meta(latest_log)
        meta_candidates = [file_meta(lineage_path), adapter_meta, latest_log_meta]
        newest = max((float(meta.get("mtime_epoch") or 0) for meta in meta_candidates), default=0.0)
        train_end = latest_metric if latest_metric and latest_metric.get("event") == "train_end" else None
        completed = runtime.get("status") == "completed" or bool(train_end) or bool(adapter_meta.get("exists"))
        item = {
            "run_id": run_id,
            "run_dir": rel(run_dir),
            "lineage_path": rel(lineage_path),
            "lineage_read_error": err,
            "runtime_status": runtime.get("status"),
            "finished_at": runtime.get("finished_at"),
            "final_step": results.get("final_step"),
            "final_loss": results.get("final_loss"),
            "adapter_model": rel(adapter_model) if adapter_meta.get("exists") else None,
            "train_end": bool(train_end),
            "completed": completed,
            "evidence_mtime_epoch": newest,
            "evidence_mtime": dt.datetime.fromtimestamp(newest, dt.timezone.utc).isoformat(timespec="seconds")
            if newest
            else None,
        }
        previous = evidence.get(run_id)
        if not previous or float(previous.get("evidence_mtime_epoch") or 0) < newest:
            evidence[run_id] = item
    return evidence


def nvidia_smi() -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "error": str(exc)}
    if proc.returncode != 0:
        return {"available": False, "error": proc.stderr.strip() or proc.stdout.strip()}
    gpus = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 6:
            continue
        try:
            total = int(parts[2])
            used = int(parts[3])
            free = int(parts[4])
            util = int(parts[5])
        except ValueError:
            continue
        gpus.append(
            {
                "index": parts[0],
                "name": parts[1],
                "memory_total_mib": total,
                "memory_used_mib": used,
                "memory_free_mib": free,
                "utilization_gpu_percent": util,
                "headroom_percent": round((free / total) * 100, 1) if total else None,
                "oom_risk": "high" if free < 2048 else "medium" if free < 4096 else "low",
            }
        )
    return {"available": True, "gpus": gpus, "sampled_at": utc_now()}


def queue_status() -> list[dict[str, Any]]:
    items = []
    for path in QUEUE_LOGS:
        item = tail_lines(path)
        item["stale"] = bool((item.get("age_seconds") or 0) > QUEUE_STALE_SECONDS) if item.get("exists") else None
        pid_path = path.with_suffix(".pid") if path.suffix == ".log" else None
        if pid_path and pid_path.exists():
            item["pid_file"] = read_pid_file(pid_path)
        items.append(item)
    return items


def pid_files() -> list[dict[str, Any]]:
    if not RUN_LOGS_DIR.exists():
        return []
    return [read_pid_file(path) for path in sorted(RUN_LOGS_DIR.glob("*.pid"))]


def best_metric_for_run(run_id: str | None, metrics: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [metric for metric in metrics if metric.get("run_id") == run_id]
    return max(matches, key=metric_sort_key) if matches else None


def run_pid_status(run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    pid_path = RUN_LOGS_DIR / f"{run_id}.pid"
    return read_pid_file(pid_path) if pid_path.exists() else None


def enrich_record(
    record: dict[str, Any],
    metrics: list[dict[str, Any]],
    artifact_evidence: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    item = dict(record)
    run_id = item.get("run_id")
    metric = best_metric_for_run(run_id, metrics)
    evidence = artifact_evidence.get(run_id)
    pid_status = run_pid_status(run_id)
    if metric:
        item["latest_metric"] = metric
    if evidence:
        item["artifact_evidence"] = evidence
    if pid_status:
        item["pid_file"] = pid_status

    status = item.get("status") or "unknown"
    detail: list[str] = []
    if evidence and evidence.get("completed"):
        item["effective_status"] = "completed"
        if status != "completed":
            detail.append(f"run record says {status}; host artifacts indicate completed")
    elif status == "launched" and metric and metric.get("source_stale"):
        item["effective_status"] = "stale"
        detail.append(f"latest metric source is stale ({metric.get('source_age_seconds')}s old)")
    else:
        item["effective_status"] = status

    if status == "launched" and pid_status and pid_status.get("pid_alive") is False:
        detail.append(f"pid {pid_status.get('pid')} is not alive")
        fresh_progress = (
            metric
            and not metric.get("source_stale")
            and metric.get("step") is not None
            and metric.get("total") is not None
        )
        if item["effective_status"] == "launched" and not fresh_progress:
            item["effective_status"] = "stale"
    if metric and metric.get("completion_evidence"):
        detail.append(f"metric source reports {metric.get('completion_evidence')}")
        if item["effective_status"] != "completed":
            item["effective_status"] = "completed"
    item["status_detail"] = "; ".join(detail) if detail else None
    item["sort_mtime_epoch"] = max(
        float(metric.get("source_mtime_epoch") or 0) if metric else 0.0,
        float(evidence.get("evidence_mtime_epoch") or 0) if evidence else 0.0,
        float(file_meta(RUN_RECORDS_DIR / f"{run_id}.json").get("mtime_epoch") or 0) if run_id else 0.0,
    )
    return item


def active_run(
    records: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    artifact_evidence: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    enriched = [enrich_record(record, metrics, artifact_evidence) for record in records]
    if not enriched:
        return None

    def priority(item: dict[str, Any]) -> tuple[int, float]:
        effective = item.get("effective_status")
        record_status = item.get("status")
        metric = item.get("latest_metric") or {}
        pid_status = item.get("pid_file") or {}
        live = effective == "launched" and (pid_status.get("pid_alive") is True or not metric.get("source_stale"))
        current_record = record_status == "launched"
        completed = effective == "completed"
        stale = effective == "stale"
        return (
            4 if live else 3 if current_record else 2 if completed else 1 if stale else 0,
            float(item.get("sort_mtime_epoch") or 0),
        )

    return max(enriched, key=priority)


def monitor_commands() -> list[str]:
    return [
        "Get-Content -Tail 80 experiment\\phase1\\run_records\\logs\\sft__4b__headline__seed2.out.log",
        "Get-Content experiment\\phase1\\run_records\\logs\\sft__4b__headline__seed2.pid",
        "Get-Content -Tail 80 experiment\\phase1\\run_records\\logs\\queue_remaining_4b_headline.log",
        "Get-Content -Tail 80 experiment\\phase1\\run_records\\logs\\queue_amendment_a_after_headline.log",
        "nvidia-smi",
    ]


def status_payload() -> dict[str, Any]:
    records = run_records()
    metrics = discover_metrics()
    artifact_evidence = discover_artifact_evidence()
    enriched_records = [enrich_record(record, metrics, artifact_evidence) for record in records]
    return {
        "generated_at": utc_now(),
        "repo_root": str(REPO_ROOT),
        "known_monitors": KNOWN_MONITORS,
        "active_run": active_run(records, metrics, artifact_evidence),
        "latest_metrics": metrics[:10],
        "queues": queue_status(),
        "run_records": enriched_records[:40],
        "artifact_evidence": sorted(
            artifact_evidence.values(), key=lambda item: item.get("evidence_mtime_epoch") or 0, reverse=True
        )[:20],
        "pid_files": pid_files(),
        "gpu": nvidia_smi(),
        "paths": {
            "run_records": rel(RUN_RECORDS_DIR),
            "run_logs": rel(RUN_LOGS_DIR),
            "artifact_runs": rel(ARTIFACT_RUNS_DIR),
        },
        "monitor_commands": monitor_commands(),
    }


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 1 Local Dashboard</title>
  <style>
    :root { color-scheme: dark light; --bg: #111318; --panel: #1b2028; --line: #313947; --text: #f0f4f8; --muted: #aeb9c8; --ok: #50c878; --warn: #f2b84b; --bad: #ff6b6b; --accent: #62b6ff; }
    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: var(--bg); color: var(--text); }
    header { padding: 18px 22px; border-bottom: 1px solid var(--line); display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
    h1 { font-size: 20px; margin: 0; letter-spacing: 0; }
    main { padding: 18px 22px 28px; display: grid; gap: 16px; }
    section { border: 1px solid var(--line); background: var(--panel); border-radius: 6px; padding: 14px; min-width: 0; }
    h2 { font-size: 15px; margin: 0 0 12px; }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .metric-grid { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); }
    .kv { padding: 9px 10px; background: #151922; border: 1px solid #26303d; border-radius: 4px; }
    .kv span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }
    .kv strong { font-size: 15px; overflow-wrap: anywhere; }
    .muted { color: var(--muted); }
    .ok { color: var(--ok); } .warn { color: var(--warn); } .bad { color: var(--bad); }
    progress { width: 100%; height: 14px; accent-color: var(--accent); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border-bottom: 1px solid var(--line); padding: 7px 6px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-weight: 600; }
    pre { margin: 0; max-height: 280px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; line-height: 1.35; color: #d7e1ee; }
    code { color: #d7e1ee; background: #11151d; padding: 1px 4px; border-radius: 3px; }
    .stack { display: grid; gap: 10px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .pill { display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; color: var(--muted); font-size: 12px; }
    @media (max-width: 720px) { header, main { padding-left: 12px; padding-right: 12px; } th:nth-child(5), td:nth-child(5) { display: none; } }
  </style>
</head>
<body>
  <header>
    <h1>Phase 1 Local Dashboard</h1>
    <div class="row"><span id="stamp" class="muted">Loading...</span><span class="pill">refreshes every 10s</span></div>
  </header>
  <main id="app" aria-live="polite"></main>
  <script>
    const app = document.getElementById('app');
    const stamp = document.getElementById('stamp');
    const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const val = (v, fallback='unavailable') => v === null || v === undefined || v === '' ? fallback : esc(v);
    const pct = (m) => m && m.step && m.total ? Math.min(100, Math.round((m.step / m.total) * 1000) / 10) : null;
    const riskClass = (risk) => risk === 'high' ? 'bad' : risk === 'medium' ? 'warn' : 'ok';
    const statusClass = (status) => status === 'completed' ? 'ok' : status === 'stale' ? 'warn' : status === 'failed' ? 'bad' : '';
    function metricCard(label, value) { return `<div class="kv"><span>${esc(label)}</span><strong>${val(value)}</strong></div>`; }
    function renderActive(active, known) {
      const m = active?.latest_metric || {};
      const progress = pct(m);
      const status = active?.effective_status || active?.status;
      const sourceHealth = m.source_stale ? `stale (${m.source_age_seconds}s old)` : (m.source_path ? 'fresh' : 'unavailable');
      const pid = active?.pid_file?.pid || known?.active_seed2_pid;
      const pidHealth = active?.pid_file?.pid_alive === false ? 'dead' : active?.pid_file?.pid_alive === true ? 'alive' : 'unknown';
      return `<section><h2>Active Run</h2>
        <div class="stack">
          <div class="metric-grid">
            ${metricCard('Run', active?.run_id)}
            <div class="kv"><span>Status</span><strong class="${statusClass(status)}">${val(status)}</strong></div>
            ${metricCard('Record Status', active?.status)}
            ${metricCard('Status Detail', active?.status_detail)}
            ${metricCard('PID', pid ? `${pid} (${pidHealth})` : null)}
            ${metricCard('Container', known?.active_container)}
            ${metricCard('Step', m.step && m.total ? `${m.step}/${m.total}` : m.step)}
            ${metricCard('Loss', m.loss)}
            ${metricCard('Epoch', m.epoch)}
            ${metricCard('GPU Mem', m.gpu_mem)}
            ${metricCard('ETA', m.eta)}
            ${metricCard('Metric Source', m.source_path)}
            <div class="kv"><span>Metric Health</span><strong class="${m.source_stale ? 'warn' : ''}">${esc(sourceHealth)}</strong></div>
            ${metricCard('Completion Evidence', active?.artifact_evidence?.completed ? active.artifact_evidence.lineage_path : m.completion_evidence)}
          </div>
          ${progress === null ? '<div class="muted">No step progress detected yet.</div>' : `<div><progress value="${progress}" max="100"></progress><div class="muted">${progress}% complete</div></div>`}
        </div>
      </section>`;
    }
    function renderGpu(gpu) {
      if (!gpu?.available) return `<section><h2>VRAM</h2><p class="muted">${val(gpu?.error, 'nvidia-smi unavailable')}</p></section>`;
      const rows = (gpu.gpus || []).map(g => `<tr><td>${val(g.index)}</td><td>${val(g.name)}</td><td>${val(g.memory_used_mib)} / ${val(g.memory_total_mib)} MiB</td><td>${val(g.memory_free_mib)} MiB</td><td class="${riskClass(g.oom_risk)}">${val(g.oom_risk)}</td></tr>`).join('');
      return `<section><h2>VRAM</h2><table><thead><tr><th>GPU</th><th>Name</th><th>Used</th><th>Headroom</th><th>OOM Risk</th></tr></thead><tbody>${rows || '<tr><td colspan="5" class="muted">No GPUs reported.</td></tr>'}</tbody></table></section>`;
    }
    function renderQueues(queues) {
      const body = (queues || []).map(q => {
        const pidState = q.pid_file?.pid_alive === false ? 'dead' : q.pid_file?.pid_alive === true ? 'alive' : 'unknown';
        return `<section><h2>${val(q.path)}</h2><div class="row"><span class="pill">${q.exists ? 'exists' : 'missing'}</span><span class="pill ${q.stale ? 'warn' : ''}">age ${val(q.age_seconds)}s${q.stale ? ' stale' : ''}</span>${q.pid_file?.pid ? `<span class="pill ${pidState === 'dead' ? 'bad' : ''}">pid ${esc(q.pid_file.pid)} ${pidState}</span>` : ''}</div><pre>${esc((q.tail || []).join('\\n') || q.error || 'No lines.')}</pre></section>`;
      }).join('');
      return `<div class="grid">${body}</div>`;
    }
    function renderRecords(records) {
      const rows = (records || []).map(r => `<tr><td>${val(r.run_id)}</td><td class="${statusClass(r.effective_status)}">${val(r.effective_status)}</td><td>${val(r.status)}</td><td>${val(r.status_detail)}</td><td>${val(r.launched_at)}</td><td>${val(r.path)}</td></tr>`).join('');
      return `<section><h2>Run Records</h2><table><thead><tr><th>Run</th><th>Effective</th><th>Record</th><th>Detail</th><th>Launched</th><th>Path</th></tr></thead><tbody>${rows || '<tr><td colspan="6" class="muted">No run records found.</td></tr>'}</tbody></table></section>`;
    }
    function renderCommands(commands, paths) {
      return `<section><h2>Monitor Commands And Paths</h2><div class="stack">
        <div class="metric-grid">${metricCard('Run records', paths?.run_records)}${metricCard('Run logs', paths?.run_logs)}${metricCard('Artifacts', paths?.artifact_runs)}</div>
        <pre>${esc((commands || []).join('\\n'))}</pre>
      </div></section>`;
    }
    async function load() {
      try {
        const res = await fetch('/api/status', {cache: 'no-store'});
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const data = await res.json();
        stamp.textContent = `Updated ${data.generated_at}`;
        app.innerHTML = [
          `<div class="grid">${renderActive(data.active_run, data.known_monitors)}${renderGpu(data.gpu)}</div>`,
          `<section><h2>Queue Logs</h2>${renderQueues(data.queues)}</section>`,
          renderRecords(data.run_records),
          renderCommands(data.monitor_commands, data.paths)
        ].join('');
      } catch (err) {
        stamp.textContent = 'Update failed';
        app.innerHTML = `<section><h2>Error</h2><pre>${esc(err.stack || err.message || err)}</pre></section>`;
      }
    }
    load();
    setInterval(load, 10000);
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "Phase1Dashboard/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_bytes(HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            payload = json.dumps(status_payload(), indent=2).encode("utf-8")
            self.send_bytes(payload, "application/json; charset=utf-8")
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PHASE1_DASHBOARD_PORT", "8765")))
    parser.add_argument("--pid-file", type=Path, help="Write the dashboard process ID to this file")
    parser.add_argument("--stdout-log", type=Path, help="Append stdout to this file")
    parser.add_argument("--stderr-log", type=Path, help="Append stderr to this file")
    return parser.parse_args()


def install_process_files(args: argparse.Namespace) -> None:
    if args.stdout_log:
        args.stdout_log.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = args.stdout_log.open("a", encoding="utf-8", buffering=1)
    if args.stderr_log:
        args.stderr_log.parent.mkdir(parents=True, exist_ok=True)
        sys.stderr = args.stderr_log.open("a", encoding="utf-8", buffering=1)
    if args.pid_file:
        args.pid_file.parent.mkdir(parents=True, exist_ok=True)
        args.pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    install_process_files(args)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Phase 1 dashboard serving {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping dashboard.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
