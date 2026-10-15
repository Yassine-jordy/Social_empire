"""1.2.7 IsoBuilding.upgrade: sell(UPGR), then buy at the same tile.

Costs/refunds follow upstream 880cde18 cmd_sell/cmd_buy and Config.DIVISOR_SELL.
The upgraded item ID represents the level; no training queue or timer is used.
"""
from legacy_actions import integer


def is_upgrade(command):
    args = command.get('args')
    return (command.get('cmd') == 'sell' and isinstance(args, list)
            and len(args) == 6 and args[5] == 'UPGR')


def apply(save, sale, purchase, config, now):
    args = purchase.get('args') if isinstance(purchase, dict) else None
    if not purchase or purchase.get('cmd') != 'buy' or not isinstance(args, list) or len(args) != 8:
        raise ValueError('Upgrade requires its matching purchase')
    x, y, old_id, town_id, free, reason = sale['args']
    new_id, nx, ny, orientation, new_town, new_free, multiplier, kind = args
    for value in (x, y, old_id, town_id, free, new_id, nx, ny, orientation, new_town, new_free, multiplier):
        integer(value)
    if (x >= 100 or y >= 100 or town_id >= len(save['maps'])
            or (nx, ny, new_town) != (x, y, town_id)
            or free != 0 or new_free != 0 or multiplier != 1 or orientation != 1 or kind != 'b'
            or old_id == 1529 or new_id == 1529):
        raise ValueError('Invalid building upgrade pair')
    town = save['maps'][town_id]
    matches = [row for row in town['items'] if row[1:3] == [x, y]]
    if len(matches) != 1 or matches[0][0] != old_id:
        raise ValueError('Upgrade building is not owned or is ambiguous')
    row = matches[0]
    definitions = {int(item['id']): item for item in config['items']}
    old, new = definitions.get(old_id), definitions.get(new_id)
    if (not old or not new or old.get('type') != 'b' or new.get('type') != 'b'
            or int(old.get('upgrades_to', 0)) != new_id):
        raise ValueError('Upgrade is not available')
    if (len(row) > 6 and row[6]) or (len(row) > 7 and row[7]):
        raise ValueError('Occupied or active building cannot be upgraded')
    level = sum(int(entry['exp_required']) <= town['xp'] for entry in config['levels'])
    if level < int(new.get('min_level', 0)):
        raise ValueError('Upgrade level requirement not met')
    fields = {'g':'coins', 'w':'wood', 's':'stone', 'f':'food', 'c':'cash'}
    cost_type, refund_type = new['cost_type'], old['cost_type']
    if cost_type not in fields or refund_type not in fields:
        raise ValueError('Unsupported upgrade resource type')
    cost, old_cost, xp = int(new['cost']), int(old['cost']), int(new['xp'])
    for value in (cost, old_cost, xp):
        integer(value)
    payer = save['playerInfo'] if cost_type == 'c' else town
    # Flash checks full affordability before crediting the sale refund.
    if payer[fields[cost_type]] < cost:
        raise ValueError('Insufficient upgrade resources')
    payer[fields[cost_type]] -= cost
    if refund_type != 'c':
        town[fields[refund_type]] += old_cost // 20
    town['xp'] += xp
    town['items'][town['items'].index(row)] = [new_id, x, y, orientation, now, 0]
