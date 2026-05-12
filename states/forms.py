# states/forms.py
from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    choosing_roles = State()
    choosing_course = State()

class ParentChildLink(StatesGroup):
    waiting_for_child_id = State()