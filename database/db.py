# database/db.py
import sqlite3

conn = sqlite3.connect('sigma_crm.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS threads 
                      (user_id INTEGER PRIMARY KEY, thread_id INTEGER)''')

    # Таблица профилей пользователей для хранения username (избегаем конфликта со старой таблицей users)
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_profiles
                      (user_id INTEGER PRIMARY KEY, username TEXT)''')

    # Таблица для хранения ролей пользователей. Один юзер - несколько ролей
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_roles
                      (user_id INTEGER, role TEXT, PRIMARY KEY (user_id, role))''')

    # Таблица привязки детей к родителям
    cursor.execute('''CREATE TABLE IF NOT EXISTS parent_child
                      (parent_id INTEGER, child_id INTEGER, PRIMARY KEY (parent_id, child_id))''')

    conn.commit()

# --- Функции пользователей ---
def save_user(user_id: int, username: str):
    cursor.execute("INSERT OR REPLACE INTO user_profiles (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def get_user_id_by_username(username: str):
    cursor.execute("SELECT user_id FROM user_profiles WHERE username = ?", (username,))
    res = cursor.fetchone()
    return res[0] if res else None

# --- Функции потоков (топиков) ---
def save_thread(user_id: int, thread_id: int):
    cursor.execute("INSERT OR REPLACE INTO threads VALUES (?, ?)", (user_id, thread_id))
    conn.commit()

def get_thread(user_id: int):
    cursor.execute("SELECT thread_id FROM threads WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def get_user_by_thread(thread_id: int):
    cursor.execute("SELECT user_id FROM threads WHERE thread_id = ?", (thread_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def delete_thread(user_id: int):
    cursor.execute("DELETE FROM threads WHERE user_id = ?", (user_id,))
    conn.commit()

# --- Функции ролей пользователей ---
def add_user_role(user_id: int, role: str):
    cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()

def get_user_roles(user_id: int):
    cursor.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def clear_user_roles(user_id: int):
    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    conn.commit()

# --- Функции связей родитель-ребенок ---
def link_parent_child(parent_id: int, child_id: int):
    cursor.execute("INSERT OR IGNORE INTO parent_child (parent_id, child_id) VALUES (?, ?)", (parent_id, child_id))
    conn.commit()

def get_children(parent_id: int):
    cursor.execute("SELECT child_id FROM parent_child WHERE parent_id = ?", (parent_id,))
    return [row[0] for row in cursor.fetchall()]

def is_child_linked(parent_id: int, child_id: int):
    cursor.execute("SELECT 1 FROM parent_child WHERE parent_id = ? AND child_id = ?", (parent_id, child_id))
    return bool(cursor.fetchone())