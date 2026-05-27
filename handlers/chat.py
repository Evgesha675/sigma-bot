from aiogram import Router, types, F
from config import GROUP_ID
from database.db import get_thread, get_user_by_thread

router = Router()

@router.message(F.chat.id != GROUP_ID)
async def from_client(message: types.Message):
    # Пропускаем только если топик существует
    tid = get_thread(message.from_user.id)
    if not tid: return # Игнорируем всё, если диалог не открыт
    
    await message.bot.copy_message(GROUP_ID, message.from_user.id, message.message_id, message_thread_id=tid)

@router.message(F.chat.id == GROUP_ID, F.message_thread_id)
async def from_admin(message: types.Message):
    user_id = get_user_by_thread(message.message_thread_id)
    if user_id:
        try:
            await message.bot.copy_message(user_id, GROUP_ID, message.message_id)
        except: pass