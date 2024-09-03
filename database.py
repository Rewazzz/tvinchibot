import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'database.db'

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            student_group TEXT,
            description TEXT,
            photo_path TEXT,
            telegram_id TEXT,
            gender TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viewed_profiles (
            user_id INTEGER,
            viewed_user_id INTEGER,
            viewed_time TEXT,
            PRIMARY KEY (user_id, viewed_user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            liked_user_id INTEGER,
            PRIMARY KEY (user_id, liked_user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            user_id INTEGER,
            matched_user_id INTEGER,
            PRIMARY KEY (user_id, matched_user_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_user(user_id, name, age, student_group, description, photo_path, telegram_id, gender):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, name, age, student_group, description, photo_path, telegram_id, gender)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            age = excluded.age,
            student_group = excluded.student_group,
            description = excluded.description,
            photo_path = excluded.photo_path,
            telegram_id = excluded.telegram_id,
            gender = excluded.gender
    ''', (user_id, name, age, student_group, description, photo_path, telegram_id, gender))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def add_like(user_id, liked_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)', (user_id, liked_user_id))
    conn.commit()
    conn.close()

def check_match(user_id, liked_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?', (liked_user_id, user_id))
    match_exists = cursor.fetchone() is not None
    conn.close()
    return match_exists

def add_viewed_profile(user_id, viewed_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO viewed_profiles (user_id, viewed_user_id, viewed_time)
        VALUES (?, ?, ?)
    ''', (user_id, viewed_user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_viewed_profiles(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT viewed_user_id FROM viewed_profiles WHERE user_id = ? AND viewed_time >= ?', (user_id, (datetime.now() - timedelta(days=1)).isoformat()))
    viewed_profiles = cursor.fetchall()
    conn.close()
    return viewed_profiles

def get_user_likes(user_id, liked_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?', (user_id, liked_user_id))
    user_likes = cursor.fetchone() is not None
    conn.close()
    return user_likes

def set_user_like_status(user_id, liked_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)', (user_id, liked_user_id))
    conn.commit()
    conn.close()

def add_match(user_id, matched_user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO matches (user_id, matched_user_id) VALUES (?, ?)', (user_id, matched_user_id))
    conn.commit()
    conn.close()

def get_user_profile(user_id):
    user = get_user(user_id)
    if user:
        name, age, student_group, description, photo_path = user[1:6]
        return f"""
        Имя: {name}
        Возраст: {age}
        Группа: {student_group}
        Описание: {description}
        """
    return "Профиль не найден."

def get_user_profile_photo(user_id):
    user = get_user(user_id)
    return user[5] if user else None

def get_user_name(user_id):
    user = get_user(user_id)
    return user[1] if user else "Имя не найдено"

def get_user_age(user_id):
    user = get_user(user_id)
    return user[2] if user else "Возраст не найден"

def get_user_group(user_id):
    user = get_user(user_id)
    return user[3] if user else "Группа не найдена"

def get_user_description(user_id):
    user = get_user(user_id)
    return user[4] if user else "Описание не найдено"

def get_user_telegram_id(user_id):
    user = get_user(user_id)
    return user[6] if user else "Telegram ID не найден"
