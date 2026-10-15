"""Upstream 880cde18 cmd_finish_collection adapted to this server's gifts array.

Prices/eligibility: Flash 1.2.7 Config.PRIZE_COLLECTIONS_CASH and
CollectableManager.getRealPrice/checkCanComplete/arUniqueCollections.
"""
from legacy_actions import integer

PRICES = (0,5,5,5,5,5,5,5,5,5,15,5,5,5,5,5,5,5,5,5,20,400,400,999)
UNIQUE = (21,22)


def redeem(save, args, config):
    if not isinstance(args, list) or len(args) not in (1,3):
        raise ValueError('Invalid collection redemption arguments')
    cid = integer(args[0], 1)
    rewards = config['globals']['COLLECTION_REWARDS']
    if cid >= len(rewards) or cid >= len(PRICES):
        raise ValueError('Unknown collection')
    reward = integer(rewards[cid], 1)
    item = next((i for i in config['items'] if int(i['id']) == reward), None)
    if not item or item.get('type') not in ('u','b'):
        raise ValueError('Invalid collection reward')
    private = save['privateState']
    collections = private.get('collections')
    if collections is None or collections == []:
        collections = [[]] + [[0]*6 for _ in range(23)]
        private['collections'] = collections
    if not isinstance(collections, list) or len(collections) != 24 or collections[0] != []:
        raise ValueError('Missing collection state')
    row = collections[cid]
    if not isinstance(row, list) or len(row) != 6 or any(type(n) is not int or n < 0 for n in row) or row[0] not in (0,1):
        raise ValueError('Invalid collection counts')
    completed = private.get('collectionsCompleted', [])
    gifts = private['gifts']
    if not isinstance(completed, list) or not isinstance(gifts, list):
        raise ValueError('Invalid collection inventory state')
    count = integer(gifts[reward]) if reward < len(gifts) else 0
    if cid in UNIQUE and (row[0] or cid in completed or count):
        raise ValueError('Unique collection already redeemed')
    paid = len(args) == 3
    if paid:
        integer(args[1], 1)
        integer(args[2], 1)
        price = PRICES[cid] if cid in (10,20) else max(1, PRICES[cid]-sum(n > 0 for n in row[1:]))
        if args[1] != 1 or args[2] != price or cid == 23 or row[0]:
            raise ValueError('Invalid collection purchase')
        if integer(save['playerInfo']['cash']) < price:
            raise ValueError('Insufficient collection cash')
    else:
        if any(n < 1 for n in row[1:]):
            raise ValueError('Collection is incomplete')
        if int(item.get('subcat_functional',0)) != 411 and (count or any(r[0] == reward for m in save['maps'] for r in m['items'])):
            raise ValueError('Collection reward is already owned')
    bought = private.get('boughtUnits', [])
    if not isinstance(bought, list):
        raise ValueError('Invalid bought unit state')
    if paid:
        save['playerInfo']['cash'] -= price
    # Actual 1.2.7 getReward consumes available pieces for both exchange and
    # cash purchase; upstream's older handler only consumed them on exchange.
    row[1:] = [max(0,n-1) for n in row[1:]]
    row[0] = 1
    if cid not in completed:
        completed.append(cid)
    private['collectionsCompleted'] = completed
    gifts.extend([0] * max(0,reward+1-len(gifts)))
    gifts[reward] = count+1
    ignored_race = 'h' if save['maps'][0].get('race') == 't' else 't'
    if item['type'] != 'b' and item.get('race') != ignored_race and reward not in bought:
        bought.append(reward)
    private['boughtUnits'] = bought
