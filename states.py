from aiogram.fsm.state import StatesGroup, State

class UserRegister(StatesGroup):
    name = State()
    phone = State()

class TreePlanting(StatesGroup):
    photo = State()
    location = State()
