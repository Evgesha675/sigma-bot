# keyboards/inline.py
# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def cancel_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    return builder.as_markup()

# Добавь эту кнопку во все свои функции (role_keyboard, deep_link_slots_keyboard и т.д.)
# Пример для выбора роли:
def role_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👨‍👩‍👧 Я Родитель", callback_data="set_role_Родитель")
    builder.button(text="🎓 Я Ученик", callback_data="set_role_Ученик")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    return builder.adjust(1).as_markup()

def close_topic_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Завершить диалог", callback_data=f"close_{user_id}")
    return builder.as_markup()

def admin_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Выдать роли", callback_data="admin_users")
    return builder.adjust(1).as_markup()

def admin_roles_keyboard(target_id):
    builder = InlineKeyboardBuilder()
    for role in ["Родитель", "Ученик", "Администратор"]:
        builder.button(text=f"Выдать: {role}", callback_data=f"admin_setrole_{target_id}_{role}")
    builder.button(text="🔙 Назад", callback_data="admin_back")
    return builder.adjust(1).as_markup()

def deep_link_slots_keyboard(slots):
    builder = InlineKeyboardBuilder()
    if not slots:
        builder.button(text="❌ Нет мест", callback_data="back_to_menu")
    else:
        for s in slots:
            builder.button(text=f"✅ {s['course_name']} | {s['date']} {s['time']}", 
                           callback_data=f"dl_book|{s['date']}|{s['time']}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    return builder.adjust(1).as_markup()