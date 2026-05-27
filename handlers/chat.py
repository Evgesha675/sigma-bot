# handlers/chat.py
from aiogram import Router, types, F
from config import GROUP_ID
from database.db import get_thread, save_thread, get_user_roles, get_user_by_thread

router = Router()

@router.message(F.chat.id != GROUP_ID)
async def from_client(message: types.Message):
    """Пересылка от клиента админам в топик"""
    if not message.text or message.text.startswith('/') or message.text in ["📚 Расписание и запись", "💬 Связь с менеджером"]:
        return

    from handlers.user import get_or_create_thread
    thread_id = await get_or_create_thread(message.bot, message.from_user)

    try:
        await message.bot.copy_message(
            chat_id=GROUP_ID,
            from_chat_id=message.from_user.id,
            message_id=message.message_id,
            message_thread_id=thread_id
        )
    except Exception:
        await message.bot.send_message(GROUP_ID, f"📩 {message.from_user.full_name}: {message.text}")

@router.message(F.chat.id == GROUP_ID, F.message_thread_id)
async def from_admin(message: types.Message):
    """Обратная связь: от админа в топике к клиенту"""
    if not message.message_thread_id or (message.text and message.text.startswith('/')):
        return
        
    user_id = get_user_by_thread(message.message_thread_id)
    if user_id:
        try:
            await message.bot.copy_message(
                chat_id=user_id,
                from_chat_id=GROUP_ID,
                message_id=message.message_id
            )
        except Exception:
            await message.answer("❌ Ошибка: клиент заблокировал бота.")