# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from config import WEBAPP_URL

def main_menu():
    kb = [
        [KeyboardButton(text="📱 Главное меню / Направления")],
        [KeyboardButton(text="🗓 Расписание (Web App)", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Нажмите на кнопку ниже")