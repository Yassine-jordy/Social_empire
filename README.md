# Social Empires — Community Server Project

A development project based on the **Social Empires preservation project by the Social Emperors team**.

The goal of this project is to preserve Social Empires while experimenting with a more modern server architecture, browser compatibility, networking, accounts, persistent player data, multiplayer features, and eventually player-vs-player functionality.

> This is an unofficial preservation and educational project.
> Original Social Empires game assets, artwork, sounds, trademarks, and other game content belong to their respective rights holders.

---

## Current Status

Status reviewed against the code and isolated runtime tests on **26 September 2026**.

This is a partially restored server. Fresh account registration/login, account ownership checks and JSON save/reload across a server restart now work in isolated backend tests. The asset archive is configurable; this workspace points to the preserved original archive. Full gameplay and online multiplayer are not yet complete.

### Implemented — removed from the remaining-work list

- Flask server, configuration loading and existing patches.
- UUID player creation, JSON save/load and basic persistence across reloads.
- Ruffle integration and same-origin loader, SWF and API URLs.
- Server binding to all network interfaces for LAN access.
- Login/register pages, password hashing and parameterized SQLite account functions.
- Versioned SQLite schema initialization, account-to-player linking, login and logout.
- Persistent session secret for direct/WSGI launch, with an environment override.
- Account ownership checks on game/PvP endpoints; private visits to other players are blocked pending a public-state protocol.
- Absolute resource/data paths, configurable asset archive and safe existing-cache serving.
- Atomic JSON save replacement and a local import command for compatible 0.04a UUID saves.
- Regression tests for fresh/legacy databases, authorization, rollback, imports and restart recovery.
- Transactional batches, core save validation, supported/versionless migrations, future-version rejection and pre-migration backups.
- Final inventory gift fix; explicit rejection of unknown and unfinished commands, including both quest start and completion.
- Static neighbours and enumeration/loading of other local player saves.
- PvP battle insertion, sent/received history queries, seen flags and notification UI.
- Generic item placement, movement and resource arithmetic.

These are implemented components, not certification that their complete workflows work. PvP history still does not validate combat or update defenders; generic gameplay commands still trust client input after authentication. Abrupt process failure during account creation can leave an unlinked save; account/file recovery across such failures remains unfinished.

### Confirmed blockers and defects

- Resource collection and mission rewards remain replayable; costs and item ownership need authoritative validation.
- Resurrection, quests, collectables, upgrades and unfinished commands are explicitly unsupported; PvP result submission is paused.
- Save/schema guards protect persistence, but full backup restoration, cross-store crash recovery and multiple-worker safety remain incomplete.
- Special-building progression, transfers, training and production still lack gameplay validation.

Browser playthroughs, cross-device LAN access and full Chrome/Edge/Firefox compatibility were not verified in the latest audit. The remaining work below separates fixes to existing components from features that still need implementation.

---

# Ruffle Support

The original Social Empires client is an Adobe Flash application.

This project can run the Flash client using **Ruffle**, allowing the game to run inside modern web browsers without requiring Adobe Flash Player or a dedicated Flash browser.

Target browsers for compatibility testing include:

- Google Chrome
- Microsoft Edge
- Mozilla Firefox

The web page loads Ruffle from an external, currently unpinned URL. The loader and game SWF must also be available locally; template integration alone does not establish full client compatibility.

---

# Architecture

The current architecture is:

```text
Browser / Ruffle / Social Empires SWF
                  │
                  ▼
              Flask server
                  ├── Account functions → SQLite users table
                  ├── PvP history → SQLite battle tables
                  ├── Game commands → in-memory players → JSON saves
                  └── Configuration, assets and static quest maps
```

Game state is still stored in JSON files. SQLite holds account links and battle history; it does not yet provide transactional gameplay persistence. The next architectural step is a transactional command/save boundary, followed by coordinated multiplayer state changes.

---

# Installation

## Requirements

You need:

- Windows or Linux
- Python 3 and pip (the audit used Python 3.12.14)
- A modern web browser
- Required Social Empires game assets

Run commands from the directory containing `server.py` (`Social_empire/` in the supplied workspace). Install the Python dependencies:

```bash
pip install -r requirements.txt
```

---

# Running the Server

Resource paths resolve from the application directory, independently of the working directory. From the directory containing `server.py`, start it with:

```bash
py server.py
```

or:

```bash
python server.py
```

The default server port is:

```text
5050
```

---

# Playing Locally

Open `http://127.0.0.1:5050/` for the account page. A successful login redirects to `/ruffle.html`; opening that page without a session redirects to login.

Register an account at `/register`, then log in. The database schema and session secret are initialized automatically. Configure the asset archive below before loading the game. The secret is stored in the private database unless `SOCIAL_EMPIRES_SECRET_KEY` overrides it; keep the database private and preserve it with the saves.

---

# LAN Access / Remote Clients

The current server binds to `0.0.0.0:5050`. Another device can address it using the server computer's actual LAN IP, subject to network/firewall configuration. This provides network reachability; full multiplayer is still unfinished.

Game endpoints now enforce account ownership, but economy/combat validation and other P0 work remain. Keep development on a trusted local environment. Cross-device LAN/VPN testing remains on the checklist.

---

# Dynamic Server Address

The Ruffle client uses:

```javascript
window.location.origin
```

instead of hardcoding addresses such as:

```text
127.0.0.1
192.168.x.x
```

This avoids hardcoded hostnames in Ruffle resource URLs for:

- localhost
- LAN
- VPN
- remote server
- future domain name

For example:

```javascript
const base = window.location.origin;
```

The SWF loader, static resources and dynamic API endpoints are then built using the current server origin.

This prevents the Ruffle page from mixing local and LAN origins for those resources. The legacy `/play.html` route now also derives resource URLs from the current request origin.

---

# Game Assets

The complete original game asset collection is very large and is intentionally not tracked in this repository.

Large asset directories should remain excluded through `.gitignore`.

Example:

```gitignore
assets/
default01.static.socialpointgames.com/
```

By default, the source server expects this layout beside server.py:

```text
Social_empire/
├── server.py
├── assets/
│   ├── flash/SELoader.swf
│   ├── flash/SocialEmpires0926bsec.swf
│   ├── buildingsprites/
│   ├── buildingthumbs/
│   └── ...remaining asset directories...
├── config/
├── templates/
└── villages/
```

In the supplied original release, the existing archive is under `social-emperors_0.04a/bundle/assets/`. Configure its location in an ignored `server.local.json` beside `server.py`; use `server.local.example.json` as a starting point:

```json
{
  "assets_dir": "../../social-emperors_0.04a/bundle/assets",
  "data_dir": "."
}
```

This workspace already has that asset setting. Relative paths resolve from the application directory. `SOCIAL_EMPIRES_ASSETS_DIR` and `SOCIAL_EMPIRES_DATA_DIR` override the file. Defaults are bundled/app assets and the directory beside the source or executable, preserving the usual existing save/database locations. Config/templates resolve from the source or packaged bundle directory. The server serves existing cached assets, but no longer downloads missing assets in response to arbitrary requests; missing files return 404.

The audit found 235 missing direct item asset references and two empty asset files in the original archive. Some references may need aliases or client-specific handling; investigate each before replacing or deleting content. Soul Mixer artwork is present in the original archive; its missing backend is a separate issue.

---

# Saves

Player save files should not normally be committed to the public repository.

Example `.gitignore`:

```gitignore
saves/
*.db
*.sqlite
*.sqlite3
.env
```

Account and battle functions already use `social_empires.db`; game state remains in `saves/*.save.json`. Keep both private. Existing original saves are not automatically linked to the new account UI. To import a compatible **0.04a save with a UUID player ID**, stop the server and create a new account from it using:

```bash
python manage.py import-save "path/to/player.save.json" --username restored_player
```

The command prompts for a new password, copies the save, preserves its ID and original file, and refuses an existing username, existing destination/player ID, incomplete save or unsupported version. Restart the server and log in. It does not overwrite an existing account's empire or automatically migrate older/unknown save schemas. Backups and full crash recovery are still required.

---

# Remaining Development Work

Completed foundations are listed under Current Status. The checkboxes below contain only unfinished work. Preserve compatible saves, the existing asset archive and successful restoration code. Recover unknown mechanics from the client/configuration rather than inventing them.

## First milestone — backend checks implemented

Fresh-database registration, login/logout, authenticated state access, a saved map change and login after a separate-process restart are covered by automated tests. Existing account and battle rows survive schema initialization. A compatible legacy save can be copied and linked through the local import command. The original archive is configured for this workspace; full Ruffle gameplay remains to be verified.

Save-safety implementation is verified; the next unfinished task is authoritative resource collection (owned producer, configured output, timer and atomic timestamp update), followed by remaining economy rules. See the [restoration roadmap](docs/restoration/NEXT_RESTORATION_ROADMAP.md#continuation-checkpoint--26-september-2026).

Run isolated tests from this directory after installing requirements:

```bash
python -m unittest discover -s tests -v
```

Tests use disposable data directories, never real player saves. They do not certify all browser gameplay, combat or special systems.

## P0 — Critical fixes

- [ ] Complete per-command argument/state validation; envelope validation and explicit unsupported-command rejection are implemented.
- [ ] Extend core save validation to verified special-system invariants; missing-version handling and unsupported-future-version rejection are implemented.
- [ ] Verify backup restoration and retention; recover abrupt account-database/save-file interruptions. Migration backups, process-local serialization, atomic replacement and failed-batch rollback are implemented; multiple workers remain unsupported.
- [ ] Restore resurrection from verified death records; it is currently rejected without consuming potions. Final-gift placement is fixed.
- [ ] Reject unaffordable purchases, collection/sale of nonexistent items, invalid inventory transfers and repeated reward claims.
- [ ] Implement validated, idempotent PvP with coordinated database/JSON persistence; result submission is currently disabled.
- [ ] Render notification usernames as text and acknowledge only the battles actually displayed.

## P1 — Core gameplay

- [ ] Capture baseline-client command traces and expected save changes for placement, collection, upgrades, training and inventory.
- [ ] Enforce building ownership, placement bounds/collisions, level/quantity limits, costs and resource caps.
- [ ] Implement authoritative production timers and collection timestamp updates for food, gold, wood and stone.
- [ ] Implement configured upgrades for Town Hall, houses, barracks and other eligible buildings; preserve contained units and attributes.
- [ ] Complete training costs, eligibility, queues/timers and capacity; validate both storage endpoints before mutation and preserve unit attributes to prevent loss/duplication.
- [ ] Complete army/team management and population enforcement using observed client behavior.
- [ ] Track mission eligibility/progress, enforce real skip costs and grant each reward once.
- [ ] Restore quest start/result together with persisted attempt identity, once-only server-derived rewards, unit changes, timings and ranks. Both endpoints are currently rejected.
- [ ] Resolve required missing quest maps, including the survival reference to `100000037`.
- [ ] Fix maximum-XP level handling, deterministic patch ordering and ambiguous item lookups by functional category.
- [ ] Resolve missing/empty assets and broken UI references; pass actual public neighbour data to Ruffle.
- [ ] Pin reproducible runtime/Ruffle/build inputs and verify Chrome/Edge/Firefox plus LAN/VPN behavior with recorded versions.
- [ ] Test core gameplay through save, server restart and continued play; update build/release instructions and development version labels.

## P2 — Special systems

- [ ] Complete cemetery death registration, resurrection eligibility/payment and removal of the recovered death record.
- [ ] Finish Soul Mixer production: 437 unique upstream reconstructed ranks/timers, exclusions, globals and input selection are loaded. Two troop slots verified in Ruffle with momo123; validated transfers preserve full unit records. These are upstream restoration values, not original Social Point balance. Server-authoritative preview/premium/queue/collection remains unfinished (premium requests return 422). See the [Soul Mixer findings](docs/restoration/BUILDING_RESTORATION_REPORT.md#soul-mixer--dedicated-analysis).
- [ ] Enforce dragon/monster/rider server-owned prices, supported activation currencies, nest ownership, progression bounds, timing and one-time grants; reject negative prices and fix the `MonsterNumber`/`monsterNumber` inconsistency.
- [ ] Recover and implement magic/mana, bosses, survival, collections, forge and event-building protocols individually.
- [ ] Verify each supported special system through restart, cancellation/failure and replay cases; explicitly label unsupported client-version features.

## P3 — Online features and deployment

- [ ] Add account recovery, administrative roles/tools, session controls and abuse/rate limits.
- [ ] Establish persistence and concurrency guarantees for multiple players/workers before enabling shared-state interactions.
- [ ] Complete safe public player views, friendships, discovery and authenticated visits beyond local-save enumeration.
- [ ] Replace ranking stubs with rankings derived from validated state; implement clans and membership roles.
- [ ] Complete PvP attack-start authorization, battle identity, result validation, cooldowns and atomic attacker/defender effects.
- [ ] Complete per-battle notifications and battle-history behavior; history storage itself already exists.
- [ ] Add production WSGI configuration, HTTPS/domain support, monitoring, restart management and backup restoration drills.
- [ ] Validate staged LAN/VPN and remote deployment after P0 fixes; assess PostgreSQL only if measured persistence/concurrency needs justify it.

The comparison audit covers all supplied files, 1,010 building/scenery records and 156 command declarations. It does not certify every SWF, browser or special-system UI. Detailed reports are stored in the local workspace's sibling `AUDIT/` directory and are not part of this source repository.

---

# Development Philosophy

This project is also intended as a practical learning project.

Areas explored through development include:

- Python
- Flask
- HTTP
- client/server architecture
- networking
- IP addressing
- ports
- LAN communication
- VPN networking
- browser security
- CORS/origins
- databases
- SQLite
- SQL
- authentication
- password hashing
- sessions
- Git
- GitHub
- APIs
- legacy Flash applications
- Ruffle
- reverse engineering
- multiplayer architecture
- server-side state
- concurrency
- deployment

---

# Git

Large game assets, player saves, databases and local configuration should not be committed.

Recommended `.gitignore`:

```gitignore
# Large game assets
assets/
default01.static.socialpointgames.com/

# Player saves
saves/

# Databases
*.db
*.sqlite
*.sqlite3

# Secrets
.env

# Python
__pycache__/
*.pyc
*.pyo

# Virtual environments
venv/
.venv/

# IDE
.vscode/

# OS files
.DS_Store
Thumbs.db
```

Before committing, verify what Git will include:

```bash
git status
```

---

# Original Project

This project is based on the **Social Empires preservation project by the Social Emperors team**.

The upstream project was created to preserve the Flash game and prevent it from being lost to time.

Original project:

```text
https://github.com/AcidCaos/socialemperors
```

Please refer to the upstream project for the original preservation work, releases and contributors.

---

# Credits

Original preservation work:

**The Social Emperors team**

Original game:

**Social Empires**

Ruffle:

**Ruffle project**

This project builds on the work of the preservation community and the original Social Emperors project.

---

# License

The Social Emperors preservation project is distributed under the **GNU General Public License v3 (GPL-3.0)**.

Original notice:

```text
Social Empires preservation project.
Copyright (C) 2022 The Social Emperors team
See the GNU General Public License <https://www.gnu.org/licenses/>.
```

Modifications to GPL-covered source code should continue to comply with the terms of the GPL-3.0 license.

See the included `LICENSE` file for the complete license text.

---

# Disclaimer

This is an unofficial preservation, research, and educational project.

It is not affiliated with or endorsed by the original Social Empires developers, publishers, or rights holders.

The purpose of the project is to study software preservation, legacy Flash applications, networking, server development, databases, and multiplayer architecture.
