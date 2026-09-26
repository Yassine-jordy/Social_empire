# Next restoration roadmap

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

Continue from social-empire-update/Social_empire. Preserve the original assets/config patches, same-origin Ruffle loader, password hashing/parameterized SQL, battle history tables/APIs, and compatible JSON saves. Avoid a rewrite.

## P0 — Critical problems, in dependency order

| Order | Work | Acceptance gate |
| --- | --- | --- |
| 1 | Reproducible launch: configure assets path to existing archive; declare supported Python/dependencies; resolve paths independently of CWD | Clean copied install serves login, config, loader and selected SWF without CDN fallback; launch from documented directory and WSGI import tested |
| 2 | Create/version users schema; account/save link and legacy import; secret initialization; real logout | Empty DB registration/login works; duplicate username and failed-save rollback tested; old save can be linked without changing its identity |
| 3 | Bind all game reads/writes to authenticated account; constrain guest/new flow; reject malformed/unsupported requests | Anonymous and cross-player requests denied; unknown commands fail explicitly; no state changes on rejection |
| 4 | Durable save boundary: schema validation, versionless/future policy, atomic writes, backup/restore, serialization | Crash/interruption leaves recoverable save; failed batch leaves no partial changes; current/legacy fixtures reload |
| 5 | Repair resurrection and final-gift crashes while preserving item state | Valid resurrection consumes correct entitlement once; last gift placement persists and reloads; invalid actions mutate nothing |
| 6 | Close reward/cost exploits and PvP replay; safely render notification usernames | Insufficient balance/nonexistent item/early collection/replayed reward rejected; duplicate battle has no second effect |

No public deployment before these gates pass. P0 containment may explicitly disable unfinished commands rather than invent their mechanics.

## P1 — Core gameplay

1. Capture client requests for buy, move, sell, collect, upgrade, training and storage using the selected baseline SWF. Keep protocol fixtures with original save deltas.
2. Implement server-owned affordability, coordinates, collision/ownership, building limits, resource caps and timers. Use actual config fields and observed client behavior; do not assume all type=b records produce resources.
3. Implement upgrades with valid source/target and state preservation. Gate house/Town Hall/population progression on repeatable client and restart tests.
4. Complete barracks/training availability, capacity, queue/timers and inventory transfers; prevent unit loss/duplication; preserve unit attributes.
5. Separate mission eligibility/progress/completion from reward claims. Add once-only rewards and real skip costs.
6. Complete quest start/end state, win/loss/abandon paths, unit results, timings/ranks and configured rewards; resolve quest-map gaps against actual selected client requests.
7. Validate all core building families in BUILDING_AUDIT.csv, then missing asset aliases and UI references. Acceptance is play→save→restart→continue, not HTTP 200 alone.

## P2 — Special systems

1. Cemetery/graveyard death registration and resurrection eligibility/payment/state removal, guided by client traces.
2. Soul Mixer: recover ActionScript request names, recipe sources, inputs, output, timing, cancellation/collection and persistent fields. **Do not implement guessed recipes.** Asset recovery is mostly a path/setup task; backend protocol is the principal gap.
3. Dragon/monster/rider progression: enforce configured costs and times, eligibility and one-time grants; fix MonsterNumber/monsterNumber inconsistency.
4. Magic/mana, boss encounters, survival, collections, forge and event buildings: recover and implement one protocol family at a time. Explicitly label unsupported client-version features.
5. Test each supported system through restart and failure/replay cases; leave unexplained mechanics marked unverified.

## P3 — Online features

1. Durable player identity, account recovery/admin roles, session controls and transactional persistence design; decide whether JSON stays authoritative or migrates with compatibility adapters.
2. Safe public player view, real friendships/visits and discovery; remove privateState leakage.
3. Ranking derived from validated state, then clan membership/roles.
4. PvP attack-start entitlement and snapshot, validated result semantics, cooldowns, transactional attacker/defender effects, idempotent battle ID, history and per-battle notifications.
5. Concurrency/load tests, abuse controls, deployment configuration, monitoring and backup restoration drill; stage LAN/VPN before wider availability.

## Updated task ledger

- [x] Inventory supplied files and compare source/config/templates.
- [x] Verify current runtime defects in disposable state.
- [x] Preserve and identify existing successful work.
- [x] Produce all ten reports plus complete command/building inventories.
- [ ] All P0 acceptance gates.
- [ ] Core building/economy/unit/mission/quest client round trips.
- [ ] Special-system protocol recovery and restoration.
- [ ] Authenticated, transactional multiplayer.
- [ ] Browser/Ruffle/SWF compatibility matrix and end-to-end playthrough.

No completion date is justified before protocol recovery. Scope milestone one as a reproducible, durable single-player game with enforced account ownership; treat full original-game feature parity as unverified until each special protocol is recovered.

## Continuation checkpoint — 26 September 2026

The preceding ledger describes the original audit. The last session had already entered implementation; its unfinished report reconciliation is now complete. Preserve those source changes. This continuation adds only the narrow quest-result containment fix, not a batch of gameplay implementations.

- [x] P0 foundations: configurable absolute paths, persistent secret, versioned account schema, legacy import, logout and authenticated ownership checks; isolated bootstrap/restart tests exist.
- [x] P0 save boundary: staged batch copy, validation before persistence, atomic replacement, publication after success and process-local serialization. Versionless/supported migrations and rejection of unsupported future saves are covered; pre-migration bytes are backed up.
- [x] Final gift placement handles an empty resulting inventory; invalid/replayed gift operations are rejected.
- [x] Unknown commands and unfinished resurrection, quest starts, collectables and PvP result submission return explicit unsupported responses. Quest completion now also rejects requests, closing the asymmetric start/end guard. These systems are contained, not restored.
- [ ] P0 recovery: verified backup restoration, routine backup retention, abrupt account/JSON interruption recovery and multi-process coherence. A process-local lock is not multi-worker safety; migration backups are not a full recovery service.
- [ ] **Next unfinished implementation task:** authoritative collection eligibility: prove an owned producer instance, validate town/coordinates/configured output, enforce its timer and update its timestamp atomically. Reject forged multiplier/cash fields and repeated early requests. Obtain the selected client's argument trace before changing uncertain protocol semantics.
- [ ] Other P0 economy: affordability and ownership for buy/sell, once-only mission claims, and transfer invariants before enabling public play.
- [ ] Special-building follow-up: reject negative/client-chosen dragon/monster/rider prices and unsupported activation currencies; enforce nest ownership, bounds, timing and entitlement. Storage must find both source and destination before mutation, retain full unit attributes and enforce configured capacity/type compatibility.
- [ ] Restore quest start/result together with a persisted attempt identity, eligibility, server-derived rewards and once-only completion. Never re-enable the removed result arithmetic in isolation.

Soul Mixer protocol/recipes, cemetery death records, magic/mana, upgrades, training queues and production/collection lifecycle remain unresolved as recorded previously. No new client trace, asset comparison or browser playthrough was performed in this continuation.
