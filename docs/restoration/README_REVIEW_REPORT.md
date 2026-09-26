# README review report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

## Completed Work

- Flask application and request routes; config patch/mod loading; UUID village creation, JSON persistence, static neighbours and real loaded-save enumeration are present. Most predate this development tree.
- Ruffle integration already existed upstream. The update specifically uses the current browser origin for the loader, game SWF and API URLs.
- Listen address changed from loopback to all interfaces. This enables a LAN bind; actual cross-device connectivity remains untested here.
- Account login/register UI, password hashing, parameterized SQLite account functions, account-to-save identifier assignment and fixed-client redirect are implemented.
- PvP history insertion/retrieval, seen flags, API routes and an attack popup are implemented. Local fixture tests verify history rows and mark-seen operations.

## Incomplete Work

- Fresh database account bootstrap fails: users table missing. Accounts and account-linked saves are partial, not merely future plans and not finished.
- Browser play is blocked by the missing assets directory in this supplied updated folder. Cross-browser compatibility was not retested.
- PvP is a submitted result log with attacker rewards, not validated combat or defender persistence.
- Real-save neighbour enumeration exists in unchanged sessions.py. Friends relationships, privacy and authenticated visit permissions do not.
- Generic placement/movement, resource arithmetic and some missions work only under trusting client assumptions. Timers, affordability, upgrades, storage integrity and reward replay protection remain unfinished.
- Soul Mixer, magic and many event commands have no backend implementation; resurrection crashes.

## Missing Work

- Fresh-install database migration and account recovery/import path for existing saves.
- Actual logout, application secret initialized for WSGI imports, ownership enforcement on every dynamic game route.
- Atomic save writes, backups/restore, strict schemas, versionless and future-version policies, failed-batch rollback, per-player concurrency controls.
- Asset installation/manifest instructions with exact expected directory and required client/loader versions.
- Separate client compatibility matrix from backend feature status; record browser/Ruffle/SWF versions and test dates.
- Endpoint errors for unsupported commands, bounded request schemas and authoritative economy.
- Safe popup rendering; per-battle notification acknowledgement; regression tests for clean and upgraded databases.
- Development release identifier separate from the legacy save-schema version; pinned reproducible dependency/build inputs.

## Incorrect Information

| README claim | Audit correction |
| --- | --- |
| Accounts, login, SQLite and account-linked saves planned | Code already added, but fresh installs fail and game ownership is unenforced. Mark partial. |
| Real players/neighbours entirely future | Existing sessions.py already lists and loads other local saves. Distinguish this from authenticated multiplayer and friends. |
| PvP persistence only future | Battle logging and attacker reward persistence added; defender effects and authoritative validation absent. |
| Game playable locally / villages and quests working | Supplied updated tree lacks assets; quest start is log-only and quest completion trusts arbitrary rewards. Qualify the claim. |
| Dynamic server address support | Correct for Ruffle; legacy play.html still receives a hardcoded LAN address. |
| Modern browser support marked working | Template support exists, but this audit does not certify Chrome/Edge/Firefox gameplay. |
| Opening ruffle.html is sufficient | Requires session; ordinary fresh account path currently fails. |

`LINUX.md` and `FLASH.md` still describe legacy Flash installation; retain as historical alternatives and add Ruffle-specific setup instructions. `RELEASES.md` records upstream versions only; add development release notes when implementation resumes. Build scripts still use old release names; launcher_build.bat names 0.03a while current code reports 0.04a. No README or application document was edited in this audit.

## Reconciliation — 26 September 2026

Updated the existing README to remove obsolete claims that backups are a stub, failed batches mutate live memory, missing-version saves crash, final gift placement crashes and unknown commands report success. Documented contained systems separately from functional restoration. Expanded remaining tasks with quest start/result atomicity, nest currency/price validation and paired storage endpoints. README now links this canonical roadmap. Historical audit counts and source comparison were not regenerated.
