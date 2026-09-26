# Command system report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

There are 156 CMD constant declarations, 42 original dispatcher branches and 43 updated branches. The only new branch is CMD_END_ATTACK. Constants themselves are byte-identical. The 113 declarations without a branch are protocol coverage gaps, not 113 independently proven missing features; aliases and version-specific commands must be resolved against client traces.

`command.command` reads metadata but does not authenticate tokens or sequence/retry fields. It calls each handler against live state and saves once at the end. `server.command_response` ignores handler outcomes and always returns success after normal completion. Unknown commands, log-only quest starts, collectable TODO and attacker-mismatch early return therefore receive false success.

## Handler findings

| Family | Working portion | Required fix |
| --- | --- | --- |
| buy/move/orient/sell | Generic item-array edits | Eligibility, affordability, bounds/collisions, actual ownership; no refund without removal |
| collect | Config-based arithmetic | Validate item instance/timer, update collection timestamp, cap multiplier/resources |
| missions | Completion/reward arrays, coin grant | Eligibility/progress, real skip cost, prevent duplicate reward |
| push/pop/store/gifts | Basic list operations | Atomic source/target checks, capacity, preserve instance attributes; final gift crash |
| level/score | Accepts client XP/level | Derive from authoritative earned XP; fix max-level lookup returning zero |
| expand/exchange | Resource mutation | Reject insufficient/invalid payment; validate map/land prerequisites |
| dragon/monster/rider | Counters/timestamps | Server timing and cost validation, one-time rewards; MonsterNumber capitalization |
| win bonus/offers/admin animal | Client-driven grants | Server reward catalogue/claim identity; privilege gating |
| graveyard | Potion purchase arithmetic | Death record handler absent; resurrection unbound map and wrong id; entitlement validation |
| quest start/end | Static map loader; end grants coins/XP/unlock | Start is log-only; arbitrary loss/replay rewards; unused units/rank/times/item rewards |
| PvP end | New persisted history, attacker coins/XP | Authenticate, valid start/victim, result validation, deduplicate, transactional defender effects |
| upgrade / magic / attack start / many events | Constants only | Recover protocol, implement or explicitly reject |

## Complete declaration-by-declaration matrix

Working column assesses backend coverage, not browser verification. All implemented state-changing branches require validation review.

| Command (constant / wire) | Original | Updated | Working | Required fix |
| --- | --- | --- | --- | --- |
| CMD_PLACE_GIFT / place_gift | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_PLACE_STORED_ITEM / place_stored_item | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PLACE_IPHONE / place_iphone | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_MOVE / move | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_EXPAND / expand | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_STORE_ITEM / store_item | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_STORE_ADD_ITEMS / store_add_items | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_COMPLETE_TUTORIAL / complete_tutorial | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_COMPLETE_MISSION / complete_mission | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RESET_COMPLETED_MISSIONS / reset_completed_missions | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_STORE_ITEM_FROMBUG / store_item_frombug | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_COLLECT / collect_new | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_PERFORM_CITY_QUEST / perform_city_quest | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ORIENT / orient | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_UPGRADE / upgrade | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_WIN_BONUS / win_bonus | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_HIRE_WORKER / hire_worker | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_START_CAMPAIGN / start_campaign | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PAY_WONDER / pay_wonder | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_WIN_TROPHY / win_trophy | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_KILL / kill | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SELL / sell | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SELL_GIFT / sell_gift | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SELL_IPHONE_ITEM / sell_iphone_item | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SELL_STORED / sell_stored_item | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_DEFAULT_TOWN / set_default_town | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_EXPLORE / explore | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY / buy | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_BUY_STORED_ITEM_CASH / buy_stored_item_cash | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_UNIT_WITH_CASH / buy_cash | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_WONDER_FRIENDS / buy_wonder_friends | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_OFFER / buy_offer | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_MAP / buy_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_NAME_MAP / name_map | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SET_DEFAULT_MAP / set_default_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET / reset | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_VARIABLES / set_variables | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_FAST_FORWARD / fast_forward | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TIME_MACHINE_FF / time_ff | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_POP_UNIT / pop_unit | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_PUSH_UNIT / push_unit | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SET_RESOURCES_TRADED / set_resources_traded | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TRADE_RESOURCE / trade_resource_b | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SAVE_MAP / save_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_LOAD_MAP / load_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_COLLECT_TREASURE / collect_treasure | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_REWARD_MISSION / reward_mission | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_GAME_STATUS / game_status | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_ATTACK_PLAYER / attack_player | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SPY / spy_player | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_START_QUEST / start_quest | Branch | Branch | partial/log-only | validate authority, state, cost, replay; test round trip |
| CMD_END_QUEST / end_quest | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_PUT_GRAVEYARD / put_graveyard | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_END_ATTACK / end_attack | None | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_END_SURVIVAL / end_survival | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CLEAN_ATTACKS / clean_attacks | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_ATTACKS / buy_attacks | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_ATTACKS_PACK / buy_attacks_pack | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_SPYINGS / buy_spyings | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_SPYINGS_PACK / buy_spyings_pack | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_EXCHANGE_CASH / exchange_cash_new | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SET_RESOURCE_ALLIES / set_resource_allies | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_SKIN / set_skin | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_UNLOCK_SKIN / unlock_skin | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_OFFER_PACK / buy_offer_pack | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CLEAR_TILES_AREA / clear_tiles_area | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_MANA / buy_mana_new | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_MAGIC / buy_magic | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_USE_MAGIC / use_magic | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CLEAR_DRAGON_HIRES / finish_dragon_help | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_NEXT_DRAGON / next_dragon | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_NEXT_MONSTER / next_monster | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_NEXT_DRAGON_STEP / next_step | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_NEXT_MONSTER_STEP / next_monster_step | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_DRAGON_BUY_STEP_CASH / buy_step_cash | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_MONSTER_BUY_STEP_CASH / buy_monster_step_cash | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RESET_DRAGON / reset_dragon | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET_MONSTER / reset_monster | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_HACKS_COUNT / system_set_count_hack | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ACTIVATE_DRAGON / activate_dragon | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_DESACTIVATE_DRAGON / desactivate_dragon | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_ACTIVATE_MONSTER / activate_monster | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_DESACTIVATE_MONSTER / desactivate_monster | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SELECT_RIDER / rider_select | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_NEXT_RIDER_STEP / rider_next_step | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RIDER_BUY_STEP_CASH / rider_buy_step_cash | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RESET_RIDER / rider_reset | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_GOLD_STATUE_CONVERSION / gold_statue_conversion | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_REPORT_BUG / report_bug | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_FINISH_COLLECTION / finish_collection | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ADD_COLLECTABLE / add_collectable | Branch | Branch | partial/log-only | validate authority, state, cost, replay; test round trip |
| CMD_SET_STRATEGY / set_strategy | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_ASSIST_NEIGHBOUR / assist_neighbor | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ASSIST_NEIGHBOUR_NEW / assist_neighbor_new | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CLEAN_RECEIVED_ASSISTS / clean_received_assists | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_SI_HELP / buy_si_help | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_FINISH_SI / finish_si | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PING / ping | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_POP_SELL / pop_sell | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ALLY_ASSIST / ally_assist | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESURRECT_HERO / resurrect_hero | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_UNLOCK_BUILDING / unlock_building | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ACCEPT_COLLECT_HELP / accept_collect_help | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_INCREASE_POPULATION / increase_population | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ASSIST_SEND_FEED / assist_send_feed | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ASSIST_RECEIVE / assist_receive | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ACTIVATE / activate | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_SUPER_OFFER_PACK / buy_super_offer_pack | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_SET_HELP_MAP / set_help_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_QUEST_VAR / set_quest_var | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RT_LEVEL_UP / rt_level_up | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RT_PUBLISH_SCORE / rt_publish_score | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_RT_PUBLISH_ACHIEVEMENT_UNIT / rt_publish_achievement_unit | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ADMIN_ADD_ANIMAL / admin_add_animal | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |
| CMD_APPLY_REWARDS_RANKING / apply_rewards_ranking | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET_ISLAND_CHANGE / reset_world_change | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_MODIFY_POSITION_UNIVERSE / modify_position_univers | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET_POSITION_UNIVERSE / reset_position_univers | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_UNIT_COLLECTION_COMPLETED / unit_collections_completed | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_UNIT_COLLECTION_REMOVE / remove_unit_collection | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SURVIVAL_END / end_survival | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SURVIVAL_BUY_MAP / buy_survival_map | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SURVIVAL_BUY_LIFE / add_survival_vida_extra | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SURVIVAL_START / start_survival | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ADD_UNIT_WAREHOUSE / add_unit_warehouse | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PLACE_WAREHOUSED_ITEM / place_warehoused_item | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_WAREHOUSE_CAPACITY / buy_warehouse_capacity | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BUY_WAREHOUSE_CAPACITY_NEW / buy_warehouse_capacity_single | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET_WAREHOUSE / reset_warehouse | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PVP_BUY_TERRITORY / buy_pvp_territory | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_PVP_BUY_ISLAND / buy_pvp_island | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_ADD_ITEMS_TO_STORE / add_items_store | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_FAKE_NEIGHBOURS / set_fake_neighbors | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_ATTACK_TEAM / set_attack_team | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TOURNAMENT_WIN_REWARD / win_reward_tournament | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TOURNAMENT_SUBSTRACT_RESOURCES / tournament_substract_resources | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TOURNAMENT_REFUND_RESOURCES / tournament_refund_resources | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_COLLECT_MONDAY_BONUS / weekly_reward | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_COLLECT_COMEBACK_BONUS / comeback_reward | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TIME_MACHINE_USE / time_ff | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_TIME_MACHINE_BUY / buy_time_packet | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_IPHONE_BOX_POPUP_SHOWED / set_iphone_box_popup_showed | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_RESET_HEAVY_SIEGE / reset_heavy_siege | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_START_HEAVY_SIEGE / start_heavy_siege | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_DARTS_RESET / darts_reset | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_DARTS_NEW_FREE / darts_new_free | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_DARTS_SHOOT_BALLOON / darts_shoot_balloon | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BAHAMUT_SUPREME_INVOCATION_TEMPLE_ADD_UNIT / add_unit_temple | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BAHAMUT_SUPREME_INVOCATION_TEMPLE_NEXT_STEP / next_temple_step | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BAHAMUT_SUPREME_INVOCATION_TEMPLE_RESET / reset_temple | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_BAHAMUT_SUPREME_INVOCATION_TEMPLE_BUY_TIME / buy_temple_step_cash | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_SET_INFO_SHOWED / set_info_showed | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CLEAR_MSG / clear_message | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_KOMPU_HURRY_UP / kompu_hurry_up | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_CROSS_PROMOTION_FINISHED / cross_promotion_finished | None | None | unhandled; acknowledged success | recover protocol and implement or return explicit unsupported |
| CMD_GRAVEYARD_BUY_POTIONS / graveyard_buy_potions | Branch | Branch | partial/unvalidated | validate authority, state, cost, replay; test round trip |

## Continuation findings — 26 September 2026

The table above is the historical comparison, not a current support matrix. Unknown/unimplemented commands now fail explicitly; requests use authenticated ownership and transactional save staging. Resurrection, quest start, collectables and PvP result submission are deliberately unavailable.

**New containment gap, fixed:** `CMD_START_QUEST` had been disabled but `CMD_END_QUEST` still awarded client-supplied gold/XP and advanced quest unlocks without a persisted start. Removed that result handler's reward arithmetic and return unsupported before any effect. A valid-shaped forged result, retried twice after an earlier map rename in the same batch, must return 422 and preserve memory and disk. Quest gameplay remains unavailable pending a verified lifecycle.

**Source-confirmed detail for remaining building work:** `CMD_PUSH_UNIT` appends an ID at destination coordinates before proving a source unit exists, and removes a source even when no destination matched. `CMD_POP_UNIT` can spawn a unit when no building was found or when the matched record has no contained-unit field; spawned attributes are reset. Require both endpoints, compatible building type/capacity and preserved unit records, not merely a list-shaped save. These are refinements of the existing transfer risk, not a claim of a new completed runtime comparison.

**Source-confirmed detail for dragon/monster/rider work:** all three buy-step handlers subtract a client-supplied price; negative values can increase cash. Dragon/monster activation sets the active flag even for an unrecognized currency, bypassing both debit branches. Post-batch schema validation accepts the resulting numeric state. Validate server-owned price/currency, owned nest, progression bounds and time before mutation. Previously recorded MonsterNumber inconsistency and missing entitlement checks remain open.

Mission replay, production/collection authority, upgrades, training queues, Soul Mixer, cemetery and magic gaps retain their earlier findings; no duplicate comparison was performed.
