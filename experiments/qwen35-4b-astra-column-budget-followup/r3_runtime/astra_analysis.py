"""Use the existing committed blinded lane for the eight fixed benchmark cells."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import adjudication as lane
from . import astra_benchmark as benchmark
from . import astra_fixed, commitments
from .astra_run import PREFIX, require_signed
from .config import EXPERIMENT_DIR, Layout, find_project_root
from .util import (
    HarnessError,
    canonical_sha256,
    read_json,
    read_jsonl,
    sha256_file,
    write_json,
)


@dataclass
class GradingCell:
    """Supply the existing lane's two config/stamp methods from the active profile."""
    proposal: astra_fixed.Proposal
    runtime: dict

    @property
    def cell(self):
        return {'grading': self.proposal.raw['grading']}

    def stamp(self):
        return {'cell_sha256': self.proposal.sha256,
                'gates_sha256': canonical_sha256(self.proposal.raw['evaluation']['gates']),
                'engine_wheel_sha256': self.runtime['engine']['wheel_sha256'],
                'engine_source_commit': self.runtime['engine']['source_commit']}


def prepare_decoys(proposal, layout, *, fit, baseline, positive, out):
    """Pre-sign calibration from prior outputs, never from this study's responses."""
    cfg = proposal.raw['grading']['decoy_sources']
    for path, digest in ((fit, proposal.raw['development']['fit_sha256']),
                         (baseline, cfg['baseline_sha256']), (positive, cfg['positive_sha256'])):
        if sha256_file(path) != digest:
            raise HarnessError('DECOY_SOURCE', 'historical calibration bytes differ from their prospective pins')
    rows = read_jsonl(fit)
    evaluation = {s: [r['question'] for r in read_jsonl(layout.local(f'{PREFIX}/inputs/{s}.jsonl'))]
                  for s in proposal.raw['evaluation']['surfaces']}
    roster = astra_fixed.select_roster(rows, evaluation, seed=proposal.raw['development']['seed'],
                                      counts=proposal.group_size)
    selected = set(roster['keys']['confab'] + roster['keys']['known_correct_answered'])
    excluded = {astra_fixed.normalize_question(q) for qs in evaluation.values() for q in qs}
    source = {r['row_key']: r for r in rows if r['row_key'] not in selected
              and astra_fixed.normalize_question(r['question']) not in excluded}
    pools = {'pos': {}, 'neg': {}}
    for kind, path, role in (('pos', positive, 'confab'), ('neg', baseline, 'known_correct_answered')):
        for r in read_jsonl(path):
            key = r['row_key']
            s = source.get(key)
            if not s or s['role'] != role or not r.get('terminated_naturally'):
                continue
            if kind == 'pos' and r.get('dose_multiplier') != cfg['positive_dose_multiplier']:
                continue
            try:
                answer = json.loads(r['answer_text'])['answer']
            except (ValueError, KeyError, TypeError):
                continue
            if not isinstance(answer, str):
                continue
            screened = benchmark.grade_one_v2(answer, s.get('aliases', []))
            if screened['degenerate']:
                continue
            if kind == 'pos':
                eligible = answer.strip().casefold().rstrip('.!?') in ("i don't know the answer", 'i do not know the answer')
            else:
                eligible = (not screened['refused_v2'] and benchmark.legacy.normalize(answer)
                            in {benchmark.legacy.normalize(a) for a in s.get('aliases', [])})
            if eligible:
                entry = {'kind': 'decoy_pos' if kind == 'pos' else 'decoy_neg', 'arm': 'decoy',
                         'row_key': key, 'text': answer,
                         'question_sha256': canonical_sha256(astra_fixed.normalize_question(s['question']))}
                if key in pools[kind] and pools[kind][key] != entry:
                    raise HarnessError('DECOY_DUPLICATE', 'a calibration source key has conflicting outputs')
                pools[kind][key] = entry
    need = int(cfg['counts_per_class'])
    counts = {k: len(v) for k, v in pools.items()}
    if any(n < need for n in counts.values()):
        raise HarnessError('DECOY_FLOOR', f'actual prior pools have {counts}; need {need} of each')
    document = {k: [v[key] for key in sorted(v, key=lambda s: s.encode())[:need]] for k, v in pools.items()}
    astra_fixed._create_only(out, astra_fixed._json_bytes(document))
    return {'eligible_counts': counts, 'selected_per_class': need, 'decoys_sha256': sha256_file(out),
            'sources': cfg, 'excluded_construction_and_eval': True, 'new_model_inference': False}


def load_cells(proposal, layout):
    freeze_path = commitments.public_path(layout, 'astra_patch_freeze.json')
    frozen = read_json(freeze_path)
    commitments.require_git(layout, 'astra_patch_freeze.json', frozen)
    if frozen['proposal_sha256'] != proposal.sha256:
        raise HarnessError('PATCH_FREEZE', 'the evaluation belongs to another proposal')
    qpath = commitments.public_path(layout, 'astra_edited_qualification.json')
    q = read_json(qpath)
    commitments.require_git(layout, 'astra_edited_qualification.json', q)
    if (q.get('passed') is not True or q.get('scored') is not False
        or q.get('binding', {}).get('proposal_sha256') != proposal.sha256
        or q.get('binding', {}).get('patch_freeze_sha256') != sha256_file(freeze_path)):
        raise HarnessError('EDITED_QUALIFICATION', 'scoring requires the same committed edited qualification')
    records, graded, manifests = {}, {}, {}
    cfg = proposal.raw['evaluation']
    for surface, spec in cfg['surfaces'].items():
        for prompt in cfg['prompts']:
            for arm in cfg['arms']:
                job = f'{surface}/{prompt}/{arm}'
                path = layout.local(f'{PREFIX}/evaluation/{job}/final.jsonl')
                m = read_json(path.with_suffix('.manifest.json'))
                rows = read_jsonl(path)
                if (m['proposal_sha256'] != proposal.sha256 or m['patch_freeze_sha256'] != sha256_file(freeze_path)
                        or m['spec_sha256'] != frozen['spec_sha256'] or m.get('qualification_sha256') != sha256_file(qpath) or m['output_sha256'] != sha256_file(path)
                        or len(rows) != spec['rows'] or len({r['id'] for r in rows}) != len(rows)
                        or any(sum(r['label'] == label for r in rows) != spec[label] for label in ('known', 'unknown'))):
                    raise HarnessError('EVAL_BINDING', 'cell output, rows or numerical edit differ from the frozen evaluation')
                source_rows = read_jsonl(layout.local(f'{PREFIX}/inputs/{surface}.jsonl'))
                if [{k: row[k] for k in ('id', 'question', 'label', 'aliases', 'source')} for row in rows] != source_rows:
                    raise HarnessError('EVAL_PAIRING', 'final rows differ from the exact normalized benchmark roster')
                records[job], graded[job], manifests[job] = rows, benchmark.grade(rows, job), m
    return records, graded, manifests


def build_pool(proposal, layout, cell, decoys_path):
    records, graded, manifests = load_cells(proposal, layout)
    decoy_pin = proposal.raw['grading'].get('decoys_sha256')
    if not decoy_pin or sha256_file(decoys_path) != decoy_pin:
        raise HarnessError('DECOY_BINDING', 'the actual held-back decoy pool must be hash-pinned before signing')
    decoys = read_json(decoys_path)
    ids = [r['row_key'] for group in ('pos', 'neg') for r in decoys[group]]
    scored_ids = {r['id'] for rows in records.values() for r in rows}
    g = proposal.raw['grading']
    if (len(set(ids)) != len(ids) or set(ids) & scored_ids
            or len(decoys['pos']) < g['positive_decoys_per_shard']
            or len(decoys['neg']) < g['negative_decoys_per_shard']):
        raise HarnessError('DECOY_FLOOR', 'decoys are duplicated, scored or below the actual registered floor')
    text_records = {job: [{'row_key': r['id'], 'answer_text': benchmark.legacy.parse_stated_confidence(r['generated_answer']).answer_text}
                          for r in rows] for job, rows in records.items()}
    cores = lane.core_items(text_records, graded)
    binding = {'schema_version': 'ehr-astra-evaluation-binding/v1', **cell.stamp(),
               'patch_freeze_sha256': sha256_file(commitments.public_path(layout, 'astra_patch_freeze.json')),
               'outputs': {job: m['output_sha256'] for job, m in manifests.items()}, 'decoys_sha256': decoy_pin}
    path = commitments.public_path(layout, 'run_binding.json')
    if path.exists() and read_json(path) != binding:
        raise HarnessError('BINDING_DRIFT', 'the first completed-evaluation binding is final')
    commitments.export(layout, 'run_binding.json', binding)
    manifest = lane.build_pool(cell, layout, cores, decoys)
    return {'candidates': len(cores), 'shards': len(manifest['shards']),
            'next': 'pool-commit, then commit run_binding.json and adjudication_pool_manifest.json before any grading'}


def rollup(proposal, layout, cell):
    try:
        records, graded, manifests = load_cells(proposal, layout)
        report = read_json(lane.Pool(layout).report)
        if report.get('terminal_void'):
            return {'verdict': 'instrument_invalid', 'reason': 'blinded_adjudication_void'}
        try:
            applied = lane.load_applied(layout,cell)
        except FileNotFoundError as exc:
            if report.get('instrument_valid'):
                raise HarnessError('ADJUDICATION_EVIDENCE','accepted adjudication lost committed evidence') from exc
            raise
        expected = {(job, row['row_key']) for job, rows in graded.items() for row in rows if not row['refused_v2']}
        if set(applied) != expected:
            raise HarnessError('ADJUDICATION_COVERAGE', 'adjudicated results differ from the complete frozen pool')
        binding = read_json(commitments.public_path(layout, 'run_binding.json'))
        commitments.require_git(layout, 'run_binding.json', binding)
        if any(binding.get(k) != v for k, v in cell.stamp().items()):
            raise HarnessError('BINDING_DRIFT', 'the analysis profile differs from the grading commitment')
        if (binding.get('outputs') != {job:m['output_sha256'] for job,m in manifests.items()}
            or binding.get('patch_freeze_sha256') != sha256_file(commitments.public_path(layout,'astra_patch_freeze.json'))):
            raise HarnessError('BINDING_DRIFT','current answers differ from the committed grading inputs')
        vectors = {job: benchmark.semantic_vectors(rows, {key: value for (arm, key), value in applied.items() if arm == job})
                   for job, rows in graded.items()}
        comparisons = {f'{surface}/{prompt}': benchmark.compare(vectors[f'{surface}/{prompt}/base'],
                                                               vectors[f'{surface}/{prompt}/edited'], proposal)
                       for surface in proposal.raw['evaluation']['surfaces']
                       for prompt in proposal.raw['evaluation']['prompts']}
        primary = '/'.join(proposal.raw['evaluation']['primary'])
        transfer = '/'.join(proposal.raw['evaluation']['transfer'])
        return {'verdict': 'primary_pass' if comparisons[primary]['passed'] else 'primary_prediction_falsified',
                'transfer_supported': comparisons[transfer]['passed'], 'comparisons': comparisons,
                'legacy_benchmark': {job: benchmark.legacy_report(rows) for job, rows in records.items()},
                'proposal_sha256': proposal.sha256, 'basis': 'frozen_detector_plus_committed_blinded_adjudication'}
    except FileNotFoundError:
        return {'verdict': 'incomplete', 'reason': 'required evaluation or grading artifact is absent'}
    except HarnessError as exc:
        if exc.code == 'INSTRUMENT_VOID':
            return {'verdict': 'incomplete', 'reason': 'adjudication is absent or awaiting regrade'}
        return {'verdict': 'instrument_invalid', 'reason': str(exc)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proposal', type=Path, default=EXPERIMENT_DIR / 'astra_r3.yaml')
    p.add_argument('--project-root', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    d = sub.add_parser('prepare-decoys')
    for name in ('fit', 'baseline', 'positive', 'out'):
        d.add_argument('--' + name, type=Path, required=True)
    b = sub.add_parser('pool-build')
    b.add_argument('--decoys', type=Path, required=True)
    sub.add_parser('pool-commit')
    ch = sub.add_parser('commit-hash')
    ch.add_argument('--shard-id', required=True)
    ch.add_argument('--graded-file', type=Path, required=True)
    rg = sub.add_parser('regrade')
    rg.add_argument('--shard-id', required=True)
    rg.add_argument('--graded-file', type=Path, required=True)
    for command in ('spot-pack', 'apply'):
        s = sub.add_parser(command)
        s.add_argument('--graded-map', type=Path, required=True)
    sp = sub.add_parser('spot-record')
    sp.add_argument('--decisions', type=Path, required=True)
    sub.add_parser('rollup')
    args = p.parse_args(argv)
    proposal = astra_fixed.load_proposal(args.proposal)
    root = find_project_root(args.project_root)
    layout = Layout(root)
    runtime = yaml.safe_load((EXPERIMENT_DIR / 'astra_runtime.yaml').read_text())
    cell = GradingCell(proposal, runtime)
    if args.command not in ('rollup', 'prepare-decoys'):
        require_signed(EXPERIMENT_DIR, runtime_role='capture')
    try:
        if args.command == 'prepare-decoys':
            result = prepare_decoys(proposal, layout, fit=args.fit, baseline=args.baseline, positive=args.positive, out=args.out)
        elif args.command == 'pool-build':
            result = build_pool(proposal, layout, cell, args.decoys)
        elif args.command == 'pool-commit':
            result = lane.commit_pool(layout)
        elif args.command == 'commit-hash':
            commitments.require_git(layout, 'run_binding.json', read_json(commitments.public_path(layout, 'run_binding.json')))
            result = lane.commit_hash(layout, args.shard_id, args.graded_file)
        elif args.command == 'regrade':
            result = lane.build_regrade(cell, layout, args.shard_id, args.graded_file)
        elif args.command == 'spot-pack':
            result = lane.spot_check_pack(cell, layout, {k: Path(v) for k, v in read_json(args.graded_map).items()})
            # The public response contains only a path; the blind pack stays private.
            result = {'rows': len(result), 'blind_pack': str(lane.Pool(layout).root / 'spot_pack.blind.jsonl')}
        elif args.command == 'spot-record':
            result = lane.record_spot_check(cell, layout, read_jsonl(args.decisions))
        elif args.command == 'apply':
            result = lane.apply(cell, layout, read_json(args.graded_map))
        else:
            result = rollup(proposal, layout, cell)
            write_json(layout.local(f'{PREFIX}/results/rollup.json'), result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except HarnessError as exc:
        print(json.dumps({'error': exc.code, 'message': exc.message}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
