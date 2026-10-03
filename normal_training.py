"""Normal Flash queues; upstream 880cde18 op.py/engine.py and 1.2.7 client.

Training costs, food surcharge, discounts and queue shape follow upstream.
Soul Mixer requests and data are deliberately handled by its existing module.
"""
import math
from legacy_actions import integer


def is_request(command):
    args = command.get('args')
    return (command.get('cmd') == 'push_queue_unit' and isinstance(args, list)
            and len(args) == 6 and type(args[5]) is int and args[5] == 1)


def start(save, args, config, now):
    x, y, building_id, unit_id, queue_id, flag = args
    for value in args:
        integer(value)
    if x >= 100 or y >= 100 or queue_id <= 0 or building_id == 1529 or flag != 1:
        raise ValueError('Invalid normal training request')
    town = save['maps'][0]
    rows = [row for row in town['items'] if row[:3] == [building_id, x, y]]
    definitions = {int(item['id']): item for item in config['items']}
    building, unit = definitions.get(building_id), definitions.get(unit_id)
    if len(rows) != 1 or not building or not unit:
        raise ValueError('Training building or unit is missing')
    if building.get('type') != 'b' or unit.get('type') != 'u' or int(building.get('trains', 0)) != unit_id:
        raise ValueError('Building cannot train this unit')
    row = rows[0]
    attrs = row[7] if len(row) > 7 else {}
    if not isinstance(attrs, dict) or 'si' in attrs:
        raise ValueError('Building is not ready')
    level = sum(int(entry['exp_required']) <= town['xp'] for entry in config['levels'])
    if level < max(int(building.get('min_level', 0)), int(unit.get('min_level', 0))):
        raise ValueError('Training level requirement not met')
    if int(unit.get('training_time', 0)) <= 0:
        raise ValueError('Missing training duration')
    queues = save['privateState'].setdefault('barracksQueues', {})
    key = str(queue_id)
    owners = [r for m in save['maps'] for r in m['items']
              if len(r) > 7 and isinstance(r[7], dict) and str(r[7].get('bq')) == key]
    queue = queues.get(key)
    if queue is None:
        if owners or attrs.get('bq'):
            raise ValueError('Queue ID is already assigned')
    elif (owners != [row] or str(attrs.get('bq')) != key or queue.get('unit') != unit_id
          or integer(queue['amount'], 1) >= 5 or not isinstance(queue.get('r'), dict)):
        raise ValueError('Queue is full or inconsistent')
    limit = int(unit.get('units_limit', 0))
    if limit and sum(q['amount'] for q in queues.values() if q['unit'] == unit_id) >= limit:
        raise ValueError('Unit queue limit reached')
    cost = int(unit['cost'])
    subcat = int(unit.get('subcat_functional', 0))
    discount_building = 131 if subcat in (78, 79, 80) else 134 if subcat == 81 else None
    if discount_building and any(int(definitions.get(r[0], {}).get('subcat_functional', 0)) == discount_building
                                 for r in town['items']):
        cost = math.ceil(cost * 0.9)
    resource = unit['cost_type']
    fields = {'g': 'coins', 'f': 'food', 'w': 'wood', 's': 'stone', 'c': 'cash'}
    if resource not in fields or cost < 0:
        raise ValueError('Invalid training cost')
    costs = {resource: cost}
    if resource != 'f':
        costs['f'] = cost * 2
    for kind, amount in costs.items():
        source = save['playerInfo'] if kind == 'c' else town
        if source.get(fields[kind], 0) < amount:
            raise ValueError('Insufficient training resources')
    for kind, amount in costs.items():
        source = save['playerInfo'] if kind == 'c' else town
        source[fields[kind]] -= amount
    if queue is None:
        queues[key] = {'ts': now, 'amount': 1, 'unit': unit_id, 'r': {'1': costs}}
        while len(row) < 8:
            row.append([] if len(row) == 6 else {})
        row[7]['bq'] = key
    else:
        queue['amount'] += 1
        queue['r'][str(queue['amount'])] = costs
