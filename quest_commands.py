"""Flash 1.2.7 Quest.start/sendResults and upstream 880cde18 quest handlers.

Combat objectives and gold/XP are evaluated by Flash, as in upstream. This
module validates the matching persisted attempt, not a server combat simulation.
Honor comes from the restored upstream globals. Unit loss follows upstream's
died-minus-recovered rule; borrowed quest units never become owned units.
"""
import json
from collections import Counter

from legacy_actions import integer
from quests import get_quest_map

COMMANDS = {'start_quest', 'start_quest_new', 'end_quest'}


def quest_id(value):
    if type(value) is int and value > 0:
        return str(value)
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return str(int(value))
    raise ValueError('Invalid quest ID')


def handle(save, command, args, config, now):
    if not isinstance(args, list):
        raise ValueError('Invalid quest arguments')
    private = save['privateState']
    active = private.get('activeQuest')
    globals_ = config['globals']
    order = [str(q) for q in globals_['ISLE_ORDER']]
    if command == 'start_quest':
        if len(args) != 2 or active:
            raise ValueError('Invalid quest start or quest already active')
        qid, town = quest_id(args[0]), integer(args[1])
        if town >= len(save['maps']) or qid not in order or get_quest_map(qid)[1] != 200:
            raise ValueError('Unknown quest or player town')
        map_ = save['maps'][town]
        unlocked = private.get('unlockedQuestIndex')
        unlocked = 0 if unlocked is None else integer(unlocked)
        if order.index(qid) > unlocked and qid not in globals_.get('UNLOCKED_FOREVER_QUESTS', []):
            raise ValueError('Quest is locked')
        # Config.MIN_LEVEL_QUESTS in the bundled 1.2.7 client is 6.
        minimum = int(globals_.get('QUESTS_MIN_LEVELS', {}).get(qid, 6))
        if int(map_.get('level', 0)) < minimum:
            raise ValueError('Quest level requirement not met')
        times = map_.get('questTimes') or {}
        if not isinstance(times, dict):
            raise ValueError('Invalid quest history')
        times[qid] = now
        map_['questTimes'] = times
        private['activeQuest'] = dict(quest_id=qid, map=town, started=now,
                                    units=dict(Counter(str(r[0]) for r in map_['items'])),
                                    registered=False)
        return
    if not isinstance(active, dict):
        raise ValueError('No active quest')
    map_ = save['maps'][active['map']]
    if command == 'start_quest_new':
        if args:
            raise ValueError('Invalid quest history arguments')
        if not active['registered']:
            map_.setdefault('lastQuestTimes', []).append(active['started'])
            active['registered'] = True
        return
    if command != 'end_quest' or len(args) != 1 or not isinstance(args[0], str):
        raise ValueError('Invalid quest result arguments')
    result = json.loads(args[0])
    if not isinstance(result, dict):
        raise ValueError('Invalid quest result')
    qid = quest_id(result['quest_id'])
    if qid != active['quest_id'] or integer(result['map']) != active['map'] or not active['registered']:
        raise ValueError('Quest result does not match registered start')
    difficulty = integer(result['difficulty'], 1)
    voluntary = integer(result['voluntary_end'])
    win = integer(result.get('win', 1-voluntary))
    if difficulty > 3 or voluntary > 1 or win > 1 or (win and voluntary):
        raise ValueError('Invalid quest outcome')
    integer(result['duration'])
    resources = result['resources']
    if not isinstance(resources, dict) or set(resources) != {'g', 'x'}:
        raise ValueError('Invalid quest resources')
    gold, xp = integer(resources['g']), integer(resources['x'])
    units = result['units']
    if not isinstance(units, list):
        raise ValueError('Invalid quest unit results')
    definitions = {int(i['id']): i for i in config['items']}
    losses, seen = {}, set()
    current = Counter(str(r[0]) for r in map_['items'])
    for row in units:
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError('Invalid quest unit result')
        uid, entered, died, recovered = [integer(n) for n in row]
        if uid in seen or definitions.get(uid, {}).get('type') != 'u' or died > entered or recovered > entered+died:
            raise ValueError('Invalid quest unit counts')
        seen.add(uid)
        lost = max(0, died-recovered)
        if lost > min(active['units'].get(str(uid), 0), current[str(uid)]):
            raise ValueError('Quest loss exceeds owned army')
        losses[uid] = lost
    # Upstream end_quest does not credit item_rewards: only gold, XP and honor.
    # Retain the original result for compatibility/audit without granting
    # client-supplied inventory items through an unverified reward path.
    ranks = private.setdefault('questsRank', {})
    rank = integer(ranks.get(qid) or 0)
    honor = globals_['HONOR_POINT_QUEST_LOSE']
    if win:
        honor = globals_['HONOR_POINT_QUEST_FIRST_TIME' if difficulty > rank else 'HONOR_POINT_QUEST'][difficulty-1]
        ranks[qid] = max(rank, difficulty)
        old = private.get('unlockedQuestIndex')
        old = -1 if old is None else integer(old)
        next_index = order.index(qid)+1
        if next_index-old <= 1:
            private['unlockedQuestIndex'] = max(next_index, old)
    map_['coins'] += gold
    map_['xp'] += xp
    save['playerInfo']['honor_points'] = integer(save['playerInfo'].get('honor_points', 0)) + integer(honor)
    for row in list(map_['items']):
        if losses.get(row[0], 0):
            map_['items'].remove(row)
            losses[row[0]] -= 1
    private.setdefault('completedQuests', {})[qid] = dict(started=active['started'],
        completed=now, result=result, honor=honor)
    del private['activeQuest']
