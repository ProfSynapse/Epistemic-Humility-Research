#!/usr/bin/env bash
# Reusable failure telemetry for RunPod one-shot wrapper jobs.
#
# RunPod has no logs API, so a wrapper that dies on a pod leaves zero
# diagnostics unless it uploads them itself. Source this file from a wrapper
# and call install_failure_trap once, after the wrapper has: (1) captured its
# own stdout+stderr to a log file via `exec > >(tee -a "$LOG") 2>&1`, and
# (2) defined the variables below. On ANY nonzero exit thereafter the trap
# uploads a failure marker plus the tail of the log to <run_tag>/_failure/ in
# the staging repo, best-effort, then re-raises the original exit code.
#
# Contract (caller sets these before install_failure_trap):
#   FAIL_STAGING_REPO   HF dataset repo id (system of record)
#   FAIL_RUN_TAG        run tag; failure lands under <run_tag>/_failure/
#   FAIL_JOB_LOG        path to the tee'd wrapper log
#   FAIL_UPLOADER       path to upload_result.py
# Optional:
#   FAIL_LOG_TAIL_LINES tail length to ship (default 400)
#
# Design invariants:
#   - best-effort: the telemetry NEVER changes the exit code the wrapper would
#     otherwise return (the trap saves $? first and re-exits with it).
#   - secret-safe: the marker and the log tail are scrubbed of hf_/rpa_ token
#     patterns before upload, since the log is captured raw and the uploader
#     does no redaction of its own.
#   - idempotent-friendly: writes to a fixed _failure/ prefix; a re-run
#     overwrites rather than accumulating.

_redact() {
    # Mask HF (hf_...) and RunPod (rpa_...) token patterns anywhere in a stream.
    sed -E 's/hf_[A-Za-z0-9]+/hf_[REDACTED]/g; s/rpa_[A-Za-z0-9]+/rpa_[REDACTED]/g'
}

_emit_failure_telemetry() {
    local rc="$1"
    # Guard: only fire on real failure and only when fully configured.
    [ "${rc}" -eq 0 ] && return 0
    [ -n "${FAIL_STAGING_REPO:-}" ] || return 0
    [ -n "${FAIL_RUN_TAG:-}" ] || return 0
    [ -n "${FAIL_UPLOADER:-}" ] || return 0

    local workdir marker tailfile
    workdir="$(mktemp -d 2>/dev/null || echo /tmp)"
    marker="${workdir}/FAILED.txt"
    tailfile="${workdir}/job_log_tail.txt"

    {
        echo "run_tag=${FAIL_RUN_TAG}"
        echo "exit_code=${rc}"
        echo "failed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "host=$(hostname 2>/dev/null || echo unknown)"
    } | _redact > "${marker}"

    if [ -n "${FAIL_JOB_LOG:-}" ] && [ -f "${FAIL_JOB_LOG}" ]; then
        tail -n "${FAIL_LOG_TAIL_LINES:-400}" "${FAIL_JOB_LOG}" | _redact > "${tailfile}"
    else
        echo "(no job log captured)" > "${tailfile}"
    fi

    echo "[failure-trap] uploading failure telemetry to ${FAIL_RUN_TAG}/_failure/"
    python "${FAIL_UPLOADER}" \
        --repo "${FAIL_STAGING_REPO}" \
        --path-prefix "${FAIL_RUN_TAG}/_failure" \
        --file "${marker}" --file "${tailfile}" >/dev/null 2>&1 \
        || echo "[failure-trap] telemetry upload failed (non-fatal)"
}

install_failure_trap() {
    # Chain onto any existing EXIT trap so callers keep their own cleanup.
    local prior
    prior="$(trap -p EXIT | sed -E "s/^trap -- '(.*)' EXIT$/\1/")"
    if [ -n "${prior}" ]; then
        trap 'rc=$?; '"${prior}"'; _emit_failure_telemetry "$rc"; exit $rc' EXIT
    else
        trap 'rc=$?; _emit_failure_telemetry "$rc"; exit $rc' EXIT
    fi
}
