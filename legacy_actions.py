"""Three recovered commands; upstream 880cde18 op.py/engine.py and Flash 1.2.7.

Queue speed-up uses the existing queue; it does not implement training/collection.
Social construction support is limited to the observed Zeppelin (299) workflow.
"""
import hashlib
import json
import math

COMMANDS = {'speed_up_queue', 'buy_si_help', 'finish_si'}


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid integer')
    return value


def receipt(save, commands, client_id, number):
    integer(number)
    if not isinstance(client_id, str) or not client_id or len(client_id) > 128:
        raise ValueError('Invalid client identity')
    key = hashlib.sha256(f'{client_id}:{number}'.encode()).hexdigest()
    value = hashlib.sha256(json.dumps(commands, sort_keys=True).encode()).hexdigest()
    receipts = save['privateState'].setdefault('legacyActionReceipts', {})
    if key in receipts:
        if receipts[key] != value:
            raise ValueError('Changed retry payload')
        return True
    if len(receipts) >= 4096:
        raise ValueError('Receipt limit reached')
    # The enclosing save transaction rolls this back if any command fails.
    receipts[key] = value
    return False


def speed_up_queue(save, args, config, now):
    if len(args) != 1 or type(args[0]) not in (str, int):
        raise ValueError('Invalid queue ID')
    key = str(args[0])
    if not key.isascii() or not key.isdigit() or int(key) <= 0:
        raise ValueError('Invalid queue ID')
    key = str(int(key))
    owners = [row for town in save['maps'] for row in town['items']
              if len(row) > 7 and str(row[7].get('bq')) == key]
    queue = save['privateState'].get('barracksQueues', {}).get(key)
    if len(owners) != 1 or not isinstance(queue, dict):
        raise ValueError('Queue is missing or ambiguous')
    amount = integer(queue['amount'], 1)
    started = integer(queue['ts'])
    unit = next((item for item in config['items'] if int(item['id']) == queue['unit']), None)
    duration_key = 'sm_training_time' if owners[0][0] == 1529 else 'training_time'
    if not unit or int(unit.get(duration_key, 0)) <= 0:
        raise ValueError('Queue has no valid duration')
    if started == 0:
        return  # Already completed: an idempotent no-op, not another charge.
    seconds = max(0, started + int(unit[duration_key]) * amount - now)
    # BuildingQueueData.remainingSeconds and Config.COST_SPEED_UP_UNIT_QUEUE=1.
    cost = math.ceil(seconds / 3600)
    if save['playerInfo']['cash'] < cost:
        raise ValueError('Insufficient cash')
    save['playerInfo']['cash'] -= cost
    queue['ts'] = 0  # Original client completion sentinel; result stays queued.


def social_building(save, args, config):
    if len(args) not in (4, 5):
        raise ValueError('Invalid social construction arguments')
    for value in args:
        integer(value)
    x, y, town_id, item_id = args[:4]
    if item_id != 299 or town_id >= len(save['maps']):
        raise ValueError('Unsupported social construction')
    rows = [row for row in save['maps'][town_id]['items'] if row[:3] == [item_id, x, y]]
    info = next((item for item in config['social_items'] if int(item['id']) == item_id), None)
    if len(rows) != 1 or not info or len(rows[0]) < 8 or 'si' not in rows[0][7]:
        raise ValueError('No active social construction here')
    workers = rows[0][7]['si']
    if not isinstance(workers, list):
        raise ValueError('Invalid construction state')
    return rows[0], info, len(info['workers'].split(','))


def buy_si_help(save, args, config):
    row, info, required = social_building(save, args, config)
    if len(args) == 5 and args[4] not in (0, 1):
        raise ValueError('Invalid no-cash flag')
    no_cash = len(args) == 5 and args[4] == 1
    if len(row[7]['si']) >= required:
        if no_cash:
            # Captured Flash batch repeats free help 20 times for 10 slots.
            # Already fulfilled: do not create excess workers or debit cash.
            return
        raise ValueError('Construction already has all workers')
    cost = 0 if no_cash else integer(info['worker_cost'])
    if save['playerInfo']['cash'] < cost:
        raise ValueError('Insufficient cash')
    save['playerInfo']['cash'] -= cost
    row[7]['si'].append('0')  # Upstream push_si: the paid/free helper placeholder.


def finish_si(save, args, config):
    if len(args) != 4:
        raise ValueError('Invalid finish arguments')
    row, info, required = social_building(save, args, config)
    if len(row[7]['si']) < required:
        raise ValueError('Construction still needs workers')
    del row[7]['si']  # Upstream completion marker; preserves other attributes.
