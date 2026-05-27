# handlers/user.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import GROUP_ID, ADMIN_IDS
from states.forms import Registration, BookingProcess
from keyboards.inline import role_keyboard, schedule_keyboard, cancel_booking_keyboard, close_topic_keyboard
from keyboards.reply import main_menu
from database.db import (get_user_roles, add_user_role, clear_user_roles, 
                         is_user_booked, check_lesson_availability, 
                         finalize_booking, cancel_booking, get_thread, save_thread)

router = Router()

async def get_or_create_thread(bot, user):
    """Находит существующий топик пользователя или создает новый"""
    thread_id = get_thread(user.id)
    if not thread_id:
        try:
            roles = get_user_roles(user.id)
            role_name = roles[0] if roles else "Клиент"
            topic = await bot.create_forum_topic(GROUP_ID, f"{user.first_name} | {role_name}")
            thread_id = topic.message_thread_id
            save_thread(user.id, thread_id)
        except Exception as e:
            print(f"Ошибка создания топика: {e}")
            return None
    return thread_id

@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    # ПРОВЕРКА НА АДМИНА
    if user_id in ADMIN_IDS:
        await message.answer("👑 <b>Вы авторизованы как Администратор</b>", 
                             reply_markup=main_menu(["Администратор"]), parse_mode="HTML")
        return

    saved_roles = get_user_roles(user_id)
    if saved_roles:
        await message.answer(f"С возвращением, {message.from_user.first_name}!", reply_markup=main_menu(saved_roles))
    else:
        await message.answer("Здравствуйте! Выберите вашу роль:", reply_markup=role_keyboard())
        await state.set_state(Registration.choosing_roles)

@router.callback_query(Registration.choosing_roles, F.data.startswith("set_role_"))
async def process_set_role(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[2]
    clear_user_roles(callback.from_user.id)
    add_user_role(callback.from_user.id, role)
    await callback.message.edit_text(f"✅ Роль <b>{role}</b> сохранена!", parse_mode="HTML")
    await callback.message.answer("Меню открыто:", reply_markup=main_menu([role]))
    await state.clear()

@router.message(F.text == "📚 Расписание и запись")
async def show_schedule(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📅 <b>Актуальное расписание:</b>", reply_markup=schedule_keyboard(), parse_mode="HTML")

@router.message(F.text == "💬 Связь с менеджером")
async def contact_manager(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Напишите ваш вопрос ниже 👇\nМенеджер получит его в вашем персональном топике.")

@router.callback_query(F.data.startswith("book_"))
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    lesson_id = int(callback.data.split("_")[1])
    if is_user_booked(callback.from_user.id, lesson_id):
        await callback.answer("Вы уже записаны!", show_alert=True)
        return
    await state.update_data(booking_lesson_id=lesson_id)
    roles = get_user_roles(callback.from_user.id)
    if "Родитель" in roles:
        await callback.message.edit_text("✍️ Введите <b>Имя и Фамилию ребенка</b>:", parse_mode="HTML")
        await state.set_state(BookingProcess.waiting_for_child_name)
    else:
        await callback.message.edit_text("📱 Введите <b>номер телефона родителя</b>:", parse_mode="HTML")
        await state.set_state(BookingProcess.waiting_for_parent_phone)

@router.message(BookingProcess.waiting_for_child_name)
async def parent_booking_final(message: types.Message, state: FSMContext):
    if message.text in ["📚 Расписание и запись", "💬 Связь с менеджером"]:
        await state.clear()
        return
    data = await state.get_data()
    res = finalize_booking(message.from_user.id, data["booking_lesson_id"], child_name=message.text)
    await message.answer(f"🎉 Записали ребенка: <b>{message.text}</b>", parse_mode="HTML", reply_markup=cancel_booking_keyboard(data["booking_lesson_id"]))
    
    report = f"🚀 <b>НОВАЯ ЗАПИСЬ</b>\nКурс: {res['name']}\nРебенок: {message.text}\nДата: {res['datetime']}"
    thread_id = await get_or_create_thread(message.bot, message.from_user)
    await message.bot.send_message(GROUP_ID, report, message_thread_id=thread_id, parse_mode="HTML")
    await state.clear()

@router.message(BookingProcess.waiting_for_parent_phone)
async def student_booking_final(message: types.Message, state: FSMContext):
    if message.text in ["📚 Расписание и запись", "💬 Связь с менеджером"]:
        await state.clear()
        return
    data = await state.get_data()
    res = finalize_booking(message.from_user.id, data["booking_lesson_id"], parent_phone=message.text)
    await message.answer(f"✅ Заявка принята! Менеджер свяжется по номеру {message.text}")
    
    report = f"🚀 <b>ЗАЯВКА (Ученик)</b>\nКурс: {res['name']}\nТел. родителя: {message.text}"
    thread_id = await get_or_create_thread(message.bot, message.from_user)
    await message.bot.send_message(GROUP_ID, report, message_thread_id=thread_id, parse_mode="HTML")
    await state.clear()