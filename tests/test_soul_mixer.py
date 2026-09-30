"""Recovered rules and real-route safeguards, not a full mixing playthrough.

Ranked test units below are synthetic arithmetic fixtures, NEVER game recipes.
"""
import copy
import json
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from test_bootstrap import server, sessions, database, PREFIX
from get_game_config import get_game_config
import soul_mixer


class SoulMixerRulesTests(unittest.TestCase):
    def test_127_power_formula_inclusive_roll_and_equal_parent_adjustment(self):
        self.assertEqual(soul_mixer.result_power(10, 20, 0), 17)
        self.assertEqual(soul_mixer.result_power(20, 10, 3), 21)
        self.assertEqual(soul_mixer.result_power(10, 20, 12), 29)
        self.assertEqual(soul_mixer.result_power(1, 1, 0), 10)
        self.assertEqual(soul_mixer.result_power(20, 20, 0), 21)
        with self.assertRaises(ValueError):
            soul_mixer.result_power(10, 20, 13)

    def fixture(self, ranks):
        return {'items': [dict(id=str(i + 1), type='u', breeding_order=str(rank),
                               sm_training_time='123') for i, rank in enumerate(ranks)]}

    def test_input_exclusion_same_type_parents_and_original_fallback(self):
        cfg = self.fixture([10, 20, 30])
        self.assertEqual(soul_mixer.select_result(cfg, [1, 2], randbelow=lambda _: 0), 3)
        self.assertEqual(soul_mixer.select_result(cfg, [1, 1], randbelow=lambda _: 0), 2)
        self.assertEqual(soul_mixer.select_result(cfg, [2, 3], randbelow=lambda _: 12), 3)

    def test_above_400_uses_inclusive_server_draw(self):
        cfg = self.fixture([400, 410, 420, 430])
        bounds = []
        def highest(n):
            bounds.append(n)
            return n - 1
        self.assertEqual(soul_mixer.select_result(cfg, [1, 2], randbelow=highest), 4)
        self.assertEqual(bounds, [13, 31])

    def test_invalid_input_missing_timer_and_ambiguous_ranks(self):
        cfg = self.fixture([10, 20, 30])
        with self.assertRaises(ValueError):
            soul_mixer.select_result(cfg, [1, 999])
        cfg['items'][0].pop('sm_training_time')
        with self.assertRaises(NotImplementedError):
            soul_mixer.select_result(cfg, [1, 2])
        with self.assertRaises(NotImplementedError):
            soul_mixer.select_result(self.fixture([10, 10]), [1, 2])

    def test_upstream_reconstruction_has_unique_orders_and_exclusions(self):
        config = get_game_config()
        units = soul_mixer.ranked_units(config)
        self.assertEqual(len(units), 437)
        self.assertEqual(len({int(u['breeding_order']) for u in units}), 437)
        source = json.loads((Path(__file__).resolve().parents[1] / 'config/soul_mixer_restoration.json').read_text())
        self.assertFalse({int(u['id']) for u in units} & set(source['excluded_unit_ids']))
        self.assertEqual(config['globals']['SOUL_MIXER_MIN_LEVEL'], 8)
        self.assertEqual(config['globals']['SOUL_MIXER_POWERUPS_LEVELS'], source['globals']['SOUL_MIXER_POWERUPS_LEVELS'])


class SoulMixerRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        username = 'mixer-' + str(uuid.uuid4())
        self.client.post('/register', data={'username': username, 'password': 'test-password'})
        self.client.post('/', data={'username': username, 'password': 'test-password'})
        self.uid = database.get_userid(username)
        self.path = Path(sessions.SAVES_DIR) / (self.uid + '.save.json')
        save = sessions.session(self.uid)
        save['maps'][0].update(items=[], coins=10000, level=8,
                               xp=int(get_game_config()['levels'][7]['exp_required']))
        sessions.save_session(self.uid)

    def post(self, commands, userid=None, client=None, number=0):
        batch = dict(ts=0, first_number=number, accessToken='', tries=0, publishActions=False,
                     commands=[dict(cmd=name, args=args) for name, args in commands])
        return (client or self.client).post(PREFIX + 'command.php', data={
            'USERID': userid or self.uid, 'user_key': 'legacy', 'language': 'en',
            'client_id': 'test', 'data': '0' * 64 + ';' + json.dumps(batch)})

    def snapshot(self):
        return copy.deepcopy(sessions.session(self.uid)), self.path.read_bytes()

    def buy(self):
        return ('buy', [1529, 40, 40, 0, 0, 0, 1, 'b'])

    def test_placement_price_limit_and_reload(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        save = sessions.session(self.uid)
        self.assertEqual(save['maps'][0]['coins'], 8000)
        self.assertEqual(save['maps'][0]['items'][0][:2], [1529, 40])
        before = self.snapshot()
        self.assertEqual(self.post([self.buy()]).status_code, 400)
        self.assertEqual(self.snapshot(), before)
        sessions.load_saved_villages()
        self.assertEqual(sessions.session(self.uid), before[0])

    def test_free_discount_invalid_town_level_and_insufficient_gold(self):
        for index, value in [(5, 1), (6, 0), (6, -1), (4, -1), (4, 99), (1, 100)]:
            args = self.buy()[1]
            args[index] = value
            before = self.snapshot()
            self.assertEqual(self.post([('buy', args)]).status_code, 400)
            self.assertEqual(self.snapshot(), before)
        for change in [dict(coins=1999), dict(xp=0)]:
            save = sessions.session(self.uid)
            original = copy.deepcopy(save['maps'][0])
            save['maps'][0].update(change)
            sessions.save_session(self.uid)
            before = self.snapshot()
            self.assertEqual(self.post([self.buy()]).status_code, 400)
            self.assertEqual(self.snapshot(), before)
            save['maps'][0] = original
            sessions.save_session(self.uid)

    def test_anonymous_and_foreign_owner(self):
        before = self.snapshot()
        self.assertIn(self.post([self.buy()], client=server.app.test_client()).status_code, (401, 403))
        self.assertEqual(self.post([self.buy()], userid=str(uuid.uuid4())).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_no_ghost_withdrawal_and_existing_input_returned_once(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        before = self.snapshot()
        pop = ('pop_unit', [40, 40, 0, 512, 45, 45, 0])
        self.assertEqual(self.post([pop]).status_code, 400)
        self.assertEqual(self.snapshot(), before)
        sessions.session(self.uid)['maps'][0]['items'][0].append([512])
        sessions.save_session(self.uid)
        self.assertEqual(self.post([pop]).status_code, 200)
        after = self.snapshot()
        self.assertEqual(after[0]['maps'][0]['items'][0][6], [])
        self.assertEqual(sum(item[0] == 512 for item in after[0]['maps'][0]['items']), 1)
        self.assertEqual(self.post([pop]).status_code, 400)
        self.assertEqual(self.snapshot(), after)

    def test_invalid_input_does_not_consume_units_and_batch_rolls_back(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        sessions.session(self.uid)['maps'][0]['items'].append([503, 45, 45, 0, 0, 0])
        sessions.save_session(self.uid)
        before = self.snapshot()
        response = self.post([('name_map', [0, 'Must roll back']),
                              ('push_unit', [45, 45, 503, 40, 40, 0])])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.snapshot(), before)

    def test_two_inputs_capacity_replay_reload_and_lossless_return(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        town = sessions.session(self.uid)['maps'][0]
        first = [512, 45, 45, 0, 123, 2, [], {'health': 30}]
        town['items'].extend([first, [512, 46, 45, 0, 124, 0], [512, 47, 45, 0, 125, 0]])
        sessions.save_session(self.uid)
        push = ('push_unit', [45, 45, 512, 40, 40, 0])
        self.assertEqual(self.post([push]).status_code, 200)
        before = self.snapshot()
        self.assertEqual(self.post([push]).status_code, 400)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.post([('push_unit', [46, 45, 512, 40, 40, 0])]).status_code, 200)
        before = self.snapshot()
        self.assertEqual(self.post([('push_unit', [47, 45, 512, 40, 40, 0])]).status_code, 400)
        self.assertEqual(self.snapshot(), before)
        sessions.load_saved_villages()
        self.assertEqual(self.post([('pop_unit', [40, 40, 0, 512, 45, 45, 0])]).status_code, 200)
        self.assertIn(first, sessions.session(self.uid)['maps'][0]['items'])

    def test_active_legacy_queue_keeps_input_units_locked(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        save = sessions.session(self.uid)
        save['maps'][0]['items'][0].extend([[512], {'bq': '1'}])
        save['privateState']['barracksQueues'] = {'1': {'ts': 123, 'unit': 512, 'amount': 1}}
        sessions.save_session(self.uid)
        before = self.snapshot()
        self.assertEqual(self.post([('pop_unit', [40, 40, 0, 512, 45, 45, 0])]).status_code, 400)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_or_unrestored_queue_requests_never_grant_or_debit(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        before = self.snapshot()
        for name, args in [('pop_queue_unit', [1, 45, 45]),
                           ('unqueue_unit', [1, 1529])]:
            for _ in range(2):
                self.assertEqual(self.post([(name, args)]).status_code, 400 if name == 'pop_queue_unit' else 422)
                self.assertEqual(self.snapshot(), before)

    def test_powerup_price_retry_reload_validation_and_atomic_failure(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        before = self.snapshot()
        self.assertEqual(self.post([('buy_powerups', [0])]).status_code, 400)
        self.assertEqual(self.snapshot(), before)
        save = sessions.session(self.uid)
        save['maps'][0]['items'][0].extend([[684, 695], {}])
        save['playerInfo']['cash'] = 50
        sessions.save_session(self.uid)
        prices = get_game_config()['globals']['SOUL_MIXER_POWERUPS_LEVELS']
        for index, level in enumerate(prices):
            before_cash = sessions.session(self.uid)['playerInfo']['cash']
            request = [('buy_powerups', [index])]
            self.assertEqual(self.post(request, number=index).status_code, 200)
            self.assertEqual(sessions.session(self.uid)['playerInfo']['cash'], before_cash - level['cash_cost'])
            sessions.load_saved_villages()
            before = self.snapshot()
            self.assertEqual(self.post(request, number=index).status_code, 200)
            self.assertEqual(self.snapshot(), before)
        for args in ([], [-1], [6], [True], ['0'], [0, 1], [5]):
            before = self.snapshot()
            self.assertEqual(self.post([('buy_powerups', args)], number=6).status_code, 400)
            self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.post([('buy_powerups', [1])], number=0).status_code, 400)
        sessions.session(self.uid)['playerInfo']['cash'] = 10
        sessions.save_session(self.uid)
        before = self.snapshot()
        with patch.object(sessions.os, 'replace', side_effect=OSError('simulated')):
            self.assertEqual(self.post([('buy_powerups', [0])], number=6).status_code, 503)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.post([('buy_powerups', [0]), ('pop_queue_unit', [1, 45, 45])], number=6).status_code, 400)
        self.assertEqual(self.snapshot(), before)

    def test_original_flash_mixing_queue_retry_and_reload(self):
        self.assertEqual(self.post([self.buy()]).status_code, 200)
        save = sessions.session(self.uid)
        building = save['maps'][0]['items'][0]
        building[1:3] = [53, 57]
        building.extend([[684, 695], {'soulMixerInputs': [[684, 54, 57, 0, 0, 0], [695, 54, 58, 0, 0, 0]]}])
        sessions.save_session(self.uid)
        before = self.snapshot()
        request = [('push_queue_unit', [53, 57, 1529, 831, 1, 0])]
        for args in ([53, 57, 1529, 503, 1, 0], [52, 57, 1529, 831, 1, 0],
                     [53, 57, 1529, 831, 0, 0], [53, 57, 1529, 831, True, 0]):
            self.assertEqual(self.post([('push_queue_unit', args)]).status_code, 400)
            self.assertEqual(self.snapshot(), before)
        with patch('command.timestamp_now', return_value=1800000000):
            self.assertEqual(self.post(request).status_code, 200)
        after = self.snapshot()
        queued = after[0]['privateState']['barracksQueues']['1']
        self.assertEqual(queued, dict(ts=1800000000, amount=1, unit=831, r={'1': None}))
        self.assertEqual(after[0]['maps'][0]['items'][0][7]['bq'], '1')
        self.assertEqual(after[0]['maps'][0]['items'][0][6], [684, 695])
        self.assertEqual(after[0]['playerInfo']['cash'], before[0]['playerInfo']['cash'])
        sessions.load_saved_villages()
        self.assertEqual(self.post(request).status_code, 200)
        self.assertEqual(self.snapshot(), after)
        self.assertEqual(self.post([('push_queue_unit', [53, 57, 1529, 831, 2, 0])]).status_code, 400)
        self.assertEqual(self.snapshot(), after)

    def test_failed_save_preserves_purchase_money_and_inventory(self):
        before = self.snapshot()
        with patch.object(sessions.os, 'replace', side_effect=OSError('simulated')):
            self.assertEqual(self.post([self.buy()]).status_code, 503)
        self.assertEqual(self.snapshot(), before)
