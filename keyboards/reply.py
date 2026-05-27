from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu(user_roles=None, is_dialog_active=False):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Расписание и запись")
    builder.button(text="💬 Связь с менеджером")
    
    if "Родитель" in (user_roles or []):
        builder.button(text="💳 Оплата")
    
    if is_dialog_active:
        builder.button(text="❌ Завершить диалог")
        
    if "Администратор" in (user_roles or []):
        builder.button(text="⚙️ Админ-панель")
        
    return builder.adjust(2).as_markup(resize_keyboard=True)