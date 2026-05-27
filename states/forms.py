# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    choosing_roles = State()

class BookingProcess(StatesGroup):
    waiting_for_child_name = State()
    waiting_for_payment_photo = State()  

class AdminPanelState(StatesGroup):
    waiting_for_user_id = State()