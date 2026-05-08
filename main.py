# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher

from aiohttp import web

from config import TOKEN, WEBAPP_PORT
from database.db import init_db
from handlers import user, chat, admin
from webapp import init_webapp

async def start_webapp():
    app = init_webapp()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEBAPP_PORT)
    await site.start()
    print(f"🚀 WebApp запущен на порту {WEBAPP_PORT}!")

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
    
    # Запускаем webapp в фоне
    asyncio.create_task(start_webapp())

    print("🚀 Бот запущен! Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")