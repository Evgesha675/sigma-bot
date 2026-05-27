from aiogram import Router, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import GROUP_ID, ADMIN_IDS
from database.db import get_user_roles, add_user_role, clear_user_roles, get_thread, save_thread
from services.sheets import sheet_manager
from keyboards.inline import role_keyboard, close_topic_keyboard
from keyboards.reply import main_menu
from states.forms import Registration, BookingProcess

router = Router()

def format_time(t_str):
    return str(t_str)[:5]

async def get_or_create_thread(bot, user):
    tid = get_thread(user.id)
    if not tid:
        topic = await bot.create_forum_topic(GROUP_ID, user.full_name)
        tid = topic.message_thread_id
        save_thread(user.id, tid)
    return tid

# --- СТАРТ И РОЛИ ---
@router.message(CommandStart())
async def start(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    sheet_manager.save_user(message.from_user.id, message.from_user.full_name)
    if message.from_user.id in ADMIN_IDS:
        return await message.answer("👑 Админ-панель", reply_markup=main_menu(["Администратор"]))
    
    roles = get_user_roles(message.from_user.id)
    if roles:
        await message.answer("С возвращением!", reply_markup=main_menu(roles))
    else:
        await message.answer("Здравствуйте! Выберите роль:", reply_markup=role_keyboard())
        await state.set_state(Registration.choosing_roles)

@router.callback_query(F.data.startswith("set_role_"))
async def process_set_role(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[2]
    clear_user_roles(callback.from_user.id)
    add_user_role(callback.from_user.id, role)
    await callback.answer("Принято!")
    await callback.message.edit_text(f"✅ Роль {role} сохранена!")
    await callback.message.answer("Главное меню:", reply_markup=main_menu([role]))

# --- ОБЩАЯ ОТМЕНА ---
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("❌ Действие отменено")
    roles = get_user_roles(callback.from_user.id)
    
    await callback.message.edit_text("Действие отменено.")
    if roles:
        await callback.message.answer("Главное меню:", reply_markup=main_menu(roles))
    else:
        await callback.message.answer("Выберите роль:", reply_markup=role_keyboard())
        await state.set_state(Registration.choosing_roles)

# --- ЛОГИКА ЗАПИСИ (ИНДЕКСНАЯ) ---
@router.message(F.text == "📚 Расписание и запись")
async def schedule(message: types.Message, state: FSMContext):
    slots = sheet_manager.get_available_slots()
    if not slots:
        return await message.answer("😔 Пока нет свободных мест.")
    
    # Сохраняем уникальные курсы в состояние, чтобы не передавать длинные строки
    courses = sorted(list({s['course_name'] for s in slots}))
    await state.update_data(courses_list=courses)
    
    builder = InlineKeyboardBuilder()
    for i, c in enumerate(courses):
        builder.button(text=f"📚 {c}", callback_data=f"sel_course|{i}")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    await message.answer("Выберите курс:", reply_markup=builder.adjust(1).as_markup())

@router.callback_query(F.data.startswith("sel_course|"))
async def select_course(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("|")[1])
    data = await state.get_data()
    courses = data.get("courses_list")
    
    if not courses: # Если FSM слетел
        return await cancel_action(callback, state)
        
    course_name = courses[index]
    await state.update_data(course=course_name)
    
    # Фильтруем слоты именно для этого курса
    slots = [s for s in sheet_manager.get_available_slots() if s['course_name'] == course_name]
    await state.update_data(slots_list=slots) # Сохраняем слоты
    
    builder = InlineKeyboardBuilder()
    for i, s in enumerate(slots):
        t = format_time(s['time'])
        builder.button(text=f"📅 {s['date']} | ⏰ {t}", callback_data=f"book_time|{i}")
    
    builder.button(text="🔙 Назад", callback_data="back_to_courses")
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    await callback.message.edit_text(f"Курс: <b>{course_name}</b>\nВыберите время:", 
                                     reply_markup=builder.adjust(1).as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "back_to_courses")
async def back_to_courses(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # Просто вызываем функцию schedule, передав message
    await schedule(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("book_time|"))
async def book_time(callback: types.CallbackQuery, state: FSMContext):
    index = int(callback.data.split("|")[1])
    data = await state.get_data()
    
    slot = data['slots_list'][index]
    await state.update_data(d=slot['date'], t=format_time(slot['time']))
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    await callback.message.edit_text("Введите Имя и телефон для записи:", reply_markup=builder.as_markup())
    await state.set_state(BookingProcess.waiting_for_child_name)
    await callback.answer()

@router.message(BookingProcess.waiting_for_child_name)
async def booking_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sheet_manager.book_slot(message.from_user.id, message.from_user.full_name, 
                            data.get("course"), data['d'], data['t'], message.text, "Клиент")
    await message.answer("✅ Записали!")
    tid = await get_or_create_thread(message.bot, message.from_user)
    msg = f"🚀 <b>ЗАПИСЬ</b>\nКурс: {data.get('course')}\n📅 {data['d']} {data['t']}\n👤 Данные: {message.text}"
    await message.bot.send_message(GROUP_ID, msg, message_thread_id=tid, 
                                   reply_markup=close_topic_keyboard(message.from_user.id), parse_mode="HTML")
    await state.clear()

# --- СВЯЗЬ И ОПЛАТА ---
@router.message(F.text == "💬 Связь с менеджером")
async def contact(message: types.Message):
    await message.answer("⏳ Минутку, открываю диалог...")
    tid = await get_or_create_thread(message.bot, message.from_user)
    await message.bot.send_message(GROUP_ID, f"📩 Запрос от {message.from_user.full_name}", 
                                   message_thread_id=tid, reply_markup=close_topic_keyboard(message.from_user.id))
    await message.answer("✅ Менеджер уведомлен! Пишите вопрос сюда.")

@router.message(F.text == "💳 Оплата")
async def payment(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_action")
    await message.answer("💳 <b>Оплата</b>\n\nПришлите скриншот чека и ФИО ребенка.", 
                         reply_markup=builder.as_markup(), parse_mode="HTML")