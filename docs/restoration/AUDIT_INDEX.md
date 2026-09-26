# Social Empires comparison and restoration audit

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

The current development tree adds useful account UI, same-origin Ruffle URLs and PvP history, but is not a complete playable fresh install or an authenticated multiplayer server. Five existing files changed; three functional files are new against the available baseline (database.py, register.html and account.css). Four other presence differences (.gitignore, LICENSE and two installers) are not established as newly authored upstream functionality because the source baseline is sparse. See the file report for provenance limits.

Critical findings: missing users schema; missing updated assets; unauthenticated save reads/writes; repeatable economy/reward exploits; resurrection/final-gift/versionless-save crashes; non-atomic persistence. The only added gameplay branch is end_attack (42→43 of 156 declarations). Soul Mixer artwork exists in the original archive; its mixing protocol and backend remain unrecovered.

## Reports

1. [File comparison](FILE_DIFFERENCE_REPORT.md)
2. [README review](README_REVIEW_REPORT.md)
3. [Runtime tests](RUNTIME_TEST_REPORT.md)
4. [Buildings and Soul Mixer](BUILDING_RESTORATION_REPORT.md)
5. [Command system](COMMAND_SYSTEM_REPORT.md)
6. [Assets and configuration](ASSET_CONFIGURATION_REPORT.md)
7. [Save system](SAVE_SYSTEM_REPORT.md)
8. [Online readiness](ONLINE_MULTIPLAYER_READINESS_REPORT.md)
9. [Next restoration roadmap](NEXT_RESTORATION_ROADMAP.md)
10. [Source review supplement](SOURCE_CODE_REVIEW.md)

## Evidence and limits

Complete file hashes, mapped differences, source diff, all 1010 building/scenery entries and all 156 command declarations are included beside these reports. runtime_results.json and supplement_results.json contain raw test observations; logs preserve tracebacks. audit.py and supplement.py document exact inputs and fixture setup. Dependencies and disposable runtime state are isolated here; do not copy fixture accounts/database into production.

This is a complete supplied-file inventory and backend/config review, with targeted runtime tests. It is **not** an exhaustive Flash decompilation or client playthrough of every building, event, browser or SWF. No client UI, animation or Soul Mixer recipe behavior is certified. No restoration code changes were made; implementation starts only after this audit.

Recommended order: reproducible install → schema/accounts/ownership → durable saves and crash fixes → authoritative core gameplay → evidence-based special systems → transactional online multiplayer.

## Current continuation

Reports are now version-controlled here without duplicate report copies. Local raw evidence remains under the parent workspace AUDIT directory. Follow the latest roadmap checkpoint, command report and save report rather than treating the original analysis-only snapshot as current. The 25 September save-safety log recorded 24 passing tests; this continuation verifies the preserved implementation plus the new quest-result regression. See RUNTIME_TEST_REPORT.md for the new run result.
