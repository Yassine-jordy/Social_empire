import copy
import unittest
from unittest.mock import patch
import test_legacy_actions
from test_bootstrap import sessions


class CollectionRedemptionTests(unittest.TestCase):
    post = test_legacy_actions.LegacyActionsTests.post

    def setUp(self):
        test_legacy_actions.LegacyActionsTests.setUp(self)
        s = sessions.session(self.uid)
        s['privateState']['collections'] = [[]]+[[0]*6 for _ in range(23)]
        s['privateState']['collections'][6] = [0,1,1,1,1,1]
        s['privateState']['collectionsCompleted'] = []
        s['privateState']['gifts'] = [0]*2000
        sessions.save_session(self.uid)

    def test_exchange_retry_reload(self):
        action = [('finish_collection',[6])]
        self.assertEqual(self.post(action).status_code,200)
        sessions.load_saved_villages()
        after = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(after['privateState']['gifts'][551],1)
        self.assertEqual(after['privateState']['collections'][6],[1,0,0,0,0,0])
        self.assertIn(6,after['privateState']['collectionsCompleted'])
        self.assertIn(551,after['privateState']['boughtUnits'])
        self.assertEqual(self.post(action).status_code,200)
        self.assertEqual(sessions.session(self.uid),after)
        self.assertEqual(self.post(action,2).status_code,400)
        self.assertEqual(sessions.session(self.uid),after)

    def test_cash_price_and_retry(self):
        s = sessions.session(self.uid)
        s['privateState']['collections'][6] = [0,1,0,0,0,0]
        sessions.save_session(self.uid)
        before = copy.deepcopy(s)
        self.assertEqual(self.post([('finish_collection',[6,1,1])]).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
        action = [('finish_collection',[6,1,4])]
        self.assertEqual(self.post(action).status_code,200)
        self.assertEqual(sessions.session(self.uid)['playerInfo']['cash'],96)
        self.assertEqual(sessions.session(self.uid)['privateState']['collections'][6],[1,0,0,0,0,0])
        after = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post(action).status_code,200)
        self.assertEqual(self.post(action,2).status_code,400)
        self.assertEqual(sessions.session(self.uid),after)

    def test_invalid_and_disk_failure_atomic(self):
        before = copy.deepcopy(sessions.session(self.uid))
        for args in ([],[0],[24],[True],[1],[6,1],[23,1,999],[21,1,400],[6,False,1]):
            self.assertEqual(self.post([('finish_collection',args)]).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)
        with patch.object(sessions.os,'replace',side_effect=OSError('simulated')):
            self.assertEqual(self.post([('finish_collection',[6])]).status_code,503)
        self.assertEqual(sessions.session(self.uid),before)

    def test_unique_and_repeatable_decorations(self):
        s = sessions.session(self.uid)
        s['privateState']['collections'][21] = [0,2,2,2,2,2]
        s['privateState']['collections'][1] = [0,2,2,2,2,2]
        sessions.save_session(self.uid)
        self.assertEqual(self.post([('finish_collection',[21])],1).status_code,200)
        self.assertEqual(self.post([('finish_collection',[21])],2).status_code,400)
        self.assertEqual(self.post([('finish_collection',[1])],2).status_code,200)
        self.assertEqual(self.post([('finish_collection',[1])],3).status_code,200)
        self.assertEqual(sessions.session(self.uid)['privateState']['gifts'][176],2)
