# database/db.py
import sqlite3

conn = sqlite3.connect('sigma_crm.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS threads 
                      (user_id INTEGER PRIMARY KEY, thread_id INTEGER)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_roles
                      (user_id INTEGER, role TEXT, PRIMARY KEY (user_id, role))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS parent_child
                      (parent_id INTEGER, child_id INTEGER, PRIMARY KEY (parent_id, child_id))''')

    # Таблицы для расписания и записи
    cursor.execute('''CREATE TABLE IF NOT EXISTS schedule
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       course_name TEXT, 
                       date_time TEXT, 
                       total_spots INTEGER, 
                       booked_spots INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings
                      (user_id INTEGER, 
                       lesson_id INTEGER, 
                       child_name TEXT, 
                       parent_phone TEXT,
                       PRIMARY KEY (user_id, lesson_id))''')
    conn.commit()

    # Добавляем тестовые занятия для демки
    cursor.execute("SELECT COUNT(*) FROM schedule")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO schedule (course_name, date_time, total_spots) VALUES (?, ?, ?)", [
            ("Математика (Пробное)", "15 мая в 18:00", 5),
            ("Программирование (Пробное)", "16 мая в 17:30", 3)
        ])
        conn.commit()

# ==========================================
# --- БАЗОВЫЕ ФУНКЦИИ (ТОПИКИ И РОЛИ) ---
# ==========================================

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

def add_user_role(user_id: int, role: str):
    cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()

def get_user_roles(user_id: int):
    cursor.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def clear_user_roles(user_id: int):
    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    conn.commit()

# ==========================================
# --- РАСПИСАНИЕ И БРОНИРОВАНИЕ ---
# ==========================================

def get_available_lessons():
    """Получает все уроки для клавиатуры"""
    cursor.execute("SELECT id, course_name, date_time, total_spots, booked_spots FROM schedule")
    return cursor.fetchall()

def check_lesson_availability(lesson_id: int):
    cursor.execute("SELECT total_spots, booked_spots, course_name, date_time FROM schedule WHERE id = ?", (lesson_id,))
    return cursor.fetchone()

def is_user_booked(user_id: int, lesson_id: int):
    cursor.execute("SELECT 1 FROM bookings WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id))
    return bool(cursor.fetchone())

def finalize_booking(user_id: int, lesson_id: int, child_name: str = None, parent_phone: str = None):
    lesson = check_lesson_availability(lesson_id)
    if not lesson or lesson[1] >= lesson[0]:
        return "full"
        
    cursor.execute("INSERT INTO bookings (user_id, lesson_id, child_name, parent_phone) VALUES (?, ?, ?, ?)", 
                   (user_id, lesson_id, child_name, parent_phone))
    cursor.execute("UPDATE schedule SET booked_spots = booked_spots + 1 WHERE id = ?", (lesson_id,))
    conn.commit()
    return {"name": lesson[2], "datetime": lesson[3]}

def cancel_booking(user_id: int, lesson_id: int):
    cursor.execute("SELECT 1 FROM bookings WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id))
    if not cursor.fetchone():
        return False
        
    cursor.execute("DELETE FROM bookings WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id))
    cursor.execute("UPDATE schedule SET booked_spots = booked_spots - 1 WHERE id = ?", (lesson_id,))
    conn.commit()
    return True

# ==========================================
# --- АДМИНСКИЕ ФУНКЦИИ ---
# ==========================================

def add_lesson(course_name: str, date_time: str, total_spots: int):
    cursor.execute("INSERT INTO schedule (course_name, date_time, total_spots) VALUES (?, ?, ?)", 
                   (course_name, date_time, total_spots))
    conn.commit()

def delete_lesson(lesson_id: int):
    cursor.execute("DELETE FROM schedule WHERE id = ?", (lesson_id,))
    cursor.execute("DELETE FROM bookings WHERE lesson_id = ?", (lesson_id,))
    conn.commit()