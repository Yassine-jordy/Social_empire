import copy
import json
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from test_bootstrap import server, sessions, database, PREFIX
from get_game_config import get_game_config


class LegacyActionsTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        name = 'legacy-' + str(uuid.uuid4())
        self.client.post('/register', data=dict(username=name,password='test-password'))
        self.client.post('/', data=dict(username=name,password='test-password'))
        self.uid = database.get_userid(name)
        save = sessions.session(self.uid)
        save['maps'][0]['items'] = []
        save['playerInfo']['cash'] = 100
        sessions.save_session(self.uid)

    def post(self, commands, number=1):
        batch = dict(ts=0, first_number=number, accessToken='', tries=1, publishActions='0',
                     commands=[dict(cmd=name,args=args) for name,args in commands])
        return self.client.post(PREFIX+'command.php',data=dict(USERID=self.uid,user_key='legacy',
            language='en',client_id='legacy-test',data='0'*64+';'+json.dumps(batch)))

    def test_store_frombug_transfer_retry_reload_and_validation(self):
        save = sessions.session(self.uid)
        save['maps'][0]['items'] = [[299,59,55,0,0,0,[],{}]]
        save['privateState']['gifts'] = [0] * 300
        sessions.save_session(self.uid)
        action = [('store_item_frombug',[59,55,0,299])]
        self.assertEqual(self.post(action).status_code,200)
        sessions.load_saved_villages()
        save = sessions.session(self.uid)
        self.assertEqual(save['maps'][0]['items'],[])
        self.assertEqual(save['privateState']['gifts'][299],1)
        before = copy.deepcopy(save)
        self.assertEqual(self.post(action).status_code,200)
        self.assertEqual(sessions.session(self.uid),before)
        for args in ([59,55,0,299], [59,55,-1,299], [59,55,1,299], [59,55,0,999999], [59,55,0]):
            self.assertEqual(self.post([('store_item_frombug',args)],number=2).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)
        save = sessions.session(self.uid)
        save['maps'][0]['items'] = [[299,59,55,0,0,0,[],{'si':[]}]]
        sessions.save_session(self.uid)
        before = copy.deepcopy(save)
        self.assertEqual(self.post(action,number=3).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)

    def test_zeppelin_observed_batch_and_retry_reload(self):
        commands = [('buy',[299,59,55,0,0,1,1,'b'])]
        commands += [('buy_si_help',[59,55,0,299,1])] * 20
        commands += [('finish_si',[59,55,0,299])]
        self.assertEqual(self.post(commands).status_code,200)
        save = sessions.session(self.uid)
        self.assertEqual(save['maps'][0]['items'][0][7],{})
        self.assertEqual(save['playerInfo']['cash'],100)
        before = copy.deepcopy(save)
        sessions.load_saved_villages()
        self.assertEqual(self.post(commands).status_code,200)
        self.assertEqual(sessions.session(self.uid),before)

    def test_social_paid_help_validation_and_transaction_rollback(self):
        self.assertEqual(self.post([('buy',[299,59,55,0,0,1,1,'b'])]).status_code,200)
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post([('buy_si_help',[59,55,0,299]),('finish_si',[59,55,0,299])]).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
        self.assertEqual(self.post([('buy_si_help',[59,55,0,299])]).status_code,200)
        save = sessions.session(self.uid)
        self.assertEqual(save['playerInfo']['cash'],95)
        self.assertEqual(save['maps'][0]['items'][0][7]['si'],['0'])
        for name,args in [('buy_si_help',[58,55,0,299,1]),('finish_si',[59,55,0,299]),
                          ('buy_si_help',[59,55,0,299,2]),('buy_si_help',[59,55,-1,299,1])]:
            before = copy.deepcopy(sessions.session(self.uid))
            self.assertEqual(self.post([(name,args)],number=2).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)
        save['playerInfo']['cash']=0
        sessions.save_session(self.uid)
        self.assertEqual(self.post([('buy_si_help',[59,55,0,299])],number=2).status_code,400)

    def test_existing_queue_speedup_price_retry_and_reload(self):
        save = sessions.session(self.uid)
        save['maps'][0]['items'] = [[1529,53,57,0,0,0,[684,695],{'bq':'1'}]]
        save['privateState']['barracksQueues']={'1':dict(ts=1800000000,amount=1,unit=831)}
        sessions.save_session(self.uid)
        args=[('speed_up_queue',['1'])]
        with patch('command.timestamp_now',return_value=1800000000):
            self.assertEqual(self.post(args).status_code,200)
        save = sessions.session(self.uid)
        self.assertEqual(save['playerInfo']['cash'],67) # ceil(116000/3600)
        self.assertEqual(save['privateState']['barracksQueues']['1']['ts'],0)
        self.assertEqual(save['maps'][0]['items'][0][6],[684,695])
        before=copy.deepcopy(save)
        sessions.load_saved_villages()
        self.assertEqual(self.post(args).status_code,200)
        self.assertEqual(sessions.session(self.uid),before)
        self.assertEqual(self.post(args,number=2).status_code,200)
        self.assertEqual(sessions.session(self.uid)['playerInfo']['cash'],67)
        self.assertEqual(self.post([('speed_up_queue',['missing'])],number=3).status_code,400)
        self.assertEqual(self.post([('speed_up_queue',['2'])],number=3).status_code,400)

    def test_speedup_insufficient_cash_and_ambiguous_owner_are_atomic(self):
        save=sessions.session(self.uid)
        save['maps'][0]['items']=[[1529,53,57,0,0,0,[],{'bq':'1'}]]
        save['privateState']['barracksQueues']={'1':dict(ts=1800000000,amount=1,unit=831)}
        save['playerInfo']['cash']=1
        sessions.save_session(self.uid)
        before=copy.deepcopy(save)
        with patch('command.timestamp_now',return_value=1800000000):
            self.assertEqual(self.post([('speed_up_queue',['1'])]).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
        save['playerInfo']['cash']=100
        save['maps'][0]['items'].append([26,52,52,0,0,0,[],{'bq':'1'}])
        sessions.save_session(self.uid)
        before=copy.deepcopy(save)
        self.assertEqual(self.post([('speed_up_queue',['1'])]).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
