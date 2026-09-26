import sqlite3
import os
import secrets
from contextlib import closing
from bundle import BASE_DIR
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = os.path.join(BASE_DIR, "social_empires.db")


def get_connection():
    return sqlite3.connect(DB_NAME)

def get_userid(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT userid FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    return user[0]

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        userid TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(users)")}
    if not {"username", "password_hash"}.issubset(columns):
        conn.close()
        raise RuntimeError("Unsupported users schema: username and password_hash are required")
    if "userid" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN userid TEXT")
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
        cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_username_unique ON users(username)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_userid_unique ON users(userid) WHERE userid IS NOT NULL")
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS application_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pvp_battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_userid TEXT NOT NULL,
            victim_userid TEXT NOT NULL,
            win INTEGER NOT NULL,
            gold INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            honor INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            victim_units TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    if "seen_by_victim" not in {row[1] for row in cursor.execute("PRAGMA table_info(pvp_battles)")}:
        cursor.execute("""
            ALTER TABLE pvp_battles
            ADD COLUMN seen_by_victim INTEGER DEFAULT 0
        """)
    cursor.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)")

    conn.commit()
    conn.close()


def get_session_secret():
    configured = os.environ.get("SOCIAL_EMPIRES_SECRET_KEY")
    if configured:
        return configured
    with closing(get_connection()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO application_settings(key, value) VALUES ('session_secret', ?)",
                     (secrets.token_hex(32),))
        return conn.execute("SELECT value FROM application_settings WHERE key = 'session_secret'").fetchone()[0]


def register_user(username, password, create_village=None, discard_village=None):
    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()
    userid = None

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        if create_village is not None:
            userid = create_village()
            cursor.execute("UPDATE users SET userid = ? WHERE username = ?", (userid, username))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        conn.rollback()
        if userid is not None and discard_village is not None:
            discard_village(userid)
        return False
    except Exception:
        conn.rollback()
        if userid is not None and discard_village is not None:
            discard_village(userid)
        raise

    finally:
        conn.close()


def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return False

    return check_password_hash(user[0], password)

def set_userid(username, userid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET userid = ? WHERE username = ?",
        (userid, username)
    )

    conn.commit()
    conn.close()
def record_pvp_battle(
    attacker_userid,
    victim_userid,
    win,
    gold,
    xp,
    honor,
    duration,
    victim_units
):
    import json

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pvp_battles (
            attacker_userid,
            victim_userid,
            win,
            gold,
            xp,
            honor,
            duration,
            victim_units
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        attacker_userid,
        victim_userid,
        int(win),
        int(gold),
        int(xp),
        int(honor),
        int(duration),
        json.dumps(victim_units)
    ))

    conn.commit()
    conn.close()

def get_received_pvp_battles(userid, limit=20):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM pvp_battles
            WHERE victim_userid = ?
            ORDER BY id DESC
            LIMIT ?
    """,    (userid, limit))

        battles = cursor.fetchall()
        conn.close()

        return battles    

def get_sent_pvp_battles(userid, limit=20):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM pvp_battles
            WHERE attacker_userid = ?
            ORDER BY id DESC
            LIMIT ?
        """, (userid, limit))

        battles = cursor.fetchall()
        conn.close()

        return battles


def get_unseen_pvp_battles(userid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pvp_battles
        WHERE victim_userid = ?
        AND seen_by_victim = 0
        ORDER BY id DESC
    """, (userid,))

    battles = cursor.fetchall()
    conn.close()

    return battles


def mark_pvp_battles_seen(userid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE pvp_battles
        SET seen_by_victim = 1
        WHERE victim_userid = ?
        AND seen_by_victim = 0
    """, (userid,))

    conn.commit()
    conn.close()       

def get_username_by_userid(userid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username FROM users WHERE userid = ?",
        (userid,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    return user[0]

if __name__ == "__main__":
    init_database()

    username = input("Username: ")
    password = input("Password: ")

    if register_user(username, password):
        print("Account created successfully.")
    else:
        print("Username already exists.")
