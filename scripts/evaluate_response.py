"""Evaluate deterministic rules against authored labels; keep results private.

This is a calibration/evaluation loop, not model training. External accuracy needs
independently labelled civilian cases and a held-out set, not these toy examples.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.response_rules import RULE_VERSION, evaluate_response, instant  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=ROOT / 'examples/response-rule-cases.json')
    parser.add_argument('--stress', type=int, default=5000, help='Generated invariant trials (0..100000), not HTTP load')
    args = parser.parse_args()
    if not 0 <= args.stress <= 100000:
        parser.error('Choose between zero and 100,000 rule-engine stress trials.')
    if args.cases.stat().st_size > 1024 * 1024:
        parser.error('Use an evaluation file of at most 1 MiB.')
    raw = args.cases.read_bytes(); dataset = json.loads(raw)
    if dataset['contract'] != 'sampati.response-evaluation.v1' or not 1 <= len(dataset['cases']) <= 10000:
        parser.error('Use the documented contract with 1..10000 labelled cases.')
    now = instant(dataset['now']); policy = dataset['freshness_hours']
    if isinstance(policy, bool) or not isinstance(policy, int) or not 1 <= policy <= 168:
        parser.error('freshness_hours must be an integer from 1 to 168.')
    rows = []; durations = []; false_reviewable = 0
    for case in dataset['cases']:
        facts = deepcopy(dataset['base_facts'])
        for patch in case['patches']:
            path = patch['path']; target = facts
            if not path: raise ValueError('Patch paths cannot be empty.')
            for key in path[:-1]: target = target[key]
            if isinstance(target, dict) and path[-1] not in target: raise ValueError('Patch path must already exist.')
            target[path[-1]] = patch['value']
        started = time.perf_counter()
        decision = evaluate_response(facts, now=now, freshness_hours=policy)
        durations.append((time.perf_counter() - started) * 1000)
        codes = {b['code'] for b in decision['blockers']}
        matched = (decision['status'] == case['expected_status'] and set(case['required_blockers']) <= codes
            and ('expected_cargo_kg' not in case or Decimal(decision['cargo_kg']) == Decimal(case['expected_cargo_kg'])))
        false_reviewable += case['expected_status'] == 'blocked' and decision['status'] == 'reviewable'
        rows.append({'name': case['name'], 'matched': matched, 'expected': case['expected_status'],
            'actual': decision['status'], 'required_blockers': case['required_blockers'], 'actual_blockers': sorted(codes)})

    rng = random.Random(26250); stress_passed = 0
    # Isolated generated evidence: one shared store, up to 50 needs, exact decimal
    # balances. No database, browser, network or aircraft operations are exercised.
    for iteration in range(args.stress):
        facts = deepcopy(dataset['base_facts']); template = deepcopy(facts['needs'][0]); facts['needs'] = []
        count = rng.randint(1, 50); on_hand = Decimal(rng.randint(1, 100000)) / 1000
        reserved = Decimal(rng.randint(0, int(on_hand * 1000))) / 1000
        for i in range(count):
            facts['needs'].append({**template, 'request_id': f'generated-{i:03}', 'reference': f'GEN-{i:03}',
                'quantity': str(Decimal(rng.randint(1, 5000)) / 1000), 'committed': '0', 'on_hand': str(on_hand), 'reserved': str(reserved)})
        started = time.perf_counter(); result = evaluate_response(facts, now=now, freshness_hours=policy)
        durations.append((time.perf_counter() - started) * 1000)
        available = on_hand - reserved
        allocated = sum((Decimal(row['proposed']) for row in result['allocations']), Decimal(0))
        okay = allocated <= available and all(Decimal(row['shortfall']) >= 0 and Decimal(row['proposed']) >= 0 for row in result['allocations'])
        rng.shuffle(facts['needs'])
        okay = okay and evaluate_response(facts, now=now, freshness_hours=policy) == result
        if result['selected_aircraft']:
            candidate = next(a for a in facts['aircraft'] if a['aircraft_id'] == result['selected_aircraft'])
            okay = okay and Decimal(result['cargo_kg']) <= Decimal(candidate['support']['cargo_allowance_kg'])
        if not okay: raise AssertionError(f'Generated resource invariant failed at trial {iteration}.')
        stress_passed += 1

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / '.local/evaluations' / ('response-' + stamp); out.mkdir(parents=True, exist_ok=False)
    matches = sum(row['matched'] for row in rows)
    report = {'rule_version': RULE_VERSION, 'dataset_sha256': hashlib.sha256(raw).hexdigest(), 'python': platform.python_version(),
        'cases': rows, 'matched': matches, 'labelled_cases': len(rows), 'false_reviewable': false_reviewable,
        'expected_blocked_cases': sum(row['expected'] == 'blocked' for row in rows),
        'generated_invariant_trials': stress_passed, 'timing_samples': len(durations),
        'rule_function_median_ms': statistics.median(durations), 'rule_function_max_ms': max(durations),
        'limitations': 'Authored synthetic labels; no field accuracy, ML training, HTTP capacity or humanitarian outcome is established.'}
    (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (out / 'cases.json').write_bytes(raw)
    (out / 'RESULTS.md').write_text(f"# Private deterministic response evaluation\n\nRule: {RULE_VERSION}\n\nAuthored cases matched: {matches}/{len(rows)}. False reviewable results: {false_reviewable}/{report['expected_blocked_cases']} expected-blocked cases.\n\nGenerated resource-invariant trials: {stress_passed}. Includes exact stock bounds, cargo bounds and input-order stability. These are rule-function trials, not concurrent HTTP users.\n\nMedian rule-function duration: {report['rule_function_median_ms']:.3f} ms; maximum {report['rule_function_max_ms']:.3f} ms on this machine (mixed 1–50 need workloads).\n\n{report['limitations']}\n\nReproduce: `.venv/Scripts/python.exe scripts/evaluate_response.py --stress {args.stress}`. The supplied dataset is archived as cases.json; custom runs pass `--cases PATH`.\n", encoding='utf-8')
    print(out / 'RESULTS.md')
    print(json.dumps({key: report[key] for key in ['matched', 'labelled_cases', 'false_reviewable', 'expected_blocked_cases', 'generated_invariant_trials']}))
    return 0 if matches == len(rows) and not false_reviewable else 1


if __name__ == '__main__':
    raise SystemExit(main())
