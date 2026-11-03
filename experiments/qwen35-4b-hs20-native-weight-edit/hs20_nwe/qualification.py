"""Owned-process SIGKILL/resume checks for the three incremental instruments.

Only private journals are copied. The report contains artifact references and
hashes; it never contains questions or generated responses.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

from .util import HarnessError, read_json, read_jsonl, sha256_file, write_json, write_jsonl


def localize_worker(ctx):
    from .localize import reduce_rows
    rows = read_jsonl(ctx.layout.local('materialize/fit_l.jsonl', shared=True))
    result = reduce_rows(ctx.cell, ctx.layout.local('capture/fit_l'), rows,
                         ctx.layout.local('localization'), blocks=ctx.cell.cell['candidates']['blocks'])
    return {'n_rows': len(rows), 'recomputed': result['recomputed_this_pass']}


def generation_worker(ctx):
    from . import stages
    return stages.generate(ctx, ['screen_baseline'])


def drill(ctx, module):
    from . import stages
    if module not in {'extract', 'generation', 'localize'} or ctx.layout.tag:
        raise HarnessError('DRILL_SCOPE', 'run a named drill from the full namespace')
    from .integrity import verify
    verify(ctx.cell, ctx.layout)
    tag = 'kill-resume'  # Same captured rows support the localize persistence drill.
    smoke = stages.Ctx.create(ctx.project_root, tag=tag, gpu_ack=ctx.gpu_ack)
    if module == 'extract':
        stages.smoke_prepare(ctx, smoke, ['fit_l', 'fit_screen', 'decoy', 'heldout'], int(ctx.cell.cell['qualification']['rows']))
        stages.emit_static(smoke)
    commands = {'extract': ['stage', 'extract-fit-l'],
                'generation': ['drill-worker', 'generation'],
                'localize': ['drill-worker', 'localize']}
    paths = {'extract': 'capture/fit_l/capture.runlog.jsonl',
             'generation': 'runlog/screen_baseline.jsonl',
             'localize': 'localization/localization.runlog.jsonl'}
    row_files = {'extract': 'fit_l', 'generation': 'fit_screen', 'localize': 'fit_l'}
    journal = smoke.layout.local(paths[module])
    expected = len(read_jsonl(smoke.layout.local(f'materialize/{row_files[module]}.jsonl', shared=True)))
    report_path = ctx.layout.local(f'results/evidence/drill_{module}.json', shared=True)
    if report_path.exists():
        raise HarnessError('DRILL_EXISTS', 'do not overwrite a measured drill')
    if journal.exists():
        raise HarnessError('DRILL_EXISTS', 'drill must begin with a fresh journal')
    command = [sys.executable, '-m', 'hs20_nwe', '--project-root', str(ctx.project_root),
               '--smoke-tag', tag, *(['--gpu-ack'] if ctx.gpu_ack else []), *commands[module]]
    log_path = ctx.layout.local(f'qualification/{module}.private.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with log_path.open('ab') as stream:
        child = subprocess.Popen(command, stdout=stream, stderr=stream, start_new_session=True)
        stopped = False
        try:
            deadline = started + 1800
            while child.poll() is None and time.monotonic() < deadline:
                try:
                    rows = read_jsonl(journal) if journal.exists() else []
                except (ValueError, OSError):
                    rows = []
                if len(rows) >= 4:
                    os.killpg(child.pid, signal.SIGSTOP)
                    stopped = True
                    break
                time.sleep(.001 if module == 'localize' else .02)
            if not stopped:
                raise HarnessError('DRILL_NOT_INTERRUPTED', 'worker ended or timed out before the measured interruption')
            before = read_jsonl(journal)
            if not 4 <= len(before) < expected:
                raise HarnessError('DRILL_NOT_INTERRUPTED', 'need both committed and unfinished rows at SIGKILL')
            before_ref = ctx.layout.ref(f'qualification/{module}.before.jsonl')
            after_ref = ctx.layout.ref(f'qualification/{module}.after.jsonl')
            write_jsonl(ctx.layout.to_local(before_ref), before)
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=30)
            killed_pid = child.pid
            resume_started = time.monotonic()
            resumed = subprocess.run(command, stdout=stream, stderr=stream, timeout=1800, check=False)
            if resumed.returncode:
                raise HarnessError('DRILL_RESUME', f'resume exited {resumed.returncode}; inspect private log')
            after = read_jsonl(journal)
            keys = [r.get('row_key', r.get('key')) for r in after]
            if after[:len(before)] != before or len(after) != expected or len(set(keys)) != expected or None in keys:
                raise HarnessError('DRILL_RESUME', 'resume changed committed rows, duplicated rows or failed to finish')
            write_jsonl(ctx.layout.to_local(after_ref), after)
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=30)
    from .integrity import evidence_stamp
    evidence = {**evidence_stamp(ctx.cell, ctx.layout), 'module': module, 'signal': 9, 'killed_pid': killed_pid, 'resume_exit_code': resumed.returncode,
                'expected_rows': expected, 'before_rows': len(before), 'after_rows': len(after),
                'before_journal': before_ref, 'after_journal': after_ref,
                'before_sha256': sha256_file(ctx.layout.to_local(before_ref)),
                'after_sha256': sha256_file(ctx.layout.to_local(after_ref)),
                'total_wall_seconds': time.monotonic() - started,
                'resume_wall_seconds': time.monotonic() - resume_started}
    write_json(report_path, evidence)
    all_paths = [ctx.layout.local(f'results/evidence/drill_{m}.json', shared=True) for m in ('extract', 'generation', 'localize')]
    if all(p.exists() for p in all_paths):
        combined = {'schema_version': 'hs20-nwe-kill-resume/v1', **evidence_stamp(ctx.cell, ctx.layout),
                    'drills': [read_json(p) for p in all_paths]}
        from .integrity import verify_drill
        if not verify_drill(ctx.cell, ctx.layout, combined):
            raise HarnessError('DRILL_EVIDENCE', 'combined drill evidence did not verify')
        write_json(ctx.layout.local('results/evidence/kill_resume_drill.json', shared=True), combined)
    return evidence
