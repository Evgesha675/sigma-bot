# handlers/chat.py
from aiogram import Router, types, F
from config import GROUP_ID
from database.db import get_thread, get_user_by_thread, save_thread
from keyboards.inline import close_topic_keyboard

# ВОТ ЭТА СТРОКА БЫЛА ПОТЕРЯНА. Она должна быть перед всеми @router...
router = Router()

from aiogram.filters import Command

# Команда /schedule для групп
@router.message(Command("schedule"))
async def schedule_command(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        # Можно дополнить логику, чтобы выдавать расписание конкретно для этой группы
        from config import GOOGLE_SCHEDULE_URL
        await message.answer(f"🗓 <b>Расписание группы:</b>\n{GOOGLE_SCHEDULE_URL}", parse_mode="HTML")

# От клиента -> в группу (в топик)
@router.message(F.chat.id != GROUP_ID)
async def from_client(message: types.Message):
    user_id = message.from_user.id
    thread_id = get_thread(user_id)
    bot = message.bot
    
    if thread_id:
        try:
            await bot.copy_message(chat_id=GROUP_ID, from_chat_id=user_id, message_id=message.message_id, message_thread_id=thread_id)
        except Exception:
            # Если топик случайно удалили, переоткрываем
            topic = await bot.create_forum_topic(GROUP_ID, f"{message.from_user.first_name} (Re-open)")
            new_thread_id = topic.message_thread_id
            save_thread(user_id, new_thread_id)
            await bot.send_message(
                GROUP_ID, 
                f"🔄 Топик переоткрыт пользователем.\n", 
                message_thread_id=new_thread_id,
                reply_markup=close_topic_keyboard(user_id)
            )
            await bot.copy_message(chat_id=GROUP_ID, from_chat_id=user_id, message_id=message.message_id, message_thread_id=new_thread_id)
    else:
        await message.answer("Пожалуйста, используйте команду /start (или кнопку меню) для связи с менеджером.")

# От админа (из топика) -> клиенту
@router.message(F.chat.id == GROUP_ID, F.message_thread_id)
async def from_admin(message: types.Message):
    if message.text and message.text.startswith("/close"):
        return # Обрабатывается в admin.py

    user_id = get_user_by_thread(message.message_thread_id)
    if user_id:
        try:
            # Копируем сообщение админа (чтобы работали фото, видео, файлы)
            await message.bot.copy_message(chat_id=user_id, from_chat_id=GROUP_ID, message_id=message.message_id)
        except Exception as e:
            # Если юзер заблокировал бота, админ увидит эту ошибку прямо в топике
            await message.answer(f"❌ Не удалось отправить клиенту. Ошибка: {str(e)}")