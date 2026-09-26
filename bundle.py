import sys
import os
import json
from pathlib import Path

# Bundled data (extracted to a temp dir)

APP_DIR = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).resolve().parent
TMP_BUNDLED_DIR = str(Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else APP_DIR)

# Optional machine-local paths; environment variables take precedence.
settings_file = APP_DIR / "server.local.json"
settings = json.loads(settings_file.read_text(encoding="utf-8")) if settings_file.exists() else {}

def configured_path(env, key, default):
    path = Path(os.environ.get(env) or settings.get(key) or default).expanduser()
    return str((APP_DIR / path).resolve() if not path.is_absolute() else path.resolve())

ASSETS_DIR = configured_path("SOCIAL_EMPIRES_ASSETS_DIR", "assets_dir", os.path.join(TMP_BUNDLED_DIR, "assets"))
STUB_DIR = os.path.join(TMP_BUNDLED_DIR, "stub")
TEMPLATES_DIR = os.path.join(TMP_BUNDLED_DIR, "templates")
VILLAGES_DIR = os.path.join(TMP_BUNDLED_DIR, "villages")
QUESTS_DIR = os.path.join(VILLAGES_DIR, "quests")
CONFIG_DIR = os.path.join(TMP_BUNDLED_DIR, "config")
CONFIG_PATCH_DIR = os.path.join(CONFIG_DIR, "patch")

# Not bundled data (next to server EXE)

BASE_DIR = configured_path("SOCIAL_EMPIRES_DATA_DIR", "data_dir", str(APP_DIR))
os.makedirs(BASE_DIR, exist_ok=True)

MODS_DIR = os.path.join(BASE_DIR, "mods")
SAVES_DIR = os.path.join(BASE_DIR, "saves")
