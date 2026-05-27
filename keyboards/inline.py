# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import get_available_lessons

def role_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍👩‍👧 Я Родитель", callback_data="set_role_Родитель")
    builder.button(text="🎓 Я Ученик", callback_data="set_role_Ученик")
    builder.adjust(1)
    return builder.as_markup()

def schedule_keyboard():
    builder = InlineKeyboardBuilder()
    lessons = get_available_lessons()
    for lesson in lessons:
        lesson_id, name, dt, total, booked = lesson
        available = total - booked
        if available > 0:
            builder.button(text=f"{name} | {dt} (Мест: {available})", callback_data=f"book_{lesson_id}")
        else:
            builder.button(text=f"❌ {name} | {dt} (МЕСТ НЕТ)", callback_data="lesson_full")
    builder.adjust(1)
    return builder.as_markup()

def cancel_booking_keyboard(lesson_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить запись", callback_data=f"cancel_{lesson_id}")
    return builder.as_markup()

def close_topic_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Завершить диалог", callback_data=f"close_{user_id}")
    return builder.as_markup()

def admin_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Управление расписанием", callback_data="admin_schedule")
    builder.button(text="👥 Управление пользователями", callback_data="admin_users")
    builder.adjust(1)
    return builder.as_markup()

def admin_schedule_edit_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить занятие", callback_data="admin_add_lesson")
    lessons = get_available_lessons()
    for lesson in lessons:
        lesson_id, name, dt, _, _ = lesson
        builder.button(text=f"❌ Удалить: {name} | {dt}", callback_data=f"admin_del_lesson_{lesson_id}")
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()

def admin_roles_keyboard(target_user_id: int):
    builder = InlineKeyboardBuilder()
    for role in ["Родитель", "Ученик", "Модератор"]:
        builder.button(text=f"Выдать: {role}", callback_data=f"admin_setrole_{target_user_id}_{role}")
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()