# handlers/user.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import COURSES, SPECIAL_OFFERS, GROUP_ID
from states.forms import Registration, ParentChildLink
from keyboards.inline import role_keyboard, offer_confirm_keyboard, courses_keyboard, close_topic_keyboard, main_inline_menu
from keyboards.reply import main_menu
from database.db import get_thread, save_thread, get_user_roles, add_user_role, clear_user_roles, link_parent_child, get_children

router = Router()

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

    # 2. Проверяем, помнит ли бот роли пользователя
    saved_roles = get_user_roles(message.from_user.id)
    
    if saved_roles:
        await state.update_data(user_roles=saved_roles)
        # Если роли известны, переходим сразу к делу
        await message.answer("Добро пожаловать в CRM! Выберите нужное действие:", reply_markup=main_inline_menu())
        # Отправляем reply-клавиатуру в зависимости от ролей
        await message.answer("Воспользуйтесь меню ниже:", reply_markup=main_menu(saved_roles))
        await proceed_to_offer_or_courses(message, state)
    else:
        # Если ролей нет, спрашиваем
        await state.update_data(temp_roles=[])
        await message.answer(
            "Здравствуйте! Выберите одну или несколько ролей, кем вы являетесь:",
            reply_markup=role_keyboard([])
        )
        await state.set_state(Registration.choosing_roles)

@router.callback_query(Registration.choosing_roles, F.data.startswith("toggle_role_"))
async def process_toggle_role(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[2]
    data = await state.get_data()
    temp_roles = data.get("temp_roles", [])
    
    if role in temp_roles:
        temp_roles.remove(role)
    else:
        temp_roles.append(role)

    await state.update_data(temp_roles=temp_roles)
    await callback.message.edit_reply_markup(reply_markup=role_keyboard(temp_roles))
    await callback.answer()

@router.callback_query(Registration.choosing_roles, F.data == "finish_roles")
async def process_finish_roles(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_roles = data.get("temp_roles", [])

    if not selected_roles:
        await callback.answer("Пожалуйста, выберите хотя бы одну роль!", show_alert=True)
        return

    # Сохраняем роли в БД
    clear_user_roles(callback.from_user.id)
    for role in selected_roles:
        add_user_role(callback.from_user.id, role)

    await state.update_data(user_roles=selected_roles)
    
    # Отправляем reply-клавиатуру в зависимости от выбранных ролей
    await callback.message.answer("Роли сохранены!", reply_markup=main_menu(selected_roles))
    await proceed_to_offer_or_courses(callback.message, state, is_callback=True)
    await callback.answer()

@router.message(F.text == "🆔 Узнать свой ID")
async def get_my_id(message: types.Message):
    await message.answer(f"Ваш ID: <code>{message.from_user.id}</code>\n"
                         "Вы можете передать его родителю для привязки.", parse_mode="HTML")

# --- Родительский интерфейс ---

@router.message(F.text == "🔗 Привязать ребенка")
async def prompt_link_child(message: types.Message, state: FSMContext):
    roles = get_user_roles(message.from_user.id)
    if "Родитель" not in roles:
        return
    await message.answer("Пожалуйста, введите ID вашего ребенка (он может получить его по кнопке '🆔 Узнать свой ID'):")
    await state.set_state(ParentChildLink.waiting_for_child_id)

@router.message(ParentChildLink.waiting_for_child_id, F.text)
async def process_link_child(message: types.Message, state: FSMContext):
    try:
        child_id = int(message.text.strip())
    except ValueError:
        await message.answer("Неверный формат ID. Пожалуйста, введите число.")
        return

    link_parent_child(message.from_user.id, child_id)
    await message.answer(f"✅ Ребенок с ID {child_id} успешно привязан!")
    await state.clear()

@router.message(F.text == "👨‍👧 Мои дети")
async def show_my_children(message: types.Message):
    roles = get_user_roles(message.from_user.id)
    if "Родитель" not in roles:
        return

    children_ids = get_children(message.from_user.id)
    if not children_ids:
        await message.answer("У вас пока нет привязанных детей.")
        return

    text = "<b>Ваши дети:</b>\n\n"
    for cid in children_ids:
        text += f"🧒 ID: <code>{cid}</code>\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "💳 Оплата")
async def mock_payment(message: types.Message):
    roles = get_user_roles(message.from_user.id)
    if "Родитель" not in roles:
        return
    await message.answer("Функция оплаты находится в разработке 🛠")

async def proceed_to_offer_or_courses(message: types.Message, state: FSMContext, is_callback=False):
    """Функция, которая решает, что показать: акцию или список курсов"""
    data = await state.get_data()
    roles = data.get("user_roles", [])
    roles_str = ", ".join(roles) if roles else "Пользователь"
    
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
    roles = data.get("user_roles", [])
    roles_str = ", ".join(roles) if roles else "Неизвестно"
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
        await msg.answer(success_text, parse_mode="HTML", reply_markup=main_menu(roles))
        await msg.answer("Также вы можете воспользоваться нашими сервисами:", reply_markup=main_inline_menu())
    else:
        await msg.edit_text(success_text, parse_mode="HTML")
        await msg.message.answer("Также вы можете воспользоваться нашими сервисами:", reply_markup=main_inline_menu())
    
    report = (
        f"🚀 <b>НОВАЯ ЗАЯВКА С САЙТА</b>\n\n"
        f"👤 Клиент: {user.first_name}\n"
        f"🎭 Статус: {roles_str}\n"
        f"📚 Тема: {course}\n"
        f"🆔 ID: <code>{user.id}</code>"
    )
    await bot.send_message(GROUP_ID, report, message_thread_id=thread_id, 
                           parse_mode="HTML", reply_markup=close_topic_keyboard(user.id))
    await state.clear()