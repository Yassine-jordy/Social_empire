# Asset and configuration report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

Original game archive: 4479 files, 1,305,608,700 bytes. Updated `Social_empire/assets/` does not exist. This is consistent with README/.gitignore policy but is a runtime prerequisite, not restored gameplay. Both SELoader.swf and SocialEmpires0926bsec.swf returned HTTP 200 after **test-only** redirection to the original archive; no asset files were copied into the application.

Configuration, all 11 patches, villages and static stub files available in both release and current tree are unchanged. Effective runtime config: 1781 items, 1010 building/scenery records, 771 units, 230 missions, 100 levels. Active base is game_config_20120826.json. The 20120723 and 4399 snapshots are not selected by client choice. mods.txt has no enabled mod.

## References and data integrity

Direct path checks use `buildingsprites/<img_name>.swf` and `buildingthumbs/<img_name>.jpg`, and flag 235 missing original references: 96 sprites and 139 JPG thumbnails. For type=b records, 68 sprites and 110 thumbnails are absent. This is a naming/reference check; aliases, generated/composite assets or client-version differences may explain individual cases. It does not certify or condemn rendering for every record.

[ASSET_REFERENCES.csv](ASSET_REFERENCES.csv) contains every item reference and both-folder presence. Empty assets: bundle/assets/buildingsprites/1410_bahamut_heart.swf, bundle/assets/buildingthumbs/2147_whirlwind_minion.jpg. These require replacement or evidence of safe fallback.

17 sprite files are not directly named by the effective items' img_name fields. They are **candidates**, not safe deletion targets; SWF internals may load them dynamically.

## Configuration risks

- Patch order uses unsorted os.listdir; explicit ordering is needed for reproducible overlapping patches.
- Patches/mods mutate one shared config object; duplicate item cleanup keeps later entries. Runtime loads successfully, but repeated patch invocation is not established safe.
- subcat_functional index maps one value to one record despite repeated categories, including Soul Mixer and Forge Island 139; callers may get the wrong member.
- get_level_from_xp returns 0 above the final threshold; clamp/define max-level semantics.
- Config assumes valid cost/reward fields and valid IDs. Missing IDs can become TypeError/KeyError in handlers rather than client errors.
- `get_neighbor_info` uses supplied map index and returns privateState; missing/invalid index can crash.
- Static quests include 35 maps; survival state references 100000037, whose file is absent (404 confirmed). Verify selected-client use before inventing that map.
- Known SWF aliases for projectiles/magicParticles/dynamic exist in server.py. General cached-download serving is broken: literal '{BASE_DIR}' string produces 404; constrain cache paths and handle network errors before enabling fallback.
- Ruffle JS is fetched from an unpinned external unpkg URL. Availability and compatibility are not reproducible; no remote Ruffle version was tested in this audit.
- Hardcoded profile/x.jpg in Ruffle friendsInfo is missing. Real-save friend enumeration is passed to legacy play.html, not the Ruffle template's placeholder friendsInfo.

## Configured target IDs absent from effective item set

No absent nonzero direct trains/upgrades_to targets detected.

## Unreferenced sprite candidates

- bundle/assets/buildingsprites/magic_black_hole.swf
- bundle/assets/buildingsprites/magic_cast.swf
- bundle/assets/buildingsprites/magic_cast_marquee.swf
- bundle/assets/buildingsprites/magic_crack.swf
- bundle/assets/buildingsprites/magic_dragon.swf
- bundle/assets/buildingsprites/magic_enlarge.swf
- bundle/assets/buildingsprites/magic_fire.swf
- bundle/assets/buildingsprites/magic_frozen.swf
- bundle/assets/buildingsprites/magic_full_limit.swf
- bundle/assets/buildingsprites/magic_golem.swf
- bundle/assets/buildingsprites/magic_heal.swf
- bundle/assets/buildingsprites/magic_poison.swf
- bundle/assets/buildingsprites/magic_range_increaser.swf
- bundle/assets/buildingsprites/magic_shield.swf
- bundle/assets/buildingsprites/magic_speed_increaser.swf
- bundle/assets/buildingsprites/magic_stone.swf
- bundle/assets/buildingsprites/magic_yeti.swf

## Build and tool status

requirements.txt declares flask and jsonpatch without versions. Both old build scripts are unchanged, assume their directory layout and require PyInstaller separately. They cannot include the missing assets as supplied; builds were not run. `config/patch.py` is an offline helper requiring patched_config.json. `tools/make_se_unit_patch.py` is unchanged development tooling, not runtime restoration. Legacy Flash installers were inventoried and not executed. No unused asset should be removed during restoration.
