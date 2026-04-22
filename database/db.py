# database/db.py
import sqlite3

conn = sqlite3.connect('sigma_crm.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS threads 
                      (user_id INTEGER PRIMARY KEY, thread_id INTEGER)''')
    # НОВОЕ: Таблица пользователей для запоминания роли
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, role TEXT)''')
    conn.commit()

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

# --- НОВОЕ: Функции пользователей ---
def save_user(user_id: int, role: str):
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, role))
    conn.commit()

def get_user_role(user_id: int):
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else None