# Social Empires — Community Server Project

A development project based on the **Social Empires preservation project by the Social Emperors team**.

The goal of this project is to preserve Social Empires while experimenting with a more modern server architecture, browser compatibility, networking, accounts, persistent player data, multiplayer features, and eventually player-vs-player functionality.

> This is an unofficial preservation and educational project.
> Original Social Empires game assets, artwork, sounds, trademarks, and other game content belong to their respective rights holders.

---

## Current Status

The game is currently playable locally through the Python/Flask server.

### Working

- Social Empires game client
- Python/Flask server
- Local player saves
- Ruffle support
- Chrome / Edge / Firefox support
- LAN access
- Dynamic server address detection
- Basic game commands
- Villages and quests
- Game configuration and patches

### Planned

- Remote Internet play
- Player accounts
- Registration and login
- SQLite database
- Account-linked player saves
- Multiple real players
- Real player neighbours
- Improved save management
- Multiplayer features
- Persistent PvP attacks
- Better security
- Server administration tools
- Backups
- Possible PostgreSQL migration
- VPS deployment
- HTTPS/domain support

---

# Ruffle Support

The original Social Empires client is an Adobe Flash application.

This project can run the Flash client using **Ruffle**, allowing the game to run inside modern web browsers without requiring Adobe Flash Player or a dedicated Flash browser.

Supported/tested browsers include:

- Google Chrome
- Microsoft Edge
- Mozilla Firefox

Ruffle is loaded by the web client and executes the original SWF game.

---

# Architecture

The current architecture is approximately:

```text
Modern Browser
      │
      ▼
    Ruffle
      │
      ▼
Social Empires SWF
      │
      ▼
Python / Flask Server
      │
      ├── Game commands
      ├── Player information
      ├── Villages
      ├── Quests
      ├── Configuration
      └── Save data
```

The long-term goal is:

```text
                    Internet
                       │
                       ▼
                 Web / Ruffle
                       │
                       ▼
                Flask Application
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
     Authentication          Game Server
            │                     │
            ▼                     ▼
         Accounts             Commands
            │                     │
            └──────────┬──────────┘
                       ▼
                    Database
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Player Saves        Multiplayer
                                 │
                                 ▼
                                PvP
```

---

# Installation

## Requirements

You need:

- Windows or Linux
- Python 3
- pip
- A modern web browser
- Required Social Empires game assets

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

---

# Running the Server

Start the server with:

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

After starting the server, open:

```text
http://127.0.0.1:5050/ruffle.html
```

in Chrome, Edge, Firefox, or another compatible modern browser.

---

# LAN Multiplayer / Remote Clients

The Flask server can listen on all network interfaces:

```python
host = "0.0.0.0"
```

This allows another device on the local network to connect to the server.

For example, if the server computer has the local IP:

```text
192.168.8.4
```

another computer on the same network can open:

```text
http://192.168.8.4:5050/ruffle.html
```

The actual LAN IP will depend on the network.

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

This allows the same client to work when accessed through:

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

This also prevents problems caused by the browser loading the page from one origin while attempting to fetch Flash resources from another origin.

---

# Game Assets

The complete original game asset collection is very large and is intentionally not tracked in this repository.

Large asset directories should remain excluded through `.gitignore`.

Example:

```gitignore
assets/
default01.static.socialpointgames.com/
```

The required game files must be placed in their expected directories before running the complete game.

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

This becomes especially important once accounts and databases are implemented.

---

# Development Roadmap

## Phase 1 — Browser Modernization

Status: **Working**

Goals:

- Run Social Empires without Adobe Flash Player
- Integrate Ruffle
- Support modern browsers
- Fix browser resource loading
- Avoid cross-origin problems
- Dynamically determine the server URL

---

## Phase 2 — Networking

Goals:

- LAN access
- Multiple computers connecting to one server
- Remote connections
- VPN testing
- Tailscale support
- Prepare server for Internet deployment

Basic LAN access is already working.

A future remote setup could look like:

```text
Player A
   │
   │ Internet / VPN
   ▼
Social Empires Server
   ▲
   │
   │ Internet / VPN
   │
Player B
```

---

## Phase 3 — Player Accounts

The current preservation server primarily works around local save data.

The goal is to introduce proper accounts.

Planned features:

- Register
- Login
- Logout
- Unique username
- Password authentication
- Player ID
- Account creation date
- Session management

Passwords must never be stored as plain text.

A secure password hashing implementation should be used.

---

## Phase 4 — Database

Initial database:

```text
SQLite
```

SQLite is suitable for the first multiplayer implementation because it is:

- simple
- local
- lightweight
- easy to back up
- integrated with Python

Possible future migration:

```text
SQLite
   │
   ▼
PostgreSQL
```

when the server requires more advanced concurrency or larger-scale deployment.

---

## Phase 5 — Account-Linked Saves

Each account should eventually own its own Social Empires save.

Conceptually:

```text
Account
   │
   ├── User ID
   ├── Username
   ├── Password hash
   │
   └── Player Save
          │
          ├── Level
          ├── Gold
          ├── Cash
          ├── Units
          ├── Buildings
          ├── Missions
          └── Progress
```

Logging into an account should automatically load the corresponding empire.

---

## Phase 6 — Real Player Neighbours

The original preservation project contains predefined/static village information.

The goal is to allow real server players to appear as neighbours.

Instead of:

```text
Player
  │
  └── Static NPC village
```

the system should eventually support:

```text
Player A
   │
   └── Neighbour
          │
          ▼
       Player B
          │
          ▼
    Player B's real save
```

This requires resolving player IDs and retrieving the appropriate player save from the server/database.

---

## Phase 7 — Multiplayer

Once accounts and player saves are separated correctly, multiplayer features can be developed.

Potential features:

- player discovery
- neighbours
- visiting other empires
- friend lists
- player information
- synchronized player state
- interactions between players

---

## Phase 8 — PvP Persistence

The original Flash client contains functionality related to attacking other players.

The current server implementation does not yet fully persist PvP attack results.

The goal is to investigate and implement server-side handling for commands related to player attacks.

Potential flow:

```text
Player A attacks Player B
          │
          ▼
     Flash Client
          │
          ▼
      Flask Server
          │
          ▼
   Validate Attack
          │
          ▼
   Process Results
          │
          ├── Player A changes
          │
          └── Player B changes
          │
          ▼
       Database
```

Important areas to investigate include attack-start and attack-end requests sent by the Flash client.

PvP logic should be validated by the server rather than trusting arbitrary client data.

---

## Phase 9 — Security

Before exposing the server publicly, additional security work will be necessary.

This includes:

- secure password hashing
- input validation
- session security
- authorization
- database validation
- rate limiting where appropriate
- protection against malformed game commands
- secret configuration through environment variables
- preventing users from modifying another player's save
- server-side validation of multiplayer actions

---

## Phase 10 — Backups

Player data should be backed up automatically.

Possible strategy:

```text
Database
   │
   ├── Current database
   │
   ├── Daily backup
   │
   └── Older backups
```

Backups become increasingly important once multiple people have persistent empires.

---

## Phase 11 — Deployment

A later version could run on a dedicated server or VPS.

Example:

```text
Players
   │
   ▼
Internet
   │
   ▼
HTTPS / Domain
   │
   ▼
Reverse Proxy
   │
   ▼
Flask Application
   │
   ▼
PostgreSQL
```

Possible future additions:

- domain name
- HTTPS
- reverse proxy
- production WSGI server
- monitoring
- automatic restart
- server logs

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
