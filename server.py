print (" [+] Loading basics...")
import os
import json
from pathlib import Path
if os.name == 'nt':
    os.system("color")
    os.system("title Social Empires Server")
else:
    import sys
    sys.stdout.write("\x1b]2;Social Empires Server\x07")

print (" [+] Loading game config...")
from get_game_config import get_game_config, patch_game_config
from database import (
    init_database,
    register_user,
    check_login,
    get_userid,
    get_received_pvp_battles,
    get_sent_pvp_battles,
    get_unseen_pvp_battles,
    mark_pvp_battles_seen,
    get_username_by_userid,
    get_session_secret
)
print (" [+] Loading players...")
from get_player_info import get_player_info, get_neighbor_info
from sessions import load_saved_villages, all_saves_userid, save_info, new_village, fb_friends_str, neighbor_session, discard_new_village, state_lock
load_saved_villages()

print (" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session, abort, g
from command import command
from engine import timestamp_now
from version import version_name
from constants import Constant
from quests import get_quest_map
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR

host = '0.0.0.0'
port = 5050

app = Flask(__name__, template_folder=TEMPLATES_DIR)
init_database()
app.secret_key = get_session_secret()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=2 * 1024 * 1024)

GAME_PREFIX = "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/"

@app.before_request
def require_player_ownership():
    game_request = request.path.startswith(GAME_PREFIX)
    api_request = request.path.startswith("/api/pvp/")
    page_request = request.path in ("/play.html", "/ruffle.html")
    if game_request or api_request or page_request or request.path in ('/', '/register', '/logout', '/new.html'):
        state_lock.acquire()
        g.state_lock_held = True
    if not (game_request or api_request or page_request):
        return
    username = session.get("ACCOUNT_USERNAME")
    userid = session.get("USERID")
    if not username or not userid or get_userid(username) != userid or userid not in all_saves_userid():
        session.clear()
        return redirect("/") if page_request else ({"error": "Authentication required"}, 401)
    if game_request:
        # A client identity is a consistency check, never the source of authority.
        for key in ("USERID", "user_id"):
            if any(value != userid for value in request.values.getlist(key)):
                return {"error": "Player identity does not match account"}, 403


@app.teardown_request
def release_state_lock(error=None):
    if g.pop('state_lock_held', False):
        state_lock.release()

print (" [+] Configuring server routes...")

##########
# ROUTES #
##########

## PAGES AND RESOURCES

@app.route("/", methods=["GET", "POST"])
def login():
    message = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if check_login(username, password):

            userid = get_userid(username)

            if userid is None or userid not in all_saves_userid():
                message = "This account has no empire."
            else:
                session.clear()
                session["ACCOUNT_USERNAME"] = username
                session["USERID"] = userid
                session["GAMEVERSION"] = "SocialEmpires0926bsec.swf"

                print("[LOGIN] Username:", username)
                print("[LOGIN] USERID:", userid)

                return redirect("/ruffle.html")

        else:
            message = "Invalid username or password."

    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    message = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            message = "Username and password are required."

        elif len(username) > 80 or len(password) > 1024:
            message = "Username or password is too long."
        elif register_user(username, password, create_village=new_village, discard_village=discard_new_village):
            return redirect("/")

        else:
            message = "Username already exists."

    return render_template("register.html", message=message)

@app.route("/play.html")
def play():
    print(session)

    if 'USERID' not in session:
        return redirect("/")
    if 'GAMEVERSION' not in session:
        return redirect("/")

    if session['USERID'] not in all_saves_userid():
        return redirect("/")
    
    USERID = session['USERID']
    GAMEVERSION = session['GAMEVERSION']
    print("[PLAY] USERID:", USERID)
    print("[PLAY] GAMEVERSION:", GAMEVERSION)
    return render_template("play.html", save_info=save_info(USERID), serverTime=timestamp_now(), friendsInfo=fb_friends_str(USERID), version=version_name, GAMEVERSION=GAMEVERSION, SERVER_ORIGIN=request.host_url.rstrip('/'))
@app.route("/api/pvp/unseen")
def pvp_unseen():
    userid = session.get("USERID")

    if not userid:
        return {"error": "Not logged in"}, 401

    battles = get_unseen_pvp_battles(userid)

    def battle_to_dict(row):
        return {
            "id": row[0],
            "attacker_userid": row[1],
            "victim_userid": row[2],
            "attacker_username": get_username_by_userid(row[1]),
            "win": row[3],
            "gold": row[4],
            "xp": row[5],
            "honor": row[6],
            "duration": row[7],
            "victim_units": json.loads(row[8]),
            "created_at": row[9],
            
        }

    return {
        "userid": userid,
        "count": len(battles),
        "battles": [battle_to_dict(row) for row in battles]
    }
@app.route("/api/pvp/mark-seen", methods=["POST"])
def pvp_mark_seen():
    userid = session.get("USERID")

    if not userid:
        return {"error": "Not logged in"}, 401

    mark_pvp_battles_seen(userid)

    return {
        "success": True,
        "userid": userid
    }
@app.route("/ruffle.html")
def ruffle():
    print(session)

    if 'USERID' not in session:
        return redirect("/")
    if 'GAMEVERSION' not in session:
        return redirect("/")

    if session['USERID'] not in all_saves_userid():
        return redirect("/")

    # Explicit per-session compatibility test; keep the normal login default.
    # 0.9.26b has no Soul Mixer panel. Never treat a query value as a file path.
    if 'client' in request.args:
        clients = {'0.9.26b': 'SocialEmpires0926bsec.swf',
                   '1.2.7': 'SocialEmpires1.2.7sec.swf'}
        selected = clients.get(request.args['client'])
        if selected is None:
            return {"error": "Unsupported client version"}, 400
        if not (Path(ASSETS_DIR) / 'flash' / selected).is_file():
            return {"error": "Selected client is missing from the asset archive"}, 404
        session['GAMEVERSION'] = selected
    
    USERID = session['USERID']
    GAMEVERSION = session['GAMEVERSION']
    print("[RUFFLE] USERID:", USERID)
    print("[RUFFLE] GAMEVERSION:", GAMEVERSION)
    return render_template("ruffle.html", save_info=save_info(USERID), serverTime=timestamp_now(), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host)

@app.route("/api/pvp/history")
def pvp_history():
    userid = session.get("USERID")

    if not userid:
        return {"error": "Not logged in"}, 401

    received = get_received_pvp_battles(userid)
    sent = get_sent_pvp_battles(userid)

    def battle_to_dict(row):
        return {
            "id": row[0],
            "attacker_userid": row[1],
            "victim_userid": row[2],
            "win": row[3],
            "gold": row[4],
            "xp": row[5],
            "honor": row[6],
            "duration": row[7],
            "victim_units": json.loads(row[8]),
            "created_at": row[9]
        }

    return {
        "userid": userid,
        "received": [battle_to_dict(row) for row in received],
        "sent": [battle_to_dict(row) for row in sent]
    }
@app.route("/new.html")
def new():
    return redirect("/register")

@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/img/<path:path>")
def images(path):
    return send_from_directory(TEMPLATES_DIR + "/img", path)

@app.route("/css/<path:path>")
def css(path):
    return send_from_directory(TEMPLATES_DIR + "/css", path)

## GAME STATIC


@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_projectiles.swf")
def similar_05122012_projectiles():
    return send_from_directory(ASSETS_DIR + "/swf", "20130417_projectiles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_magicParticles.swf")
def similar_05122012_magicParticles():
    return send_from_directory(ASSETS_DIR + "/swf", "20131010_magicParticles.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/swf/05122012_dynamic.swf")
def similar_05122012_dynamic():
    return send_from_directory(ASSETS_DIR + "/swf", "120608_dynamic.swf")

@app.route("/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def static_assets_loader(path):
    # Serve the archive or an existing cache. Missing files must not trigger
    # unbounded network downloads or writes derived from a request path.
    for directory in (ASSETS_DIR, os.path.join(BASE_DIR, "download_assets", "assets")):
        root = Path(directory).resolve()
        candidate = (root / path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return send_from_directory(str(root), path)
    abort(404)

## GAME DYNAMIC

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php", methods=['POST'])
def track_game_status_response():
    status = request.values['status']
    installId = request.values['installId']
    user_id = request.values['user_id']

    print(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
    return ("", 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php", methods=['GET','POST'])
def get_game_config_response():
    spdebug = None

    USERID = request.values['USERID']
    user_key = request.values['user_key']
    if 'spdebug' in request.values:
        spdebug = request.values['spdebug']
    language = request.values['language']

    print(f"get_game_config: USERID: {USERID}. --", request.values)
    return get_game_config()

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php", methods=['POST'])
def get_player_info_response():

    USERID = session['USERID']
    user_key = request.values['user_key']
    spdebug = request.values['spdebug'] if 'spdebug' in request.values else None
    language = request.values['language']
    neighbors = request.values['neighbors'] if 'neighbors' in request.values else None
    client_id = request.values['client_id']
    user = request.values['user'] if 'user' in request.values else None
    try:
        map = int(request.values.get('map', '0'))
    except ValueError:
        return {"error": "Invalid map"}, 400
    if map < 0:
        return {"error": "Invalid map"}, 400
    # Real-player visits need a client-compatible public-state projection.
    # Until that protocol is restored, never disclose another save's privateState.
    if user in all_saves_userid() and user != USERID:
        return {"error": "Player visits are not available yet"}, 403
    if user and user != USERID and not user.startswith("100000"):
        village = neighbor_session(user)
        if village is None:
            return {"error": "Unknown neighbor"}, 404
        if map >= len(village['maps']):
            return {"error": "Invalid map"}, 400

    print(f"get_player_info: USERID: {USERID}. user: {user} --", request.values)

    # Current Player
    if user is None or user == USERID:
        return (get_player_info(USERID), 200)
    # Arthur
    elif user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
    or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
    or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
        return (get_neighbor_info(user, map), 200)
    # Quest
    elif user.startswith("100000"): # Dirty but quick
        return get_quest_map(user)
    # Neighbor
    else:
        return (get_neighbor_info(user, map), 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/sync_error_track.php", methods=['POST'])
def sync_error_track_response():
    spdebug = None

    USERID = request.values['USERID']
    user_key = request.values['user_key']
    if 'spdebug' in request.values:
        spdebug = request.values['spdebug']
    language = request.values['language']
    error = request.values['error']
    current_failed = request.values['current_failed']
    tries = request.values['tries'] if 'tries' in request.values else None
    survival = request.values['survival']
    previous_failed = request.values['previous_failed']
    description = request.values['description']
    user_id = request.values['user_id']

    print(f"sync_error_track: USERID: {USERID}. [Error: {error}] tries: {tries}. --", request.values)
    return ("", 200)

@app.route("/null")
def flash_sync_error_response():
    sp_ref_cat = request.values['sp_ref_cat']

    if sp_ref_cat == "flash_sync_error":
        reason = "reload On Sync Error"
    elif sp_ref_cat == "flash_reload_quest":
        reason = "reload On End Quest"
    elif sp_ref_cat == "flash_reload_attack":
        reason = "reload On End Attack"

    print("flash_sync_error", reason, ". --", request.values)
    return redirect("/play.html")

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php", methods=['POST'])
def command_response():
    spdebug = None

    USERID = session['USERID']
    user_key = request.values['user_key']
    if 'spdebug' in request.values:
        spdebug = request.values['spdebug']
    language = request.values['language']
    client_id = request.values['client_id']

    print(f"command: USERID: {USERID}. --", request.values)

    data_str = request.values['data']
    if len(data_str) < 66 or data_str[64] != ';':
        return {"error": "Invalid command envelope"}, 400
    try:
        data = json.loads(data_str[65:])
    except ValueError:
        return {"error": "Invalid command JSON"}, 400
    if not isinstance(data, dict) or not all(key in data for key in
            ("ts", "first_number", "accessToken", "tries", "publishActions", "commands")):
        return {"error": "Missing command fields"}, 400
    # The bundled 0.9.26b client sends 390 commands while populating a fresh map.
    # Keep a bound, but allow that observed legitimate initialization packet.
    if not isinstance(data['commands'], list) or len(data['commands']) > 512 or any(
            not isinstance(c, dict) or not isinstance(c.get('cmd'), str) or not isinstance(c.get('args'), list)
            for c in data['commands']):
        return {"error": "Invalid commands"}, 400

    try:
        command(USERID, data)
    except NotImplementedError as error:
        return {"result": "error", "error": str(error)}, 422
    except (ValueError, TypeError, KeyError, IndexError) as error:
        return {"result": "error", "error": "Invalid command arguments or state"}, 400
    except OSError:
        app.logger.exception("Could not persist command batch")
        return {"result": "error", "error": "Save failed; batch was not applied"}, 503
    
    return ({"result": "success"}, 200)

@app.route("/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_continent_ranking.php")
def get_continent_ranking_response():

    USERID = request.values['USERID']
    worldChange = request.values['worldChange']
    if 'spdebug' in request.values:
        spdebug = request.values['spdebug']
    town_id = request.values['map']
    user_key = request.values['user_key']

    # TODO - stub
    response = {
        "world_id": 0,
        "continent": [
            {"posicion": 0, "nivel": 1, "user_id": 1111}, # villages/AcidCaos
            {"posicion": 1, "nivel": 0},
            {"posicion": 2, "nivel": 0},
            {"posicion": 3, "nivel": 0},
            {"posicion": 4, "nivel": 0},
            {"posicion": 5, "nivel": 0},
            {"posicion": 6, "nivel": 0},
            {"posicion": 7, "nivel": 0}
        ]
    }
    return(response)


########
# MAIN #
########

print (" [+] Running server...")

if __name__ == '__main__':
    app.run(host=host, port=port, debug=False)
