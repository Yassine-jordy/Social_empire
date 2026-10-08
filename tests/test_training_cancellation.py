import copy
import unittest
from unittest.mock import patch
import test_normal_training
from test_bootstrap import sessions


class TrainingCancellationTests(unittest.TestCase):
    setUp = test_normal_training.NormalTrainingTests.setUp
    post = test_normal_training.NormalTrainingTests.post

    def start(self, number=1):
        self.assertEqual(self.post([('push_queue_unit',[59,52,136,539,2,1])],number).status_code,200)

    def test_cancel_refund_retry_reload(self):
        before = copy.deepcopy(sessions.session(self.uid))
        self.start()
        request = [('unqueue_unit',['2',136])]
        self.assertEqual(self.post(request,2).status_code,200)
        sessions.load_saved_villages()
        after = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(after['maps'][0]['coins'],before['maps'][0]['coins'])
        self.assertEqual(after['maps'][0]['food'],before['maps'][0]['food'])
        self.assertEqual(after['privateState']['barracksQueues'],{})
        self.assertNotIn('bq',after['maps'][0]['items'][0][7])
        self.assertEqual(self.post(request,2).status_code,200)
        self.assertEqual(sessions.session(self.uid),after)
        self.assertEqual(self.post(request,3).status_code,400)
        self.assertEqual(sessions.session(self.uid),after)

    def test_last_unit_refunds_actual_discounted_cost(self):
        self.start()
        save = sessions.session(self.uid)
        save['maps'][0]['items'].append([22,50,50,0,0,0])
        sessions.save_session(self.uid)
        self.start(2)
        before = copy.deepcopy(sessions.session(self.uid))
        self.assertEqual(self.post([('unqueue_unit',['2',136])],3).status_code,200)
        after = sessions.session(self.uid)
        self.assertEqual(after['maps'][0]['coins']-before['maps'][0]['coins'],270)
        self.assertEqual(after['maps'][0]['food']-before['maps'][0]['food'],540)
        queue = after['privateState']['barracksQueues']['2']
        self.assertEqual(queue['amount'],1)
        self.assertEqual(queue['ts'],before['privateState']['barracksQueues']['2']['ts'])
        self.assertEqual(queue['r'],{'1':{'g':300,'f':600}})
        self.assertEqual(self.post([('unqueue_unit',['2',136])],4).status_code,200)
        self.assertEqual(sessions.session(self.uid)['maps'][0]['coins'],10000)

    def test_invalid_requests_and_save_failure_are_atomic(self):
        self.start()
        before = copy.deepcopy(sessions.session(self.uid))
        for args in ([],['2'],['2',137],['3',136],[True,136],['2',True]):
            self.assertEqual(self.post([('unqueue_unit',args)],2).status_code,400)
            self.assertEqual(sessions.session(self.uid),before)
        with patch.object(sessions.os,'replace',side_effect=OSError('simulated')):
            self.assertEqual(self.post([('unqueue_unit',['2',136])],2).status_code,503)
        self.assertEqual(sessions.session(self.uid),before)
        self.assertEqual(self.post([('unqueue_unit',['2',136])],2).status_code,200)

    def test_historical_queue_without_cost_receipts(self):
        self.start()
        save = sessions.session(self.uid)
        del save['privateState']['barracksQueues']['2']['r']
        sessions.save_session(self.uid)
        self.assertEqual(self.post([('unqueue_unit',['2',136])],2).status_code,200)
        self.assertEqual(sessions.session(self.uid)['maps'][0]['coins'],10000)
        self.assertEqual(sessions.session(self.uid)['maps'][0]['food'],10000)
