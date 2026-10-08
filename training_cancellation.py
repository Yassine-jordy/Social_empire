"""Flash BuildingQueueData.removeUnit; upstream 880cde18 cmd_unqueue_unit.

Each request cancels the last queued unit, retaining earlier units and their
timer. Refund recorded costs; old queues without receipts use upstream costs.
"""
import math
from legacy_actions import integer


def cancel(save, args, config):
    if not isinstance(args, list) or len(args) != 2:
        raise ValueError('Invalid training cancellation arguments')
    key, building_id = args
    if type(key) not in (str, int) or not str(key).isascii() or not str(key).isdigit() or int(key) <= 0:
        raise ValueError('Invalid training queue ID')
    key = str(int(key))
    integer(building_id, 1)
    if building_id == 1529:
        raise NotImplementedError('Soul Mixer cancellation has not been restored')
    queues = save['privateState'].get('barracksQueues', {})
    queue = queues.get(key)
    owners = [(town, row) for town in save['maps'] for row in town['items']
              if len(row) > 7 and isinstance(row[7], dict) and str(row[7].get('bq')) == key]
    if not isinstance(queue, dict) or len(owners) != 1:
        raise ValueError('Training queue is missing or ambiguous')
    town, row = owners[0]
    definitions = {int(item['id']): item for item in config['items']}
    building = definitions.get(building_id)
    unit = definitions.get(integer(queue['unit'], 1))
    if (row[0] != building_id or not building or building.get('type') != 'b'
            or not unit or unit.get('type') != 'u'
            or int(building.get('trains', 0)) != queue['unit']):
        raise ValueError('Training queue does not match its building')
    amount = integer(queue['amount'], 1)
    if amount > 5:
        raise ValueError('Invalid training queue amount')
    fields = {'g': 'coins', 'f': 'food', 'w': 'wood', 's': 'stone', 'c': 'cash'}
    if 'r' in queue:
        receipts = queue['r']
        costs = receipts.get(str(amount)) if isinstance(receipts, dict) else None
        if not isinstance(costs, dict) or not costs:
            raise ValueError('Missing recorded training cost')
    else:
        # Compatibility for historical saves predating per-unit cost receipts.
        cost = int(unit['cost'])
        subcat = int(unit.get('subcat_functional', 0))
        discount = 131 if subcat in (78, 79, 80) else 134 if subcat == 81 else None
        if discount and any(int(definitions.get(r[0], {}).get('subcat_functional', 0)) == discount
                            for r in town['items']):
            cost = math.ceil(cost * 0.9)
        costs = {unit['cost_type']: cost}
        # Preserve upstream's legacy fallback, including its food surcharge.
        costs['f'] = costs.get('f', 0) + cost * 2
    for kind, refund in costs.items():
        if kind not in fields:
            raise ValueError('Invalid training refund resource')
        integer(refund)
        source = save['playerInfo'] if kind == 'c' else town
        integer(source[fields[kind]])
    for kind, refund in costs.items():
        source = save['playerInfo'] if kind == 'c' else town
        source[fields[kind]] += refund
    if 'r' in queue:
        del queue['r'][str(amount)]
    if amount == 1:
        del queues[key]
        del row[7]['bq']
    else:
        queue['amount'] = amount - 1
