import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "social_empires.db"


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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        userid TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    conn.commit()
    conn.close()


def register_user(username, password):
    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

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
if __name__ == "__main__":
    init_database()

    username = input("Username: ")
    password = input("Password: ")

    if register_user(username, password):
        print("Account created successfully.")
    else:
        print("Username already exists.")