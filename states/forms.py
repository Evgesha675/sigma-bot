# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    choosing_role = State()
    choosing_course = State()