"""Frozen R1 comparison, no behavioral scoring."""
import json
import jsonschema
from . import astra_benchmark as benchmark
from .util import HarnessError, canonical_sha256
RUNS=("original_a","original_b","permuted_a","permuted_b","resume")
N=20

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
            if not row.get('completion_token_ids') or row.get('finish_reason') not in ('stop', 'eos'):
                raise HarnessError('QUAL_FINISH', 'qualification requires natural termination and retained token IDs')
        signature = canonical_sha256(sorted(rows, key=lambda r: r['id']))
        if canonical is not None and signature != canonical:
            raise HarnessError('QUAL_PARITY', 'repeats, permutation or resume changed persisted output')
        canonical = signature
    return {'rows': N, 'runs': len(RUNS), 'canonical_output_sha256': canonical,
            'completion_token_ids_identical': True, 'finish_reasons_identical': True, 'whole_schema_valid': True}

