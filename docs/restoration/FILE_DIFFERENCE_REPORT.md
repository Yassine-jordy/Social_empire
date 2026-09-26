# File difference report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

## Comparison boundaries

The original folder is a packaged release, not a source checkout. Its `bundle/` maps to `Social_empire/` in the updated tree. Original source comparisons use the available local sparse checkout `C:/Users/belai/AppData/Local/Temp/socialemperors-source-audit-20260924`, whose HEAD is `f642e0bae5a341f48e73b58f2e6d33a8436992c1`. This is a source proxy, not proof of executable reproducibility. The earlier audit is supporting context only; findings here were rechecked against current files and runtime.

The updated HEAD is `b2efd7d`. The original folder also contains a separate `aethermarch/` project and earlier audit documents. These are inventoried but are not treated as Social Empires release functionality. `.git` metadata and bytecode caches are excluded from content inventories.

Inventoried 4670 original-folder files, 101 updated files, and 94 available baseline-source files. Logical mapping: 89 identical, 5 changed, 7 present only in the updated material, and 4,537 baseline entries not supplied in the updated folder. This last count includes 4,479 assets plus packaged dependencies; it is **not** a count of deliberate deletions. Sparse baseline omissions mean LICENSE, .gitignore and the two Flash installers cannot be called newly authored features.

Exact paths, byte sizes and SHA-256 hashes: [FILE_INVENTORY.csv](FILE_INVENTORY.csv). Full mapped comparison: [FILE_COMPARISON.csv](FILE_COMPARISON.csv). Text changes: [SOURCE_DIFF.patch](SOURCE_DIFF.patch).

## Important differences

| File | Original | Updated / change | Purpose | Impact | Status |
| --- | --- | --- | --- | --- | --- |
| server.py | Save selector; loopback bind | Account login/register; all-interface bind; three PvP APIs; hardcoded legacy player address | Accounts, LAN access and battle notifications | Fresh registration fails; gameplay routes still unauthenticated; logout removed | Partial / fresh accounts Broken |
| command.py | 42 dispatcher branches | 43 branches; adds database import and end_attack | Persist submitted PvP history and attacker rewards | Useful history scaffold; repeatable arbitrary rewards and split persistence | Partial |
| database.py | Absent in baseline source | New SQLite functions, hashed passwords, account linking, battle rows and seen flag | Persistence foundation | No users CREATE TABLE; battle table works | Partial / account bootstrap Broken |
| templates/login.html | Village and client version selector | Username/password form and registration link | Account entry | Existing saves cannot be selected/imported through this page; no logout action | Partial |
| templates/register.html; templates/css/account.css | Absent | Registration form and shared account styling | Account UI | Pages render; submit blocked by missing schema | Partial |
| templates/ruffle.html | Ruffle already integrated; fixed local addresses | location.origin loader/static/dynamic URLs; PvP popup | Fix browser origin on LAN; expose attack history | Origin fix implemented; popup uses unsafe innerHTML; shows one battle then marks all seen | Partial |
| README.md | Preservation release instructions | Community roadmap and browser/LAN instructions | Document future service direction | Accounts/SQLite/PvP statements lag code; gameplay working claims too broad | Partial |
| assets/ | 4,479 files / 1,305,608,700 bytes | Entire directory absent | Repository intentionally excludes large assets | Fresh updated checkout cannot load SWFs without restoring asset path | Broken as supplied |
| saves/ | Existing release save | No supplied updated saves | Separate working trees / ignored player data | Need explicit import and account ownership migration | Partial |
| .gitignore; LICENSE; distr/* | Not available in sparse source baseline or release layout | Ignore rules, GPL text, two legacy Flash installers | Repository packaging/documentation | Presence difference, not established new restoration functionality | Working as static files; installers untested |
| engine.py; sessions.py; constants.py; version.py; get_player_info.py; get_game_config.py; quests.py; bundle.py | Baseline implementation | Byte-identical | Preserve preservation server | Successful behavior and known defects retained | Partial |
| config/*; villages/*; stub/*; templates/play.html; build/*; tools/*; mods/*; FLASH.md; LINUX.md; RELEASES.md | Available baseline files | Byte-identical | No restoration changes in these files | Do not credit old patches, neighbours or graveyard handler to this update | Partial; component-specific details in other reports |

## Function-level changes and preserved behavior

`server.login`: replaces save/client selection with password verification, lookup of account userid, reloading all saves, and cookie session assignment. Fixed client is `SocialEmpires0926bsec.swf`. The original GET cleared the session; the new GET does not. Code after the first template return is unreachable.

`server.register`: calls register_user → new_village → set_userid in separate operations. No atomic account/save creation or rollback. `server.play` now passes hardcoded `192.168.8.4`; `templates/play.html` is unchanged. `server.ruffle` is substantially unchanged; URL modernization is in its template.

`server.pvp_history`, `pvp_unseen`, `pvp_mark_seen`: cookie-gated queries and bulk seen update. These endpoints enforce presence of USERID, while the old game routes still trust submitted USERID. `pvp_unseen` additionally queries the missing users table.

`database.init_database`: creates pvp_battles and tries ALTER TABLE for seen_by_victim; catches every OperationalError from ALTER, potentially masking migration failures. `register_user` hashes passwords and uses bound SQL; `check_login` verifies hashes. These work with a manually provisioned fixture schema, not on the shipped fresh database.

`command.do_command / CMD_END_ATTACK`: writes a shared debug JSON before checking attacker mismatch; inserts a battle; then credits attacker coins/XP. Does not validate battle start, enemy existence, server-computed results or replay. The outer command function saves JSON only after the batch completes. Mismatch logs and returns, allowing HTTP success without processing.

No new engine arithmetic, production scheduler, building behavior, migrations, neighbours, constants, missions or configuration patches were found. Full branch inventory and all important inherited defects are documented in the command, runtime and save reports.
