# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from database.db import init_db
from handlers import user, chat, admin

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализация базы данных
    init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Подключаем роутеры. ВАЖНО: chat.router должен быть последним!
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(chat.router)
    
    print("🚀 Бот запущен! Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")