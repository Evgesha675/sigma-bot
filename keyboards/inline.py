# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import COURSES, GOOGLE_SCHEDULE_URL, COMMON_CHAT_URL

def role_keyboard(selected_roles: list = None):
    if selected_roles is None:
        selected_roles = []

    builder = InlineKeyboardBuilder()

    parent_text = "✅ Я Родитель 👨‍👩‍👧" if "Родитель" in selected_roles else "Я Родитель 👨‍👩‍👧"
    student_text = "✅ Я Ученик 🎓" if "Ученик" in selected_roles else "Я Ученик 🎓"

    builder.button(text=parent_text, callback_data="toggle_role_Родитель")
    builder.button(text=student_text, callback_data="toggle_role_Ученик")

    if selected_roles:
        builder.button(text="➡️ Завершить выбор ролей", callback_data="finish_roles")

    builder.adjust(1)
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

def course_details_keyboard(course_code: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Записаться на пробное занятие", callback_data=f"trial_{course_code}")
    builder.button(text="🔙 Назад к списку курсов", callback_data="back_to_courses")
    builder.adjust(1)
    return builder.as_markup()

def close_topic_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Завершить диалог", callback_data=f"close_{user_id}")
    return builder.as_markup()

def main_inline_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🗓 Расписание и ДЗ (Google Schedule)", url=GOOGLE_SCHEDULE_URL)
    builder.button(text="💬 Общий чат", url=COMMON_CHAT_URL)
    builder.adjust(1)
    return builder.as_markup()