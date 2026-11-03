"""Registered Astra workflow using the installed engine's public CLI.

Preparation is CPU-only. Capture and evaluation refuse an unsigned experiment.
The numerical patch is frozen in Git before any benchmark generation. All model
execution remains in the pinned desktop containers, through EngineCLI.
"""
from __future__ import annotations

import argparse
import fcntl
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

from . import astra_benchmark as benchmark
from . import astra_capture, astra_fixed, commitments
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

PREFIX = 'astra-r1'


def plan(proposal) -> dict:
    evaluation = proposal.raw['evaluation']
    return {'proposal_sha256': proposal.sha256, 'launch_authority': False,
            'construction': ['sign construction and evaluation contracts', 'capture 64 U + 64 K P-struct anchors',
                             'derive one sparse patch', 'validate and export', 'read back and audit',
                             'freeze exact patch and export hashes in Git'],
            'evaluation_cells': [{'surface': s, 'prompt': p, 'arm': a, 'rows': spec['rows']}
                                 for s, spec in evaluation['surfaces'].items()
                                 for p in evaluation['prompts'] for a in evaluation['arms']],
            'initial_completions': evaluation['initial_completions'],
            'maximum_completions_including_format_retries': evaluation['maximum_evaluation_completions_including_retries'],
            'acceptance': 'all detector-negative rows -> committed blinded adjudication -> paired roll-up',
            'pending_before_sign': ['evaluation runtime digest and invariance smoke', 'decoy feasibility',
                                    'synthetic export/readback', 'measured persistence declarations and formal signing']}


def require_signed(directory: Path, *, runtime_role: str) -> dict:
    manifest = yaml.safe_load((directory / 'experiment.yaml').read_text())
    if manifest['status'] not in ('signed', 'running'):
        raise HarnessError('UNSIGNED', 'the draft does not authorize capture or evaluation')
    instrument = manifest['instrument']
    for name in instrument['configs'] + instrument['modules']:
        if instrument.get('pins', {}).get(name) != sha256_file(directory / name):
            raise HarnessError('INSTRUMENT_DRIFT', 'a registered instrument file is unpinned or changed')
    runtime = yaml.safe_load((directory / 'astra_runtime.yaml').read_text())
    digest = runtime[runtime_role].get('image_digest')
    if not digest or os.environ.get('EHR_RUNTIME_IMAGE_ID') != digest:
        raise HarnessError('RUNTIME_BINDING', 'run inside the registered image and record its actual image ID')
    if runtime_role == 'evaluation' and runtime[runtime_role].get('qualified') is not True:
        raise HarnessError('RUNTIME_UNQUALIFIED', 'the real model invariance and resume smoke is still required')
    return runtime


def _engine(root):
    from engine_host.cli_boundary import EngineCLI
    return EngineCLI(root, plugin_roots=(EXPERIMENT_DIR,))


def _gpu(root, layout, operation, arguments, *, ack: bool, role: str, cli=None):
    if not ack:
        raise HarnessError('GPU_ACK', 'pass --gpu-ack for this exact GPU stage')
    require_signed(EXPERIMENT_DIR, runtime_role=role)
    lockpath = layout.local(f'{PREFIX}/gpu-writer.lock')
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    with lockpath.open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HarnessError('ACTIVE_WRITER', 'another Astra stage owns the GPU writer lock') from exc
        start = time.monotonic()
        journal = layout.local(f'{PREFIX}/operations.jsonl')
        append_jsonl(journal, {'event': 'start', 'operation': operation, 'arguments': arguments,
                               'image': os.environ['EHR_RUNTIME_IMAGE_ID'], 'time': time.time()})
        code = 0
        try:
            (cli or _engine(root)).run(operation, arguments, guard_parent=True, pass_fds=(lock.fileno(),))
        except subprocess.CalledProcessError as exc:
            code = exc.returncode
            raise
        except BaseException:
            code = -1
            raise
        finally:
            append_jsonl(journal, {'event': 'end', 'operation': operation, 'exit_code': code,
                                   'wall_seconds': time.monotonic() - start, 'time': time.time()})


def materialize(proposal, layout, *, fit: Path, selfaware: Path, ambigqa: Path) -> dict:
    """Hash-check sources, strip old responses, and stage exactly the new roster."""
    base = f'{PREFIX}/inputs'
    roster_path = layout.local(f'{base}/roster.json')
    if not roster_path.exists():
        astra_fixed.prepare_roster(proposal, fit, {'selfaware': selfaware, 'ambigqa': ambigqa}, roster_path)
    roster = astra_fixed.load_roster(proposal, roster_path)
    if sha256_file(fit) != proposal.raw['development']['fit_sha256']:
        raise HarnessError('INPUT_HASH', 'FIT source changed')
    source = {r['row_key']: r for r in read_jsonl(fit)}
    ordered = roster['keys']['confab'] + roster['keys']['known_correct_answered']
    capture_rows = [{'row_key': key, 'question': source[key]['question']} for key in ordered]
    target = layout.local(f'{base}/capture_rows.jsonl')
    if target.exists() and read_jsonl(target) != capture_rows:
        raise HarnessError('INPUT_DRIFT', 'staged development questions changed')
    write_jsonl(target, capture_rows)
    counts = {}
    for name, path in (('selfaware', selfaware), ('ambigqa', ambigqa)):
        rows = benchmark.load_surface(proposal, name, path)
        target = layout.local(f'{base}/{name}.jsonl')
        if target.exists() and read_jsonl(target) != rows:
            raise HarnessError('INPUT_DRIFT', 'staged benchmark rows changed')
        write_jsonl(target, rows)
        counts[name] = len(rows)
    record = {'proposal_sha256': proposal.sha256, 'roster_sha256': roster['roster_sha256'], 'counts': counts,
              'files': {p.name: sha256_file(p) for p in sorted(layout.local(base).glob('*'))}}
    write_json(layout.local(f'{PREFIX}/materialized.json'), record)
    return record


def capture_config(proposal, layout) -> dict:
    c = proposal.raw['development']['capture']
    return {'rows_path': layout.ref(f'{PREFIX}/inputs/capture_rows.jsonl'),
            'output_dir': layout.ref(f'{PREFIX}/capture'), 'render_fn': 'hs20_nwe.astra_render:render_pstruct',
            'families': ['anchor'], 'layers': [c['hidden_state']], 'every_k': c['every_k'],
            'max_new_tokens': c['max_new_tokens'], 'forward_only': True, 'use_cache': c['use_cache'], 'resume': True,
            'capture_sites': [{'layer': proposal.patch['decoder_block'], 'module': c['module'], 'tensor': t}
                              for t in c['tensors']]}


def capture(proposal, root, layout, model: Path, *, ack: bool):
    require_signed(EXPERIMENT_DIR, runtime_role='capture')
    os.environ['HS20NWE_RENDER_MODEL'] = str(model.resolve())
    os.environ['HS20NWE_RENDER_REVISION'] = proposal.raw['model']['revision']
    rows = read_jsonl(layout.local(f'{PREFIX}/inputs/capture_rows.jsonl'))
    request = astra_capture.make_request(proposal, model, rows)
    request_path = layout.local(f'{PREFIX}/capture_request.json')
    if request_path.exists() and read_json(request_path) != request:
        raise HarnessError('CAPTURE_DRIFT', 'expected capture changed; resume in the original namespace')
    write_json(request_path, request)
    config_path = layout.local(f'{PREFIX}/capture.yaml')
    write_yaml(config_path, capture_config(proposal, layout))
    _gpu(root, layout, 'mechinterp', ['extract', '--mi-config', layout.ref(f'{PREFIX}/capture.yaml'),
                                    '--model', str(model.resolve()), '--model-revision', proposal.raw['model']['revision'],
                                    '--i-know-this-runs-on-gpu'], ack=ack, role='capture')
    return astra_capture.verify_request(proposal, layout.local(f'{PREFIX}/capture'), request_path,
                                        [r['row_key'] for r in rows])


def require_frozen(proposal, layout, base_model: Path, edited_model: Path) -> dict:
    """Only the audited numerical edit named by a public Git commitment is usable."""
    frozen = read_json(commitments.public_path(layout, 'astra_patch_freeze.json'))
    commitments.require_git(layout, 'astra_patch_freeze.json', frozen)
    if frozen['proposal_sha256'] != proposal.sha256:
        raise HarnessError('PATCH_FREEZE', 'the frozen numerical patch belongs to another proposal')
    for ref, digest in frozen['artifacts'].items():
        if sha256_file(layout.to_local(ref)) != digest:
            raise HarnessError('PATCH_FREEZE', 'a frozen patch, audit or export artifact changed')
    audit = read_json(layout.to_local(frozen['audit_ref']))
    if not audit.get('passed') or audit.get('spec_sha256') != frozen['spec_sha256']:
        raise HarnessError('PATCH_FREEZE', 'the frozen patch has no matching passed realized audit')
    for model, hashes in ((base_model, frozen['base_files_sha256']),
                           (edited_model, frozen['edited_files_sha256'])):
        for name, digest in hashes.items():
            if sha256_file(model / name) != digest:
                raise HarnessError('PATCH_FREEZE', 'the checkpoint differs from its byte pins')
    return frozen


def freeze(proposal, layout, *, base_model: Path, edited_model: Path, audit_ref: str, spec_ref: str,
           payload_ref: str, prepare_ref: str) -> dict:
    """Export a text-free exact edit commitment; the lead makes the Git commit."""
    require_signed(EXPERIMENT_DIR, runtime_role='capture')
    audit, prepared = read_json(layout.to_local(audit_ref)), read_json(layout.to_local(prepare_ref))
    spec = sha256_file(layout.to_local(spec_ref))
    if (not audit.get('passed') or audit.get('proposal_sha256') != proposal.sha256
            or audit.get('spec_sha256') != spec or prepared.get('spec_sha256') != spec
            or audit.get('prepare_report_sha256') != sha256_file(layout.to_local(prepare_ref))
            or audit.get('payload_sha256') != sha256_file(layout.to_local(payload_ref))):
        raise HarnessError('PATCH_FREEZE', 'prepare, spec, payload and passed audit must identify the same edit')
    # Every base sidecar must survive export byte-for-byte. Only checkpoint
    # shards are allowed to differ; the engine validates all untouched tensors.
    base_files = {p.relative_to(base_model).as_posix(): sha256_file(p)
                  for p in sorted(base_model.rglob('*')) if p.is_file()}
    edited_files = {p.relative_to(edited_model).as_posix(): sha256_file(p)
                    for p in sorted(edited_model.rglob('*')) if p.is_file()}
    shards = proposal.raw['model']['files_sha256']
    if any(base_files.get(n) != h for n, h in shards.items()):
        raise HarnessError('BASE_HASH', 'base model differs from its registered shards')
    if any(edited_files.get(n) != h for n, h in base_files.items() if n not in shards):
        raise HarnessError('EXPORT_SIDECARS', 'tokenizer/config/other base sidecars changed or were omitted')
    export = edited_model / 'mechinterp-weight-export.manifest.json'
    if not export.is_file():
        raise HarnessError('EXPORT_MANIFEST', 'only an engine-verified export may be frozen')
    export_record = read_json(export)
    if (export_record.get('schema_version') != 'mechinterp-weight-export/v1'
            or export_record.get('spec', {}).get('sha256') != spec
            or export_record.get('payload', {}).get('sha256') != audit.get('payload_sha256')
            or export_record.get('totals', {}).get('tensors_modified') != 1
            or export_record.get('totals', {}).get('noop') is not False
            or any(edited_files.get(name) != info.get('sha256')
                   for name, info in export_record.get('output', {}).get('weight_files', {}).items())):
        raise HarnessError('EXPORT_MANIFEST', 'the export receipt does not bind this exact nonzero patch and checkpoint')
    refs = (audit_ref, spec_ref, payload_ref, prepare_ref,
            layout.ref(f'{PREFIX}/materialized.json'), layout.ref(f'{PREFIX}/tokenizer_preflight.json'),
            layout.ref(f'{PREFIX}/inputs/roster.json'), layout.ref(f'{PREFIX}/capture_request.json'),
            layout.ref(f'{PREFIX}/capture/manifest.json'))
    if read_json(layout.local(f'{PREFIX}/tokenizer_preflight.json')).get('passed') is not True:
        raise HarnessError('TOKENIZER_PREFLIGHT', 'full-surface tokenizer feasibility must pass before the patch freeze')
    document = {'schema_version': 'ehr-astra-patch-freeze/v1', 'proposal_sha256': proposal.sha256,
                'spec_sha256': spec, 'audit_ref': audit_ref,
                'artifacts': {r: sha256_file(layout.to_local(r)) for r in refs},
                'base_files_sha256': base_files, 'edited_files_sha256': edited_files,
                'export_manifest_sha256': sha256_file(export),
                'note': 'Commit this public hash-only file before any benchmark generation.'}
    target = commitments.public_path(layout, 'astra_patch_freeze.json')
    if target.exists():
        if read_json(target) != document:
            raise HarnessError('PATCH_FREEZE', 'the first numerical freeze is final')
    else:
        commitments.export(layout, 'astra_patch_freeze.json', document)
    return document


def preflight(proposal, layout, model: Path) -> dict:
    """Tokenizer-only length/renderer feasibility, without target generation."""
    os.environ['HS20NWE_RENDER_MODEL'] = str(model.resolve())
    os.environ['HS20NWE_RENDER_REVISION'] = proposal.raw['model']['revision']
    from .astra_render import _tokenizer
    tokenizer = _tokenizer()
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    ceiling = runtime['evaluation']['max_model_len']
    reports = []
    for name in proposal.raw['evaluation']['surfaces']:
        rows = read_jsonl(layout.local(f'{PREFIX}/inputs/{name}.jsonl'))
        for prompt in proposal.raw['evaluation']['prompts']:
            for attempt in (0, 1):  # retry 2 uses the identical retry prompt
                rendered = benchmark.prompts(rows, prompt, attempt)
                tokenized = [tokenizer.encode(r['prompt'], add_special_tokens=False) for r in rendered]
                maximum = max(map(len, tokenized))
                fits = maximum + proposal.raw['evaluation']['decode']['max_new_tokens'] <= ceiling
                reports.append({'surface': name, 'prompt': prompt, 'retry': bool(attempt),
                                'rows': len(rows), 'max_prompt_tokens': maximum, 'fits': fits,
                                'prompt_roster_sha256': canonical_sha256(rendered),
                                'tokenization_roster_sha256': canonical_sha256(tokenized)})
    result = {'proposal_sha256': proposal.sha256, 'tokenizer_revision': proposal.raw['model']['revision'],
              'context_limit': ceiling, 'surfaces': reports, 'passed': all(r['fits'] for r in reports)}
    write_json(layout.local(f'{PREFIX}/tokenizer_preflight.json'), result)
    if not result['passed']:
        raise HarnessError('CONTEXT_LENGTH', 'prospectively revise the unsigned context; never truncate evaluation questions')
    return result


def read_tensor(proposal, model: Path, expected_sha256: str, out: Path) -> dict:
    """CPU-only safetensors readback inside a torch-capable registered image."""
    import numpy as np
    import torch
    from safetensors import safe_open

    index = read_json(model / 'model.safetensors.index.json')['weight_map']
    if proposal.tensor.removesuffix('.weight') + '.bias' in index:
        raise HarnessError('CAPTURE_BIAS', 'the registered bias-free down projection has a checkpoint bias')
    shard = (model / index[proposal.tensor]).resolve()
    if not shard.is_relative_to(model.resolve()):
        raise HarnessError('TENSOR_PATH', 'the target shard escapes the checkpoint')
    with safe_open(str(shard), framework='pt', device='cpu') as handle:
        tensor = handle.get_tensor(proposal.tensor)
    if tensor.dtype != torch.bfloat16 or tuple(tensor.shape) != proposal.shape:
        raise HarnessError('TENSOR_BINDING', 'target readback has the wrong dtype or shape')
    values = tensor.float().numpy()
    digest = astra_fixed.bf16_raw_sha256(values)
    if digest != expected_sha256:
        raise HarnessError('TENSOR_HASH', 'readback differs from the engine-pinned tensor bytes')
    data = io.BytesIO()
    np.save(data, values, allow_pickle=False)
    astra_fixed._create_only(out, data.getvalue())
    return {'tensor': proposal.tensor, 'shape': list(tensor.shape), 'dtype': 'bfloat16',
            'tensor_sha256': digest, 'npy_sha256': sha256_file(out), 'bias_absent': True}


def batch_arguments(proposal, runtime, layout, model: Path, prompt_ref: str, out_ref: str) -> list[str]:
    e = runtime['evaluation']
    d = proposal.raw['evaluation']['decode']
    if e['engine'] == 'hf-batched':
        return ['--prompts', prompt_ref, '--out-dir', out_ref, '--model', str(model.resolve()),
                '--model-revision', proposal.raw['model']['revision'],
                '--tokenizer-revision', proposal.raw['model']['revision'], '--engine', 'hf-batched',
                '--compute-dtype', 'bfloat16', '--seed', str(d['seed']), '--temperature', str(d['temperature']),
                '--max-new-tokens', str(d['max_new_tokens']), '--batch-size', str(e['batch_size']),
                '--json-schema', layout.ref(f'{PREFIX}/response_schema.json'),
                '--structured-output-backend', e['structured_output_backend'], '--resume']
    if e['engine'] != 'vllm':
        raise HarnessError('EVALUATION_ENGINE', 'only the registered HF or vLLM engine is admitted')
    return ['--prompts', prompt_ref, '--out-dir', out_ref, '--model', str(model.resolve()),
            '--model-revision', proposal.raw['model']['revision'],
            '--tokenizer-revision', proposal.raw['model']['revision'], '--engine', 'vllm',
            '--compute-dtype', 'bfloat16', '--seed', str(d['seed']), '--temperature', str(d['temperature']),
            '--max-new-tokens', str(d['max_new_tokens']), '--batch-size', str(e['batch_size']),
            '--expected-vllm-version', e['vllm_version'], '--min-compute-capability', str(e['min_compute_capability']),
            '--vllm-model-runner', e['model_runner'],
            '--tensor-parallel-size', '1', '--max-num-seqs', str(e['max_num_seqs']),
            '--max-num-batched-tokens', str(e['max_num_batched_tokens']), '--max-model-len', str(e['max_model_len']),
            '--gpu-memory-utilization', str(e['gpu_memory_utilization']),
            '--limit-mm-per-prompt', '{"image":0,"video":0}',
            '--json-schema', layout.ref(f'{PREFIX}/response_schema.json'),
            '--structured-output-backend', 'xgrammar', '--resume']


def evaluate_cell(proposal, root, layout, *, surface, prompt, arm, base_model, edited_model, ack):
    runtime = require_signed(EXPERIMENT_DIR, runtime_role='evaluation')
    if runtime['evaluation']['engine'] == 'vllm' and os.environ.get('VLLM_BATCH_INVARIANT') != '1':
        raise HarnessError('BATCH_INVARIANCE', 'set VLLM_BATCH_INVARIANT=1 before process startup')
    frozen = require_frozen(proposal, layout, base_model, edited_model)
    rows = read_jsonl(layout.local(f'{PREFIX}/inputs/{surface}.jsonl'))
    original = read_json(layout.local(f'{PREFIX}/materialized.json'))
    if sha256_file(layout.local(f'{PREFIX}/inputs/{surface}.jsonl')) != original['files'][surface + '.jsonl']:
        raise HarnessError('INPUT_DRIFT', 'normalized evaluation rows changed after materialization')
    model = base_model if arm == 'base' else edited_model
    # Both arms render with the exact base tokenizer. Exported sidecar equality
    # is checked by the freeze step before this method is admitted.
    os.environ['HS20NWE_RENDER_MODEL'] = str(base_model.resolve())
    os.environ['HS20NWE_RENDER_REVISION'] = proposal.raw['model']['revision']
    write_json(layout.local(f'{PREFIX}/response_schema.json'), benchmark.JSON_SCHEMA)
    cell = f'{surface}/{prompt}/{arm}'
    pending, attempts = rows, []
    for idx in range(proposal.raw['evaluation']['max_attempts_per_item']):
        if not pending:
            break
        rel = f'{PREFIX}/evaluation/{cell}/attempt-{idx}'
        prompt_rows = benchmark.prompts(pending, prompt, idx)
        target = layout.local(rel + '/prompts.jsonl')
        if target.exists() and read_jsonl(target) != prompt_rows:
            raise HarnessError('PROMPT_DRIFT', 'a prior attempt used different prompt bytes')
        write_jsonl(target, prompt_rows)
        args = batch_arguments(proposal, runtime, layout, model, layout.ref(rel + '/prompts.jsonl'), layout.ref(rel + '/output'))
        _gpu(root, layout, 'batch-generate', args, ack=ack, role='evaluation')
        completed = read_jsonl(layout.local(rel + '/output/completions.jsonl'))
        if len(completed) != len(pending) or {r['id'] for r in completed} != {r['id'] for r in pending}:
            raise HarnessError('EVAL_ROSTER', 'generation is incomplete or duplicated')
        attempts.append(completed)
        invalid = {r['id'] for r in completed if benchmark.legacy.parse_stated_confidence(r['completion_text']).stated_confidence is None}
        pending = [r for r in rows if r['id'] in invalid]
    merged = benchmark.merge_attempts(rows, attempts)
    output = layout.local(f'{PREFIX}/evaluation/{cell}/final.jsonl')
    write_jsonl(output, merged)
    record = {'cell': cell, 'proposal_sha256': proposal.sha256, 'patch_freeze_sha256':
              sha256_file(commitments.public_path(layout, 'astra_patch_freeze.json')),
              'spec_sha256': frozen['spec_sha256'], 'rows': len(merged), 'output_sha256': sha256_file(output),
              'generation_attempts': sum(r['generation_attempts'] for r in merged)}
    write_json(output.with_suffix('.manifest.json'), record)
    return record


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proposal', type=Path, default=EXPERIMENT_DIR / 'astra_r1.yaml')
    p.add_argument('--project-root', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('plan')
    f = sub.add_parser('freeze')
    f.add_argument('--base-model', type=Path, required=True)
    f.add_argument('--edited-model', type=Path, required=True)
    for name in ('audit', 'spec', 'payload', 'prepare'):
        f.add_argument('--' + name + '-ref', required=True)
    pf = sub.add_parser('preflight')
    pf.add_argument('--model', type=Path, required=True)
    tr = sub.add_parser('read-tensor')
    tr.add_argument('--model', type=Path, required=True)
    tr.add_argument('--expected-sha256', required=True)
    tr.add_argument('--out', type=Path, required=True)
    m = sub.add_parser('materialize')
    for name in ('fit', 'selfaware', 'ambigqa'):
        m.add_argument('--' + name, type=Path, required=True)
    c = sub.add_parser('capture')
    c.add_argument('--model', type=Path, required=True)
    c.add_argument('--gpu-ack', action='store_true')
    e = sub.add_parser('eval-cell')
    e.add_argument('--surface', choices=('selfaware', 'ambigqa'), required=True)
    e.add_argument('--prompt', choices=('P-struct', 'P-rc'), required=True)
    e.add_argument('--arm', choices=('base', 'edited'), required=True)
    e.add_argument('--base-model', type=Path, required=True)
    e.add_argument('--edited-model', type=Path, required=True)
    e.add_argument('--gpu-ack', action='store_true')
    args = p.parse_args(argv)
    try:
        proposal = astra_fixed.load_proposal(args.proposal)
        if args.command == 'plan':
            result = plan(proposal)
        elif args.command == 'read-tensor':
            result = read_tensor(proposal, args.model, args.expected_sha256, args.out)
        else:
            root = find_project_root(args.project_root)
            layout = Layout(root)
            if args.command == 'materialize':
                result = materialize(proposal, layout, fit=args.fit, selfaware=args.selfaware, ambigqa=args.ambigqa)
            elif args.command == 'preflight':
                result = preflight(proposal, layout, args.model)
            elif args.command == 'freeze':
                result = freeze(proposal, layout, base_model=args.base_model, edited_model=args.edited_model,
                                audit_ref=args.audit_ref, spec_ref=args.spec_ref, payload_ref=args.payload_ref,
                                prepare_ref=args.prepare_ref)
            elif args.command == 'capture':
                result = capture(proposal, root, layout, args.model, ack=args.gpu_ack)
            else:
                result = evaluate_cell(proposal, root, layout, surface=args.surface, prompt=args.prompt, arm=args.arm,
                                       base_model=args.base_model, edited_model=args.edited_model, ack=args.gpu_ack)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (HarnessError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
