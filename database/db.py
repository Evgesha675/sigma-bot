# database/db.py
import sqlite3

conn = sqlite3.connect('sigma_crm.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS threads (user_id INTEGER PRIMARY KEY, thread_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_roles (user_id INTEGER, role TEXT, PRIMARY KEY (user_id, role))''')
    conn.commit()

def save_thread(user_id, thread_id):
    cursor.execute("INSERT OR REPLACE INTO threads VALUES (?, ?)", (user_id, thread_id))
    conn.commit()

def get_thread(user_id):
    cursor.execute("SELECT thread_id FROM threads WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def get_user_by_thread(thread_id):
    cursor.execute("SELECT user_id FROM threads WHERE thread_id = ?", (thread_id,))
    res = cursor.fetchone()
    return res[0] if res else None

def delete_thread(user_id):
    cursor.execute("DELETE FROM threads WHERE user_id = ?", (user_id,))
    conn.commit()

def add_user_role(user_id, role):
    cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()

def get_user_roles(user_id):
    cursor.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def clear_user_roles(user_id):
    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    conn.commit()