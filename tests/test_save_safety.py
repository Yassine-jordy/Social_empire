"""Regression tests for batch durability, migrations and inventory failure paths."""
import copy
import json
import uuid
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

# Reuse the suite's disposable installation rather than importing real player data.
from test_bootstrap import server, sessions, database, PREFIX
import command
import version
from constants import Constant
from save_schema import validate_save


class SaveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.client=server.app.test_client()
        username='safety-'+str(uuid.uuid4())
        self.client.post('/register',data={'username':username,'password':'test-password'})
        self.client.post('/',data={'username':username,'password':'test-password'})
        self.uid=database.get_userid(username)
        self.path=Path(sessions.SAVES_DIR)/(self.uid+'.save.json')

    def batch(self, commands):
        return {'ts':0,'first_number':0,'accessToken':'','tries':0,'publishActions':False,
                'commands':[{'cmd':name,'args':args} for name,args in commands]}

    def post(self, commands):
        return self.client.post(PREFIX+'command.php',data={'USERID':self.uid,'user_key':'legacy',
            'language':'en','client_id':'test','data':'0'*64+';'+json.dumps(self.batch(commands))})

    def snapshot(self):
        return copy.deepcopy(sessions.session(self.uid)), self.path.read_bytes()

    def test_observed_onboarding_batch_size_and_upper_bound(self):
        # The real client initializes 390 objects in one packet. Exercise a
        # packet of that size without depending on unrelated object handlers.
        commands = [('name_map', [0, 'Initialized'])] * 390
        self.assertEqual(self.post(commands).status_code, 200)
        before = self.snapshot()
        self.assertEqual(self.post(commands + [('name_map', [0, 'Overflow'])] * 123).status_code, 400)
        self.assertEqual(self.snapshot(), before)

    def test_late_invalid_arguments_roll_back_memory_and_disk(self):
        before=self.snapshot()
        response=self.post([('name_map',[0,'Must roll back']),('move',[])])
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.snapshot(),before)

    def test_unknown_and_stub_commands_are_not_success(self):
        for name in ('unknown','upgrade','start_quest','add_collectable'):
            with self.subTest(name=name):
                before=self.snapshot()
                self.assertEqual(self.post([('name_map',[0,'Must roll back']),(name,[])]).status_code,422)
                self.assertEqual(self.snapshot(),before)

    def test_write_failure_rolls_back_batch(self):
        before=self.snapshot()
        with patch.object(sessions.os,'replace',side_effect=OSError('disk unavailable')):
            response=self.post([('name_map',[0,'Must roll back'])])
        self.assertEqual(response.status_code,503)
        self.assertEqual(self.snapshot(),before)

    def test_last_gift_placement_persists_empty_inventory(self):
        state=sessions.session(self.uid)['privateState'];state['gifts']=[0]*513;state['gifts'][512]=1
        sessions.save_session(self.uid)
        count=len(sessions.session(self.uid)['maps'][0]['items'])
        self.assertEqual(self.post([('place_gift',[512,10,10,0,0])]).status_code,200)
        saved=json.loads(self.path.read_text())
        self.assertEqual(saved['privateState']['gifts'],[])
        self.assertEqual(len(saved['maps'][0]['items']),count+1)
        sessions.load_saved_villages()
        self.assertEqual(sessions.session(self.uid),saved)

    def test_missing_negative_and_replayed_gifts_rejected(self):
        for cmd,args in [('place_gift',[512,10,10,0,0]),('place_gift',[-1,10,10,0,0]),('sell_gift',[512,0])]:
            before=self.snapshot()
            self.assertEqual(self.post([(cmd,args)]).status_code,400)
            self.assertEqual(self.snapshot(),before)

    def test_resurrection_rejected_without_consuming_potion(self):
        sessions.session(self.uid)['privateState']['potion']=2;sessions.save_session(self.uid)
        before=self.snapshot()
        self.assertEqual(self.post([('resurrect_hero',[512,10,10,0,'1'])]).status_code,422)
        self.assertEqual(self.snapshot(),before)

    def test_pvp_rejection_has_no_database_or_file_side_effects(self):
        with closing(database.get_connection()) as conn:
            before_rows=conn.execute('SELECT COUNT(*) FROM pvp_battles').fetchone()[0]
        before=self.snapshot()
        with patch.object(command,'record_pvp_battle') as record:
            self.assertEqual(self.post([('name_map',[0,'No partial save']),('end_attack',['{}'])]).status_code,422)
            record.assert_not_called()
        with closing(database.get_connection()) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM pvp_battles').fetchone()[0],before_rows)
        self.assertEqual(self.snapshot(),before)

    def test_quest_result_without_start_rejected_and_batch_rolled_back(self):
        result = {'map': 0, 'resources': {'g': 999999, 'x': 999999},
                  'units': [], 'win': 1, 'duration': 0, 'voluntary_end': 0,
                  'quest_id': 0, 'difficulty': 0}
        before = self.snapshot()
        for _ in range(2):
            response = self.post([('name_map', [0, 'Must not persist']),
                                  ('end_quest', [json.dumps(result)])])
            self.assertEqual(response.status_code, 422)
            self.assertEqual(self.snapshot(), before)

    def test_concurrent_batches_do_not_lose_updates(self):
        sessions.session(self.uid)['playerInfo']['cash']=100;sessions.save_session(self.uid)
        before=sessions.session(self.uid)['maps'][0]['coins']
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:command.command(self.uid,self.batch([(Constant.CMD_EXCHANGE_CASH,[0])])),range(4)))
        self.assertEqual(sessions.session(self.uid)['maps'][0]['coins'],before+10000)
        self.assertEqual(json.loads(self.path.read_text())['playerInfo']['cash'],80)

    def test_versionless_migration_backup_and_reload(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(sessions,'SAVES_DIR',directory):
            save=copy.deepcopy(sessions.session(self.uid));save.pop('version')
            path=Path(directory)/(self.uid+'.save.json');path.write_text(json.dumps(save))
            original=path.read_bytes()
            try:
                sessions.load_saved_villages()
                self.assertEqual(sessions.session(self.uid)['version'],'0.04a')
                backups=list((Path(directory)/'backups').glob('*.bak'))
                self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),original)
                sessions.load_saved_villages()
                self.assertEqual(len(list((Path(directory)/'backups').glob('*.bak'))),1)
            finally:
                # The suite's next setup reloads its normal saves below.
                pass
        sessions.load_saved_villages()

    def test_future_and_malformed_files_preserved_without_blocking_valid_player(self):
        original=copy.deepcopy(sessions.session(self.uid))
        with tempfile.TemporaryDirectory() as directory, patch.object(sessions,'SAVES_DIR',directory):
            good=Path(directory)/(self.uid+'.save.json');good.write_text(json.dumps(original))
            bad=copy.deepcopy(original);bad['version']='99.0';bad['playerInfo']['pid']=str(uuid.uuid4())
            future=Path(directory)/(bad['playerInfo']['pid']+'.save.json');future.write_text(json.dumps(bad))
            corrupt=Path(directory)/'corrupt.save.json';corrupt.write_text('{')
            before=future.read_bytes()
            sessions.load_saved_villages()
            self.assertEqual(sessions.all_saves_userid(),[self.uid])
            self.assertEqual(future.read_bytes(),before);self.assertEqual(corrupt.read_text(),'{')
        sessions.load_saved_villages()

    def test_failed_migration_does_not_mutate_input(self):
        save=copy.deepcopy(sessions.session(self.uid));save.pop('version');save['maps']=[]
        before=copy.deepcopy(save)
        with self.assertRaises((ValueError,IndexError)):version.migrate_loaded_save(save)
        self.assertEqual(save,before)

    def test_core_schema_rejects_missing_fields_and_truncated_items(self):
        for mutation in (lambda s:s['privateState'].pop('gifts'),lambda s:s.update(maps=[]),
                         lambda s:s['maps'][0]['items'].append([512]),
                         lambda s:s['maps'][0].update(coins=float('nan'))):
            save=copy.deepcopy(sessions.session(self.uid));mutation(save)
            with self.assertRaises(ValueError):validate_save(save)

    def test_all_supported_versions_migrate_and_future_version_is_untouched(self):
        for v in (None,'0.01a','0.02a','0.03a','0.04a'):
            save=copy.deepcopy(sessions.session(self.uid));save['version']=v
            version.migrate_loaded_save(save);self.assertEqual(save['version'],'0.04a')
        save=copy.deepcopy(sessions.session(self.uid));save['version']='99.0';before=copy.deepcopy(save)
        with self.assertRaises(ValueError):version.migrate_loaded_save(save)
        self.assertEqual(save,before)
