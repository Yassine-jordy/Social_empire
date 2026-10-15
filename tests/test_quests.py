import copy
import json
import unittest
from unittest.mock import patch

import test_legacy_actions
from test_bootstrap import sessions


class QuestTests(unittest.TestCase):
    post = test_legacy_actions.LegacyActionsTests.post
    start = [('start_quest', ['100000006', 0]), ('start_quest_new', [])]

    def setUp(self):
        test_legacy_actions.LegacyActionsTests.setUp(self)
        s = sessions.session(self.uid)
        s['maps'][0]['level'] = 80
        s['maps'][0]['items'] = [[539, 20, 20, 0, 0, 0]]
        s['privateState']['unlockedQuestIndex'] = 0
        s['privateState']['questsRank'] = {}
        s['playerInfo']['honor_points'] = 0
        sessions.save_session(self.uid)

    def result(self, **changes):
        # QuestIslaTrolls1.sendResults, including the borrowed high elf.
        value = dict(map=0, resources={'g': 0, 'x': 0}, units=[[557,1,0,1]],
                     win=1, duration=30, voluntary_end=0, quest_id='100000006',
                     difficulty=1, set_unlocked_index=1)
        value.update(changes)
        return [('end_quest', [json.dumps(value)])]

    def test_start_end_retry_and_reload(self):
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post(self.start).status_code, 200)
        sessions.load_saved_villages()
        active = copy.deepcopy(sessions.session(self.uid))
        self.assertTrue(active['privateState']['activeQuest']['registered'])
        self.assertEqual(self.post(self.start).status_code, 200)
        self.assertEqual(self.post([('start_quest_new',[])], 2).status_code, 200)
        self.assertEqual(len(sessions.session(self.uid)['maps'][0]['lastQuestTimes']), 1)
        # Client-reported combat gold/XP, not invented fixed quest rewards.
        action = self.result(resources={'g': 150, 'x': 25})
        self.assertEqual(self.post(action, 3).status_code, 200)
        sessions.load_saved_villages()
        after = copy.deepcopy(sessions.session(self.uid))
        self.assertNotIn('activeQuest', after['privateState'])
        self.assertIn('100000006', after['privateState']['completedQuests'])
        self.assertEqual(after['maps'][0]['xp'], before['maps'][0]['xp']+25)
        self.assertEqual(after['maps'][0]['coins'], before['maps'][0]['coins']+150)
        self.assertEqual(after['playerInfo']['honor_points'], 10)
        self.assertEqual(after['privateState']['unlockedQuestIndex'], 1)
        self.assertEqual(after['privateState']['questsRank']['100000006'], 1)
        self.assertEqual(after['maps'][0]['items'], before['maps'][0]['items'])
        self.assertEqual(self.post(action, 3).status_code, 200)
        self.assertEqual(self.post(action, 4).status_code, 400)
        self.assertEqual(sessions.session(self.uid), after)

    def test_replay_quest_uses_repeat_honor(self):
        for n in (1, 3):
            self.assertEqual(self.post(self.start, n).status_code, 200)
            self.assertEqual(self.post(self.result(), n+1).status_code, 200)
        self.assertEqual(sessions.session(self.uid)['playerInfo']['honor_points'], 15)

    def test_loss_and_unit_ownership(self):
        self.assertEqual(self.post(self.start).status_code, 200)
        before = copy.deepcopy(sessions.session(self.uid))
        bad = self.result(win=0, units=[[539,2,2,0]])
        self.assertEqual(self.post(bad, 2).status_code, 400)
        self.assertEqual(sessions.session(self.uid), before)
        action = self.result(win=0, voluntary_end=1, units=[[539,1,1,0]])
        self.assertEqual(self.post(action, 2).status_code, 200)
        sessions.load_saved_villages()
        after = sessions.session(self.uid)
        self.assertEqual(after['maps'][0]['items'], [])
        self.assertEqual(after['playerInfo']['honor_points'], 0)
        self.assertEqual(after['privateState']['questsRank'], {})
        self.assertEqual(after['privateState']['unlockedQuestIndex'], 0)

    def test_invalid_start_and_missing_attempt(self):
        before = copy.deepcopy(sessions.session(self.uid))
        for action in ([('start_quest',[])], [('start_quest',['100000007',0])],
                       [('start_quest',['100000006',1])], [('start_quest_new',[])],
                       [('start_quest',[True,0])], self.result()):
            self.assertEqual(self.post(action).status_code, 400)
            self.assertEqual(sessions.session(self.uid), before)
        sessions.session(self.uid)['maps'][0]['level'] = 1
        sessions.save_session(self.uid)
        self.assertEqual(self.post(self.start).status_code, 400)

    def test_invalid_results_and_disk_failure_are_atomic(self):
        self.assertEqual(self.post(self.start).status_code, 200)
        before = copy.deepcopy(sessions.session(self.uid))
        for changes in ({'quest_id':'100000007'}, {'map':1}, {'difficulty':4},
                        {'win':1,'voluntary_end':1}, {'resources':{'g':-1,'x':0}},
                        {'units':[[539,1,2,0]]}, {'units':[[1529,1,0,0]]},
                        {'units':[[539,1,0,0],[539,1,0,0]]}):
            self.assertEqual(self.post(self.result(**changes),2).status_code, 400)
            self.assertEqual(sessions.session(self.uid), before)
        with patch.object(sessions.os, 'replace', side_effect=OSError('simulated')):
            self.assertEqual(self.post(self.result(),2).status_code, 503)
        self.assertEqual(sessions.session(self.uid), before)
        self.assertEqual(self.post(self.result(),2).status_code, 200)

    def test_start_batch_rollback_and_overlapping_start(self):
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post([self.start[0],('start_quest_new',[1])]).status_code,400)
        self.assertEqual(sessions.session(self.uid), before)
        self.assertEqual(self.post(self.start).status_code,200)
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post(self.start,2).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
