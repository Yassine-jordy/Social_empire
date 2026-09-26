"""Conservative checks for persisted player state; never invent missing progress."""
import math


def validate_save(save):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def number(value):
        return type(value) in (int, float) and math.isfinite(value)

    require(isinstance(save, dict), 'Save must be an object')
    player, maps, state = (save.get(k) for k in ('playerInfo', 'maps', 'privateState'))
    require(isinstance(player, dict) and isinstance(state, dict), 'Missing player/private state')
    require(isinstance(maps, list) and len(maps) > 0, 'Save needs at least one map')
    pid = player.get('pid')
    require(isinstance(pid, (str, int)) and not isinstance(pid, bool) and bool(str(pid)), 'Invalid player ID')
    require(not any(c in str(pid) for c in '/\\:') and str(pid) not in ('.', '..'), 'Unsafe player ID')
    index = player.get('default_map')
    require(type(index) is int and 0 <= index < len(maps), 'Invalid default map')
    names = player.get('map_names')
    require(isinstance(names, list) and len(names) >= len(maps) and all(isinstance(n, str) for n in names), 'Invalid map names')
    require(isinstance(player.get('name'), str) and number(player.get('cash')), 'Invalid player name/cash')
    for key in ('gifts', 'completedMissions', 'rewardedMissions'):
        require(isinstance(state.get(key), list), 'Missing or invalid privateState.' + key)
    require(all(type(n) is int and n >= 0 for n in state['gifts']), 'Invalid gift counts')
    require(type(state.get('potion')) is int and state['potion'] >= 0, 'Invalid potion count')
    for town in maps:
        require(isinstance(town, dict), 'Invalid map object')
        require('oil' not in town and 'steel' not in town, 'Unsupported game save')
        require(all(number(town.get(k)) for k in ('coins', 'wood', 'stone', 'food', 'xp', 'level')), 'Invalid map resources/level')
        require(isinstance(town.get('items'), list), 'Invalid map items')
        for item in town['items']:
            require(isinstance(item, list) and len(item) >= 6, 'Truncated item record')
            require(all(number(v) for v in item[:6]), 'Invalid item fields')
            if len(item) > 6:
                require(isinstance(item[6], list), 'Invalid contained units')
