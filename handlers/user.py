# handlers/user.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import COURSES, SPECIAL_OFFERS, GROUP_ID
from states.forms import Registration
from keyboards.inline import role_keyboard, offer_confirm_keyboard, courses_keyboard, close_topic_keyboard
from keyboards.reply import main_menu
from database.db import get_thread, save_thread, get_user_role, save_user

router = Router()

# Обрабатываем и команду /start (в т.ч. с сайта), и кнопку "Главное меню"
@router.message(CommandStart())
@router.message(F.text == "📱 Главное меню / Направления")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    
    # 1. Проверяем, есть ли параметры (переход с сайта)
    args = message.text.split() if message.text.startswith('/start') else []
    if len(args) > 1:
        param = args[1]
        if param in SPECIAL_OFFERS:
            await state.update_data(selected_course=SPECIAL_OFFERS[param], is_special=True)
        elif param in COURSES:
            await state.update_data(selected_course=COURSES[param])

    # 2. Проверяем, помнит ли бот роль пользователя
    saved_role = get_user_role(message.from_user.id)
    
    if saved_role:
        await state.update_data(user_role=saved_role)
        # Если роль известна, переходим сразу к делу
        await proceed_to_offer_or_courses(message, state)
    else:
        # Если роли нет, спрашиваем
        await message.answer(
            "Здравствуйте! Для начала уточните, пожалуйста: вы родитель или ученик?", 
            reply_markup=role_keyboard()
        )
        await state.set_state(Registration.choosing_role)

@router.callback_query(Registration.choosing_role, F.data.startswith("role_"))
async def process_role(callback: types.CallbackQuery, state: FSMContext):
    role = "Родитель" if callback.data == "role_parent" else "Ученик"
    
    # СОХРАНЯЕМ РОЛЬ В БАЗУ ДАННЫХ НАВСЕГДА
    save_user(callback.from_user.id, role)
    await state.update_data(user_role=role)
    
    await proceed_to_offer_or_courses(callback.message, state, is_callback=True)
    await callback.answer()

async def proceed_to_offer_or_courses(message: types.Message, state: FSMContext, is_callback=False):
    """Функция, которая решает, что показать: акцию или список курсов"""
    data = await state.get_data()
    role = data.get("user_role", "Пользователь")
    
    greeting = "Спасибо!" if is_callback else f"С возвращением, {message.chat.first_name}!"
    
    if data.get("is_special"):
        text = (f"{greeting}\n\nВы выбрали спецпредложение: <b>{data.get('selected_course')}</b>.\n"
                "Хотите обсудить его с менеджером и забронировать место?")
        if is_callback:
            await message.edit_text(text, reply_markup=offer_confirm_keyboard(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=offer_confirm_keyboard(), parse_mode="HTML")
    
    elif "selected_course" in data:
        # Перешел по прямой ссылке курса
        # Здесь мы имитируем callback, чтобы завершить рег-ю
        dummy_callback = types.CallbackQuery(id="0", from_user=message.chat, chat_instance="0", message=message, data="")
        await finish_registration(dummy_callback, state, direct_message=True)
    
    else:
        text = f"{greeting}\nВыберите интересующее вас направление обучения:"
        if is_callback:
            await message.edit_text(text, reply_markup=courses_keyboard())
        else:
            await message.answer(text, reply_markup=courses_keyboard(), reply_markup_bottom=main_menu())
        await state.set_state(Registration.choosing_course)

@router.callback_query(F.data.startswith("confirm_offer_"))
async def process_offer_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "confirm_offer_yes":
        await finish_registration(callback, state)
    else:
        await callback.message.edit_text("Хорошо! Тогда выберите любое другое направление из нашего списка:", reply_markup=courses_keyboard())
        await state.set_state(Registration.choosing_course)
    await callback.answer()

@router.callback_query(Registration.choosing_course, F.data.startswith("course_"))
async def process_course(callback: types.CallbackQuery, state: FSMContext):
    course_code = callback.data[7:] 
    await state.update_data(selected_course=COURSES.get(course_code))
    await finish_registration(callback, state)
    await callback.answer()

async def finish_registration(callback: types.CallbackQuery, state: FSMContext, direct_message=False):
    data = await state.get_data()
    role = data.get("user_role", "Неизвестно")
    course = data.get("selected_course")
    user = callback.from_user
    bot = callback.bot
    msg = callback if direct_message else callback.message
    
    thread_id = get_thread(user.id)
    if not thread_id:
        topic = await bot.create_forum_topic(GROUP_ID, f"{user.first_name} | {course}")
        thread_id = topic.message_thread_id
        save_thread(user.id, thread_id)

    success_text = f"Заявка на <b>{course}</b> принята! Чат с менеджером открыт.\nНапишите ваш вопрос ниже 👇"
    
    if direct_message:
        await msg.answer(success_text, parse_mode="HTML", reply_markup=main_menu())
    else:
        await msg.edit_text(success_text, parse_mode="HTML")
    
    report = (
        f"🚀 <b>НОВАЯ ЗАЯВКА С САЙТА</b>\n\n"
        f"👤 Клиент: {user.first_name}\n"
        f"🎭 Статус: {role}\n"
        f"📚 Тема: {course}\n"
        f"🆔 ID: <code>{user.id}</code>"
    )
    await bot.send_message(GROUP_ID, report, message_thread_id=thread_id, 
                           parse_mode="HTML", reply_markup=close_topic_keyboard(user.id))
    await state.clear()