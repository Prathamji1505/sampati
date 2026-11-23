"""Pure, clock-injected rules for civilian preparation. No dispatch or stock writes."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

RULE_VERSION = 'civilian-response.v1'
LIMITS = {'requests': 50, 'aircraft': 500, 'file_bytes': 65536}


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def quantity(value):
    result = format(Decimal(value), 'f')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Evidence timestamps must include a timezone.')
    return result.astimezone(timezone.utc)


def fresh(value, now, hours):
    age = (now - instant(value)).total_seconds()
    return -300 <= age <= hours * 3600


def label(value):
    return ' '.join(value.casefold().split())


def evaluate_response(facts, *, now, freshness_hours=24):
    """Same evidence, clock and policy produce the same explained preparation plan.

    The caller supplies validated, organisation-scoped facts. Request commitments
    include reservations/issues already assigned elsewhere; candidates are reported
    capabilities rather than flight clearance. No heuristic confidence score.
    """
    blockers = []

    def block(code, message, subject=None):
        blockers.append({'code': code, 'message': message, 'subject': subject})

    signal = facts['signal']
    if signal['state'] != 'verified':
        block('signal_unverified', 'A coordinator must verify the warning or news report first.')
    if not fresh(signal['observed_at'], now, freshness_hours) or instant(signal['expires_at']) <= now:
        block('signal_outdated', 'The warning is expired, old or future-dated. Obtain current evidence.')
    if signal['certainty'] in {'unknown', 'unlikely'}:
        block('signal_uncertain', 'Clarify the warning certainty before planning resources.')

    context = facts['conditions']
    if not fresh(context['observed_at'], now, freshness_hours):
        block('conditions_outdated', 'Obtain a current dated operator/context report.')
    for field, description in [('weather', 'Weather assessment'), ('destination_access', 'Destination access assessment')]:
        if context[field] != 'confirmed':
            block('conditions_' + field, description + ' is missing or reports a hold.')

    # Allocate once per position in stable deadline/reference/ID order. This is a
    # transparent earliest-deadline heuristic, not an optimal response solution.
    remaining_stock = {}
    allocations = []
    cargo = Decimal(0)
    used_requests = set()
    for row in sorted(facts['needs'], key=lambda r: (instant(r['needed_by']), r['reference'], r['request_id'])):
        request_id = row['request_id']
        if request_id in used_requests:
            block('duplicate_request', 'Select each request only once.', request_id)
            continue
        used_requests.add(request_id)
        compatible = row['unit'] == row['item_unit'] and row['category'] == row['item_category']
        if row['status'] != 'reviewed':
            block('request_unreviewed', 'The supply request must currently be reviewed.', request_id)
        if label(row['locality']) != label(signal['locality']):
            block('locality_mismatch', 'The request locality does not match this warning. Review the affected area.', request_id)
        if not compatible:
            block('item_mismatch', 'The selected item must match the request category and unit; no conversion is inferred.', request_id)
        if row['incompatible_commitments']:
            block('commitment_mismatch', 'Earlier allocations conflict with the current request. Reconcile them first.', request_id)
        if row['item_name_confirmed'] is not True:
            block('item_confirmation', 'Confirm that this catalog item is the exact supply requested.', request_id)
        need = max(Decimal(0), Decimal(row['quantity']) - Decimal(row['committed']))
        if not need:
            block('already_allocated', 'This need already has its quantity committed; follow its existing delivery.', request_id)
        stock_key = (row['item_id'], row['location_id'])
        if stock_key not in remaining_stock:
            remaining_stock[stock_key] = max(Decimal(0), Decimal(row['on_hand']) - Decimal(row['reserved']))
        valid = compatible and row['status'] == 'reviewed' and not row['incompatible_commitments'] and row['item_name_confirmed']
        proposed = min(need, remaining_stock[stock_key]) if valid else Decimal(0)
        remaining_stock[stock_key] -= proposed
        shortfall = need - proposed
        if shortfall:
            block('stock_shortfall', f"{quantity(shortfall)} {row['unit']} still need a stock source.", request_id)
        if not fresh(row['stock_updated_at'], now, freshness_hours):
            block('stock_outdated', 'The stock ledger needs a current source check. A count alone does not change stock.', request_id)
        weight = Decimal(row['unit_weight_kg'])
        if row['unit'] == 'kilograms' and weight != 1:
            block('weight_unit_mismatch', 'A kilogram of supplies must contribute one kilogram of cargo mass.', request_id)
        cargo += proposed * weight
        allocations.append({'request_id': request_id, 'reference': row['reference'], 'item_id': row['item_id'],
            'location_id': row['location_id'], 'needed': quantity(need), 'proposed': quantity(proposed),
            'shortfall': quantity(shortfall), 'unit': row['unit'], 'unit_weight_kg': quantity(weight),
            'weight_kg': quantity(proposed * weight), 'weight_source': row['weight_source'], 'stock_version': row['stock_version']})
    if not allocations:
        block('no_needs', 'Select at least one reviewed, locally confirmed supply request.')
    if cargo <= 0:
        block('no_cargo', 'There is no positive supply quantity to prepare.')

    candidates = []
    for aircraft in sorted(facts['aircraft'], key=lambda a: a['aircraft_id']):
        reasons = []
        if aircraft['reported_status'] != 'available':
            reasons.append('reported_unavailable')
        if not fresh(aircraft['source_updated_at'], now, freshness_hours):
            reasons.append('aircraft_report_outdated')
        support = aircraft['support']
        if support is None:
            reasons.append('support_missing')
        else:
            if not fresh(support['observed_at'], now, freshness_hours):
                reasons.append('support_outdated')
            for field in ['crew', 'maintenance', 'fuel']:
                if support[field] != 'confirmed':
                    reasons.append(field + '_unconfirmed')
            if Decimal(support['cargo_allowance_kg']) < cargo:
                reasons.append('cargo_exceeded')
        candidates.append({'aircraft_id': aircraft['aircraft_id'], 'display_name': aircraft['display_name'],
            'eligible': not reasons and cargo > 0, 'reasons': reasons,
            'cargo_allowance_kg': support['cargo_allowance_kg'] if support else None})
    eligible = [a for a in candidates if a['eligible']]
    # Smallest reported allowance that fits, then stable aircraft ID. No range,
    # route, time-of-flight or payload envelope is invented from missing data.
    selected = min(eligible, key=lambda a: (Decimal(a['cargo_allowance_kg']), a['aircraft_id'])) if eligible else None
    if selected is None:
        block('no_aircraft_candidate', 'No aircraft has current available/support reports and sufficient reported cargo allowance.')

    codes = {item['code'] for item in blockers}
    steps = [
        ('Verify warning', 'response', any(c.startswith('signal_') for c in codes)),
        ('Confirm local needs', 'relief', bool(codes & {'no_needs', 'request_unreviewed', 'locality_mismatch', 'item_mismatch', 'item_confirmation', 'commitment_mismatch', 'duplicate_request'})),
        ('Reconcile supplies and cargo weights', 'inventory', bool(codes & {'stock_shortfall', 'stock_outdated', 'already_allocated', 'no_cargo', 'weight_unit_mismatch'})),
        ('Check aircraft and operator reports', 'response', selected is None),
        ('Check weather and destination access', 'response', any(c.startswith('conditions_') for c in codes)),
        ('Record coordinator review', 'response', bool(blockers)),
        ('Reserve stock and obtain operator dispatch approval', 'inventory', True),
        ('Track source-backed arrivals and remaining needs', 'deliveries', True),
    ]
    decision = {'rule_version': RULE_VERSION, 'status': 'blocked' if blockers else 'reviewable',
        'blockers': blockers, 'allocations': allocations, 'cargo_kg': quantity(cargo),
        'selected_aircraft': selected['aircraft_id'] if selected else None, 'candidates': candidates,
        'workflow': [{'order': i + 1, 'title': title, 'route': route,
            'state': 'human_action' if i >= 6 else 'blocked' if blocked else 'awaiting_review' if i == 5 else 'checked'}
            for i, (title, route, blocked) in enumerate(steps)],
        'limitations': ['Planning evidence only; review does not reserve inventory or book an aircraft.',
            'An authorised operator must independently approve aircraft, crew, routing, load and dispatch.',
            'Earliest deadline priority is a declared heuristic; urgency and welfare outcomes need civilian validation.']}
    canonical_facts = {**facts, 'needs': sorted(facts['needs'], key=lambda row: row['request_id']),
        'aircraft': sorted(facts['aircraft'], key=lambda row: row['aircraft_id'])}
    return {**decision, 'evaluation_hash': stable_hash({'facts': canonical_facts, 'decision': decision, 'freshness_hours': freshness_hours}),
        'evaluated_at': now.astimezone(timezone.utc).isoformat(), 'freshness_hours': freshness_hours}
