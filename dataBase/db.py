import sqlite3

DB_NAME = "bot.db"

# --- Ініціалізація БД ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        course TEXT,
        bio TEXT,
        photo_id TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER,
        liked_user_id INTEGER,
        accepted INTEGER DEFAULT 0,
        PRIMARY KEY(user_id, liked_user_id)
    )
    """)

    conn.commit()
    conn.close()

# --- Функції роботи з БД ---
def add_profile(user_id, name, age, course, bio, photo_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO profiles (user_id, name, age, course, bio, photo_id, active) VALUES (?, ?, ?, ?, ?, ?, 1)",
        (user_id, name, age, course, bio, photo_id)
    )
    conn.commit()
    conn.close()

def get_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, name, age, course, bio, photo_id FROM profiles WHERE user_id=?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result

def get_active_profiles(exclude_user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM profiles WHERE active=1 AND user_id!=?",
        (exclude_user_id,)
    )
    result = cursor.fetchall()
    conn.close()
    return result

def like_profile(user_id, liked_user_id):
    """Зберігає лайк користувача."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)",
        (user_id, liked_user_id)
    )
    conn.commit()
    conn.close()

def is_mutual_like(user_id, liked_user_id):
    """Перевіряє, чи є взаємний лайк."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM likes WHERE user_id=? AND liked_user_id=?",
        (liked_user_id, user_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def set_mutual_like(user_id, liked_user_id):
    """Позначає пару як взаємну (accepted = 1)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE likes SET accepted=1 WHERE user_id=? AND liked_user_id=?",
        (user_id, liked_user_id)
    )
    cursor.execute(
        "UPDATE likes SET accepted=1 WHERE user_id=? AND liked_user_id=?",
        (liked_user_id, user_id)
    )
    conn.commit()
    conn.close()

def disable_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE profiles SET active=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def update_profile_field(user_id, field, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE profiles SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()
