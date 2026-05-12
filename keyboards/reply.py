# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu(user_roles: list = None):
    if user_roles is None:
        user_roles = []

    kb = [
        [KeyboardButton(text="📱 Главное меню / Направления")],
        [KeyboardButton(text="🆔 Узнать свой ID")]
    ]

    if "Родитель" in user_roles:
        kb.append([KeyboardButton(text="👨‍👧 Мои дети"), KeyboardButton(text="💳 Оплата")])
        kb.append([KeyboardButton(text="🔗 Привязать ребенка")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Выберите действие")