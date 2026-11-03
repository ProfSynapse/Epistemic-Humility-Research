"""Twenty-row unscored runtime qualification through the installed public CLI.

Adapts the established family-atlas presign_smoke repeat/permutation/resume
checks. Only development questions enter this namespace. It never grades model
behavior, constructs an edit, or authorizes scored study generation.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import time
from pathlib import Path

import jsonschema
import numpy as np
import yaml

from . import astra_benchmark as benchmark
from . import astra_capture, astra_fixed, astra_render, capture
from .astra_run import PREFIX, _engine, batch_arguments, capture_config
from .config import EXPERIMENT_DIR, Layout, find_project_root
from .util import (
    HarnessError,
    append_jsonl,
    canonical_sha256,
    read_json,
    read_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
    write_yaml,
)

RUNS = ('original_a', 'original_b', 'permuted_a', 'permuted_b', 'resume')
N = 20


def qualification_root(runtime):
    name = runtime['qualification'].get('namespace')
    if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}', name):
        raise HarnessError('QUAL_NAMESPACE', 'choose an explicit safe qualification namespace')
    return f'{PREFIX}/qualification/{name}'


def _token_hash(ids):
    return hashlib.sha256(json.dumps(list(ids), separators=(',', ':')).encode('ascii')).hexdigest()


def binding(proposal, runtime):
    return {'model_revision': proposal.raw['model']['revision'],
            'model_shards': proposal.raw['model']['files_sha256'],
            'generation': proposal.raw['evaluation']['decode'],
            'runtime': {k: v for k, v in runtime['evaluation'].items() if k != 'qualified'},
            'namespace': qualification_root(runtime), 'engine': runtime['engine'], 'schema_sha256': canonical_sha256(benchmark.JSON_SCHEMA),
            'source_sha256': {name: sha256_file(EXPERIMENT_DIR / 'hs20_nwe' / name)
                              for name in ('astra_qualification.py', 'astra_render.py', 'astra_run.py', 'astra_benchmark.py', 'astra_capture.py', 'capture.py')}}


def prepare(proposal, layout, model):
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    qual_root = qualification_root(runtime)
    model = model.resolve()
    for name, digest in proposal.raw['model']['files_sha256'].items():
        if sha256_file(model / name) != digest:
            raise HarnessError('QUAL_MODEL', 'qualification base shards differ from the fixed model')
    os.environ['HS20NWE_RENDER_MODEL'] = str(model)
    os.environ['HS20NWE_RENDER_REVISION'] = proposal.raw['model']['revision']
    tokenizer = astra_render._tokenizer()
    roster = astra_fixed.load_roster(proposal, layout.local(f'{PREFIX}/inputs/roster.json'))
    questions = {r['row_key']: r for r in read_jsonl(layout.local(f'{PREFIX}/inputs/capture_rows.jsonl'))}
    selected = []
    for role in astra_fixed.HISTORICAL_ROLES:
        keys = sorted(roster['keys'][role], key=lambda key: (
            len(tokenizer.encode(astra_render.render_pstruct(questions[key]), add_special_tokens=False)), key.encode()))
        selected.extend(keys[int(i)] for i in np.linspace(0, len(keys) - 1, N // 2, dtype=int))
    if len(set(selected)) != N:
        raise HarnessError('QUAL_ROSTER', 'qualification requires twenty distinct development questions')
    # Cover both prompt conditions and the historical format-retry paths.
    rows = []
    for index, key in enumerate(selected):
        prompt_kind = ('P-struct', 'P-rc')[index % 2]
        retry = (index // 2) % 2
        r = benchmark.prompts([{'id': f'qual-{index:02}', 'question': questions[key]['question']}], prompt_kind, retry)[0]
        ids = tokenizer.encode(r['prompt'], add_special_tokens=False)
        rows.append({**r, 'source_row_key': key, 'expected_prompt_sha256': hashlib.sha256(r['prompt'].encode()).hexdigest(),
                     'expected_token_ids_sha256': _token_hash(ids), 'expected_prompt_tokens': len(ids)})
    manifest = {'schema_version': 'ehr-astra-qualification/v1', 'n': N, 'binding': binding(proposal, runtime),
                'model_path': str(model), 'rows_sha256': canonical_sha256(rows)}
    path = layout.local(f'{qual_root}/manifest.json')
    if path.exists() and read_json(path) != manifest:
        raise HarnessError('QUAL_DRIFT', 'the prepared qualification namespace is bound to different source or settings')
    write_jsonl(layout.local(f'{qual_root}/original.jsonl'), rows)
    permuted = sorted(rows, key=lambda r: hashlib.sha256(('20261103:' + r['id']).encode()).hexdigest())
    write_jsonl(layout.local(f'{qual_root}/permuted.jsonl'), permuted)
    write_json(layout.local(f'{PREFIX}/response_schema.json'), benchmark.JSON_SCHEMA)
    write_json(path, manifest)
    capture_rows = [{'row_key': r['id'], 'question': questions[r['source_row_key']]['question']} for r in rows]
    write_jsonl(layout.local(f'{qual_root}/capture_rows.jsonl'), capture_rows)
    write_json(layout.local(f'{qual_root}/capture_request.json'), astra_capture.make_request(proposal, model, capture_rows))
    for name in ('original', 'resume'):
        config = capture_config(proposal, layout)
        config['rows_path'] = layout.ref(f'{qual_root}/capture_rows.jsonl')
        config['output_dir'] = layout.ref(f'{qual_root}/capture_{name}')
        write_yaml(layout.local(f'{qual_root}/capture_{name}.yaml'), config)
    return {'rows': N, 'binding_sha256': canonical_sha256(manifest['binding']), 'new_model_inference': False}


def run(proposal, root, layout, model, name, *, ack):
    if not ack:
        raise HarnessError('GPU_ACK', 'qualification requires explicit --gpu-ack')
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    qual_root = qualification_root(runtime)
    if os.environ.get('EHR_RUNTIME_IMAGE_ID') != runtime['evaluation']['image_digest']:
        raise HarnessError('QUAL_IMAGE', 'use the exact registered evaluation image')
    if os.environ.get('VLLM_BATCH_INVARIANT') != '1':
        raise HarnessError('QUAL_INVARIANCE', 'set VLLM_BATCH_INVARIANT=1 before startup')
    manifest = read_json(layout.local(f'{qual_root}/manifest.json'))
    if manifest['binding'] != binding(proposal, runtime) or manifest['model_path'] != str(model.resolve()):
        raise HarnessError('QUAL_DRIFT', 'qualification source, settings or base model changed')
    original = read_jsonl(layout.local(f'{qual_root}/original.jsonl'))
    if len(original) != N or canonical_sha256(original) != manifest['rows_sha256']:
        raise HarnessError('QUAL_ROSTER', 'only the twenty prepared development prompts are allowed')
    order = 'permuted' if name.startswith('permuted') else 'original'
    rows = read_jsonl(layout.local(f'{qual_root}/{order}.jsonl'))
    if sorted(rows, key=lambda r: r['id']) != sorted(original, key=lambda r: r['id']):
        raise HarnessError('QUAL_ROSTER', 'permuted qualification prompts differ')
    args = batch_arguments(proposal, runtime, layout, model, layout.ref(f'{qual_root}/{order}.jsonl'), layout.ref(f'{qual_root}/runs/{name}'))
    lockpath = layout.local(f'{PREFIX}/gpu-writer.lock')
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    with lockpath.open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HarnessError('ACTIVE_WRITER', 'another stage owns the GPU lock') from exc
        start = time.monotonic()
        append_jsonl(layout.local(f'{qual_root}/operations.jsonl'), {'event': 'start', 'run': name, 'time': time.time(),
                                                               'binding_sha256': canonical_sha256(manifest['binding'])})
        _engine(root).run('batch-generate', args, guard_parent=True, pass_fds=(lock.fileno(),))
        append_jsonl(layout.local(f'{qual_root}/operations.jsonl'), {'event': 'end', 'run': name,
                                                               'wall_seconds': time.monotonic() - start, 'time': time.time()})
    return {'run': name, 'rows': N, 'scored': False}


def compare(original, runs):
    if set(runs) != set(RUNS):
        raise HarnessError('QUAL_INCOMPLETE', 'four repeats and the resumed run are required')
    expected = {r['id']: r for r in original}
    canonical = None
    for name in RUNS:
        rows = runs[name]
        if len(rows) != N or len({r['id'] for r in rows}) != N or {r['id'] for r in rows} != set(expected):
            raise HarnessError('QUAL_ROSTER', 'qualification completions have missing, extra or duplicate ids')
        for row in rows:
            e = expected[row['id']]
            if (row.get('prompt_sha256') != e['expected_prompt_sha256']
                    or row.get('prompt_token_ids_sha256') != e['expected_token_ids_sha256']
                    or row.get('prompt_token_len') != e['expected_prompt_tokens']):
                raise HarnessError('QUAL_TOKENIZER', 'runtime prompt bytes or token IDs differ from the renderer')
            try:
                jsonschema.validate(json.loads(row['completion_text']), benchmark.JSON_SCHEMA)
            except (ValueError, jsonschema.ValidationError) as exc:
                raise HarnessError('QUAL_SCHEMA', 'qualification output is not valid whole JSON, without salvage') from exc
            if not row.get('completion_token_ids') or row.get('finish_reason') != 'stop':
                raise HarnessError('QUAL_FINISH', 'qualification requires natural termination and retained token IDs')
        signature = canonical_sha256(sorted(rows, key=lambda r: r['id']))
        if canonical is not None and signature != canonical:
            raise HarnessError('QUAL_PARITY', 'repeats, permutation or resume changed persisted output')
        canonical = signature
    return {'rows': N, 'runs': len(RUNS), 'canonical_output_sha256': canonical,
            'completion_token_ids_identical': True, 'finish_reasons_identical': True, 'whole_schema_valid': True}


def verify(proposal, layout):
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    qual_root = qualification_root(runtime)
    manifest = read_json(layout.local(f'{qual_root}/manifest.json'))
    if manifest['binding'] != binding(proposal, runtime):
        raise HarnessError('QUAL_DRIFT', 'qualification evidence belongs to different source/settings')
    original = read_jsonl(layout.local(f'{qual_root}/original.jsonl'))
    runs = {name: read_jsonl(layout.local(f'{qual_root}/runs/{name}/completions.jsonl')) for name in RUNS}
    report = compare(original, runs)
    kill = read_json(layout.local(f'{qual_root}/kill_evidence.json'))
    before = layout.local(f'{qual_root}/before_completions.jsonl')
    prefix = read_jsonl(before)
    if (kill.get('signal') != 'SIGKILL' or kill.get('container_exit_code') != 137
            or kill.get('image_digest') != runtime['evaluation']['image_digest']
            or not kill.get('container_id') or not 0 < len(prefix) < N
            or kill.get('before_rows') != len(prefix) or kill.get('before_sha256') != sha256_file(before)
            or runs['resume'][:len(prefix)] != prefix):
        raise HarnessError('QUAL_RESUME', 'hard-kill evidence does not show an exact retained partial prefix')
    report.update(passed=True, binding=manifest['binding'], kill_evidence=kill, scored=False)
    write_json(layout.local(f'{qual_root}/qualification.json'), report)
    return report


def verify_capture(proposal, layout, base_tensor):
    """Hash-check actual site captures and compare hard-resume with uninterrupted."""
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    qual_root = qualification_root(runtime)
    keys = [r['row_key'] for r in read_jsonl(layout.local(f'{qual_root}/capture_rows.jsonl'))]
    if len(keys) != N:
        raise HarnessError('QUAL_ROSTER', 'capture qualification requires the same twenty development prompts')
    manifests, loaded = {}, {}
    for name in ('original', 'resume'):
        directory = layout.local(f'{qual_root}/capture_{name}')
        astra_capture.verify_request(proposal, directory, layout.local(f'{qual_root}/capture_request.json'), keys)
        manifests[name] = capture.load_manifest(directory)
        loaded[name] = [capture.read_row(directory, r, hidden_state=proposal.patch['hidden_state'],
                                        sites=[(proposal.patch['decoder_block'], 'mlp.down_proj', t) for t in ('input', 'output')])
                        for r in manifests[name]['rows']]
    if manifests['original']['rows'] != manifests['resume']['rows']:
        raise HarnessError('QUAL_CAPTURE_PARITY', 'capture rows or tensor bytes changed across resume')
    before = layout.local(f'{qual_root}/capture_before.jsonl')
    prefix = read_jsonl(before)
    kill = read_json(layout.local(f'{qual_root}/capture_kill_evidence.json'))
    if (kill.get('signal') != 'SIGKILL' or kill.get('container_exit_code') != 137
            or kill.get('image_digest') != runtime['capture']['image_digest'] or not kill.get('container_id')
            or not 4 <= len(prefix) < N or kill.get('before_rows') != len(prefix)
            or kill.get('before_sha256') != sha256_file(before)
            or manifests['resume']['rows'][:len(prefix)] != prefix):
        raise HarnessError('QUAL_CAPTURE_RESUME', 'capture hard-kill evidence lacks an exact retained partial prefix')
    site_in = capture.site_key(proposal.patch['decoder_block'], 'mlp.down_proj', 'input')
    site_out = capture.site_key(proposal.patch['decoder_block'], 'mlp.down_proj', 'output')
    inputs = np.stack([r['sites'][site_in] for r in loaded['original']])
    outputs = np.stack([r['sites'][site_out] for r in loaded['original']])
    base = np.load(base_tensor, allow_pickle=False)
    report = {'passed': True, 'rows': N, 'tensor_bytes_identical': True, 'kill_evidence': kill,
              'base_tensor_sha256': astra_fixed.bf16_raw_sha256(base),
              'linear_consistency': astra_capture.linear_consistency(inputs, inputs[:0], outputs, base, proposal)}
    write_json(layout.local(f'{qual_root}/capture_qualification.json'), report)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare')
    a.add_argument('--model', type=Path, required=True)
    r = sub.add_parser('run')
    r.add_argument('--model', type=Path, required=True)
    r.add_argument('--name', choices=RUNS, required=True)
    r.add_argument('--gpu-ack', action='store_true')
    sub.add_parser('verify')
    v = sub.add_parser('verify-capture')
    v.add_argument('--base-tensor', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        proposal = astra_fixed.load_proposal(EXPERIMENT_DIR / 'astra_r1.yaml')
        root = find_project_root()
        layout = Layout(root)
        result = (verify_capture(proposal, layout, args.base_tensor) if args.command == 'verify-capture'
                  else prepare(proposal, layout, args.model) if args.command == 'prepare'
                  else run(proposal, root, layout, args.model, args.name, ack=args.gpu_ack) if args.command == 'run'
                  else verify(proposal, layout))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except HarnessError as exc:
        print(json.dumps({'error': exc.code, 'message': exc.message}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
