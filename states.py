from aiogram.fsm.state import StatesGroup, State

class UserRegister(StatesGroup):
    name = State()
    phone = State() # Shu yerda telefon so'rash xatosi tuzatildi

class TreePlanting(StatesGroup):
    photo = State()
    location = State()
