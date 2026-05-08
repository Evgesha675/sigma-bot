# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.web_app_info import WebAppInfo
from config import COURSES, WEBAPP_URL, COMMON_CHAT_URL

def role_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Я Родитель 👨‍👩‍👧", callback_data="role_parent")
    builder.button(text="Я Ученик 🎓", callback_data="role_student")
    return builder.as_markup()

def offer_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, хочу узнать подробности! ✅", callback_data="confirm_offer_yes")
    builder.button(text="Нет, посмотреть все курсы 📚", callback_data="confirm_offer_no")
    return builder.as_markup()

def courses_keyboard():
    builder = InlineKeyboardBuilder()
    for code, name in COURSES.items():
        builder.button(text=name, callback_data=f"course_{code}")
    builder.adjust(1) # Все кнопки в один столбец для удобства на телефоне
    return builder.as_markup()

def close_topic_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Завершить диалог", callback_data=f"close_{user_id}")
    return builder.as_markup()

def main_inline_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🗓 Расписание (Web App)", web_app=WebAppInfo(url=WEBAPP_URL))
    builder.button(text="💬 Общий чат", url=COMMON_CHAT_URL)
    builder.adjust(1)
    return builder.as_markup()