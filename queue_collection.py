"""Collect an existing queue result (Flash 1.2.7 IsoBuilding.unitFinished).

Upstream 880cde18 cmd_pop_queue_unit / player_pop_queue_unit supplies the
decrement/removal behavior. The current client sends three arguments, not four.
No queue creation, result selection or power-up behavior is changed here.
"""
from legacy_actions import integer


def collect(save, args, config, now):
    if not isinstance(args, list) or len(args) != 3:
        raise ValueError('Invalid queue collection arguments')
    key, x, y = args
    if type(key) not in (str, int) or not str(key).isascii() or not str(key).isdigit() or int(key) <= 0:
        raise ValueError('Invalid queue ID')
    key = str(int(key))
    integer(x)
    integer(y)
    if x >= 100 or y >= 100:
        raise ValueError('Invalid unit coordinates')
    owners = [(town, row) for town in save['maps'] for row in town['items']
              if len(row) > 7 and isinstance(row[7], dict) and str(row[7].get('bq')) == key]
    queues = save['privateState'].get('barracksQueues', {})
    queue = queues.get(key)
    if len(owners) != 1 or not isinstance(queue, dict):
        raise ValueError('Queue is missing or ambiguous')
    town, building = owners[0]
    amount = integer(queue['amount'], 1)
    started = integer(queue['ts'])
    unit_id = integer(queue['unit'], 1)
    unit = next((item for item in config['items'] if int(item['id']) == unit_id), None)
    is_mixer = building[0] == 1529
    duration = int(unit.get('sm_training_time' if is_mixer else 'training_time', 0)) if unit else 0
    if not unit or duration <= 0 or (is_mixer and int(unit.get('breeding_order', 0)) <= 0):
        raise ValueError('Invalid queued unit')
    # Flash's queue completion sentinel is ts=0; otherwise respect its timer.
    if started and now < started + duration:
        raise ValueError('Queue is not ready')
    if any(row[1:3] == [x, y] for row in town['items']):
        raise ValueError('Unit destination is occupied')
    if 'r' in queue:
        if not isinstance(queue['r'], dict):
            raise ValueError('Invalid queue cost state')
        queue['r'].pop(str(amount), None)
    queue['amount'] = amount - 1
    if queue['amount'] == 0:
        del queues[key]
        del building[7]['bq']
    if not is_mixer:
        town['xp'] += int(unit.get('xp', 0))
    town['items'].append([unit_id, x, y, 0, now, 0])
