import copy
import unittest
from unittest.mock import patch
import test_legacy_actions
from test_bootstrap import sessions
from get_game_config import get_game_config


class NormalTrainingTests(unittest.TestCase):
    post = test_legacy_actions.LegacyActionsTests.post
    def setUp(self):
        test_legacy_actions.LegacyActionsTests.setUp(self)
        save = sessions.session(self.uid)
        save['maps'][0].update(items=[[136,59,52,0,0,0]], xp=100000000, coins=10000, food=10000)
        save['privateState']['barracksQueues'] = {}
        sessions.save_session(self.uid)

    def test_exact_training_retry_reload_collection(self):
        action = [('push_queue_unit',[59,52,136,539,2,1])]
        with patch('command.timestamp_now', return_value=1800000000):
            self.assertEqual(self.post(action).status_code,200)
            self.assertEqual(self.post(action).status_code,200)
        sessions.load_saved_villages()
        save = sessions.session(self.uid)
        self.assertEqual((save['maps'][0]['coins'],save['maps'][0]['food']),(9700,9400))
        self.assertEqual(save['privateState']['barracksQueues']['2'],
                         dict(ts=1800000000,amount=1,unit=539,r={'1':{'g':300,'f':600}}))
        self.assertEqual(get_game_config()['items'][next(i for i,v in enumerate(get_game_config()['items']) if int(v['id'])==539)]['training_time'],10)
        collect = [('pop_queue_unit',['2',60,53])]
        with patch('command.timestamp_now', return_value=1800000009):
            self.assertEqual(self.post(collect,number=2).status_code,400)
        with patch('command.timestamp_now', return_value=1800000010):
            self.assertEqual(self.post(collect,number=2).status_code,200)
            self.assertEqual(self.post(collect,number=2).status_code,200)
        sessions.load_saved_villages()
        self.assertEqual(sum(r[0]==539 for r in sessions.session(self.uid)['maps'][0]['items']),1)
        self.assertEqual(sessions.session(self.uid)['privateState']['barracksQueues'],{})

    def test_validation_and_capacity(self):
        action = [('push_queue_unit',[59,52,136,539,2,1])]
        save = sessions.session(self.uid)
        save['maps'][0]['food'] = 599
        sessions.save_session(self.uid)
        before = copy.deepcopy(save)
        self.assertEqual(self.post(action).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)

    def test_discount_and_failed_save_are_atomic(self):
        save = sessions.session(self.uid)
        save['maps'][0]['items'].append([22,50,50,0,0,0])
        sessions.save_session(self.uid)
        before = copy.deepcopy(save)
        action = [('push_queue_unit',[59,52,136,539,2,1])]
        with patch.object(sessions.os,'replace',side_effect=OSError('simulated')):
            self.assertEqual(self.post(action).status_code,503)
        self.assertEqual(sessions.session(self.uid),before)
        self.assertEqual(self.post(action).status_code,200)
        after = sessions.session(self.uid)
        self.assertEqual((after['maps'][0]['coins'],after['maps'][0]['food']),(9730,9460))
        save = sessions.session(self.uid)
        save['maps'][0]['food'] = 10000
        sessions.save_session(self.uid)
        for args in ([58,52,136,539,2,1],[59,52,136,540,2,1]):
            self.assertEqual(self.post([('push_queue_unit',args)]).status_code,400)
        for number in range(1,6):
            self.assertEqual(self.post(action,number=number).status_code,200)
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post(action,number=6).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
