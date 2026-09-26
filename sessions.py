import json
import os
import copy
import uuid
import random
import tempfile
import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from save_schema import validate_save
from flask import session
# from flask_session import SqlAlchemySessionInterface, current_app

from version import version_code
from engine import timestamp_now
from version import migrate_loaded_save
from constants import Constant

from bundle import VILLAGES_DIR, SAVES_DIR

__villages = {}  # ALL static neighbors
'''__villages = {
    "USERID_1": {
        "playerInfo": {...},
        "maps": [{...},{...}]
        "privateState": {...}
    },
    "USERID_2": {...}
}'''

__saves = {}  # ALL saved villages
state_lock = RLock()
_staged = ContextVar('staged_save', default=None)


@contextmanager
def save_transaction(USERID):
    """Serialize batches in this process; publish only after durable file replacement."""
    with state_lock:
        original = session(USERID)
        if original is None:
            raise ValueError('Unknown player')
        candidate = copy.deepcopy(original)
        token = _staged.set((USERID, candidate))
        try:
            yield candidate
            validate_save(candidate)
            save_session(USERID)
            __saves[USERID] = candidate
        finally:
            _staged.reset(token)
'''__saves = {
    "USERID_1": {
        "playerInfo": {...},
        "maps": [{...},{...}]
        "privateState": {...}
    },
    "USERID_2": {...}
}'''

with open(os.path.join(VILLAGES_DIR, "initial.json"), encoding="utf-8") as initial_file:
    __initial_village = json.load(initial_file)

# Load saved villages

def load_saved_villages():
    global __villages
    global __saves
    # Empty in memory
    __villages = {}
    __saves = {}
    # Saves dir check
    if not os.path.exists(SAVES_DIR):
        try:
            print(f"Creating '{SAVES_DIR}' folder...")
            os.mkdir(SAVES_DIR)
        except:
            print(f"Could not create '{SAVES_DIR}' folder.")
            exit(1)
    if not os.path.isdir(SAVES_DIR):
        print(f"'{SAVES_DIR}' is not a folder... Move the file somewhere else.")
        exit(1)
    # Static neighbors in /villages
    for file in os.listdir(VILLAGES_DIR):
        if file == "initial.json" or not file.endswith(".json"):
            continue
        print(f" * Loading static neighbour {file}... ", end='')
        with open(os.path.join(VILLAGES_DIR, file), encoding="utf-8") as village_file:
            village = json.load(village_file)
        if not is_valid_village(village):
            print("Invalid neighbour")
            continue
        USERID = village["playerInfo"]["pid"]
        if str(USERID) in __villages:
            print(f"Ignored: duplicated PID '{USERID}'.")
        else:
            __villages[str(USERID)] = village
            print("Ok.")
    # Invalid or unsupported files stay untouched and do not stop other players loading.
    for file in sorted(os.listdir(SAVES_DIR)):
        if not file.endswith('.save.json'):
            continue
        filename = os.path.join(SAVES_DIR, file)
        try:
            with open(filename, encoding='utf-8') as f:
                save = json.load(f)
            modified = migrate_loaded_save(save)
            USERID = str(save['playerInfo']['pid'])
            if file != USERID + '.save.json':
                raise ValueError('Filename does not match player ID')
            if USERID in __saves or USERID in __villages:
                raise ValueError('Duplicate player ID')
            if modified:
                backup_file(filename)
            __saves[USERID] = save
            if modified:
                try:
                    save_session(USERID)
                except Exception:
                    __saves.pop(USERID, None)
                    raise
            print(f' * Loaded save {file}')
        except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
            print(f' * Skipped save {file}: {error}')


# New village

def new_village() -> str:
    # Generate USERID
    USERID: str = str(uuid.uuid4())
    assert USERID not in all_userid()
    # Copy init
    village = copy.deepcopy(__initial_village)
    # Custom values
    village["version"] = version_code
    village["playerInfo"]["pid"] = USERID
    village["maps"][0]["timestamp"] = timestamp_now()
    village["privateState"]["dartsRandomSeed"] = abs(int((2**16 - 1) * random.random()))
    # Memory saves
    __saves[USERID] = village
    # Generate save file
    try:
        save_session(USERID)
    except Exception:
        __saves.pop(USERID, None)
        raise
    print("Done.")
    return USERID

# Access functions

def discard_new_village(USERID):
    """Rollback only a village just allocated by account registration."""
    if str(uuid.UUID(USERID)) != USERID:
        raise ValueError("Invalid new village ID")
    filename = os.path.join(SAVES_DIR, USERID + '.save.json')
    if os.path.exists(filename):
        os.unlink(filename)
    __saves.pop(USERID, None)


def import_village(filename):
    """Copy a compatible legacy save into this server without changing its source."""
    with open(filename, encoding='utf-8') as f:
        village = json.load(f)
    if not is_valid_village(village) or village.get('version') != version_code:
        raise ValueError("Import requires a valid 0.04a save; migrate older saves separately")
    # Import must be usable by current routes, not merely pass the historic validator.
    for section in ('playerInfo', 'privateState'):
        if not isinstance(village[section], dict) or not set(__initial_village[section]).issubset(village[section]):
            raise ValueError("Incomplete save section: " + section)
    if not village['maps'] or any(not set(__initial_village['maps'][0]).difference({'__#__ITEMS_hint'}).issubset(m) for m in village['maps']):
        raise ValueError("Incomplete save maps")
    USERID = village['playerInfo']['pid']
    if not isinstance(USERID, str) or str(uuid.UUID(USERID)) != USERID:
        raise ValueError("Import requires a canonical UUID player identity")
    if USERID in all_userid() or os.path.exists(os.path.join(SAVES_DIR, USERID+'.save.json')):
        raise ValueError("That player identity already exists; refusing to overwrite")
    __saves[USERID] = village
    try:
        save_info(USERID)
        save_session(USERID)
    except Exception:
        __saves.pop(USERID, None)
        raise
    return USERID

def all_saves_userid() -> list:
    "Returns a list of the USERID of every saved village."
    return list(__saves.keys())

def all_userid() -> list:
    "Returns a list of the USERID of every village."
    return list(__villages.keys()) + list(__saves.keys())

def save_info(USERID: str) -> dict:
    save = __saves[USERID]
    default_map = save["playerInfo"]["default_map"]
    empire_name = str(save["playerInfo"]["map_names"][default_map])
    xp = save["maps"][default_map]["xp"]
    level = save["maps"][default_map]["level"]
    return{"userid": USERID, "name": empire_name, "xp": xp, "level": level}

def all_saves_info() -> list:
    saves_info = []
    for userid in __saves:
        saves_info.append(save_info(userid))
    return list(saves_info)

def session(USERID: str) -> dict:
    assert(isinstance(USERID, str))
    staged = _staged.get()
    if staged is not None and staged[0] == USERID:
        return staged[1]
    return __saves[USERID] if USERID in __saves else None

def neighbor_session(USERID: str) -> dict:
    assert(isinstance(USERID, str))
    if USERID in __saves:
        return __saves[USERID]
    if USERID in __villages:
        return __villages[USERID]

def fb_friends_str(USERID: str) -> list:
    DELETE_ME = [{"uid": "1111", "pic_square":"http://127.0.0.1:5050/img/profile/Paladin_Justiciero.jpg"},
        {"uid": "aa_002", "pic_square":"/1025.png"}]
    friends = []
    # static villages
    for key in __villages:
        vill = __villages[key]
        # Avoid Arthur being loaded as friend.
        if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
            continue
        frie = {}
        frie["uid"] = vill["playerInfo"]["pid"]
        frie["pic_square"] = vill["playerInfo"]["pic"]
        if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
        friends += [frie]
    # other players
    for key in __saves:
        vill = __saves[key]
        if vill["playerInfo"]["pid"] == USERID:
            continue
        frie = {}
        frie["uid"] = vill["playerInfo"]["pid"]
        frie["pic_square"] = vill["playerInfo"]["pic"]
        if not frie["pic_square"]: frie["pic_square"] = "/img/profile/1025.png"
        friends += [frie]
    return friends

def neighbors(USERID: str) -> list:
    neighbors = []
    # static villages
    for key in __villages:
        vill = __villages[key]
        # Avoid Arthur being loaded as multiple neigtbors.
        if vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
        or vill["playerInfo"]["pid"] == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
            continue
        neigh = dict(vill["playerInfo"])
        neigh["coins"] = vill["maps"][0]["coins"]
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neigh["wood"] = vill["maps"][0]["wood"]
        neigh["food"] = vill["maps"][0]["food"]
        neigh["stone"] = vill["maps"][0]["stone"]
        neighbors += [neigh]
    # other players
    for key in __saves:
        vill = __saves[key]
        if vill["playerInfo"]["pid"] == USERID:
            continue
        # Expose a directory entry, never another account's private player fields.
        neigh = {field: vill["playerInfo"][field] for field in ("pid", "name", "pic")}
        neigh["xp"] = vill["maps"][0]["xp"]
        neigh["level"] = vill["maps"][0]["level"]
        neighbors += [neigh]
    return neighbors

# Check for valid village
# The reason why this was implemented is to warn the user if a save game from Social Wars was used by accident

def is_valid_village(save: dict):
    try:
        validate_save(save)
        return True
    except (ValueError, TypeError, KeyError):
        return False

# Persistency

def backup_session(USERID: str):
    return backup_file(os.path.join(SAVES_DIR, USERID + '.save.json'))


def backup_file(filename):
    """Keep exact pre-migration bytes once per content hash; never overwrite a backup."""
    with open(filename, 'rb') as source:
        content = source.read()
    digest = hashlib.sha256(content).hexdigest()
    directory = os.path.join(SAVES_DIR, 'backups')
    os.makedirs(directory, exist_ok=True)
    target = os.path.join(directory, os.path.basename(filename) + '.' + digest + '.bak')
    try:
        with open(target, 'xb') as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError:
        with open(target, 'rb') as existing:
            if existing.read() != content:
                raise OSError('Existing migration backup is incomplete')
    return target

def save_session(USERID: str):
    # TODO 
    file = f"{USERID}.save.json"
    print(f" * Saving village at {file}... ", end='')
    village = session(USERID)
    validate_save(village)
    if not USERID or os.path.basename(USERID) != USERID or any(c in USERID for c in '/\\:'):
        raise ValueError("Invalid save identity")
    os.makedirs(SAVES_DIR, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".save-", suffix=".tmp", dir=SAVES_DIR)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(village, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, os.path.join(SAVES_DIR, file))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Done.")
