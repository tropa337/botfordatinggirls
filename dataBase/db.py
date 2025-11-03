import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Налаштування підключення до БД
DB_CONFIG = {
    "dbname": "dv_knu",           # Змінив на bot_db
    "user": "dv_knu_user",           
    "password": "e96gkA539jHZiaIKKPXmDJJ5CIJ3j6pp",          
    "host": "dpg-d44fnsripnbc73frua00-a",
    "port": "5432"
}

class DatabaseError(Exception):
    """Власний виняток для помилок БД"""
    pass

def get_connection():
    """Створення підключення до БД"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        raise DatabaseError(f"Помилка підключення до БД: {e}")

def init_db():
    """Ініціалізація структури БД"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Таблиця профілів
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id BIGINT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    age INTEGER CHECK (age >= 16 AND age <= 100),
                    gender VARCHAR(20) NOT NULL,
                    looking_for VARCHAR(20) NOT NULL,
                    faculty VARCHAR(100),
                    specialty VARCHAR(100),
                    accessibility INTEGER CHECK (accessibility >= 0 AND accessibility <= 10),
                    course VARCHAR(50),
                    bio TEXT,
                    photo_id VARCHAR(255),
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблиця лайків
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    user_id BIGINT NOT NULL,
                    liked_user_id BIGINT NOT NULL,
                    accepted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(user_id, liked_user_id)
                )
            """)
            
        conn.commit()
        print("✅ Базу даних успішно ініціалізовано!")
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Помилка ініціалізації БД: {e}")
    finally:
        conn.close()

def add_profile(user_id: int, name: str, age: int, gender: str, looking_for: str, 
                faculty: str, specialty: str, accessibility: int, course: str, 
                bio: str, photo_id: str) -> bool:
    """Додавання або оновлення профілю"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO profiles 
                (user_id, name, age, gender, looking_for, faculty, specialty, 
                 accessibility, course, bio, photo_id, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    looking_for = EXCLUDED.looking_for,
                    faculty = EXCLUDED.faculty,
                    specialty = EXCLUDED.specialty,
                    accessibility = EXCLUDED.accessibility,
                    course = EXCLUDED.course,
                    bio = EXCLUDED.bio,
                    photo_id = EXCLUDED.photo_id,
                    active = TRUE,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, name, age, gender, looking_for, faculty, specialty, 
                  accessibility, course, bio, photo_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Помилка додавання профілю: {e}")
    finally:
        conn.close()

def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Отримання профілю"""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"Помилка отримання профілю: {e}")
        return None
    finally:
        conn.close()

def get_active_profiles(exclude_user_id: int, looking_for: Optional[str] = None):
    """Отримання активних профілів"""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if looking_for and looking_for.lower() != "усіх":
                cursor.execute(
                    "SELECT * FROM profiles WHERE active = TRUE AND user_id != %s AND gender = %s",
                    (exclude_user_id, looking_for)
                )
            else:
                cursor.execute(
                    "SELECT * FROM profiles WHERE active = TRUE AND user_id != %s",
                    (exclude_user_id,)
                )
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        print(f"Помилка отримання активних профілів: {e}")
        return []
    finally:
        conn.close()

def like_profile(user_id: int, liked_user_id: int) -> bool:
    """Додавання лайка"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO likes (user_id, liked_user_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, liked_user_id) 
                DO NOTHING
            """, (user_id, liked_user_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Помилка додавання лайка: {e}")
    finally:
        conn.close()

def is_mutual_like(user_id: int, liked_user_id: int) -> bool:
    """Перевірка взаємного лайка"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM likes 
                WHERE user_id = %s AND liked_user_id = %s
            """, (liked_user_id, user_id))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        print(f"Помилка перевірки взаємного лайка: {e}")
        return False
    finally:
        conn.close()

def set_mutual_like(user_id: int, liked_user_id: int) -> bool:
    """Відмітка взаємного лайка"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE likes 
                SET accepted = TRUE 
                WHERE (user_id = %s AND liked_user_id = %s)
                OR (user_id = %s AND liked_user_id = %s)
            """, (user_id, liked_user_id, liked_user_id, user_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Помилка встановлення взаємного лайка: {e}")
    finally:
        conn.close()

def disable_profile(user_id: int) -> bool:
    """Деактивація профілю"""
    return update_profile_field(user_id, "active", False)

def enable_profile(user_id: int) -> bool:
    """Активація профілю"""
    return update_profile_field(user_id, "active", True)

def update_profile_field(user_id: int, field: str, value: Any) -> bool:
    """Безпечне оновлення поля профілю"""
    allowed_fields = {
        'name', 'age', 'gender', 'looking_for', 'faculty', 
        'specialty', 'accessibility', 'course', 'bio', 'photo_id', 'active'
    }
    
    if field not in allowed_fields:
        raise ValueError(f"Неприпустиме поле для оновлення: {field}")
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            query = f"UPDATE profiles SET {field} = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
            cursor.execute(query, (value, user_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        conn.rollback()
        raise DatabaseError(f"Помилка оновлення профілю: {e}")
    finally:
        conn.close()

def has_liked(user_id: int, liked_user_id: int) -> bool:
    """Перевірка, чи вже лайкав користувач"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM likes WHERE user_id = %s AND liked_user_id = %s",
                (user_id, liked_user_id)
            )
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        print(f"Помилка перевірки лайка: {e}")
        return False
    finally:
        conn.close()