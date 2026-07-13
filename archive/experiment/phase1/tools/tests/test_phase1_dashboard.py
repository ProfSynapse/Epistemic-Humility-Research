import importlib.util
import time
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "phase1_dashboard.py"
SPEC = importlib.util.spec_from_file_location("phase1_dashboard", MODULE_PATH)
assert SPEC and SPEC.loader
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


def write_log(path: Path, text: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.touch()
    import os

    os.utime(path, (mtime, mtime))


def test_parse_tqdm_stderr_line_extracts_progress_fields() -> None:
    metric = dashboard.parse_tqdm_stderr_line("  3%|...| 100/3599 [13:57<8:31:22, 8.77s/it]")

    assert metric == {
        "step": 100,
        "total": 3599,
        "elapsed": "13:57",
        "eta": "8:31:22",
        "percent": 3.0,
        "rate": "8.77s/it",
        "source_format": "stderr_tqdm",
    }


def test_parse_tqdm_stderr_line_ignores_unrelated_stderr() -> None:
    assert dashboard.parse_tqdm_stderr_line("WARNING: tokenizer emitted a warning") is None
    assert dashboard.parse_tqdm_stderr_line("loss=1.0 step=100 total=3599") is None


def test_discover_metrics_uses_stderr_tqdm_when_stdout_has_no_metric(tmp_path, monkeypatch) -> None:
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", logs_dir)
    monkeypatch.setattr(dashboard, "ARTIFACT_RUNS_DIR", tmp_path / "missing_artifacts")
    now = time.time()
    write_log(logs_dir / "kto__4b__headline__seed2.out.log", "starting trainer\n", now)
    write_log(
        logs_dir / "kto__4b__headline__seed2.err.log",
        "loading model\n  3%|...| 100/3599 [13:57<8:31:22, 8.77s/it]\n",
        now + 1,
    )

    metrics = dashboard.discover_metrics()

    assert len(metrics) == 1
    assert metrics[0]["run_id"] == "kto__4b__headline__seed2"
    assert metrics[0]["source_format"] == "stderr_tqdm"
    assert metrics[0]["source_kind"] == "stderr_log"
    assert metrics[0]["step"] == 100
    assert metrics[0]["total"] == 3599


def test_best_metric_preserves_stdout_priority_over_newer_stderr(tmp_path, monkeypatch) -> None:
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", logs_dir)
    monkeypatch.setattr(dashboard, "ARTIFACT_RUNS_DIR", tmp_path / "missing_artifacts")
    now = time.time()
    write_log(
        logs_dir / "kto__4b__headline__seed2.out.log",
        "100 / 3599 | 1.25 | 1e-05 | 0.4 | 0.1 | 14GiB | 00:40 | 2.0 | 8:31:22\n",
        now,
    )
    write_log(logs_dir / "kto__4b__headline__seed2.err.log", "3%|...| 110/3599 [14:00<8:29:00, 8.77s/it]\n", now + 10)

    metrics = dashboard.discover_metrics()
    best = dashboard.best_metric_for_run("kto__4b__headline__seed2", metrics)

    assert best is not None
    assert best["source_format"] == "stdout_table"
    assert best["step"] == 100


def test_best_metric_prefers_stderr_progress_over_stdout_dict_without_progress(tmp_path, monkeypatch) -> None:
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", logs_dir)
    monkeypatch.setattr(dashboard, "ARTIFACT_RUNS_DIR", tmp_path / "missing_artifacts")
    now = time.time()
    write_log(logs_dir / "kto__4b__headline__seed2.out.log", "{'event': 'trainer_start', 'loss': 1.25}\n", now + 10)
    write_log(logs_dir / "kto__4b__headline__seed2.err.log", "3%|...| 110/3599 [14:00<8:29:00, 8.77s/it]\n", now)

    metrics = dashboard.discover_metrics()
    best = dashboard.best_metric_for_run("kto__4b__headline__seed2", metrics)

    assert best is not None
    assert best["source_format"] == "stderr_tqdm"
    assert best["step"] == 110
    assert best["total"] == 3599


def test_best_metric_preserves_artifact_priority_over_logs(tmp_path, monkeypatch) -> None:
    logs_dir = tmp_path / "logs"
    artifact_run = tmp_path / "artifacts" / "kto__4b__headline__seed2" / "logs"
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", logs_dir)
    monkeypatch.setattr(dashboard, "ARTIFACT_RUNS_DIR", tmp_path / "artifacts")
    now = time.time()
    write_log(artifact_run / "training_latest.jsonl", '{"step": 120, "total_steps": 3599, "loss": 1.1}\n', now)
    write_log(logs_dir / "kto__4b__headline__seed2.err.log", "3%|...| 130/3599 [15:00<8:00:00, 8.77s/it]\n", now + 10)

    metrics = dashboard.discover_metrics()
    best = dashboard.best_metric_for_run("kto__4b__headline__seed2", metrics)

    assert best is not None
    assert best["source_format"] == "jsonl"
    assert best["source_kind"] == "artifact_jsonl"
    assert best["step"] == 120
    assert best["total"] == 3599


def test_active_run_can_select_live_run_from_stderr_metric(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", tmp_path / "logs")
    run_id = "kto__4b__headline__seed2"
    metric = {
        "run_id": run_id,
        "step": 100,
        "total": 3599,
        "source_kind": "stderr_log",
        "source_format": "stderr_tqdm",
        "source_stale": False,
        "source_mtime_epoch": time.time(),
    }
    record = {"run_id": run_id, "status": "launched"}

    active = dashboard.active_run([record], [metric], {})

    assert active is not None
    assert active["run_id"] == run_id
    assert active["latest_metric"]["source_format"] == "stderr_tqdm"
    assert active["effective_status"] == "launched"


def test_enrich_record_keeps_launched_with_dead_pid_when_fresh_progress_exists(tmp_path, monkeypatch) -> None:
    run_id = "kto__4b__headline__seed2"
    monkeypatch.setattr(dashboard, "RUN_LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(dashboard, "RUN_RECORDS_DIR", tmp_path / "records")
    monkeypatch.setattr(
        dashboard,
        "run_pid_status",
        lambda candidate: {"pid": "63816", "pid_alive": False} if candidate == run_id else None,
    )
    metric = {
        "run_id": run_id,
        "step": 110,
        "total": 3599,
        "source_kind": "stderr_log",
        "source_format": "stderr_tqdm",
        "source_stale": False,
        "source_mtime_epoch": time.time(),
    }
    record = {"run_id": run_id, "status": "launched"}

    enriched = dashboard.enrich_record(record, [metric], {})

    assert enriched["effective_status"] == "launched"
    assert enriched["status_detail"] == "pid 63816 is not alive"
