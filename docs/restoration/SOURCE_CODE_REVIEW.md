# Source code review supplement

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.
Function-level changed behavior is in FILE_DIFFERENCE_REPORT.md; command, persistence and security findings are in their dedicated reports. All available Python files were inspected directly or through complete AST/config/dispatcher scans. Markers are clues rather than proof of a defect: exception handling and optional branches may legitimately use pass.

## TODO / pass inventory

| File | Line | Marker |
| --- | --- | --- |
| command.py | 45 | frame = args[3] # TODO ?? |
| command.py | 52 | level = 0 # TODO |
| command.py | 91 | num_units_contained_when_harvested = args[4]#TODO does this affect multiplier? |
| command.py | 117 | pass # TODO : add to graveyard |
| command.py | 138 | cash_to_substract = 0 # TODO |
| command.py | 194 | level = 0 # TODO |
| command.py | 201 | map = save["maps"][0] # TODO : xp must be general, since theres no given town_id |
| command.py | 210 | map = save["maps"][0] # TODO : xp must be general, since theres no given town_id |
| command.py | 271 | orientation = 0#TODO |
| command.py | 443 | # TODO |
| command.py | 471 | pass # TODO |
| command.py | 474 | level = 0 # TODO |
| command.py | 529 | # save["privateState"]["questsRank"] = TODO |
| command.py | 530 | # save["maps"]["questTimes"] [quest_id] = TODO min (... , duration_sec) |
| command.py | 531 | # save["maps"]["lastQuestTimes"] [quest_id] = TODO min (... , duration_sec) |
| command.py | 538 | # TODO |
| database.py | 52 | pass |
| server.py | 412 | # TODO - stub |
| sessions.py | 238 | # TODO |
| sessions.py | 242 | # TODO |
