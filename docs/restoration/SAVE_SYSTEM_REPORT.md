# Save system report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

## Format and compatibility

`sessions.py:114` deep-copies villages/initial.json, assigns UUID pid and current 0.04a version, initializes time/seed and writes `<USERID>.save.json`. Data comprises playerInfo, maps and privateState. Map items use positional arrays: ID, x, y, orientation, timestamp, level, optional contained units and attributes. Generic purchases create six-field arrays; consumers must handle optional fields consistently.

`sessions.session` reads the global in-memory save dictionary; save_session opens the live file with `w` and dumps JSON. Account records store only userid, while battle records live in SQLite. Game state has not moved into SQLite.

Runtime-confirmed: create, save and reload a fresh village preserves the snapshot. The supplied original save validates as 0.04a without migration; it was inspected in memory only. This does not prove a full playthrough or account ownership mapping. Existing saves have no import/link workflow in the new login UI.

## Migration tests

| Input | Result | Required fix |
| --- | --- | --- |
| version null | Migrates through 0.01a → 0.04a | Keep supported path and test incomplete nested objects. |
| 0.01a / 0.02a / 0.03a fixture | Reaches 0.04a | Tested with otherwise current-shaped fixture, not historical save corpus. |
| 0.04a | No migration | Validate schema even when version already current. |
| No version key | KeyError before fallback | Use safe version detection before direct indexing. |
| 99.0 | Returns modified=True, preserves unknown version | Reject/quarantine future schemas; never silently rewrite them. |
| Current save missing gifts | Accepted; migration skips; field stays absent | Validate/repair required nested fields with explicit rules. |
| Empty maps, empty playerInfo/privateState | is_valid_village returns True | Require map/player identity and all mandatory shape/types. |

`version.py:11` accesses save['version'] before its missing-key check. `sessions.load_saved_villages` catches malformed JSON but not migration errors; a versionless save can abort server startup. Malformed static-neighbour JSON has no protective catch. Duplicate save PIDs silently replace earlier entries. A present but incomplete privateState can survive validation and crash later commands.

## Corruption and consistency risks

- No atomic temp-write/replace or fsync strategy. A crash during truncation/write can destroy the last good save. `backup_session` is an empty stub.
- Global mutable dictionaries have no locks. Login reloads all saves, so concurrent requests can replace objects or discard in-flight mutations. Multiple WSGI workers would have divergent copies.
- Command batches mutate live state before final saving; exceptions do not roll back earlier changes. Resurrection also consumes a potion before crashing when applicable; final gift placement mutates inventory/items before crashing.
- PvP database insert commits before attacker map validation and JSON persistence. A failed command may leave a battle row without its corresponding saved reward. No transaction spans these stores.
- Registration inserts an account before save creation and userid assignment. Failure can leave an orphan account or unlinked save.
- Save filenames derive from save identity and are not constrained to canonical UUIDs when importing. Validate imported PID and resolved storage path.
- Paths resolve against current working directory, so changing launcher/WSGI directory can create a different database or fail to locate config.

## Preservation plan

Keep JSON compatibility initially. Add schema validation, explicit version policy, backups before migration, atomic writes and per-player serialized command processing. Introduce a transaction boundary before implementing two-player effects. Provide an explicit legacy-save import that preserves PID, assigns ownership once, checks duplicates and verifies a restore. Acceptance: interrupted writes leave the prior save usable; failing batches leave no partial state; restart preserves both account links and valid gameplay state.

## Implemented checkpoint — 26 September 2026

The earlier corruption bullets are baseline findings superseded where noted here. `sessions.save_transaction` stages a deep copy, validates and saves it before publishing to the in-memory registry. Failed commands and failed replacement leave the prior memory/disk snapshot intact. `state_lock` serializes this process; it does not synchronize multiple workers. `save_schema.validate_save` checks core structural/numeric fields and item shape, not gameplay affordability, ownership, timers or every special-system field.

`version.py` now handles missing versions and rejects unsupported future versions. Loading isolates invalid files; migrations preserve original bytes via content-addressed backups. Compatible legacy import/account linking and ordinary registration rollback are implemented. `backup_session` is no longer an empty stub. Backups are chiefly pre-migration evidence; routine retention, an exercised restore workflow, cross-store crash recovery and multi-process guarantees remain open.

Gift regression tests cover final-item removal and invalid/replayed requests. Resurrection and PvP result processing are explicitly disabled before mutation, not functionally restored. Quest-result requests are now also disabled, with repeated rejection and earlier-command batch rollback covered by a regression test.
