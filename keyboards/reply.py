# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = [[KeyboardButton(text="📱 Главное меню / Направления")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Нажмите на кнопку ниже")