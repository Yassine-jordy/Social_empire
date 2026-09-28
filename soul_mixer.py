"""Recovered Soul Mixer rules, pinned to the bundled 1.2.7/1.4.07 clients.

Ranks/timers/prices use the explicitly authorized upstream reconstruction,
with provenance in config/soul_mixer_restoration.json. They are not historical
production data. Production remains disabled pending a server-result handshake.
"""
import math
import secrets

BUILDING_ID = 1529
MISSING_DATA = ('Soul Mixer requires original breeding_order, sm_training_time '
                'and SOUL_MIXER_POWERUPS_LEVELS data; mixing is not restored')


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Expected a nonnegative integer')
    return value


def result_power(first, second, roll):
    """PopupSoulMixer.getResultPower: Utils.getRandom(0,12) is inclusive."""
    integer(first, 1)
    integer(second, 1)
    integer(roll)
    if roll > 12:
        raise ValueError('Invalid random roll')
    power = max(10, math.ceil(min(first, second) * .3 + max(first, second) * .7))
    power += roll
    return power + 1 if power == max(first, second) else power


def ranked_units(config):
    units = [item for item in config['items'] if int(item.get('breeding_order', 0)) > 0]
    if not units:
        raise NotImplementedError(MISSING_DATA)
    if any(item.get('type') != 'u' or int(item.get('sm_training_time', 0)) <= 0 for item in units):
        raise NotImplementedError('Soul Mixer ranking data lacks verified unit durations')
    # A tie's original AS3 sort order is not established; do not invent one.
    powers = [int(item['breeding_order']) for item in units]
    if len(set(powers)) != len(powers):
        raise NotImplementedError('Soul Mixer rank tie ordering requires client evidence')
    return sorted(units, key=lambda item: int(item['breeding_order']))


def select_result(config, parent_ids, *, randbelow=secrets.randbelow):
    """Server-side port of generateResultUnit, not exposed as a client endpoint.

    Parents survive. No prices, unit rankings or training durations are invented.
    Output is server-selected; the old client's proposed unit is never accepted
    as a replacement for this selection.
    """
    if len(parent_ids) != 2:
        raise ValueError('Two input units required')
    for item_id in parent_ids:
        integer(item_id, 1)
    units = ranked_units(config)
    by_id = {int(item['id']): item for item in units}
    if any(item_id not in by_id for item_id in parent_ids):
        raise ValueError('Input unit is not eligible for Soul Mixer')
    first, second = (int(by_id[item_id]['breeding_order']) for item_id in parent_ids)
    power = result_power(first, second, randbelow(13))
    if power > 400:
        maximum = int(units[-1]['breeding_order'])
        if maximum < 400:
            raise NotImplementedError('Inconsistent Soul Mixer rank ceiling')
        power = 400 + randbelow(maximum - 400 + 1)
    for item in units:
        if int(item['id']) not in parent_ids and int(item['breeding_order']) >= power:
            return int(item['id'])
    # Exact client fallback, even if the final entry is an input unit.
    return int(units[-1]['id'])


def validate_purchase(save, args, config):
    """Enforce existing *temporary* placement config; not historical pricing."""
    if len(args) != 8 or args[0] != BUILDING_ID:
        raise ValueError('Invalid Soul Mixer purchase')
    _, x, y, frame, town_id, free, multiplier, item_type = args
    for value in (x, y, frame, town_id, free):
        integer(value)
    if free != 0 or type(multiplier) not in (int, float) or multiplier != 1 or item_type != 'b':
        raise ValueError('Soul Mixer purchase requires its configured price')
    if town_id >= len(save['maps']):
        raise ValueError('Invalid town')
    building = next(item for item in config['items'] if int(item['id']) == BUILDING_ID)
    town = save['maps'][town_id]
    # Client grid size; expansion/terrain collision validation remains shared work.
    if x >= 100 or y >= 100:
        raise ValueError('Position is outside the client map')
    if any(item[1:3] == [x, y] for item in town['items']):
        raise ValueError('Occupied position')
    level = sum(int(row['exp_required']) <= town['xp'] for row in config['levels'])
    if level < int(building['min_level']):
        raise ValueError('Soul Mixer level requirement not met')
    count = sum(item[0] == BUILDING_ID for m in save['maps'] for item in m['items'])
    if count >= int(building['units_limit']):
        raise ValueError('Soul Mixer building limit reached')
    if building['cost_type'] != 'g' or town['coins'] < int(building['cost']):
        raise ValueError('Insufficient gold for Soul Mixer')


def reject_unrestored_mixing():
    # Explicit rather than fake success, even if a mod adds some missing fields:
    # the stock popup still rolls locally and ignores server-selected results.
    raise NotImplementedError(MISSING_DATA + '; authoritative result handshake also required')


def store_input(save, building, args, config):
    """Atomically move an owned deployed unit into one of two input slots."""
    if len(args) != 6:
        raise ValueError('Invalid input arguments')
    for value in args:
        integer(value)
    x, y, unit_id, bx, by, town_id = args
    if town_id >= len(save['maps']):
        raise ValueError('Invalid town')
    town = save['maps'][town_id]
    if building[0] != BUILDING_ID or building[1:3] != [bx, by]:
        raise ValueError('Invalid Soul Mixer')
    eligible = {int(item['id']) for item in ranked_units(config)}
    if unit_id not in eligible:
        raise ValueError('Ineligible Soul Mixer input')
    unit = next((row for row in town['items'] if row[:3] == [unit_id, x, y]), None)
    if unit is None or unit is building:
        raise ValueError('Input unit is not deployed here')
    if len(building) < 7:
        building.append([])
    if len(building) < 8:
        building.append({})
    attrs = building[7]
    queue = save['privateState'].get('barracksQueues', {}).get(str(attrs.get('bq')), {})
    if queue.get('amount', 0) or len(building[6]) >= 2:
        raise ValueError('Soul Mixer is occupied')
    # Retain complete source rows for safe withdrawal, including unit attributes.
    attrs.setdefault('soulMixerInputs', []).append(unit)
    building[6].append(unit_id)
    town['items'].remove(unit)


def return_input(save, building, args):
    validate_withdrawal(save, building, args)
    records = building[7].get('soulMixerInputs', []) if len(building) > 7 else []
    row = next((row for row in records if row[0] == args[3]), None)
    if row is None:
        # Legacy ID-only storage has no recoverable instance attributes.
        row = [args[3], args[4], args[5], args[6], 0, 0]
    else:
        records.remove(row)
        row[1:4] = args[4:7]
    building[6].remove(args[3])
    save['maps'][args[2]]['items'].append(row)


def validate_withdrawal(save, building, args):
    """Permit recovery of previously housed units, but never mint missing units."""
    if len(args) != 7:
        raise ValueError('Soul Mixer inputs must be returned, not destroyed')
    for value in args:
        integer(value)
    if args[2] >= len(save['maps']) or args[4] >= 100 or args[5] >= 100:
        raise ValueError('Invalid withdrawal position')
    if len(building) < 7 or args[3] not in building[6]:
        raise ValueError('Unit is not housed in this Soul Mixer')
    attrs = building[7] if len(building) > 7 else {}
    if not isinstance(attrs, dict):
        raise ValueError('Invalid Soul Mixer attributes')
    queue = save['privateState'].get('barracksQueues', {}).get(str(attrs.get('bq')), {})
    if queue.get('amount', 0):
        raise ValueError('Cannot withdraw units from an active Soul Mixer')
    if any(item[1:3] == args[4:6] for item in save['maps'][args[2]]['items']):
        raise ValueError('Occupied withdrawal position')
