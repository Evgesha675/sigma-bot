# handlers/admin.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from config import GROUP_ID, ADMIN_IDS
from database.db import get_user_by_thread, delete_thread, get_user_id_by_username, add_user_role
from keyboards.reply import main_menu # Добавили импорт

router = Router()

async def execute_close(bot, user_id: int, thread_id: int):
    try:
        # Теперь бот выдает нижнее меню при закрытии
        await bot.send_message(
            user_id, 
            "<b>Ваш диалог с менеджером завершен.</b>\nЕсли возникнут вопросы — нажмите кнопку ниже!", 
            parse_mode="HTML",
            reply_markup=main_menu() 
        )
        await bot.close_forum_topic(GROUP_ID, thread_id)
        delete_thread(user_id)
    except Exception as e:
        logging.error(f"Ошибка закрытия топика: {e}")

@router.message(F.chat.id == GROUP_ID, Command("close"))
async def close_via_command(message: types.Message):
    user_id = get_user_by_thread(message.message_thread_id)
    if user_id:
        await execute_close(message.bot, user_id, message.message_thread_id)
        await message.answer("✅ Диалог закрыт.")
    else:
        await message.answer("❌ Этот топик не привязан к активному диалогу.")

@router.callback_query(F.data.startswith("close_"))
async def close_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await execute_close(callback.bot, user_id, callback.message.message_thread_id)
    await callback.message.edit_text(callback.message.text + "\n\n✅ <b>ДИАЛОГ ЗАКРЫТ</b>", parse_mode="HTML")
    await callback.answer()

# Админские команды для назначения ролей

def is_admin(user_id: int):
    return user_id in ADMIN_IDS

@router.message(Command("add_mod"))
async def add_mod_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /add_mod @username_или_ID")
        return

    target = args[1].replace('@', '')

    if target.isdigit():
        target_id = int(target)
    else:
        target_id = get_user_id_by_username(target)

    if not target_id:
        await message.answer("Пользователь не найден в базе. Попросите его написать /start боту.")
        return

    add_user_role(target_id, "Модератор")
    await message.answer(f"✅ Пользователь {target} назначен Модератором.")

@router.message(Command("add_teacher"))
async def add_teacher_command(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Использование: /add_teacher @username_или_ID")
        return

    target = args[1].replace('@', '')

    if target.isdigit():
        target_id = int(target)
    else:
        target_id = get_user_id_by_username(target)

    if not target_id:
        await message.answer("Пользователь не найден в базе. Попросите его написать /start боту.")
        return

    add_user_role(target_id, "Преподаватель")
    await message.answer(f"✅ Пользователь {target} назначен Преподавателем.")