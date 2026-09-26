# Online multiplayer readiness report

> Continuation checkpoint: 26 September 2026. The original 25 September audit below is historical evidence, not the current implementation status. See [roadmap](NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026) for completed fixes and remaining gates. Existing reports were moved into this repository for version control; raw CSV/JSON/log evidence and disposable dependencies remain in the workspace at `social-empire-update/AUDIT/`. Relative evidence filenames below refer to that directory. No baseline comparisons were rerun.
Audit date: 25 September 2026. Analysis only; application source, supplied configuration/assets, and original saves were not changed. Tests and dependencies are isolated under `AUDIT/`.

Evidence labels: **runtime confirmed** = reproduced in this audit; **source confirmed** = directly visible in code/data; **unverified** = needs client execution, traces, or further testing. Working means the stated narrow operation passes, not that the entire game is complete.

Verdict: **not ready for untrusted network players**. All-interface binding was added without closing existing game-route authorization gaps.

| System | Implemented | Missing / risk | Priority |
| --- | --- | --- | --- |
| Registration | Form, hash helper, account→UUID linking | users schema absent; no atomic creation/import/recovery | P0 |
| Authentication | Password verification; Flask cookie on login | Fixed known secret in __main__; no secret for imported WSGI app; no actual logout; no throttling | P0 |
| Ownership | Account userid field and page session checks | Game endpoints accept submitted USERID and ignore user_key/token/hash; anonymous mutation reproduced | P0 |
| Sessions | Flask signed-cookie support | Account existence/ownership checks missing on game routes; /new.html bypasses account flow | P0 |
| Multiple players | Global save dictionaries and UUID files | No locking, worker coherence or transactional updates | P0/P3 |
| Friends/visits | Static neighbours and other loaded saves | No friendship data/permissions; neighbor response includes privateState | P3 |
| Ranking | Fixed eight-position continent response | Stub, no authoritative scores or ranking | P3 |
| Clans | No implemented clan service found | Recover client protocol and implement membership/roles | P3 |
| Attacks | Battle rows/history, attacker coins/XP, seen flags | No start authorization, replay protection, combat validation or defender changes | P0 validation, P3 complete PvP |
| Administration | Console logging | No roles, moderation/recovery/audit tools | P3 |
| Deployment | Flask dev runner | Managed secrets, production WSGI config, HTTPS, persistent volumes and restore verification | P3 after P0 |

## Confirmed exploit paths

Anonymous requests with a valid disposable player's USERID and invalid user_key read player state and rename the map; both return HTTP 200. No stolen login cookie was needed. The command request's 64-character prefix is sliced but never verified. Client accessToken and sequence fields are read but not enforced. Unknown commands return success.

Collection ignores ownership, coordinates and elapsed time. Selling pays even if no item was removed. Unit pop spawns an item even without a source container. Reward missions and PvP can be replayed. Many costs clamp at zero instead of rejecting insufficient funds. These are authority failures, not simply missing UI checks.

## New risks introduced by the development work

`templates/ruffle.html:335` concatenates attacker_username into innerHTML. Registration does not constrain that value; when the users schema exists, attacker-controlled HTML can reach another player's notification. This is a source-confirmed stored-XSS sink; browser exploit execution was not performed. Render names as text.

The popup displays battles[0] but its acknowledgement updates every unseen row. Other unread battles can disappear without being shown. Fetch only happens on page load, so it is not live notification delivery.

`CMD_END_ATTACK` trusts both victim identity and reward values. Its attacker comparison is against request-supplied USERID, not the authenticated account. It overwrites pvp_last_battle.json before this comparison, allowing unauthenticated debug-file churn. Battle log commits and JSON rewards are non-atomic.

SQL queries use bound parameters and passwords use Werkzeug hash helpers: preserve these good foundations. Do not replace the project wholesale. First enforce identity and authoritative state transitions, then make persistence transactional, then finish social/PvP features.

The asset fallback builds a write path directly from a route path before send_from_directory applies serving safeguards. Constrain resolved paths to the asset cache and bound downloads; traversal was not exercised. Cached downloads currently return 404 because the serving path is the literal string '{BASE_DIR}/download_assets/assets'.
