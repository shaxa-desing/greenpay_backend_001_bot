from aiogram.fsm.state import StatesGroup, State

class UserRegister(StatesGroup):
    name = State()
    phone = State()

class TreePlanting(StatesGroup):
    category = State() # Mevali / Manzarali
    name = State()     # Olma, Gilos / Archa...
    photo = State()
    location = State()

class CardUpdate(StatesGroup):
    card_number = State()
    phone_number = State()
