import copy
import unittest
from unittest.mock import patch
import test_normal_training
from test_bootstrap import sessions


class BuildingUpgradeTests(unittest.TestCase):
    setUp = test_normal_training.NormalTrainingTests.setUp
    post = test_normal_training.NormalTrainingTests.post
    request = [('sell',[59,52,136,0,0,'UPGR']),('buy',[390,59,52,1,0,0,1,'b'])]

    def test_captured_pair_retry_and_reload(self):
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post(self.request).status_code,200)
        sessions.load_saved_villages()
        after = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(after['maps'][0]['coins'],5000)
        self.assertEqual(after['maps'][0]['wood'],before['maps'][0]['wood']+50)
        self.assertEqual(after['maps'][0]['xp'],before['maps'][0]['xp']+500)
        self.assertEqual(after['maps'][0]['items'][0][:4],[390,59,52,1])
        self.assertEqual(after['privateState']['barracksQueues'],{})
        self.assertEqual(self.post(self.request).status_code,200)
        self.assertEqual(sessions.session(self.uid),after)
        self.assertEqual(self.post(self.request,2).status_code,400)
        self.assertEqual(sessions.session(self.uid),after)

    def test_invalid_pairs_atomic(self):
        before = copy.deepcopy(sessions.session(self.uid))
        requests = [self.request[:1], [self.request[0],('buy',[2,59,52,1,0,0,1,'b'])],
                    [self.request[0],('buy',[390,60,52,1,0,0,1,'b'])],
                    [('sell',[58,52,136,0,0,'UPGR']),self.request[1]],
                    [self.request[0],('buy',[390,59,52,1,0,1,1,'b'])]]
        for request in requests:
            self.assertEqual(self.post(request).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)

    def test_resources_level_active_queue_and_disk_failure(self):
        for field, value in [('coins',4999),('xp',0)]:
            save = sessions.session(self.uid)
            original = save['maps'][0][field]
            save['maps'][0][field] = value
            sessions.save_session(self.uid)
            before = copy.deepcopy(save)
            self.assertEqual(self.post(self.request).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)
            sessions.session(self.uid)['maps'][0][field] = original
            sessions.save_session(self.uid)
        save = sessions.session(self.uid)
        save['maps'][0]['items'][0].extend([[],{'bq':'2'}])
        sessions.save_session(self.uid)
        before = copy.deepcopy(save)
        self.assertEqual(self.post(self.request).status_code,400)
        self.assertEqual(sessions.session(self.uid),before)
        sessions.session(self.uid)['maps'][0]['items'][0][7].clear()
        sessions.save_session(self.uid)
        before = copy.deepcopy(sessions.session(self.uid))
        with patch.object(sessions.os,'replace',side_effect=OSError('simulated')):
            self.assertEqual(self.post(self.request).status_code,503)
        self.assertEqual(sessions.session(self.uid),before)
        self.assertEqual(self.post(self.request).status_code,200)
