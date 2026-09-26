# Runtime test report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.

Audit date: 25 September 2026. Tests ran against the unchanged current Python modules with disposable saves, config copies and SQLite database under `AUDIT/runtime`. No supplied save or application file was modified. `supplement_results.json` records matching before/after hashes for all supplied files.

## Environment and method

Python 3.12.14; isolated Flask 3.1.3, Werkzeug 3.1.8, jsonpatch 1.33 and their dependencies. These satisfy the unpinned requirements but are not necessarily the developer's previous environment. Exact installation output was recorded during the audit. The system `python` command was unavailable; the bundled Python runtime was used.

The app imported successfully and registered 23 routes. Flask's test client exercised routes; direct dispatcher calls exercised state transitions. A separate loopback-only WSGI server served a real HTTP login-page request successfully. The production `0.0.0.0:5050` listener was not launched or exposed. Tests set an in-memory audit secret because importing server.py leaves app.secret_key unset; this does not fix the application. Running server.py directly instead uses the hardcoded SECRET_KEY.

Fresh-database failures were measured first. Only afterwards, a manually created users table in the disposable database allowed diagnostic positive account tests. This fixture must not be confused with working application schema initialization. Original asset paths were injected into the test module only to check local SWF serving. The application still has no assets directory.

Evidence: [audit.py](audit.py), [runtime_results.json](runtime_results.json), [audit_run.log](audit_run.log), [supplement.py](supplement.py), [supplement_results.json](supplement_results.json), [final_checks.py](final_checks.py), [final_results.json](final_results.json). Raw logs retain tracebacks and exact command arguments. Use a fresh disposable runtime directory for a rerun: the retained directory now contains the diagnostic users fixture and test data.

## Server, player and account tests

| Feature | Test | Result | Error / limitation | Required fix |
| --- | --- | --- | --- | --- |
| Startup | Import current server with installed dependencies | Working: 23 routes | WSGI import has no secret | Initialize secret independently of __main__ |
| HTTP serving | Ephemeral loopback WSGI listener, GET / | 200 | LAN/browser not tested | Add clean-install and LAN acceptance tests |
| Configuration | Import patches; POST get_game_config | Working; 200, 1,781 effective items | Unsorted patch order | Specify deterministic order |
| Login page | GET / | 200 | Page success is not login success | None for page rendering |
| Registration | Fresh DB, POST username/password | Broken; 500 | sqlite3.OperationalError: no such table: users | Versioned users schema migration |
| Login | Fresh DB, POST credentials | Broken; 500 | Same missing table | Same migration |
| Account functions | Manually supplied users fixture, register/login | Both redirect 302; password verification accepts correct and rejects wrong password | Fixture schema only | Ship correct schema and transactional creation |
| Logout | Follow / link with active session, then GET ruffle.html | Defect; still 200 | Session retained | Explicit logout clears account and game session |
| Guest creation | Anonymous GET /new.html | 302 after creating a save/session | Bypasses account flow | Define and enforce guest policy |
| New player | sessions.new_village | Working; UUID and save file | Does not validate full gameplay | Keep and integrate atomic account linking |
| Load/save/reload | Save snapshot, reload all villages, compare | Working; equal | Single-process happy path only | Durability/concurrency tests after persistence changes |
| Old supplied save | Parse, validate, migrate in memory | Accepted 0.04a; no migration | Did not play or link it to account | Explicit legacy import/ownership workflow |
| Read ownership | Anonymous get_player_info with invalid user_key | Defect; 200 returns player state | No authentication/ownership check | Derive player identity from session |
| Write ownership | Anonymous name_map with invalid key | Defect; 200 success; map name changed | Same | Enforce authority before dispatch |
| Ruffle HTML | Session fixture, GET ruffle.html | 200 | No browser/SWF gameplay certification | Complete asset setup and client verification |
| Required assets | Inspect current path | Broken prerequisite; directory absent | Client loader cannot be served locally as supplied | Configure/copy known archive through documented setup |
| Original asset serving | Inject archive path; GET loader and selected game SWF | Both 200 | Test-only injection | Preserve serving path support |
| Download cache | Create disposable cached asset, request it | Broken; 404 | Literal {BASE_DIR} serving path | Use resolved interpolated directory |

The initial binary-asset probe tried to decode SWF bytes as UTF-8 and raised UnicodeDecodeError in the **test helper**, not the server. The corrected supplemental probes check status without decoding and both pass.

## Economy and buildings

| Feature | Test | Result | Error / limitation | Required fix |
| --- | --- | --- | --- | --- |
| Placement | Buy Soul Mixer (cost 2,000) with 250 gold, level 1 | Item added, coins 250→0, XP 4→204 | Unaffordable and below minimum level accepted | Check funds, level, limits and placement before mutation |
| Move/sell | Buy item, move 10,10→12,12, sell | Array edits succeed; item removed | Happy path only; invalid purchase still allowed | Validated instance lifecycle |
| Sell absent item | Sell Soul Mixer at nonexistent coordinates | Coins 250→350 | Paid without removing item | Require matching owned instance |
| Gold collection | Collect configured gold building twice at nonexistent 999,999 | Coins 250→650 | No owned building or timer required | Validate instance and elapsed time |
| Food collection | Same for food | Food 700→1,200 | Same | Same |
| Wood collection | Same for wood | Wood 850→890 | Same | Same |
| Stone collection | Same for stone | Stone 250→600 | Same | Same |
| Production timers | Immediate repeated collection | Both grant resources | No timestamp update/enforcement in collect branch | Store and enforce server collection time |
| Upgrading | POST upgrade | 200 success | No dispatcher branch; no upgrade applied | Recover arguments and implement validated upgrade |
| Soul Mixer | Generic buy/move/sell | Partial backend placement | No mixing jobs/recipes/collection handler; UI untested | Client protocol recovery before implementation |

## Units, missions, quests and special systems

| Feature | Test | Result | Error / limitation | Required fix |
| --- | --- | --- | --- | --- |
| Unit storage | Push existing unit into existing Town Hall, pop, save/reload | Item count returns to original | Count/round-trip check does not verify all unit attributes | Preserve complete instance metadata; validate capacity |
| Unit creation exploit | Pop from nonexistent container with output coordinates | New unit appears | Source inventory not required | Atomic source validation |
| Training | Review configured trains and handlers | Partial data; no authoritative training queue found | Client lifecycle not executed | Trace actual train requests, enforce building/time/cost/capacity |
| Army management | Review team constants/storage and strategy handler | Strategy assignment and generic containers only | Team commands largely unhandled | Recover and validate team management |
| Resurrection | Call resurrect_hero | Broken; UnboundLocalError | Local map never assigned; branch also uses wrong id | Correct variables and validate dead-unit entitlement/payment |
| Last inventory gift | Place sole remaining gift | Broken; IndexError | Tail cleanup indexes empty list | Guard empty inventory; atomic mutation |
| Mission complete | complete_mission with skip flag | Completion appended | No real progress validation; skip cost zero | Validate eligibility and configured skip cost |
| Mission rewards | Reward same mission twice without completing it | Coins 250→270 | Repeatable unearned rewards | Separate eligible/completed/claimed states |
| Mission start/progress | Handler/config review | No authoritative progress tracker identified | Completion supplied by client | Define progress from validated actions |
| Quest map | Known 100000002 | 200 | Map serving only | Retain loader |
| Missing survival map | 100000037 | 404 | Initial survival state references absent map | Recover actual required map or disable supported-client path explicitly |
| Quest start | start_quest | Only logs; no state change | Fake success | Persist active attempt and eligibility |
| Quest completion | Submit losing/abandoned result twice | Coins 250→496; XP 4→28 | Loss still unlocks progress; accepts arbitrary/replayed rewards | Validate attempt/outcome/rewards and record claim once |
| Dragon/monster/rider | Source review | Counters/timestamps exist | Time/cost not authoritative; capitalization defect | Trace and validate complete progression |
| Magic/events | Source/coverage review | Many commands absent | Not client-playtested | Recover protocol per system |

## PvP and protocol tests

| Feature | Test | Result | Error / limitation | Required fix |
| --- | --- | --- | --- | --- |
| PvP record/reward | Submit same end_attack twice | Two DB rows; coins 250→496, XP 4→28 | Client-specified rewards; replay; no defender mutation | Server attack identity, validated outcomes and atomic two-player changes |
| History | GET history with victim session | 200; records returned | Fixture sessions; no authenticated combat test | Keep query functionality, add valid battle lifecycle |
| Unseen anonymous | GET unseen without session | 401 | Correct narrow guard | Apply equivalent ownership enforcement to game endpoints |
| Unseen with fresh DB battle | GET unseen as victim | 500 | Username lookup requires absent users table | Schema migration |
| Mark seen | POST with victim session | 200; update executes | Bulk update; UI displays only first battle | Acknowledge exactly displayed battle IDs |
| Unknown command | Valid envelope with audit_unknown | 200 success | Unhandled command | Structured unsupported response |
| Malformed command | data=x | 500, IndexError | Envelope indexed without validation | Bounded shape validation and 4xx response |
| Failed batch | Rename map then resurrection failure | Memory name changed; disk retains prior name | No rollback; inconsistent in-memory/disk state | Transactional command boundary |

The first failed-batch probe used zero-reward mission 0 and showed no coin difference; it was inconclusive for monetary rollback. `final_results.json` uses a map-name mutation and directly demonstrates the partial-state defect. No inference of a coin increase is made from the initial probe.

## Migration and persistence tests

| Feature | Test | Result | Error / limitation | Required fix |
| --- | --- | --- | --- | --- |
| Legacy versions | Null, 0.01a, 0.02a, 0.03a fixtures | Become 0.04a | Otherwise current-shaped fixtures | Add authentic historical fixture corpus |
| Current version | 0.04a | No migration | Does not repair missing fields | Separate schema validation from migration |
| Missing version | Remove key | KeyError | Direct indexing before fallback | Safe version lookup |
| Future version | 99.0 | modified=True, version unchanged | Unknown schema would be rewritten | Explicit unsupported-version policy |
| Missing nested field | Current save without gifts | Accepted, not repaired | Validator too shallow | Full shape validation |
| Invalid shape | Empty maps/playerInfo/privateState | Accepted | Missing identity/maps not rejected | Enforce mandatory fields and types |
| Backups | Call backup_session; inspect source | No operation | Stub returns None | Implement tested backup/restore |
| Maximum level | XP=10^12 | Returns level 0 | Fall-through default | Define maximum-level behavior |
| Supplied-file preservation | Rehash every original/current inventoried file | No changed hashes | Audit artifacts excluded by design | None |

No load/concurrency, abrupt-write interruption, full browser playthrough, real LAN peer, compiled build or exhaustive SWF protocol test was performed. These limits are explicit acceptance work in NEXT_RESTORATION_ROADMAP.md, not silently counted as passes.

## Continuation validation — 26 September 2026

Ran `python -m unittest discover -s tests -v` with Python 3.14.0 and the existing isolated dependencies on PYTHONPATH: **25 tests passed in 7.431 seconds**. The existing 24 tests were retained; one regression now rejects a valid-shaped quest completion without a persisted start, checks repeated submissions and verifies earlier commands in the rejected batch do not change memory or disk. Local full output: `social-empire-update/AUDIT/continuation_tests.log`.

Tests use temporary data/assets and SQLite; supplied saves were not loaded for mutation. This verifies the last implementation checkpoint and the small containment change, not original-client protocol behavior. No asset inventory, prior exploit comparison or browser playthrough was repeated.
