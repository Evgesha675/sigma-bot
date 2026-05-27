# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(user_roles: list = None):
    if user_roles is None:
        user_roles = []

    # Общее меню для всех
    kb = [
        [KeyboardButton(text="📚 Расписание и запись")],
        [KeyboardButton(text="💬 Связь с менеджером")]
    ]

    # Кнопка только для родителя
    if "Родитель" in user_roles:
        kb.append([KeyboardButton(text="💳 Оплата")])

    # --- ВОТ СЮДА ДОБАВЛЯЕМ КНОПКУ АДМИНА ---
    if "Администратор" in user_roles:
        kb.append([KeyboardButton(text="⚙️ Админ-панель")])

    # Возвращаем готовую клавиатуру
    return ReplyKeyboardMarkup(
        keyboard=kb, 
        resize_keyboard=True, 
        input_field_placeholder="Выберите действие ниже 👇"
    )