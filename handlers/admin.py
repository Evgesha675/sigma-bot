# handlers/admin.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import GROUP_ID, ADMIN_IDS
from database.db import get_user_by_thread, delete_thread, add_lesson, delete_lesson, clear_user_roles, add_user_role
from keyboards.reply import main_menu
from keyboards.inline import admin_main_keyboard, admin_schedule_edit_keyboard, admin_roles_keyboard
from states.forms import AdminPanelState

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# --- 1. ПАНЕЛЬ УПРАВЛЕНИЯ ---
@router.message(Command("admin"))
@router.message(F.text == "⚙️ Админ-панель")
async def show_admin_panel(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🛠 <b>Панель администратора</b>\nВыберите раздел для управления:", 
                         reply_markup=admin_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_back")
async def admin_back_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 <b>Панель администратора</b>\nВыберите раздел:", 
                                     reply_markup=admin_main_keyboard(), parse_mode="HTML")

# --- 2. УПРАВЛЕНИЕ РАСПИСАНИЕМ ---
@router.callback_query(F.data == "admin_schedule")
async def admin_schedule_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("📅 <b>Расписание:</b>\nНажмите на крестик, чтобы удалить занятие, или добавьте новое.", 
                                     reply_markup=admin_schedule_edit_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_add_lesson")
async def admin_add_lesson_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text(
        "Введите данные нового занятия в формате:\n\n"
        "<code>Название | ДД.ММ в ЧЧ:ММ | Количество мест</code>\n\n"
        "<i>Пример: Робототехника | 20 мая в 15:00 | 10</i>", 
        parse_mode="HTML"
    )
    await state.set_state(AdminPanelState.waiting_for_lesson_data)

@router.message(AdminPanelState.waiting_for_lesson_data, F.text)
async def admin_save_lesson(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split("|")
        name = parts[0].strip()
        dt = parts[1].strip()
        spots = int(parts[2].strip())
        
        add_lesson(name, dt, spots)
        await message.answer(f"✅ Занятие <b>{name}</b> успешно добавлено!", parse_mode="HTML")
    except Exception:
        await message.answer("❌ Ошибка формата. Попробуйте снова через админ-панель.")
    await state.clear()

@router.callback_query(F.data.startswith("admin_del_lesson_"))
async def admin_del_lesson(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    lesson_id = int(callback.data.split("_")[3])
    delete_lesson(lesson_id)
    await callback.answer("Занятие удалено!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=admin_schedule_edit_keyboard())

# --- 3. УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (ВЫДАЧА РОЛЕЙ) ---
@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("Отправьте мне <b>Telegram ID</b> пользователя, которому нужно выдать роль:", parse_mode="HTML")
    await state.set_state(AdminPanelState.waiting_for_user_id)

@router.message(AdminPanelState.waiting_for_user_id, F.text)
async def admin_get_user_id(message: types.Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
        await message.answer(f"Выберите роль для ID <code>{target_id}</code>:", 
                             reply_markup=admin_roles_keyboard(target_id), parse_mode="HTML")
    except ValueError:
        await message.answer("❌ Неверный ID. Это должны быть только цифры.")
    await state.clear()

@router.callback_query(F.data.startswith("admin_setrole_"))
async def admin_set_role(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    parts = callback.data.split("_")
    target_id = int(parts[2])
    role = parts[3]
    
    clear_user_roles(target_id)
    add_user_role(target_id, role)
    
    await callback.message.edit_text(f"✅ Пользователю с ID <code>{target_id}</code> выдана роль <b>{role}</b>.", parse_mode="HTML")
    await callback.answer()

# --- СТАРАЯ ФУНКЦИЯ ЗАКРЫТИЯ ТОПИКА ИЗ CRM ---
@router.callback_query(F.data.startswith("close_"))
async def close_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    try:
        await callback.bot.send_message(user_id, "<b>Ваш диалог с менеджером завершен.</b>", parse_mode="HTML", reply_markup=main_menu())
        await callback.bot.close_forum_topic(GROUP_ID, callback.message.message_thread_id)
        delete_thread(user_id)
        await callback.message.edit_text(callback.message.text + "\n\n✅ <b>ДИАЛОГ ЗАКРЫТ</b>", parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка закрытия: {e}")
    await callback.answer()