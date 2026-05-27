# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database.db import init_db
from handlers import user, admin

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Роутеры (Admin выше, чтобы он мог перехватывать действия быстрее)
    dp.include_router(admin.router)
    dp.include_router(user.router)
    
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")