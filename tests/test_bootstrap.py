"""Isolated installation/account regression tests; never use real player data."""
import os
import sys
import tempfile
import unittest
import sqlite3
import json
import subprocess
import copy
import uuid
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
workspace = tempfile.TemporaryDirectory(prefix="social-empires-tests-")
os.environ['SOCIAL_EMPIRES_DATA_DIR'] = workspace.name
assets = Path(workspace.name) / 'assets'
(assets / 'flash').mkdir(parents=True)
(assets / 'flash/SELoader.swf').write_bytes(b'asset-fixture')
os.environ['SOCIAL_EMPIRES_ASSETS_DIR'] = str(assets)
os.environ.pop('SOCIAL_EMPIRES_SECRET_KEY', None)

import server
import database
import sessions

server.app.config['TESTING'] = True
PREFIX = server.GAME_PREFIX

class BootstrapTests(unittest.TestCase):
    def account(self, name):
        client = server.app.test_client()
        self.assertEqual(client.post('/register', data={'username': name, 'password': 'test-password'}).status_code, 302)
        self.assertEqual(client.post('/', data={'username': name, 'password': 'test-password'}).status_code, 302)
        return client, database.get_userid(name)

    def form(self, uid):
        return {'USERID': uid, 'user_key': 'legacy-placeholder', 'language': 'en', 'client_id': 'test'}

    def command(self, client, uid, name):
        data = {'ts': 0, 'first_number': 0, 'accessToken': '', 'tries': 0,
                'publishActions': False, 'commands': [{'cmd': 'name_map', 'args': [0, name]}]}
        return client.post(PREFIX+'command.php', data={**self.form(uid), 'data': '0'*64+';'+json.dumps(data)})

    def test_fresh_registration_passwords_and_duplicate(self):
        client, uid = self.account('fresh')
        self.assertTrue(Path(sessions.SAVES_DIR, uid+'.save.json').exists())
        self.assertTrue(database.check_login('fresh', 'test-password'))
        self.assertFalse(database.check_login('fresh', 'wrong'))
        count = len(sessions.all_saves_userid())
        self.assertEqual(client.post('/register', data={'username':'fresh','password':'different'}).status_code, 200)
        self.assertEqual(len(sessions.all_saves_userid()), count)
        self.assertEqual(database.get_userid('fresh'), uid)
        with closing(database.get_connection()) as conn:
            self.assertNotEqual(conn.execute('SELECT password_hash FROM users WHERE username=?', ('fresh',)).fetchone()[0], 'test-password')

    def test_registration_failure_rolls_back_account(self):
        def fail():raise OSError('simulated disk error')
        with self.assertRaises(OSError):
            database.register_user('failed', 'test-password', create_village=fail)
        with closing(database.get_connection()) as conn:
            self.assertIsNone(conn.execute('SELECT username FROM users WHERE username=?', ('failed',)).fetchone())

    def test_new_save_failure_cleans_memory(self):
        before = sessions.all_saves_userid()
        with patch.object(sessions, 'save_session', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):sessions.new_village()
        self.assertEqual(before, sessions.all_saves_userid())

    def test_anonymous_and_cross_account_access(self):
        alice, aid = self.account('alice'); bob, bid = self.account('bob')
        anon = server.app.test_client()
        self.assertEqual(anon.post(PREFIX+'get_player_info.php', data=self.form(aid)).status_code, 401)
        self.assertEqual(self.command(anon, aid, 'hacked').status_code, 401)
        self.assertEqual(alice.post(PREFIX+'get_player_info.php', data=self.form(bid)).status_code, 403)
        self.assertEqual(self.command(alice, bid, 'hacked').status_code, 403)
        self.assertEqual(alice.post(PREFIX+'get_player_info.php', data={**self.form(aid), 'user':bid}).status_code, 403)
        own = alice.post(PREFIX+'get_player_info.php', data=self.form(aid))
        self.assertEqual(own.status_code, 200)
        neighbor = next(n for n in own.json['neighbors'] if n['pid']==bid)
        self.assertEqual(set(neighbor), {'pid','name','pic','xp','level'})
        self.assertEqual(sessions.session(bid)['playerInfo']['map_names'][0], 'My Empire')
        self.assertEqual(anon.get('/api/pvp/history').status_code, 401)
        self.assertEqual(bob.get('/api/pvp/history').status_code, 200)

    def test_logout_and_guest_path(self):
        client, uid = self.account('logout')
        self.assertEqual(client.get('/ruffle.html').status_code, 200)
        self.assertEqual(client.get('/logout').status_code, 302)
        self.assertEqual(self.command(client, uid, 'bad').status_code, 401)
        count = len(sessions.all_saves_userid())
        self.assertEqual(client.get('/new.html').location, '/register')
        self.assertEqual(len(sessions.all_saves_userid()), count)

    def test_optional_client_is_allowlisted_and_session_scoped(self):
        client, uid = self.account('client-version')
        other, _ = self.account('client-version-other')
        self.assertEqual(client.get('/ruffle.html?client=../secret').status_code, 400)
        self.assertEqual(client.get('/ruffle.html?client=1.2.7').status_code, 404)
        with patch.object(server.Path, 'is_file', return_value=True):
            response = client.get('/ruffle.html?client=1.2.7')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SocialEmpires1.2.7sec.swf', response.data)
        with client.session_transaction() as state:
            self.assertEqual(state['GAMEVERSION'], 'SocialEmpires1.2.7sec.swf')
        with other.session_transaction() as state:
            self.assertEqual(state['GAMEVERSION'], 'SocialEmpires1.2.7sec.swf')
        client.get('/logout')
        with patch.object(server.Path, 'is_file', return_value=True):
            self.assertEqual(client.get('/ruffle.html?client=1.2.7').status_code, 302)
        client.post('/', data={'username':'client-version', 'password':'test-password'})
        response = client.get('/ruffle.html')
        self.assertIn(b'SocialEmpires1.2.7sec.swf', response.data)

    def test_default_client_survives_plain_logout_login(self):
        client, uid = self.account('relogin-client')
        for _ in range(2):
            page = client.get('/ruffle.html')
            self.assertIn(b'SocialEmpires1.2.7sec.swf', page.data)
            self.assertEqual(page.headers['Cache-Control'], 'no-store')
            client.get('/logout')
            with client.session_transaction() as state:
                self.assertNotIn('USERID', state)
                self.assertNotIn('ACCOUNT_USERNAME', state)
            client.post('/', data={'username':'relogin-client', 'password':'test-password'})
        with patch.object(server.Path, 'is_file', return_value=True):
            client.get('/ruffle.html?client=0.9.26b')
        client.get('/logout')
        client.post('/', data={'username':'relogin-client', 'password':'test-password'})
        self.assertIn(b'SocialEmpires0926bsec.swf', client.get('/ruffle.html').data)

    def test_assets_cache_and_path_traversal(self):
        client = server.app.test_client(); prefix='/default01.static.socialpointgames.com/static/socialempires/'
        with client.get(prefix+'flash/SELoader.swf') as response:
            self.assertEqual(response.data, b'asset-fixture')
        cache=Path(workspace.name)/'download_assets/assets';cache.mkdir(parents=True,exist_ok=True)
        (cache/'cached.txt').write_text('cached')
        with client.get(prefix+'cached.txt') as response:
            self.assertEqual(response.data, b'cached')
        self.assertEqual(client.get(prefix+'missing.swf').status_code, 404)
        self.assertEqual(client.get(prefix+'../social_empires.db').status_code, 404)
        self.assertEqual(client.get(prefix+'..%5csocial_empires.db').status_code, 404)

    def test_unsupported_action_offers_recovery_without_acknowledging(self):
        client, uid = self.account('unsupported-recovery')
        before = copy.deepcopy(sessions.session(uid))
        for name, args in [('speed_up_queue', ['1']),
                           ('buy_si_help', [59, 55, 0, 299, 1]),
                           ('finish_si', [59, 55, 0, 299])]:
            batch = dict(ts=0, first_number=1, accessToken='', tries=1, publishActions='0',
                         commands=[dict(cmd=name, args=args)])
            response = client.post(PREFIX+'command.php', data={**self.form(uid),
                'data':'0'*64+';'+json.dumps(batch)})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json['result'], 'error')
            self.assertEqual(response.json['code'], 'unsupported_action')
            self.assertEqual(response.json['recovery'], 'reload_saved_empire')
            self.assertEqual(sessions.session(uid), before)

    def test_malformed_command_rejected(self):
        client, uid = self.account('malformed')
        for payload in ('x', '0'*64+';not-json', '0'*64+';[]'):
            self.assertEqual(client.post(PREFIX+'command.php', data={**self.form(uid),'data':payload}).status_code, 400)

    def test_failed_write_preserves_disk_save(self):
        client, uid = self.account('atomic')
        path=Path(sessions.SAVES_DIR)/f'{uid}.save.json';before=path.read_bytes()
        with patch.object(sessions.os, 'replace', side_effect=OSError('simulated interruption')):
            with self.assertRaises(OSError):sessions.save_session(uid)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(Path(sessions.SAVES_DIR).glob('.save-*.tmp')), [])

    def test_restart_from_different_directory(self):
        client, uid = self.account('restart')
        self.assertEqual(self.command(client, uid, 'Persistent Empire').status_code, 200)
        code = '''import server,database,sessions,json
c=server.app.test_client()
assert c.post('/',data={'username':'restart','password':'test-password'}).status_code==302
uid=database.get_userid('restart')
assert sessions.session(uid)['playerInfo']['map_names'][0]=='Persistent Empire'
assert c.get('/ruffle.html').status_code==200
print('RESTART_OK')
'''
        env=dict(os.environ);env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
        run=subprocess.run([sys.executable,'-B','-c',code],env=env,cwd=workspace.name,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        self.assertIn('RESTART_OK', run.stdout)
        self.assertEqual(database.get_session_secret(), server.app.secret_key)

    def test_migrate_legacy_database_preserves_rows(self):
        path=Path(workspace.name)/'legacy.db'
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute('CREATE TABLE users(username TEXT UNIQUE, password_hash TEXT)')
            conn.execute("INSERT INTO users VALUES('legacy','retained-hash')")
            conn.execute('CREATE TABLE pvp_battles(id INTEGER PRIMARY KEY, attacker_userid TEXT, victim_userid TEXT, win INTEGER, gold INTEGER, xp INTEGER, honor INTEGER, duration INTEGER, victim_units TEXT, created_at TEXT)')
            conn.execute("INSERT INTO pvp_battles VALUES(1,'a','b',1,10,2,0,5,'[]','old')")
        with patch.object(database,'DB_NAME',str(path)):
            database.init_database();database.init_database()
            with closing(database.get_connection()) as conn:
                self.assertEqual(conn.execute('SELECT password_hash FROM users').fetchone()[0], 'retained-hash')
                self.assertEqual(conn.execute('SELECT gold,seen_by_victim FROM pvp_battles').fetchone(), (10,0))
                self.assertEqual(conn.execute('SELECT version FROM schema_migrations').fetchall(), [(1,)])

    def test_legacy_import_preserves_source_and_identity(self):
        _, uid = self.account('import-source')
        village=copy.deepcopy(sessions.session(uid));legacy_id=str(uuid.uuid4())
        village['playerInfo']['pid']=legacy_id
        source=Path(workspace.name)/'external.save.json';source.write_text(json.dumps(village),encoding='utf-8')
        before=source.read_bytes()
        self.assertTrue(database.register_user('imported','test-password',
            create_village=lambda:sessions.import_village(source),discard_village=sessions.discard_new_village))
        self.assertEqual(database.get_userid('imported'),legacy_id)
        self.assertEqual(sessions.session(legacy_id),village)
        self.assertEqual(source.read_bytes(),before)
        with self.assertRaises(ValueError):sessions.import_village(source)

if __name__ == '__main__':
    unittest.main()
